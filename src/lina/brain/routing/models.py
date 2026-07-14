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
    CAMERA_OPEN = "camera_open"
    CAMERA_ANALYZE = "camera_analyze"
    CAMERA_MONITOR = "camera_monitor"
    SCREEN_MONITOR = "screen_monitor"
    REGION_MONITOR = "region_monitor"
    LIVE_VISION_PAUSE = "live_vision_pause"
    LIVE_VISION_RESUME = "live_vision_resume"
    LIVE_VISION_STOP = "live_vision_stop"
    LIVE_VISION_STATUS = "live_vision_status"
    READ_FILE = "read_file"
    MEMORY_STORE = "memory_store"
    MEMORY_RECALL = "memory_recall"
    UNSUPPORTED = "unsupported"
    UNSAFE = "unsafe"
    CANCEL = "cancel"


class ToolStatus(str, Enum):
    PREPARING = "preparing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class ToolErrorCategory(str, Enum):
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PERSISTENCE_ERROR = "persistence_error"
    EXECUTION_ERROR = "execution_error"
    STALE_REQUEST = "stale_request"
    UNSUPPORTED = "unsupported"


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
    duration_ms: int | None = None
    retryable: bool = False


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
