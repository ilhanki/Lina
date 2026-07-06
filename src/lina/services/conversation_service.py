"""Conversation service for Lina."""

from lina.brain.brain import Brain
from lina.brain.model_provider import ModelResponse


class ConversationService:
    """Coordinates user messages with the Brain."""

    def __init__(self, brain: Brain) -> None:
        self._brain = brain

    def handle_message(self, user_message: str) -> ModelResponse:
        return self._brain.respond(user_message)

