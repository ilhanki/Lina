"""Speech capability orchestration."""

from collections.abc import Callable
import threading

from lina.speech.audio_recorder import AudioRecorder, NoOpAudioRecorder
from lina.speech.models import (
    SpeechServiceError,
    SpeechState,
    SpeechSynthesisResult,
    SpeechTranscriptionResult,
    SpeechUnavailableError,
)
from lina.speech.providers import STTProvider, TTSProvider


class SpeechService:
    """Coordinate speech providers without owning engine-specific behavior."""

    def __init__(
        self,
        stt_provider: STTProvider,
        tts_provider: TTSProvider,
        audio_recorder: AudioRecorder | None = None,
    ) -> None:
        self._stt_provider = stt_provider
        self._tts_provider = tts_provider
        self._audio_recorder = audio_recorder or NoOpAudioRecorder()
        self._state = SpeechState.IDLE
        self._transcription_lock = threading.Lock()
        self._state_listeners: list[Callable[[SpeechState], None]] = []

    def subscribe_state(self, listener: Callable[[SpeechState], None]) -> None:
        if listener not in self._state_listeners:
            self._state_listeners.append(listener)

    def unsubscribe_state(self, listener: Callable[[SpeechState], None]) -> None:
        if listener in self._state_listeners:
            self._state_listeners.remove(listener)

    def _set_state(self, state: SpeechState) -> None:
        self._state = state
        for listener in tuple(self._state_listeners):
            try:
                listener(state)
            except Exception:
                continue

    def get_state(self) -> SpeechState:
        """Return the current speech state."""
        return self._state

    def is_stt_available(self) -> bool:
        """Return whether speech transcription is available."""
        return (
            self._audio_recorder.is_available()
            and self._stt_provider.is_available()
        )

    def is_tts_available(self) -> bool:
        """Return whether speech synthesis is available."""
        return self._tts_provider.is_available()

    def transcribe_once(self) -> SpeechTranscriptionResult:
        """Run one explicit transcription request without sending its text."""
        if not self._transcription_lock.acquire(blocking=False):
            raise SpeechServiceError("Speech transcription is already active")

        try:
            if not self.is_stt_available():
                self._set_state(SpeechState.UNAVAILABLE)
                raise SpeechUnavailableError("Speech-to-text is unavailable")

            self._set_state(SpeechState.LISTENING)
            recording = self._audio_recorder.record_once()
            self._set_state(SpeechState.TRANSCRIBING)
            result = self._stt_provider.transcribe(recording)
        except SpeechUnavailableError:
            self._set_state(SpeechState.UNAVAILABLE)
            raise
        except SpeechServiceError:
            self._set_state(SpeechState.ERROR)
            self._set_state(SpeechState.IDLE)
            raise
        except Exception as error:
            self._set_state(SpeechState.ERROR)
            self._set_state(SpeechState.IDLE)
            raise SpeechServiceError("Speech transcription failed") from error
        finally:
            self._transcription_lock.release()

        self._set_state(SpeechState.IDLE)
        return result

    def stop_listening(self) -> None:
        """Stop the current explicit recording without starting another one."""
        if self._state is SpeechState.LISTENING:
            self._audio_recorder.stop()

    def speak(self, text: str) -> SpeechSynthesisResult:
        """Speak text when synthesis is available."""
        if not self.is_tts_available():
            self._set_state(SpeechState.UNAVAILABLE)
            return SpeechSynthesisResult(
                success=False,
                message="Text-to-speech provider is unavailable",
            )

        self._set_state(SpeechState.SPEAKING)
        try:
            result = self._tts_provider.speak(text)
        except Exception as error:
            self._set_state(SpeechState.ERROR)
            raise SpeechServiceError("Speech synthesis failed") from error

        self._set_state(SpeechState.IDLE)
        return result

    def stop_speaking(self) -> None:
        """Stop speech synthesis and return to the idle state."""
        try:
            self._tts_provider.stop()
        except Exception as error:
            self._set_state(SpeechState.ERROR)
            raise SpeechServiceError("Could not stop speech synthesis") from error

        self._set_state(SpeechState.IDLE)

    def shutdown(self) -> None:
        """Stop active local speech work and prevent later state callbacks."""
        self.stop_listening()
        try:
            self._tts_provider.stop()
        except Exception:
            pass
        self._state_listeners.clear()
