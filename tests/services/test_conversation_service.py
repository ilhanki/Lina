from lina.brain.model_provider import ModelResponse
from lina.brain.prompt_builder import ConversationTurn
from lina.services.conversation_service import ConversationService


class FakeBrain:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.histories: list[list[ConversationTurn]] = []

    def respond(
        self,
        user_message: str,
        conversation_history: list[ConversationTurn] | None = None,
    ) -> ModelResponse:
        self.messages.append(user_message)
        self.histories.append(list(conversation_history or []))
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


def test_conversation_service_sends_previous_turns_to_brain() -> None:
    brain = FakeBrain()
    service = ConversationService(brain=brain)

    service.handle_message("Hello")
    service.handle_message("What did I say?")

    assert brain.histories[0] == []
    assert brain.histories[1] == [
        ConversationTurn(user_message="Hello", assistant_response="Response: Hello")
    ]


def test_conversation_service_limits_history() -> None:
    brain = FakeBrain()
    service = ConversationService(brain=brain, history_limit=1)

    service.handle_message("First")
    service.handle_message("Second")
    service.handle_message("Third")

    assert brain.histories[2] == [
        ConversationTurn(user_message="Second", assistant_response="Response: Second")
    ]
