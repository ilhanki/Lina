"""Conversation service for Lina."""

from lina.brain.brain import Brain
from lina.brain.model_provider import ModelResponse
from lina.brain.prompt_builder import ConversationTurn


class ConversationService:
    """Coordinates user messages with the Brain."""

    def __init__(self, brain: Brain, history_limit: int = 6) -> None:
        self._brain = brain
        self._history_limit = history_limit
        self._history: list[ConversationTurn] = []

    def handle_message(self, user_message: str) -> ModelResponse:
        response = self._brain.respond(
            user_message,
            conversation_history=self._history,
        )
        self._history.append(
            ConversationTurn(
                user_message=user_message,
                assistant_response=response.text,
            )
        )
        self._history = self._history[-self._history_limit :]
        return response
