"""Conversation service for Lina."""

from lina.brain.brain import Brain
from lina.brain.context_manager import ContextManager
from lina.brain.intent import IntentType
from lina.brain.intent_analyzer import IntentAnalyzer
from lina.brain.model_provider import ModelResponse
from lina.brain.prompt_builder import ConversationTurn
from lina.services.deterministic_response_service import DeterministicResponseService
from lina.services.project_context_service import ProjectContextService
from lina.services.tool_execution_service import ToolExecutionService


class ConversationService:
    """Coordinates user messages with the Brain."""

    def __init__(
        self,
        brain: Brain,
        intent_analyzer: IntentAnalyzer | None = None,
        deterministic_response_service: DeterministicResponseService | None = None,
        project_context_service: ProjectContextService | None = None,
        context_manager: ContextManager | None = None,
        tool_execution_service: ToolExecutionService | None = None,
        history_limit: int = 6,
    ) -> None:
        self._brain = brain
        self._intent_analyzer = intent_analyzer or IntentAnalyzer()
        self._deterministic_response_service = (
            deterministic_response_service or DeterministicResponseService()
        )
        self._context_manager = context_manager or ContextManager(
            project_context_service=project_context_service,
            history_limit=history_limit,
        )
        self._tool_execution_service = tool_execution_service
        self._history_limit = history_limit
        self._history: list[ConversationTurn] = []

    def handle_message(self, user_message: str) -> ModelResponse:
        intent = self._intent_analyzer.analyze(user_message)

        if intent.type is IntentType.CURRENT_TIME and self._tool_execution_service:
            response = ModelResponse(
                text=self._tool_execution_service.execute("current_time").text
            )
        elif self._deterministic_response_service.can_handle(intent):
            response = self._deterministic_response_service.handle(intent)
        else:
            context = self._context_manager.build_context(
                user_message=user_message,
                intent=intent,
                conversation_history=self._history,
            )
            response = self._brain.respond_with_context(context)

        self._history.append(
            ConversationTurn(
                user_message=user_message,
                assistant_response=response.text,
            )
        )
        self._history = self._history[-self._history_limit :]
        return response
