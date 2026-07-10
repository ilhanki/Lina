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


@dataclass(frozen=True)
class SpeechSynthesisResult:
    """Outcome of a speech synthesis request."""

    success: bool
    message: str | None = None


class SpeechServiceError(Exception):
    """Raised when a controlled speech operation cannot be completed."""
