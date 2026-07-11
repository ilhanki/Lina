"""Application request and result models for conversation use cases."""

from __future__ import annotations

from dataclasses import dataclass

from lina.brain.model_provider import ModelResponse
from lina.vision.models import ImageAttachment


@dataclass(frozen=True, slots=True)
class ConversationInput:
    """Text input with at most one optional image attachment."""

    text: str
    image_attachment: ImageAttachment | None = None


@dataclass(frozen=True, slots=True)
class ConversationResult:
    """Conversation response and attachment lifecycle decision."""

    response: ModelResponse
    attachment_consumed: bool = False
