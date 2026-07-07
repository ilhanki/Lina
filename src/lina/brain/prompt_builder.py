"""Prompt construction for Lina's Brain."""

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ConversationTurn:
    """A completed user and assistant exchange."""

    user_message: str
    assistant_response: str


class PromptBuilder:
    """Builds model prompts from conversation inputs."""

    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt.strip()

    def build(
        self,
        user_message: str,
        history: Sequence[ConversationTurn] | None = None,
        project_context: str | None = None,
    ) -> str:
        message = user_message.strip()
        sections = [f"System:\n{self._system_prompt}"]

        if project_context and project_context.strip():
            sections.append(
                "Project context:\n"
                "Aşağıdaki proje bağlamına dayan. Bu bağlamda olmayan proje geçmişi, "
                "commit, URL, dosya veya yapılan iş uydurma.\n"
                f"{project_context.strip()}"
            )

        if history:
            history_lines: list[str] = []
            for turn in history:
                history_lines.append(f"User: {turn.user_message.strip()}")
                history_lines.append(f"Assistant: {turn.assistant_response.strip()}")
            sections.append("Conversation history:\n" + "\n".join(history_lines))

        sections.append(f"User:\n{message}")
        return "\n\n".join(sections)

    def build_from_context(self, context) -> str:
        return self.build(
            user_message=context.user_message,
            history=context.conversation_history,
            project_context=context.project_context,
        )
