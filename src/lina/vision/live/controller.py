"""Bounded, latest-frame-wins live vision controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
import logging
import threading
import time

from lina.vision.live.change_detector import FrameChangeDetector
from lina.vision.live.frame_source import FrameSource
from lina.vision.live.models import LiveVisionError, LiveVisionFrame, LiveVisionMetrics, LiveVisionSession, LiveVisionSnapshot, LiveVisionState
from lina.vision.live.policy import build_analysis_prompt, speech_summary


Analyzer = Callable[[LiveVisionFrame, str], str]
Listener = Callable[[LiveVisionSnapshot], None]
_logger = logging.getLogger("lina.live_vision")


class LiveVisionController:
    """Own one live session and at most one active plus one pending frame."""

    def __init__(self, analyzer: Analyzer, *, speaker: Callable[[str], bool] | None = None, cancel_analysis: Callable[[], None] | None = None, clock: Callable[[], float] = time.monotonic) -> None:
        self._analyzer = analyzer
        self._speaker = speaker
        self._cancel_analysis = cancel_analysis
        self._clock = clock
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._stop_event = threading.Event()
        self._source: FrameSource | None = None
        self._session: LiveVisionSession | None = None
        self._detector = FrameChangeDetector()
        self._snapshot = LiveVisionSnapshot(LiveVisionState.IDLE)
        self._listeners: list[Listener] = []
        self._capture_thread: threading.Thread | None = None
        self._analysis_thread: threading.Thread | None = None
        self._pending: LiveVisionFrame | None = None
        self._analysis_active = False
        self._generation = 0
        self._last_analysis_clock = float("-inf")
        self._last_spoken = ""
        self._last_spoken_at = float("-inf")
        self._durations: list[int] = []
        self._single_shot = False

    @property
    def snapshot(self) -> LiveVisionSnapshot:
        with self._lock:
            return self._with_duration(self._snapshot)

    def subscribe(self, listener: Listener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def start(self, source: FrameSource, session: LiveVisionSession, *, analyze_immediately: bool = False, single_shot: bool = False) -> str:
        self.stop()
        if session.source is not source.source:
            raise ValueError("Session source does not match frame source")
        with self._lock:
            self._generation += 1
            generation = self._generation
            self._session = session
            self._source = source
            self._stop_event.clear()
            self._wake.clear()
            self._pending = None
            self._detector = FrameChangeDetector(session.config.sensitivity)
            self._last_analysis_clock = float("-inf")
            self._durations.clear()
            self._single_shot = single_shot
            self._snapshot = LiveVisionSnapshot(LiveVisionState.STARTING, session.source, source.label, session.session_id, metrics=LiveVisionMetrics(source=session.source))
        self._emit()
        try:
            source.start()
        except LiveVisionError as error:
            self._set_state(LiveVisionState.UNAVAILABLE, str(error))
            self._release_source()
            raise
        self._set_state(LiveVisionState.MONITORING)
        self._analysis_thread = threading.Thread(target=self._analysis_loop, args=(generation,), name="lina-live-vision-analysis", daemon=True)
        self._capture_thread = threading.Thread(target=self._capture_loop, args=(generation, analyze_immediately), name="lina-live-vision-capture", daemon=True)
        self._analysis_thread.start()
        self._capture_thread.start()
        return session.session_id

    def analyze_once(self, source: FrameSource, session: LiveVisionSession) -> str:
        self.start(source, session, analyze_immediately=True, single_shot=True)
        return session.session_id

    def analyze_now(self) -> bool:
        with self._lock:
            source, session = self._source, self._session
            current = self._snapshot.state
        if source is None or session is None or current in {LiveVisionState.IDLE, LiveVisionState.STOPPING, LiveVisionState.UNAVAILABLE}:
            return False
        try:
            frame = source.capture()
        except LiveVisionError as error:
            self._set_state(LiveVisionState.ERROR, str(error))
            return False
        self._record_capture()
        self._queue(frame, force=True)
        return True

    def pause(self) -> bool:
        with self._lock:
            if self._snapshot.state not in {LiveVisionState.MONITORING, LiveVisionState.CHANGE_DETECTED}:
                return False
            self._snapshot = replace(self._snapshot, state=LiveVisionState.PAUSED, user_message="Canlı takip duraklatıldı.")
        self._emit(); return True

    def resume(self) -> bool:
        with self._lock:
            if self._snapshot.state is not LiveVisionState.PAUSED:
                return False
            self._snapshot = replace(self._snapshot, state=LiveVisionState.MONITORING, user_message="Canlı takip devam ediyor.")
        self._emit(); return True

    def stop(self) -> bool:
        with self._lock:
            active = self._source is not None or self._session is not None
            if not active:
                return False
            self._generation += 1
            self._snapshot = replace(self._snapshot, state=LiveVisionState.STOPPING, user_message="Canlı takip durduruldu.")
            self._stop_event.set(); self._pending = None; self._wake.set()
            capture, analysis = self._capture_thread, self._analysis_thread
        self._emit(); self._release_source()
        if self._cancel_analysis is not None:
            try: self._cancel_analysis()
            except Exception: pass
        current = threading.current_thread()
        for worker in (capture, analysis):
            if worker and worker is not current:
                worker.join(timeout=2.0)
        with self._lock:
            self._source = None; self._session = None; self._pending = None
            self._capture_thread = None; self._analysis_thread = None; self._analysis_active = False
            previous = self._with_duration(self._snapshot)
            self._snapshot = LiveVisionSnapshot(
                LiveVisionState.IDLE, previous.source, previous.source_label,
                last_analysis_at=previous.last_analysis_at, last_result=previous.last_result,
                user_message="Canlı takip durduruldu.", metrics=previous.metrics,
            )
        self._emit(); return True

    def shutdown(self) -> None:
        self.stop()
        self._listeners.clear()

    def _capture_loop(self, generation: int, analyze_immediately: bool) -> None:
        first = True
        while self._is_current(generation):
            with self._lock:
                session, source, state = self._session, self._source, self._snapshot.state
            if session is None or source is None:
                return
            if session.config.duration_seconds is not None and self._clock() - self._session_start_clock >= session.config.duration_seconds:
                self.stop(); return
            if state is LiveVisionState.PAUSED:
                self._stop_event.wait(min(0.2, session.config.capture_interval_seconds)); continue
            try:
                frame = source.capture()
                self._record_capture()
                changed = self._detector.observe(frame)
                if first and analyze_immediately:
                    self._queue(frame, force=True)
                elif changed:
                    self._record_change(); self._queue(frame)
                first = False
            except LiveVisionError as error:
                self._set_state(LiveVisionState.ERROR, str(error)); return
            if self._stop_event.wait(session.config.capture_interval_seconds):
                return

    @property
    def _session_start_clock(self) -> float:
        with self._lock:
            session = self._session
        if session is None:
            return self._clock()
        elapsed_wall = (datetime.now(timezone.utc) - session.started_at).total_seconds()
        return self._clock() - max(0, elapsed_wall)

    def _queue(self, frame: LiveVisionFrame, force: bool = False) -> None:
        with self._lock:
            session = self._session
            if session is None:
                return
            if not force and self._clock() - self._last_analysis_clock < session.config.minimum_analysis_interval_seconds:
                self._increment_metric("dropped_frame_count"); return
            if self._pending is not None:
                self._increment_metric("dropped_frame_count")
            self._pending = frame
            self._snapshot = replace(self._snapshot, state=LiveVisionState.CHANGE_DETECTED)
            self._wake.set()
        self._emit()

    def _analysis_loop(self, generation: int) -> None:
        while self._is_current(generation):
            self._wake.wait(0.25)
            if not self._is_current(generation): return
            with self._lock:
                frame, session = self._pending, self._session
                self._pending = None; self._wake.clear()
                if frame is None or session is None: continue
                self._analysis_active = True; self._snapshot = replace(self._snapshot, state=LiveVisionState.ANALYZING)
                self._increment_metric("analysis_request_count")
            self._emit(); started = self._clock()
            try:
                result = self._analyzer(frame, build_analysis_prompt(session.source, session.user_focus))
            except Exception:
                with self._lock: self._analysis_active = False
                if self._is_current(generation): self._set_state(LiveVisionState.ERROR, "Vision modeli şu anda kullanılamıyor.")
                continue
            duration = round((self._clock() - started) * 1000)
            with self._lock:
                self._analysis_active = False
                if not self._is_current(generation): continue
                self._last_analysis_clock = self._clock(); self._durations.append(duration)
                metrics = replace(self._snapshot.metrics, last_analysis_latency_ms=duration, average_analysis_duration_ms=round(sum(self._durations) / len(self._durations)))
                self._snapshot = replace(self._snapshot, state=LiveVisionState.MONITORING, last_analysis_at=datetime.now(timezone.utc), last_result=str(result).strip(), metrics=metrics)
            self._emit(); self._speak_if_needed(str(result).strip(), session)
            if self._single_shot and self._is_current(generation):
                self.stop()
                return

    def _speak_if_needed(self, result: str, session: LiveVisionSession) -> None:
        if not self._speaker or not session.config.voice_feedback_enabled or not result: return
        now = self._clock(); normalized = result.casefold()
        if normalized == self._last_spoken and now - self._last_spoken_at < session.config.repeat_speech_cooldown_seconds: return
        self._last_spoken, self._last_spoken_at = normalized, now
        try: self._speaker(speech_summary(result))
        except Exception: return

    def _record_capture(self) -> None: self._increment_metric("captured_frame_count")
    def _record_change(self) -> None: self._increment_metric("meaningful_change_count")

    def _increment_metric(self, field: str) -> None:
        metrics = self._snapshot.metrics
        self._snapshot = replace(self._snapshot, metrics=replace(metrics, **{field: getattr(metrics, field) + 1}))

    def _set_state(self, state: LiveVisionState, message: str = "") -> None:
        with self._lock: self._snapshot = replace(self._snapshot, state=state, user_message=message)
        self._emit()

    def _release_source(self) -> None:
        with self._lock: source = self._source
        if source:
            try: source.stop()
            except Exception: pass

    def _is_current(self, generation: int) -> bool:
        with self._lock: return generation == self._generation and not self._stop_event.is_set()

    def _with_duration(self, snapshot: LiveVisionSnapshot) -> LiveVisionSnapshot:
        with self._lock: session = self._session
        seconds = max(0.0, (datetime.now(timezone.utc) - session.started_at).total_seconds()) if session else snapshot.metrics.session_duration_seconds
        return replace(snapshot, metrics=replace(snapshot.metrics, session_duration_seconds=round(seconds, 1)))

    def _emit(self) -> None:
        snapshot = self.snapshot
        for listener in tuple(self._listeners):
            try: listener(snapshot)
            except Exception: continue
