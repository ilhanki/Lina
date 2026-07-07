"""Conversation service for Lina."""

from lina.brain.brain import Brain
from lina.brain.intent_analyzer import IntentAnalyzer
from lina.brain.model_provider import ModelResponse
from lina.brain.prompt_builder import ConversationTurn
from lina.services.deterministic_response_service import DeterministicResponseService


class ConversationService:
    """Coordinates user messages with the Brain."""

    def __init__(
        self,
        brain: Brain,
        intent_analyzer: IntentAnalyzer | None = None,
        deterministic_response_service: DeterministicResponseService | None = None,
        history_limit: int = 6,
    ) -> None:
        self._brain = brain
        self._intent_analyzer = intent_analyzer or IntentAnalyzer()
        self._deterministic_response_service = (
            deterministic_response_service or DeterministicResponseService()
        )
        self._history_limit = history_limit
        self._history: list[ConversationTurn] = []

    def handle_message(self, user_message: str) -> ModelResponse:
        intent = self._intent_analyzer.analyze(user_message)

        if self._deterministic_response_service.can_handle(intent):
            response = self._deterministic_response_service.handle(intent)
        else:
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
