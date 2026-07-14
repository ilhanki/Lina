"""Typed models shared by the voice layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VoiceState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    WAKE_LISTENING = "wake_listening"
    WAKE_DETECTED = "wake_detected"
    COMMAND_LISTENING = "command_listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    COOLDOWN = "cooldown"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class VoiceSettings:
    enabled: bool = False
    responses_enabled: bool = False
    voice_id: str | None = None
    rate: float = 1.0
    volume: float = 1.0
    barge_in_enabled: bool = True
    hands_free_enabled: bool = False
    wake_word_enabled: bool = False
    wake_phrase: str = "Hey Lina"
    return_to_wake_listening: bool = True
    voice_confirmation_enabled: bool = True
    microphone_device_id: int | None = None
    cooldown_seconds: float = 1.5

    def __post_init__(self) -> None:
        if not 0.5 <= self.rate <= 2.0:
            raise ValueError("Speech rate must be between 0.5 and 2.0")
        if not 0.0 <= self.volume <= 1.0:
            raise ValueError("Speech volume must be between 0.0 and 1.0")
        if not 1.0 <= self.cooldown_seconds <= 3.0:
            raise ValueError("Wake cooldown must be between one and three seconds")


@dataclass(frozen=True, slots=True)
class SystemVoice:
    id: str
    name: str
    language: str | None = None


@dataclass(frozen=True, slots=True)
class VoicePlaybackResult:
    completed: bool
    cancelled: bool = False
    error_message: str | None = None


class VoiceError(RuntimeError):
    """Base error exposed by the voice layer without engine details."""


class VoiceUnavailableError(VoiceError):
    """Raised when local TTS is not available."""


class VoicePlaybackError(VoiceError):
    """Raised when local playback fails."""
