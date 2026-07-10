"""Speech capability orchestration."""

from lina.speech.models import (
    SpeechServiceError,
    SpeechState,
    SpeechSynthesisResult,
    SpeechTranscriptionResult,
)
from lina.speech.providers import STTProvider, TTSProvider


class SpeechService:
    """Coordinate speech providers without owning engine-specific behavior."""

    def __init__(self, stt_provider: STTProvider, tts_provider: TTSProvider) -> None:
        self._stt_provider = stt_provider
        self._tts_provider = tts_provider
        self._state = SpeechState.IDLE

    def get_state(self) -> SpeechState:
        """Return the current speech state."""
        return self._state

    def is_stt_available(self) -> bool:
        """Return whether speech transcription is available."""
        return self._stt_provider.is_available()

    def is_tts_available(self) -> bool:
        """Return whether speech synthesis is available."""
        return self._tts_provider.is_available()

    def transcribe_once(self) -> SpeechTranscriptionResult:
        """Run one explicit transcription request without sending its text."""
        if not self.is_stt_available():
            self._state = SpeechState.UNAVAILABLE
            raise SpeechServiceError("Speech-to-text provider is unavailable")

        self._state = SpeechState.TRANSCRIBING
        try:
            result = self._stt_provider.transcribe_once()
        except SpeechServiceError:
            self._state = SpeechState.ERROR
            raise
        except Exception as error:
            self._state = SpeechState.ERROR
            raise SpeechServiceError("Speech transcription failed") from error

        self._state = SpeechState.IDLE
        return result

    def speak(self, text: str) -> SpeechSynthesisResult:
        """Speak text when synthesis is available."""
        if not self.is_tts_available():
            self._state = SpeechState.UNAVAILABLE
            return SpeechSynthesisResult(
                success=False,
                message="Text-to-speech provider is unavailable",
            )

        self._state = SpeechState.SPEAKING
        try:
            result = self._tts_provider.speak(text)
        except Exception as error:
            self._state = SpeechState.ERROR
            raise SpeechServiceError("Speech synthesis failed") from error

        self._state = SpeechState.IDLE
        return result

    def stop_speaking(self) -> None:
        """Stop speech synthesis and return to the idle state."""
        try:
            self._tts_provider.stop()
        except Exception as error:
            self._state = SpeechState.ERROR
            raise SpeechServiceError("Could not stop speech synthesis") from error

        self._state = SpeechState.IDLE
