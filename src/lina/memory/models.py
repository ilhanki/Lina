"""Memory models for Lina."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """Supported memory categories."""

    USER_PREFERENCE = "user_preference"
    PROJECT_DECISION = "project_decision"
    CONVERSATION_NOTE = "conversation_note"
    SYSTEM_NOTE = "system_note"


@dataclass(frozen=True)
class MemoryRecord:
    """A stored memory item."""

    id: int | None
    type: MemoryType
    content: str
    created_at: datetime
    updated_at: datetime
    source: str
    is_active: bool = True
