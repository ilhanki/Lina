"""Models shared by Lina speech services and providers."""

from dataclasses import dataclass
from enum import Enum, auto


class SpeechState(Enum):
    """Current state of the speech capability."""

    IDLE = auto()
    LISTENING = auto()
    TRANSCRIBING = auto()
    SPEAKING = auto()
    ERROR = auto()
    UNAVAILABLE = auto()


@dataclass(frozen=True)
class SpeechTranscriptionResult:
    """Text produced by a single speech transcription request."""

    text: str
    confidence: float | None
    source: str
    is_final: bool
    language: str | None = None
    duration_seconds: float | None = None


@dataclass(frozen=True)
class AudioRecordingResult:
    """In-memory audio captured by an explicit recording request."""

    audio_data: bytes
    sample_rate: int
    channels: int
    duration_seconds: float


@dataclass(frozen=True)
class SpeechSynthesisResult:
    """Outcome of a speech synthesis request."""

    success: bool
    message: str | None = None


class SpeechServiceError(Exception):
    """Raised when a controlled speech operation cannot be completed."""


class SpeechUnavailableError(SpeechServiceError):
    """Raised when a required speech component is unavailable."""


class SpeechRecordingError(SpeechServiceError):
    """Raised when an explicit microphone recording cannot be completed."""


class SpeechTranscriptionError(SpeechServiceError):
    """Raised when recorded audio cannot be transcribed."""
