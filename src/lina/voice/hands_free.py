"""Hands-free wake, command transcription and automatic-send coordination."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
import threading
import time

from lina.speech.models import SpeechNoInputError, SpeechServiceError, SpeechTranscriptionResult
from lina.speech.service import SpeechService
from lina.voice.controller import VoiceController


CommandCallback = Callable[[str], None]
FeedbackCallback = Callable[[str], None]
_logger = logging.getLogger("lina.voice")


@dataclass(frozen=True, slots=True)
class HandsFreeMetrics:
    wake_detection_count: int = 0
    false_wake_cancel_count: int = 0


class HandsFreeConversationService:
    """Run one post-wake command at a time without depending on Qt."""

    def __init__(self, voice: VoiceController, speech: SpeechService) -> None:
        self._voice = voice
        self._speech = speech
        self._command_callback: CommandCallback | None = None
        self._feedback_callback: FeedbackCallback | None = None
        self._lock = threading.RLock()
        self._worker: threading.Thread | None = None
        self._shutdown = False
        self._generation = 0
        self._wake_detection_count = 0
        self._false_wake_cancel_count = 0
        self._last_wake_at: float | None = None
        self._voice.subscribe_wake_detected(self._wake_detected)

    @property
    def is_busy(self) -> bool:
        with self._lock:
            return bool(self._worker and self._worker.is_alive())

    @property
    def metrics(self) -> HandsFreeMetrics:
        return HandsFreeMetrics(self._wake_detection_count, self._false_wake_cancel_count)

    def bind(self, command_callback: CommandCallback, feedback_callback: FeedbackCallback) -> None:
        self._command_callback = command_callback
        self._feedback_callback = feedback_callback

    def pause(self) -> bool:
        self.cancel_active()
        return self._voice.pause_hands_free()

    def resume(self) -> bool:
        return self._voice.resume_hands_free()

    def cancel_active(self) -> None:
        with self._lock:
            self._generation += 1
        self._speech.stop_listening()

    def mark_response_completed(self) -> None:
        if self._last_wake_at is None:
            return
        _logger.info("hands_free_response end_to_end_latency_ms=%d", round((time.monotonic() - self._last_wake_at) * 1000))
        self._last_wake_at = None

    def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        self.cancel_active()
        self._voice.pause_hands_free()
        with self._lock:
            worker = self._worker
        if worker and worker is not threading.current_thread():
            worker.join(timeout=2.0)
        self._command_callback = None
        self._feedback_callback = None

    def _wake_detected(self) -> None:
        with self._lock:
            if self._shutdown or (self._worker and self._worker.is_alive()):
                return
            self._generation += 1
            self._wake_detection_count += 1
            self._last_wake_at = time.monotonic()
            generation = self._generation
            worker = threading.Thread(
                target=self._capture_command,
                args=(generation,),
                name="lina-hands-free-command",
                daemon=True,
            )
            self._worker = worker
        self._feedback("Dinliyorum.")
        self._voice.begin_listening()
        worker.start()

    def _capture_command(self, generation: int) -> None:
        started = time.monotonic()
        try:
            result = self._speech.transcribe_once()
        except SpeechNoInputError:
            if self._is_current(generation):
                self._false_wake_cancel_count += 1
                self._feedback("Bir şey duyamadım.")
                self._voice.finish_interaction()
            return
        except SpeechServiceError:
            if self._is_current(generation):
                _logger.warning("hands_free_failed error_category=transcription")
                self._feedback("Mikrofona erişilemiyor.")
                self._voice.finish_interaction()
            return
        if not self._is_current(generation):
            return
        self._voice.begin_transcribing()
        self._handle_result(result, started)

    def _handle_result(self, result: SpeechTranscriptionResult, started: float) -> None:
        text = " ".join(result.text.split()).strip()
        if not text:
            self._false_wake_cancel_count += 1
            self._feedback("Seni anlayamadım.")
            self._voice.finish_interaction()
            return
        if result.confidence is not None and result.confidence < 0.45:
            self._false_wake_cancel_count += 1
            self._feedback("Tekrar söyler misin?")
            self._voice.finish_interaction()
            return
        _logger.info(
            "hands_free_command command_duration_ms=%s transcription_duration_ms=%d",
            round(result.duration_seconds * 1000) if result.duration_seconds is not None else "not_exposed",
            round((time.monotonic() - started) * 1000),
        )
        self._voice.begin_thinking()
        callback = self._command_callback
        if callback is not None:
            callback(text)
        else:
            self._voice.finish_interaction()

    def _is_current(self, generation: int) -> bool:
        with self._lock:
            return not self._shutdown and generation == self._generation

    def _feedback(self, message: str) -> None:
        callback = self._feedback_callback
        if callback is not None:
            callback(message)
