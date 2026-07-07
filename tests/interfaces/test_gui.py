from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.interfaces.gui import LinaGui, format_chat_message, format_error_message
from lina.services.model_diagnostics_service import (
    DiagnosticsResult,
    ModelDiagnosticsService,
    ModelStatus,
    format_status_message as format_diagnostics_message,
)


class FakeConversationService:
    def __init__(self, should_fail: bool = False) -> None:
        self.messages: list[str] = []
        self._should_fail = should_fail

    def handle_message(self, user_message: str) -> ModelResponse:
        self.messages.append(user_message)
        if self._should_fail:
            raise ModelProviderError("connection refused")
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
    assert format_chat_message("Lina", "Hello") == "Lina:\nHello\n\n"


def test_format_error_message_returns_user_friendly_text() -> None:
    assert format_error_message() == (
        "Lina şu anda modele ulaşamadı. Ollama çalışıyor mu kontrol edebilir misin?"
    )


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
        ("Lina", "Yazıyor..."),
        ("Lina", "Response: Hello"),
    ]
    assert gui.waiting_states == [True, False]
    assert gui.input_focus_count == 1


def test_gui_does_not_send_while_waiting_for_response() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")
    gui._is_waiting_for_response = True

    gui.send_message()

    assert service.messages == []


def test_gui_shows_provider_errors_as_chat_messages() -> None:
    service = FakeConversationService(should_fail=True)
    gui = _create_test_gui(service, input_text="Hello")

    gui.send_message()

    assert gui.recorded_messages == [
        ("İlhan", "Hello"),
        ("Lina", "Yazıyor..."),
        ("Lina", format_error_message()),
    ]
    assert gui.waiting_states == [True, False]
    assert gui.input_focus_count == 1


def _create_test_gui(service: FakeConversationService, input_text: str):
    gui = LinaGui.__new__(LinaGui)
    gui._conversation_service = service
    gui._thread_factory = ImmediateThread
    gui._root = _FakeRoot()
    gui._is_waiting_for_response = False
    gui._diagnostics_service = None
    gui.recorded_messages = []
    gui.waiting_states = []
    gui.input_was_cleared = False
    gui.input_focus_count = 0
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
    gui._focus_input = lambda: setattr(
        gui,
        "input_focus_count",
        gui.input_focus_count + 1,
    )
    return gui


class _FakeRoot:
    def after(self, delay_ms: int, callback, *args) -> None:
        callback(*args)


# --- GUI diagnostics tests ---


class _FakeDiagnosticsService:
    def __init__(self, result: DiagnosticsResult) -> None:
        self._result = result
        self.check_count = 0

    def check_status(self) -> DiagnosticsResult:
        self.check_count += 1
        return self._result

    @property
    def configured_model(self) -> str:
        return self._result.model_name


def test_gui_runs_diagnostics_on_init_when_service_provided() -> None:
    service = FakeConversationService()
    diagnostics = _FakeDiagnosticsService(
        DiagnosticsResult(
            status=ModelStatus.READY,
            model_name="llama3",
            message="Model hazır.",
        )
    )
    gui = _create_test_gui(service, input_text="")
    gui._diagnostics_service = diagnostics
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui._run_initial_diagnostics()

    assert diagnostics.check_count == 1
    assert "llama3" in gui._status_updates[-1]


def test_gui_does_not_run_diagnostics_when_no_service() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="")
    gui._diagnostics_service = None
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui._run_initial_diagnostics()

    assert gui._status_updates == []


def test_gui_shows_unreachable_status() -> None:
    service = FakeConversationService()
    diagnostics = _FakeDiagnosticsService(
        DiagnosticsResult(
            status=ModelStatus.OLLAMA_UNREACHABLE,
            model_name="llama3",
            message="",
        )
    )
    gui = _create_test_gui(service, input_text="")
    gui._diagnostics_service = diagnostics
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui._run_initial_diagnostics()

    assert "Ollama" in gui._status_updates[-1]
