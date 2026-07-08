"""Conversation service for Lina."""

from lina.brain.brain import Brain
from lina.brain.context_manager import ContextManager
from lina.brain.intent import IntentType
from lina.brain.intent_analyzer import IntentAnalyzer
from lina.brain.model_provider import ModelResponse
from lina.brain.prompt_builder import ConversationTurn
from lina.memory.models import MemoryType
from lina.memory.service import MemoryService
from lina.services.deterministic_response_service import DeterministicResponseService
from lina.services.project_context_service import ProjectContextService
from lina.services.tool_execution_service import ToolExecutionError, ToolExecutionService


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
        memory_service: MemoryService | None = None,
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
        self._memory_service = memory_service
        self._history_limit = history_limit
        self._history: list[ConversationTurn] = []

    def handle_message(self, user_message: str) -> ModelResponse:
        intent = self._intent_analyzer.analyze(user_message)

        if intent.type in {
            IntentType.MEMORY_REMEMBER,
            IntentType.MEMORY_RECALL,
            IntentType.MEMORY_LIST,
            IntentType.MEMORY_FORGET,
            IntentType.MEMORY_CLEAR,
        }:
            response = self._handle_memory_intent(intent.type, user_message)
        elif intent.type is IntentType.CURRENT_TIME and self._tool_execution_service:
            try:
                response = ModelResponse(
                    text=self._tool_execution_service.execute("current_time").text
                )
            except ToolExecutionError:
                response = self._deterministic_response_service.handle(intent)
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

    def _handle_memory_intent(
        self,
        intent_type: IntentType,
        user_message: str,
    ) -> ModelResponse:
        if self._memory_service is None:
            return ModelResponse(
                text="Hafıza sistemi şu anda yapılandırılmamış."
            )

        if intent_type is IntentType.MEMORY_REMEMBER:
            content = _extract_memory_content(user_message)
            if not content:
                return ModelResponse(
                    text=(
                        "Neyi hatırlamamı istediğini yazman gerekiyor. "
                        "Örnek: bunu hatırla: kısa cevapları seviyorum."
                    )
                )
            memory = self._memory_service.add_memory(
                MemoryType.CONVERSATION_NOTE,
                content,
                source="explicit_user_request",
            )
            if memory is None:
                return ModelResponse(text="Bunu zaten hatırlıyorum İlhan.")
            return ModelResponse(text=f"Tamam İlhan, bunu hatırlayacağım: {content}.")

        if intent_type in {IntentType.MEMORY_RECALL, IntentType.MEMORY_LIST}:
            memories = self._memory_service.list_memories()
            if not memories:
                return ModelResponse(text="Şu an hafızamda kayıtlı bir bilgi yok.")
            lines = ["Şunları hatırlıyorum:"]
            lines.extend(f"- {memory.content}" for memory in memories)
            return ModelResponse(text="\n".join(lines))

        if intent_type is IntentType.MEMORY_FORGET:
            content = _extract_memory_content(user_message)
            if not content:
                return ModelResponse(
                    text=(
                        "Neyi unutmamı istediğini yazman gerekiyor. "
                        "Örnek: şunu unut: kısa cevapları seviyorum."
                    )
                )
            removed_count = self._memory_service.forget_memory_by_content(content)
            if removed_count == 0:
                return ModelResponse(text="Bunu hafızamda bulamadım.")
            return ModelResponse(text="Tamam, bunu hafızamdan kaldırdım.")

        if intent_type is IntentType.MEMORY_CLEAR:
            self._memory_service.clear_memories()
            return ModelResponse(text="Hafızamdaki tüm kayıtları temizledim.")

        raise ValueError(f"Unsupported memory intent: {intent_type.value}")


def _extract_memory_content(message: str) -> str:
    if ":" not in message:
        return ""
    return message.split(":", 1)[1].strip()
