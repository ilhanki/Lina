"""Brain orchestrator for Lina."""

from lina.brain.model_provider import ModelProvider, ModelRequest, ModelResponse


class Brain:
    """Minimal Brain orchestrator."""

    def __init__(self, model_provider: ModelProvider) -> None:
        self._model_provider = model_provider

    def respond(self, user_message: str) -> ModelResponse:
        request = ModelRequest(prompt=user_message)
        return self._model_provider.generate(request)

