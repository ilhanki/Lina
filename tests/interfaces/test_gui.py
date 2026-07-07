from lina.brain.model_provider import ModelResponse
from lina.interfaces.gui import LinaGui, format_chat_message


class FakeConversationService:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def handle_message(self, user_message: str) -> ModelResponse:
        self.messages.append(user_message)
        return ModelResponse(text=f"Response: {user_message}")


class ImmediateThread:
    def __init__(self, target, args, daemon) -> None:
        self._target = target
        self._args = args
        self.daemon = daemon

    def start(self) -> None:
        self._target(*self._args)


def test_gui_class_can_be_imported() -> None:
    assert LinaGui is not None


def test_format_chat_message_formats_sender_and_message() -> None:
    assert format_chat_message("Lina", "Hello") == "Lina: Hello\n\n"


def test_fake_gui_does_not_send_empty_message() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="   ")

    gui.send_message()

    assert service.messages == []
    assert gui.recorded_messages == []


def test_fake_gui_send_message_calls_conversation_service() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")

    gui.send_message()

    assert service.messages == ["Hello"]
    assert gui.input_was_cleared
    assert gui.recorded_messages == [
        ("İlhan", "Hello"),
        ("Lina", "yazıyor..."),
        ("Lina", "Response: Hello"),
    ]
    assert gui.waiting_states == [True, False]


def test_gui_does_not_send_while_waiting_for_response() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")
    gui._is_waiting_for_response = True

    gui.send_message()

    assert service.messages == []


def _create_test_gui(service: FakeConversationService, input_text: str):
    gui = LinaGui.__new__(LinaGui)
    gui._conversation_service = service
    gui._thread_factory = ImmediateThread
    gui._root = _FakeRoot()
    gui._is_waiting_for_response = False
    gui.recorded_messages = []
    gui.waiting_states = []
    gui.input_was_cleared = False
    gui._get_input_text = lambda: input_text.strip()
    gui._clear_input = lambda: setattr(gui, "input_was_cleared", True)
    gui._append_message = lambda sender, message: gui.recorded_messages.append(
        (sender, message)
    )
    gui._remove_last_message = lambda: None
    gui._set_waiting_state = lambda is_waiting: (
        setattr(gui, "_is_waiting_for_response", is_waiting),
        gui.waiting_states.append(is_waiting),
    )
    return gui


class _FakeRoot:
    def after(self, delay_ms: int, callback, *args) -> None:
        callback(*args)
