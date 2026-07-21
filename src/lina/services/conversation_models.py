"""Application request and result models for conversation use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from lina.brain.model_provider import ModelResponse
from lina.files.models import DocumentAttachment
from lina.vision.models import ImageAttachment


@dataclass(frozen=True, slots=True)
class ConversationInput:
    """Text input with at most one optional image attachment."""

    text: str
    image_attachment: ImageAttachment | None = None
    document_attachment: DocumentAttachment | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.image_attachment is not None and self.document_attachment is not None:
            raise ValueError("A request can contain either an image or a document, not both")


@dataclass(frozen=True, slots=True)
class ConversationResult:
    """Conversation response and attachment lifecycle decision."""

    response: ModelResponse
    attachment_consumed: bool = False
    assistant_created_at: datetime | None = None
    quality_rejected: bool = False
    response_safe_for_speech: bool = True
