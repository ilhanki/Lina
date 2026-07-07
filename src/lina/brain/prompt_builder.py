"""Prompt construction for Lina's Brain."""


class PromptBuilder:
    """Builds model prompts from conversation inputs."""

    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt.strip()

    def build(self, user_message: str) -> str:
        message = user_message.strip()
        return f"System:\n{self._system_prompt}\n\nUser:\n{message}"
