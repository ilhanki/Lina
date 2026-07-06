from lina.brain.brain import Brain
from lina.brain.model_provider import ModelRequest, ModelResponse


class FakeModelProvider:
    def __init__(self) -> None:
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return ModelResponse(text=f"Response: {request.prompt}")


def test_brain_sends_user_message_to_model_provider() -> None:
    provider = FakeModelProvider()
    brain = Brain(model_provider=provider)

    brain.respond("Hello")

    assert provider.requests == [ModelRequest(prompt="Hello")]


def test_brain_returns_model_response() -> None:
    provider = FakeModelProvider()
    brain = Brain(model_provider=provider)

    response = brain.respond("Hello")

    assert response == ModelResponse(text="Response: Hello")

