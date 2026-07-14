"""Bounded, latest-frame-wins live vision controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from difflib import SequenceMatcher
import logging
import threading
import time

from lina.vision.live.change_detector import FrameChangeDetector
from lina.vision.live.frame_source import FrameSource
from lina.vision.live.models import (
    CameraConversationContext, CameraConversationState, ChangeRegionsEvent, LiveVisionError, LiveVisionFrame, LiveVisionMetrics,
    LiveVisionSession, LiveVisionSnapshot, LiveVisionSource, LiveVisionState,
    OverlayGeometry, OverlayGeometryEvent, PreviewFrameEvent, SessionStoppedEvent,
)
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
        self._preview_listeners: list[Callable[[PreviewFrameEvent], None]] = []
        self._change_region_listeners: list[Callable[[ChangeRegionsEvent], None]] = []
        self._overlay_geometry_listeners: list[Callable[[OverlayGeometryEvent], None]] = []
        self._stopped_listeners: list[Callable[[SessionStoppedEvent], None]] = []
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
        self._latest_frame: LiveVisionFrame | None = None
        self._last_user_question = ""

    @property
    def snapshot(self) -> LiveVisionSnapshot:
        with self._lock:
            return self._with_duration(self._snapshot)

    @property
    def camera_context(self) -> CameraConversationContext:
        with self._lock:
            session_id = self._session.session_id if self._session is not None else ""
            return CameraConversationContext(
                session_id=session_id,
                state=self._camera_state(self._snapshot.state),
                latest_frame=self._latest_frame,
                latest_semantic_summary=self._snapshot.last_result,
                latest_spoken_summary=self._last_spoken,
                last_analysis_at=self._snapshot.last_analysis_at,
                last_user_question=self._last_user_question,
            )

    def subscribe(self, listener: Listener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def subscribe_preview_frame(self, listener: Callable[[PreviewFrameEvent], None]) -> None:
        if listener not in self._preview_listeners:
            self._preview_listeners.append(listener)

    def subscribe_change_regions(self, listener: Callable[[ChangeRegionsEvent], None]) -> None:
        if listener not in self._change_region_listeners:
            self._change_region_listeners.append(listener)

    def subscribe_overlay_geometry(self, listener: Callable[[OverlayGeometryEvent], None]) -> None:
        if listener not in self._overlay_geometry_listeners:
            self._overlay_geometry_listeners.append(listener)

    def subscribe_session_stopped(self, listener: Callable[[SessionStoppedEvent], None]) -> None:
        if listener not in self._stopped_listeners:
            self._stopped_listeners.append(listener)

    def update_overlay_geometry(self, geometry: OverlayGeometry) -> bool:
        with self._lock:
            session = self._session
            generation = self._generation
        if session is None or session.source not in {LiveVisionSource.SCREEN, LiveVisionSource.REGION}:
            return False
        self._notify(
            self._overlay_geometry_listeners,
            OverlayGeometryEvent(session.session_id, generation, geometry),
        )
        return True

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
            self._latest_frame = None
            self._last_user_question = ""
            self._last_spoken = ""
            self._last_spoken_at = float("-inf")
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
            self.stop()
            return False
        self._record_capture()
        with self._lock: self._latest_frame = frame
        with self._lock:
            generation = self._generation
        self._emit_preview(frame, generation, session.session_id)
        self._queue(frame, force=True)
        return True

    def capture_current_frame(self, question: str = "") -> LiveVisionFrame | None:
        """Capture one ephemeral camera frame for a user question."""
        with self._lock:
            source, session, state = self._source, self._session, self._snapshot.state
            generation = self._generation
        if (
            source is None or session is None or session.source is not LiveVisionSource.CAMERA
            or state in {LiveVisionState.IDLE, LiveVisionState.PAUSED, LiveVisionState.STOPPING, LiveVisionState.UNAVAILABLE}
        ):
            return None
        try:
            frame = source.capture()
        except LiveVisionError:
            return None
        self._record_capture()
        with self._lock:
            self._latest_frame = frame
            self._last_user_question = " ".join(question.split())[:500]
        self._emit_preview(frame, generation, session.session_id)
        return frame

    def set_automatic_commentary(self, enabled: bool) -> bool:
        with self._lock:
            if self._session is None or self._session.source is not LiveVisionSource.CAMERA:
                return False
            self._session = replace(
                self._session,
                config=replace(self._session.config, automatic_commentary_enabled=enabled),
            )
        return True

    def set_commentary_muted(self, muted: bool) -> bool:
        with self._lock:
            if self._session is None or self._session.source is not LiveVisionSource.CAMERA:
                return False
            self._session = replace(
                self._session,
                config=replace(self._session.config, voice_feedback_enabled=not muted),
            )
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
            stopped_session_id = self._session.session_id if self._session is not None else ""
            stopped_generation = self._generation
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
            self._source = None; self._session = None; self._pending = None; self._latest_frame = None
            self._capture_thread = None; self._analysis_thread = None; self._analysis_active = False
            previous = self._with_duration(self._snapshot)
            self._snapshot = LiveVisionSnapshot(
                LiveVisionState.IDLE, previous.source, previous.source_label,
                last_analysis_at=previous.last_analysis_at, last_result=previous.last_result,
                user_message="Canlı takip durduruldu.", metrics=previous.metrics,
            )
        self._emit()
        if stopped_session_id:
            self._notify(
                self._stopped_listeners,
                SessionStoppedEvent(stopped_session_id, stopped_generation),
            )
        return True

    def shutdown(self) -> None:
        self.stop()
        self._listeners.clear()
        self._preview_listeners.clear()
        self._change_region_listeners.clear()
        self._overlay_geometry_listeners.clear()
        self._stopped_listeners.clear()

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
                with self._lock: self._latest_frame = frame
                self._emit_preview(frame, generation, session.session_id)
                changed = self._detector.observe(frame)
                self._emit_change_regions(generation, session.session_id)
                if first and analyze_immediately:
                    self._queue(frame, force=True)
                elif changed and session.config.automatic_commentary_enabled:
                    self._record_change(); self._queue(frame)
                first = False
            except LiveVisionError as error:
                self._set_state(LiveVisionState.ERROR, str(error))
                self.stop()
                return
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
                with self._lock:
                    previous_result = self._snapshot.last_result
                result = self._analyzer(frame, build_analysis_prompt(session.source, session.user_focus, previous_result))
            except Exception:
                with self._lock: self._analysis_active = False
                if self._is_current(generation):
                    if session.source is LiveVisionSource.CAMERA:
                        with self._lock:
                            self._last_analysis_clock = self._clock()
                        self._set_state(LiveVisionState.MONITORING, "Görüntüyü şu anda yorumlayamıyorum.")
                        continue
                    self._set_state(LiveVisionState.ERROR, "Vision modeli şu anda kullanılamıyor.")
                    self.stop(); return
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
        if _similar_summary(normalized, self._last_spoken) and now - self._last_spoken_at < session.config.repeat_speech_cooldown_seconds: return
        self._last_spoken, self._last_spoken_at = normalized, now
        try: self._speaker(speech_summary(result))
        except Exception: return

    def _record_capture(self) -> None: self._increment_metric("captured_frame_count")
    def _record_change(self) -> None: self._increment_metric("meaningful_change_count")

    def _increment_metric(self, field: str) -> None:
        with self._lock:
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
        self._notify(self._listeners, snapshot)

    def _emit_preview(self, frame: LiveVisionFrame, generation: int, session_id: str) -> None:
        self._notify(
            self._preview_listeners,
            PreviewFrameEvent(session_id, generation, frame),
        )

    def _emit_change_regions(self, generation: int, session_id: str) -> None:
        self._notify(
            self._change_region_listeners,
            ChangeRegionsEvent(
                session_id,
                generation,
                self._detector.last_regions,
                datetime.now(timezone.utc),
            ),
        )

    @staticmethod
    def _notify(listeners: list[Callable], event: object) -> None:
        for listener in tuple(listeners):
            try: listener(event)
            except Exception: continue

    @staticmethod
    def _camera_state(state: LiveVisionState) -> CameraConversationState:
        return {
            LiveVisionState.ANALYZING: CameraConversationState.ANALYZING,
            LiveVisionState.SPEAKING: CameraConversationState.SPEAKING,
            LiveVisionState.PAUSED: CameraConversationState.PAUSED,
            LiveVisionState.ERROR: CameraConversationState.ERROR,
            LiveVisionState.UNAVAILABLE: CameraConversationState.ERROR,
            LiveVisionState.IDLE: CameraConversationState.INACTIVE,
        }.get(state, CameraConversationState.OBSERVING)


def _similar_summary(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right or SequenceMatcher(None, left, right).ratio() >= 0.82:
        return True
    left_words, right_words = set(left.split()), set(right.split())
    union = left_words | right_words
    return bool(union) and len(left_words & right_words) / len(union) >= 0.8
