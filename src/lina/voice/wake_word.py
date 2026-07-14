"""Opt-in, local wake-word contracts and conservative phrase matching."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import logging
import re
import threading
import unicodedata

from lina.speech.models import AudioRecordingResult
from lina.speech.providers import STTProvider


WakeDetectedCallback = Callable[[], None]
WakeUtteranceSource = Callable[[threading.Event], Iterable[AudioRecordingResult]]
_logger = logging.getLogger("lina.voice")


class WakeWordDetector:
    """Framework-neutral detector interface used by the voice controller."""

    def is_available(self) -> bool:
        raise NotImplementedError

    def is_running(self) -> bool:
        raise NotImplementedError

    def start(self, callback: WakeDetectedCallback | None = None) -> bool:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def set_phrase(self, phrase: str) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        raise NotImplementedError


class STTWakeWordDetector(WakeWordDetector):
    """Run local STT only for energy-gated utterances supplied by the audio source."""

    def __init__(
        self,
        stt_provider: STTProvider,
        utterance_source: WakeUtteranceSource,
        phrase: str = "Hey Lina",
        on_detected: WakeDetectedCallback | None = None,
    ) -> None:
        self._stt_provider = stt_provider
        self._utterance_source = utterance_source
        self._phrase = validate_wake_phrase(phrase)
        self._on_detected = on_detected
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._shutdown = False

    def is_available(self) -> bool:
        return not self._shutdown and self._stt_provider.is_available()

    def is_running(self) -> bool:
        with self._lock:
            return bool(self._thread and self._thread.is_alive())

    def set_phrase(self, phrase: str) -> None:
        normalized = validate_wake_phrase(phrase)
        with self._lock:
            self._phrase = normalized

    def start(self, callback: WakeDetectedCallback | None = None) -> bool:
        with self._lock:
            if self._shutdown or not self.is_available():
                return False
            if callback is not None:
                self._on_detected = callback
            if self._thread and self._thread.is_alive():
                return True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, name="lina-wake-word", daemon=True)
            self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        with self._lock:
            if self._thread is thread and (thread is None or not thread.is_alive()):
                self._thread = None

    def shutdown(self) -> None:
        self._shutdown = True
        self.stop()
        self._on_detected = None

    def _run(self) -> None:
        try:
            for recording in self._utterance_source(self._stop_event):
                if self._stop_event.is_set():
                    return
                try:
                    result = self._stt_provider.transcribe(recording)
                except Exception:
                    _logger.warning("wake_detection_failed error_category=transcription")
                    continue
                with self._lock:
                    phrase = self._phrase
                    callback = self._on_detected
                if wake_phrase_matches(result.text, phrase):
                    _logger.info("wake_detected")
                    if callback is not None:
                        try:
                            callback()
                        except Exception:
                            _logger.warning("wake_detection_failed error_category=callback")
        except Exception:
            _logger.warning("wake_detection_failed error_category=audio_input")


class UnavailableWakeWordDetector(WakeWordDetector):
    def __init__(self, phrase: str = "Hey Lina") -> None:
        self._phrase = validate_wake_phrase(phrase)

    def is_available(self) -> bool:
        return False

    def is_running(self) -> bool:
        return False

    def start(self, callback: WakeDetectedCallback | None = None) -> bool:
        return False

    def stop(self) -> None:
        return None

    def set_phrase(self, phrase: str) -> None:
        self._phrase = validate_wake_phrase(phrase)

    def shutdown(self) -> None:
        return None


def normalize_wake_phrase(value: str) -> str:
    """Normalize casing and punctuation without introducing fuzzy matching."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def validate_wake_phrase(value: str) -> str:
    normalized = normalize_wake_phrase(value)
    if not 2 <= len(normalized) <= 40 or len(normalized.split()) not in {2, 3}:
        raise ValueError("Wake phrase must contain two or three short words")
    return normalized


def wake_phrase_matches(transcription: str, phrase: str = "Hey Lina") -> bool:
    """Match the configured phrase and the explicit Turkish 'he lina' variant."""
    candidate = normalize_wake_phrase(transcription)
    expected = validate_wake_phrase(phrase)
    accepted = {expected}
    if expected == "hey lina":
        accepted.add("he lina")
    return candidate in accepted
