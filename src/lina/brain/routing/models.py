"""Framework-neutral intent and tool result models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class IntentType(str, Enum):
    CHAT = "chat"
    CREATE_REMINDER = "create_reminder"
    LIST_REMINDERS = "list_reminders"
    ANALYZE_SCREEN = "analyze_screen"
    ANALYZE_REGION = "analyze_region"
    ANALYZE_IMAGE = "analyze_image"
    READ_FILE = "read_file"
    MEMORY_STORE = "memory_store"
    MEMORY_RECALL = "memory_recall"
    UNSUPPORTED = "unsupported"
    UNSAFE = "unsafe"


@dataclass(frozen=True, slots=True)
class IntentRequest:
    intent: IntentType
    confidence: float
    original_text: str
    extracted_arguments: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    source: str = "deterministic"
    intent_id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True, slots=True)
class ToolResult:
    success: bool
    user_message: str
    data: Any = None
    error_code: str | None = None
    requires_follow_up: bool = False


@dataclass(frozen=True, slots=True)
class PendingIntent:
    request: IntentRequest
    conversation_id: int | None
    missing_fields: tuple[str, ...]
    created_at: datetime
    generation_id: int


@dataclass(frozen=True, slots=True)
class RequestContext:
    conversation_id: int | None
    message_id: int | None = None
    generation_id: int = 0
    confirmed: bool = False
