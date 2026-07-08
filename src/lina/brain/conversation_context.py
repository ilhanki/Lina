"""Conversation context models for Lina's Brain."""

from dataclasses import dataclass
from typing import Sequence

from lina.brain.prompt_builder import ConversationTurn


@dataclass(frozen=True)
class ConversationContext:
    """Runtime context prepared for a single user message."""

    user_message: str
    conversation_history: Sequence[ConversationTurn]
    project_context: str | None = None
    memory_context: str | None = None
    system_notes: str | None = None
