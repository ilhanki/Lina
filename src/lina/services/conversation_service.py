"""Conversation service for Lina."""

from lina.brain.brain import Brain
from lina.brain.intent import Intent, IntentType
from lina.brain.intent_analyzer import IntentAnalyzer
from lina.brain.model_provider import ModelResponse
from lina.brain.prompt_builder import ConversationTurn
from lina.services.deterministic_response_service import DeterministicResponseService
from lina.services.project_context_service import ProjectContextService


class ConversationService:
    """Coordinates user messages with the Brain."""

    def __init__(
        self,
        brain: Brain,
        intent_analyzer: IntentAnalyzer | None = None,
        deterministic_response_service: DeterministicResponseService | None = None,
        project_context_service: ProjectContextService | None = None,
        history_limit: int = 6,
    ) -> None:
        self._brain = brain
        self._intent_analyzer = intent_analyzer or IntentAnalyzer()
        self._deterministic_response_service = (
            deterministic_response_service or DeterministicResponseService()
        )
        self._project_context_service = project_context_service
        self._history_limit = history_limit
        self._history: list[ConversationTurn] = []

    def handle_message(self, user_message: str) -> ModelResponse:
        intent = self._intent_analyzer.analyze(user_message)

        if self._deterministic_response_service.can_handle(intent):
            response = self._deterministic_response_service.handle(intent)
        elif self._is_project_awareness_intent(intent):
            response = self._brain.respond(
                user_message,
                conversation_history=self._history,
                project_context=self._collect_project_context(),
            )
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

    def _is_project_awareness_intent(self, intent: Intent) -> bool:
        return intent.type in {IntentType.PROJECT_STATUS, IntentType.PROJECT_SUMMARY}

    def _collect_project_context(self) -> str:
        if self._project_context_service is None:
            return "Proje bağlamı şu anda yapılandırılmamış."

        return self._project_context_service.collect_context().text
