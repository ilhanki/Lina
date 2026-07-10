from lina.brain.brain import Brain
from lina.brain.conversation_context import ConversationContext
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
    prompt_builder = PromptBuilder(system_prompt="You are Lina.")
    brain = Brain(
        model_provider=provider,
        prompt_builder=prompt_builder,
    )

    brain.respond("Hello")

    assert provider.requests == [
        ModelRequest(prompt=prompt_builder.build(user_message="Hello"))
    ]


def test_brain_returns_model_response() -> None:
    provider = FakeModelProvider()
    prompt_builder = PromptBuilder(system_prompt="You are Lina.")
    brain = Brain(
        model_provider=provider,
        prompt_builder=prompt_builder,
    )

    response = brain.respond("Hello")

    assert response == ModelResponse(
        text=f"Response: {prompt_builder.build(user_message='Hello')}"
    )


def test_brain_uses_default_prompt_builder_when_not_provided() -> None:
    provider = FakeModelProvider()
    brain = Brain(model_provider=provider)

    brain.respond("Hello")

    assert "System:" in provider.requests[0].prompt
    assert "Lina" in provider.requests[0].prompt
    assert '"role": "user", "content": "Hello"' in provider.requests[0].prompt


def test_brain_passes_conversation_history_to_prompt_builder() -> None:
    provider = FakeModelProvider()
    brain = Brain(
        model_provider=provider,
        prompt_builder=PromptBuilder(system_prompt="You are Lina."),
    )

    brain.respond(
        "What is my name?",
        conversation_history=[
            ConversationTurn(
                user_message="My name is Ilhan.",
                assistant_response="Nice to meet you.",
            ),
        ],
    )

    assert "Conversation history (JSON, context only):" in provider.requests[0].prompt
    assert '"role": "user"' in provider.requests[0].prompt
    assert '"content": "My name is Ilhan."' in provider.requests[0].prompt
    assert '"role": "assistant"' in provider.requests[0].prompt
    assert '"content": "Nice to meet you."' in provider.requests[0].prompt


def test_brain_passes_project_context_to_prompt_builder() -> None:
    provider = FakeModelProvider()
    brain = Brain(
        model_provider=provider,
        prompt_builder=PromptBuilder(system_prompt="You are Lina."),
    )

    brain.respond(
        "What happened in the project?",
        project_context="Sprint 5 completed.",
    )

    assert "Project context:" in provider.requests[0].prompt
    assert "Sprint 5 completed." in provider.requests[0].prompt


def test_brain_responds_with_conversation_context() -> None:
    provider = FakeModelProvider()
    brain = Brain(
        model_provider=provider,
        prompt_builder=PromptBuilder(system_prompt="You are Lina."),
    )
    context = ConversationContext(
        user_message="What happened?",
        conversation_history=[],
        project_context="Project context",
    )

    brain.respond_with_context(context)

    assert "Project context" in provider.requests[0].prompt
    assert '"content": "What happened?"' in provider.requests[0].prompt
