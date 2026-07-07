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
    ) -> str:
        message = user_message.strip()
        sections = [f"System:\n{self._system_prompt}"]

        if history:
            history_lines: list[str] = []
            for turn in history:
                history_lines.append(f"User: {turn.user_message.strip()}")
                history_lines.append(f"Assistant: {turn.assistant_response.strip()}")
            sections.append("Conversation history:\n" + "\n".join(history_lines))

        sections.append(f"User:\n{message}")
        return "\n\n".join(sections)
