from lina.brain.model_provider import ModelResponse
from lina.services.conversation_service import ConversationService


class FakeBrain:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def respond(self, user_message: str) -> ModelResponse:
        self.messages.append(user_message)
        return ModelResponse(text=f"Response: {user_message}")


def test_conversation_service_sends_user_message_to_brain() -> None:
    brain = FakeBrain()
    service = ConversationService(brain=brain)

    service.handle_message("Hello")

    assert brain.messages == ["Hello"]


def test_conversation_service_returns_model_response() -> None:
    service = ConversationService(brain=FakeBrain())

    response = service.handle_message("Hello")

    assert response == ModelResponse(text="Response: Hello")

