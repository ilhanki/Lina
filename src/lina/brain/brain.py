"""Brain orchestrator for Lina."""

from typing import Sequence

from lina.brain.model_provider import ModelProvider, ModelRequest, ModelResponse
from lina.brain.prompt_builder import ConversationTurn, PromptBuilder
from lina.brain.prompts import DEFAULT_SYSTEM_PROMPT


class Brain:
    """Minimal Brain orchestrator."""

    def __init__(
        self,
        model_provider: ModelProvider,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self._model_provider = model_provider
        self._prompt_builder = prompt_builder or PromptBuilder(
            system_prompt=DEFAULT_SYSTEM_PROMPT
        )

    def respond(
        self,
        user_message: str,
        conversation_history: Sequence[ConversationTurn] | None = None,
    ) -> ModelResponse:
        prompt = self._prompt_builder.build(
            user_message=user_message,
            history=conversation_history,
        )
        request = ModelRequest(prompt=prompt)
        return self._model_provider.generate(request)
