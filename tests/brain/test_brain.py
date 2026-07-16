from datetime import datetime

from lina.brain.brain import Brain
from lina.brain.conversation_context import ConversationContext
from lina.brain.model_provider import ModelMessage, ModelRequest, ModelResponse
from lina.brain.prompt_builder import ConversationTurn, PromptBuilder
from lina.vision.models import ImageAttachment, PNG_SIGNATURE


class FakeModelProvider:
    def __init__(self) -> None:
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return ModelResponse(text=f"Response: {request.messages[-1].content}")


def test_brain_sends_built_prompt_to_model_provider() -> None:
    provider = FakeModelProvider()
    prompt_builder = PromptBuilder(system_prompt="You are Lina.")
    brain = Brain(
        model_provider=provider,
        prompt_builder=prompt_builder,
    )

    brain.respond("Hello")

    assert provider.requests == [
        ModelRequest(
            messages=prompt_builder.build(user_message="Hello"),
            temperature=0.45,
            top_p=0.9,
            repeat_penalty=1.08,
        )
    ]


def test_brain_returns_model_response() -> None:
    provider = FakeModelProvider()
    prompt_builder = PromptBuilder(system_prompt="You are Lina.")
    brain = Brain(
        model_provider=provider,
        prompt_builder=prompt_builder,
    )

    response = brain.respond("Hello")

    assert response == ModelResponse(text="Response: Hello")


def test_brain_uses_default_prompt_builder_when_not_provided() -> None:
    provider = FakeModelProvider()
    brain = Brain(model_provider=provider)

    brain.respond("Hello")

    assert provider.requests[0].messages[0].role == "system"
    assert "Lina" in provider.requests[0].messages[0].content
    assert provider.requests[0].messages[-1] == ModelMessage(
        role="user",
        content="Hello",
    )


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

    assert provider.requests[0].messages[1:] == (
        ModelMessage(role="user", content="My name is Ilhan."),
        ModelMessage(role="assistant", content="Nice to meet you."),
        ModelMessage(role="user", content="What is my name?"),
    )


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

    assert "Project context:" in provider.requests[0].messages[0].content
    assert "Sprint 5 completed." in provider.requests[0].messages[0].content


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

    assert "Project context" in provider.requests[0].messages[0].content
    assert provider.requests[0].messages[-1] == ModelMessage(
        role="user",
        content="What happened?",
    )


def test_brain_passes_image_attachment_to_provider() -> None:
    provider = FakeModelProvider()
    brain = Brain(
        model_provider=provider,
        prompt_builder=PromptBuilder(system_prompt="Vision guidance"),
    )
    context = ConversationContext(
        user_message="Bu ekranda ne var?",
        conversation_history=[],
    )
    attachment = ImageAttachment(
        mime_type="image/png",
        data=PNG_SIGNATURE + b"image",
        width=640,
        height=360,
        captured_at=datetime(2026, 7, 11, 23, 50),
        source="screen_capture",
        display_name="Display 1",
    )

    brain.respond_with_image(context, attachment)

    assert provider.requests[0].image_attachment is attachment
    assert provider.requests[0].messages[-1].content == "Bu ekranda ne var?"
