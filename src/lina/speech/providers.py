"""Provider contracts and safe defaults for speech engines."""

from typing import Protocol

from lina.speech.models import (
    SpeechServiceError,
    SpeechSynthesisResult,
    SpeechTranscriptionResult,
)


class STTProvider(Protocol):
    """Contract for a single-request speech-to-text engine."""

    def is_available(self) -> bool:
        """Return whether the provider can currently transcribe speech."""

    def transcribe_once(self) -> SpeechTranscriptionResult:
        """Transcribe one explicit user-initiated speech request."""


class TTSProvider(Protocol):
    """Contract for a text-to-speech engine."""

    def is_available(self) -> bool:
        """Return whether the provider can currently synthesize speech."""

    def speak(self, text: str) -> SpeechSynthesisResult:
        """Synthesize the supplied text."""

    def stop(self) -> None:
        """Stop active speech synthesis, if any."""


class NoOpSTTProvider:
    """Safe default used when no speech-to-text engine is configured."""

    def is_available(self) -> bool:
        return False

    def transcribe_once(self) -> SpeechTranscriptionResult:
        raise SpeechServiceError("Speech-to-text provider is unavailable")


class NoOpTTSProvider:
    """Safe default used when no text-to-speech engine is configured."""

    def is_available(self) -> bool:
        return False

    def speak(self, text: str) -> SpeechSynthesisResult:
        return SpeechSynthesisResult(
            success=False,
            message="Text-to-speech provider is unavailable",
        )

    def stop(self) -> None:
        return None
