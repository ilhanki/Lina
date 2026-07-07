from lina.brain.brain import Brain
from lina.brain.model_provider import ModelRequest, ModelResponse
from lina.brain.prompt_builder import ConversationTurn, PromptBuilder


class FakeModelProvider:
    def __init__(self) -> None:
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return ModelResponse(text=f"Response: {request.prompt}")


def test_brain_sends_built_prompt_to_model_provider() -> None:
    provider = FakeModelProvider()
    brain = Brain(
        model_provider=provider,
        prompt_builder=PromptBuilder(system_prompt="You are Lina."),
    )

    brain.respond("Hello")

    assert provider.requests == [
        ModelRequest(prompt="System:\nYou are Lina.\n\nUser:\nHello")
    ]


def test_brain_returns_model_response() -> None:
    provider = FakeModelProvider()
    brain = Brain(
        model_provider=provider,
        prompt_builder=PromptBuilder(system_prompt="You are Lina."),
    )

    response = brain.respond("Hello")

    assert response == ModelResponse(text="Response: System:\nYou are Lina.\n\nUser:\nHello")


def test_brain_uses_default_prompt_builder_when_not_provided() -> None:
    provider = FakeModelProvider()
    brain = Brain(model_provider=provider)

    brain.respond("Hello")

    assert "System:" in provider.requests[0].prompt
    assert "Lina" in provider.requests[0].prompt
    assert "User:\nHello" in provider.requests[0].prompt


def test_brain_passes_conversation_history_to_prompt_builder() -> None:
    provider = FakeModelProvider()
    brain = Brain(
        model_provider=provider,
        prompt_builder=PromptBuilder(system_prompt="You are Lina."),
    )

    brain.respond(
        "What is my name?",
        conversation_history=[
            ConversationTurn(user_message="My name is Ilhan.", assistant_response="Nice to meet you."),
        ],
    )

    assert "Conversation history:" in provider.requests[0].prompt
    assert "User: My name is Ilhan." in provider.requests[0].prompt
    assert "Assistant: Nice to meet you." in provider.requests[0].prompt
