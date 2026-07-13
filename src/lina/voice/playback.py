"""Single-playback, cancellable audio execution service."""

from __future__ import annotations

from collections.abc import Callable
import logging
import threading

from lina.voice.models import VoicePlaybackResult
from lina.voice.tts_provider import TextToSpeechProvider


PlaybackCallback = Callable[[int, VoicePlaybackResult], None]
_logger = logging.getLogger("lina.voice")


class AudioPlaybackService:
    def __init__(self, provider: TextToSpeechProvider) -> None:
        self._provider = provider
        self._lock = threading.RLock()
        self._generation = 0
        self._active = False
        self._shutdown = False

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._active

    @property
    def is_available(self) -> bool:
        return self._provider.is_available()

    def list_voices(self):
        return self._provider.list_voices()

    def play(
        self,
        text: str,
        voice_id: str | None,
        rate: float,
        volume: float,
        callback: PlaybackCallback | None = None,
    ) -> int:
        with self._lock:
            if self._shutdown:
                raise RuntimeError("Audio playback service is shut down")
            self.stop()
            self._generation += 1
            generation = self._generation
            self._active = True
        thread = threading.Thread(
            target=self._run,
            args=(generation, text, voice_id, rate, volume, callback),
            name="lina-tts-playback",
            daemon=True,
        )
        thread.start()
        return generation

    def _run(self, generation: int, text: str, voice_id: str | None, rate: float, volume: float, callback: PlaybackCallback | None) -> None:
        try:
            self._provider.speak(text, voice_id, rate, volume)
            result = VoicePlaybackResult(completed=True)
        except Exception as error:
            _logger.warning(
                "tts_failed error_category=%s",
                _safe_error_category(error),
            )
            result = VoicePlaybackResult(completed=False, error_message="Sesli yanıt oluşturulamadı.")
        with self._lock:
            current = generation == self._generation and not self._shutdown
            if current:
                self._active = False
        if current and callback is not None:
            callback(generation, result)

    def stop(self) -> bool:
        with self._lock:
            was_active = self._active
            self._generation += 1
            self._active = False
        if was_active:
            self._provider.stop()
        return was_active

    def shutdown(self) -> None:
        with self._lock:
            self._shutdown = True
        self.stop()


def _safe_error_category(error: Exception) -> str:
    name = error.__class__.__name__.casefold()
    if "unavailable" in name:
        return "unavailable"
    if "timeout" in name or "timed out" in str(error).casefold():
        return "timeout"
    if "playback" in name:
        return "playback"
    return "synthesis"
