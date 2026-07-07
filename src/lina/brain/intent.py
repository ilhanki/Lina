"""Intent models for Lina's Brain."""

from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """Supported high-level user intent types."""

    CHAT = "chat"
    HELP = "help"
    IDENTITY = "identity"
    CAPABILITIES = "capabilities"
    CURRENT_TIME = "current_time"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Intent:
    """Represents the analyzed intent of a user message."""

    type: IntentType
