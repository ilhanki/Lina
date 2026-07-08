"""Runtime context management for Lina's Brain."""

from collections.abc import Sequence

from lina.brain.conversation_context import ConversationContext
from lina.brain.intent import Intent, IntentType
from lina.brain.prompt_builder import ConversationTurn
from lina.memory.service import MemoryService
from lina.services.git_context_service import GitContextService, format_git_context
from lina.services.project_context_service import ProjectContextService


class ContextManager:
    """Builds limited runtime context for a user message."""

    def __init__(
        self,
        project_context_service: ProjectContextService | None = None,
        git_context_service: GitContextService | None = None,
        memory_service: MemoryService | None = None,
        history_limit: int = 6,
        memory_context_max_items: int = 8,
        memory_context_max_characters: int = 1200,
    ) -> None:
        self._project_context_service = project_context_service
        self._git_context_service = git_context_service
        self._memory_service = memory_service
        self._history_limit = history_limit
        self._memory_context_max_items = memory_context_max_items
        self._memory_context_max_characters = memory_context_max_characters

    def build_context(
        self,
        user_message: str,
        intent: Intent,
        conversation_history: Sequence[ConversationTurn],
    ) -> ConversationContext:
        return ConversationContext(
            user_message=user_message,
            conversation_history=tuple(conversation_history[-self._history_limit :]),
            project_context=self._collect_project_context(intent),
            memory_context=self._collect_memory_context(),
        )

    def _collect_memory_context(self) -> str | None:
        if self._memory_service is None:
            return None
        return self._memory_service.build_memory_context(
            max_items=self._memory_context_max_items,
            max_characters=self._memory_context_max_characters,
        )

    def _collect_project_context(self, intent: Intent) -> str | None:
        if intent.type not in {IntentType.PROJECT_STATUS, IntentType.PROJECT_SUMMARY}:
            return None

        sections: list[str] = []

        if self._project_context_service is not None:
            doc_context = self._project_context_service.collect_context()
            if doc_context.has_content:
                sections.append(f"[Kaynak: proje dokümanları]\n{doc_context.text}")

        if self._git_context_service is not None:
            git_context = self._git_context_service.collect_context()
            if git_context.has_content:
                sections.append(f"[Kaynak: git]\n{format_git_context(git_context)}")

        if not sections:
            return "Proje bağlamı şu anda yapılandırılmamış."

        return "\n\n".join(sections)
