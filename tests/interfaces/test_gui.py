"""Tests for Lina GUI interface."""

from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.interfaces.gui import (
    LinaGui,
    format_chat_message,
    format_error_message,
    format_welcome_message,
    normalize_chat_message,
)
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


# --- Format function tests ---


def test_gui_class_can_be_imported() -> None:
    assert LinaGui is not None


def test_format_chat_message_formats_sender_and_message() -> None:
    assert format_chat_message("Lina", "Hello") == "Lina:\nHello\n\n"


def test_format_chat_message_removes_duplicate_assistant_label() -> None:
    assert format_chat_message("Lina", "Lina: Ben Lina.") == "Lina:\nBen Lina.\n\n"


def test_format_chat_message_removes_repeated_assistant_labels() -> None:
    assert format_chat_message("Lina", "Lina:Lina: Ben Lina.") == "Lina:\nBen Lina.\n\n"


def test_format_chat_message_removes_duplicate_user_label() -> None:
    assert format_chat_message("İlhan", "İlhan: Merhaba") == "İlhan:\nMerhaba\n\n"


def test_normalize_chat_message_preserves_normal_content() -> None:
    assert normalize_chat_message("Lina", "Ben Lina.") == "Ben Lina."


def test_format_error_message_returns_user_friendly_text() -> None:
    message = format_error_message()
    assert "Modele ulaşılamadı" in message
    assert "Ollama" in message


def test_format_error_message_for_unreachable_ollama() -> None:
    message = format_error_message(ModelProviderError("Ollama network error: connection refused"))

    assert "Ollama'ya ulaşılamıyor" in message


def test_format_error_message_for_missing_model() -> None:
    message = format_error_message(ModelProviderError("Ollama HTTP error: 404"))

    assert "model Ollama içinde bulunamadı" in message


def test_format_error_message_for_timeout() -> None:
    message = format_error_message(ModelProviderError("Ollama request timed out"))

    assert "zaman aşımına uğradı" in message


def test_format_error_message_for_unconfigured_model() -> None:
    message = format_error_message(ModelProviderError("Ollama model is not configured"))

    assert "Model adı yapılandırılmamış" in message


def test_format_welcome_message_contains_greeting() -> None:
    message = format_welcome_message()
    assert "Merhaba" in message
    assert "Lina" in message


# --- Message sending tests ---


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
        ("Lina", format_error_message(ModelProviderError("connection refused"))),
    ]
    assert gui.waiting_states == [True, False]
    assert gui.input_focus_count == 1


def test_gui_stores_last_response_text() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")

    gui.send_message()

    assert gui._last_response_text == "Response: Hello"


def test_gui_stores_error_as_last_response_text() -> None:
    service = FakeConversationService(should_fail=True)
    gui = _create_test_gui(service, input_text="Hello")

    gui.send_message()

    assert gui._last_response_text == format_error_message(
        ModelProviderError("connection refused")
    )


def test_gui_append_message_uses_normalization_in_render_path() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    chat_log = _FakeChatLog()
    gui._chat_log = chat_log
    gui._append_message = LinaGui._append_message.__get__(gui, LinaGui)

    gui._append_message("Lina", "Lina:Lina: Ben Lina.")

    assert chat_log.inserted_text == "Lina:\nBen Lina.\n\n"
    assert gui._message_ranges == [("1.0", "1.0")]


def test_gui_single_send_appends_single_final_response() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")

    gui.send_message()

    assert gui.recorded_messages.count(("Lina", "Response: Hello")) == 1


# --- Chat controls tests ---


def test_gui_clear_chat_resets_messages_and_ranges() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")
    gui._chat_log = _FakeChatLog()
    gui.send_message()

    gui.clear_chat()

    assert gui._message_ranges == []
    assert gui._last_response_text == ""


def test_gui_copy_last_response_does_nothing_when_empty() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._last_response_text = ""
    gui._clipboard = None
    gui._root.clipboard_clear = lambda: None
    gui._root.clipboard_append = lambda text: setattr(gui, "_clipboard", text)

    gui.copy_last_response()

    assert gui._clipboard is None


def test_gui_copy_last_response_copies_to_clipboard() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._last_response_text = "Test cevap"
    gui._clipboard = None
    gui._root.clipboard_clear = lambda: None
    gui._root.clipboard_append = lambda text: setattr(gui, "_clipboard", text)

    gui.copy_last_response()

    assert gui._clipboard == "Test cevap"


# --- Status update tests ---


def test_gui_updates_status_on_send() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")
    gui._status_updates = []
    original_update = gui._update_status_text
    gui._update_status_text = lambda text: (
        gui._status_updates.append(text),
        original_update(text) if hasattr(gui, '_status_text') else None,
    )

    gui.send_message()

    assert "Cevap bekleniyor..." in gui._status_updates


# --- Diagnostics tests ---


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


# --- Test helpers ---


def _create_test_gui(service: FakeConversationService, input_text: str):
    gui = LinaGui.__new__(LinaGui)
    gui._conversation_service = service
    gui._thread_factory = ImmediateThread
    gui._root = _FakeRoot()
    gui._is_waiting_for_response = False
    gui._diagnostics_service = None
    gui._last_response_text = ""
    gui._message_ranges = []
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
    gui._update_status_text = lambda text: None
    return gui


class _FakeRoot:
    def after(self, delay_ms: int, callback, *args) -> None:
        callback(*args)


class _FakeChatLog:
    """Fake ScrolledText for testing clear_chat without Tkinter."""

    def __init__(self) -> None:
        self.inserted_text = ""

    def configure(self, **kwargs) -> None:
        pass

    def delete(self, start: str, end: str) -> None:
        pass

    def insert(self, index: str, text: str) -> None:
        self.inserted_text += text

    def index(self, idx: str) -> str:
        return "1.0"

    def see(self, idx: str) -> None:
        pass
