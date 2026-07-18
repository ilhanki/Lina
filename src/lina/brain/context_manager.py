"""Runtime context management for Lina's Brain."""

from collections.abc import Sequence
import re

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
        context_character_budget: int = 12000,
    ) -> None:
        self._project_context_service = project_context_service
        self._git_context_service = git_context_service
        self._memory_service = memory_service
        self._history_limit = history_limit
        self._memory_context_max_items = memory_context_max_items
        self._memory_context_max_characters = memory_context_max_characters
        self._context_character_budget = max(1000, context_character_budget)

    def build_context(
        self,
        user_message: str,
        intent: Intent,
        conversation_history: Sequence[ConversationTurn],
    ) -> ConversationContext:
        safe_history = trim_conversation_history(
            conversation_history,
            max_turns=self._history_limit,
            character_budget=self._context_character_budget,
        )
        return ConversationContext(
            user_message=user_message,
            conversation_history=safe_history,
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


_BASE64_PATTERN = re.compile(r"(?i)\b[A-Za-z0-9+/]{200,}={0,2}\b")


def trim_conversation_history(
    history: Sequence[ConversationTurn],
    max_turns: int,
    character_budget: int,
) -> tuple[ConversationTurn, ...]:
    """Keep newest complete user/assistant pairs within a deterministic budget."""
    selected: list[ConversationTurn] = []
    used = 0
    last_signature: tuple[str, str] | None = None
    for turn in reversed(history[-max_turns:]):
        user = _safe_context_text(turn.user_message, user_content=True)
        assistant = _safe_context_text(turn.assistant_response, user_content=False)
        if not user or not assistant:
            continue
        signature = (user, assistant)
        if signature == last_signature:
            continue
        last_signature = signature
        cost = len(user) + len(assistant)
        if selected and used + cost > character_budget:
            break
        if not selected and cost > character_budget:
            available = max(1, character_budget // 2)
            user = user[-available:]
            assistant = assistant[-available:]
            cost = len(user) + len(assistant)
        selected.append(ConversationTurn(user_message=user, assistant_response=assistant))
        used += cost
    selected.reverse()
    return tuple(selected)


_CONTEXT_CONTAMINATION = re.compile(
    r"(?:<\|(?:system|developer|assistant|user)_?\|>|system prompt|developer instruction|"
    r"sistem tarafından bilinen|kullanıcının mesajını analiz eder|corresponding response|"
    r"<codex_(?:task|session|event|plan)>|<agent_(?:plan|event|policy)>)",
    re.I,
)


def _safe_context_text(text: str, *, user_content: bool = False) -> str:
    if not user_content and _CONTEXT_CONTAMINATION.search(text):
        return ""
    value = _BASE64_PATTERN.sub("[binary omitted]", text)
    value = re.sub(r"(?is)<(?:tool_debug|internal_metadata)>.*?</(?:tool_debug|internal_metadata)>", "", value)
    value = re.sub(r"(?i)data:image/[^;]+;base64,\S+", "[image omitted]", value)
    value = re.sub(r"(?is)<agent_plan>.*?</agent_plan>", "[agent plan omitted]", value)
    value = re.sub(r"(?is)<codex_(?:task|session|event|plan)>.*?</codex_(?:task|session|event|plan)>", "[codex data omitted]", value)
    value = re.sub(r"(?im)^\s*(?:system|assistant|user)\s*:\s*", "", value)
    return value.strip()
