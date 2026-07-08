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
    PROJECT_STATUS = "project_status"
    PROJECT_SUMMARY = "project_summary"
    CASUAL_GREETING = "casual_greeting"
    COMPUTER_CONTROL_STATUS = "computer_control_status"
    MEMORY_REMEMBER = "memory_remember"
    MEMORY_RECALL = "memory_recall"
    MEMORY_FORGET = "memory_forget"
    MEMORY_CLEAR = "memory_clear"
    MEMORY_LIST = "memory_list"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Intent:
    """Represents the analyzed intent of a user message."""

    type: IntentType
