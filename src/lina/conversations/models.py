"""Framework-neutral models for persisted conversations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


VALID_ROLES = frozenset({"user", "assistant", "system"})
VALID_IMAGE_SOURCES = frozenset(
    {"screen_full", "screen_region", "local_image"}
)
CONVERSATION_VIEWS = frozenset({"chats", "pinned", "archive"})


@dataclass(frozen=True, slots=True)
class ConversationSession:
    """A persisted conversation session."""

    id: int | None
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None
    is_pinned: bool = False
    is_archived: bool = False
    pinned_at: datetime | None = None
    archived_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ConversationSearchResult:
    """Safe plain-text search result for the presentation layer."""

    conversation_id: int
    title: str
    snippet: str
    matched_at: datetime
    matched_role: str | None
    match_type: str
    last_activity_at: datetime


@dataclass(frozen=True, slots=True)
class PersistedMessage:
    """A text-only persisted message with safe visual metadata."""

    id: int | None
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    sequence: int
    message_type: str = "text"
    had_image: bool = False
    image_source: str | None = None
    model_name: str | None = None

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError(f"Unsupported conversation role: {self.role}")
        if not self.content.strip():
            raise ValueError("Persisted message content must not be empty")
        if self.sequence < 1:
            raise ValueError("Persisted message sequence must be positive")
        if self.image_source is not None and self.image_source not in VALID_IMAGE_SOURCES:
            raise ValueError(f"Unsupported image source: {self.image_source}")
        if self.image_source is not None and not self.had_image:
            raise ValueError("Image source requires had_image=True")
