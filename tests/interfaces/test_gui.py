"""Tests for Lina GUI interface."""

import lina.interfaces.gui as gui_module
from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.interfaces.gui import (
    LinaGui,
    format_chat_message,
    format_error_message,
    format_unexpected_error_message,
    format_welcome_message,
    normalize_chat_message,
)
from lina.services.model_diagnostics_service import (
    DiagnosticsResult,
    ModelDiagnosticsService,
    ModelStatus,
    format_status_message as format_diagnostics_message,
)
from lina.speech.models import (
    SpeechServiceError,
    SpeechSynthesisResult,
    SpeechTranscriptionResult,
)
from lina.speech.providers import NoOpSTTProvider, NoOpTTSProvider
from lina.speech.service import SpeechService


class FakeConversationService:
    def __init__(
        self,
        should_fail: bool = False,
        response_text: str | None = None,
        unexpected_error: Exception | None = None,
    ) -> None:
        self.messages: list[str] = []
        self._should_fail = should_fail
        self._response_text = response_text
        self._unexpected_error = unexpected_error

    def handle_message(self, user_message: str) -> ModelResponse:
        self.messages.append(user_message)
        if self._unexpected_error is not None:
            raise self._unexpected_error
        if self._should_fail:
            raise ModelProviderError("connection refused")
        if self._response_text is not None:
            return ModelResponse(text=self._response_text)
        return ModelResponse(text=f"Response: {user_message}")


class ImmediateThread:
    def __init__(self, target, args, daemon) -> None:
        self._target = target
        self._args = args
        self.daemon = daemon

    def start(self) -> None:
        self._target(*self._args)


class FakeSTTProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    def transcribe_once(self) -> SpeechTranscriptionResult:
        self.call_count += 1
        if self._error is not None:
            raise self._error
        return SpeechTranscriptionResult(
            text="Merhaba Lina",
            confidence=0.9,
            source="fake",
            is_final=True,
        )


class FakeTTSProvider:
    def is_available(self) -> bool:
        return False

    def speak(self, text: str) -> SpeechSynthesisResult:
        return SpeechSynthesisResult(success=False)

    def stop(self) -> None:
        return None


# --- Format function tests ---


def test_gui_class_can_be_imported() -> None:
    assert LinaGui is not None


def test_format_chat_message_formats_sender_and_message() -> None:
    assert format_chat_message("Lina", "Hello") == "Lina:\nHello\n\n"


def test_format_chat_message_removes_duplicate_assistant_label() -> None:
    assert format_chat_message("Lina", "Lina: Ben Lina.") == "Lina:\nBen Lina.\n\n"


def test_format_chat_message_removes_repeated_assistant_labels() -> None:
    assert format_chat_message("Lina", "Lina:Lina: Ben Lina.") == "Lina:\nBen Lina.\n\n"


def test_format_chat_message_removes_spaced_repeated_assistant_labels() -> None:
    assert format_chat_message("Lina", "Lina: Lina: Ben Lina.") == "Lina:\nBen Lina.\n\n"


def test_format_chat_message_removes_labels_with_spaced_colons() -> None:
    assert format_chat_message("Lina", "Lina : Lina : Ben Lina.") == "Lina:\nBen Lina.\n\n"


def test_format_chat_message_removes_multiline_repeated_assistant_labels() -> None:
    assert format_chat_message("Lina", "Lina:\nLina: Ben Lina.") == "Lina:\nBen Lina.\n\n"


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


def test_format_error_message_for_general_provider_failure() -> None:
    message = format_error_message(ModelProviderError("Ollama request failed"))

    assert "Ollama isteği tamamlanamadı" in message


def test_format_unexpected_error_message_returns_user_friendly_text() -> None:
    message = format_unexpected_error_message()

    assert "Beklenmeyen bir hata oluştu" in message
    assert "arayüz kullanıma hazır" in message


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


def test_gui_adds_sent_message_to_input_history() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")

    gui.send_message()

    assert gui._input_history == ["Hello"]
    assert gui._input_history_index == 1


def test_gui_does_not_add_empty_message_to_input_history() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="   ")

    gui.send_message()

    assert gui._input_history == []


def test_gui_does_not_add_consecutive_duplicate_input_history() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")

    gui.send_message()
    gui.send_message()

    assert gui._input_history == ["Hello"]


def test_gui_history_previous_loads_last_message() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._message_input = _FakeMessageInput()
    gui._record_input_history("selam")
    gui._record_input_history("neler yapabiliyorsun")

    gui._navigate_input_history(-1)

    assert gui._message_input.text == "neler yapabiliyorsun"


def test_gui_history_multiple_previous_loads_older_messages() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._message_input = _FakeMessageInput()
    gui._record_input_history("selam")
    gui._record_input_history("neler yapabiliyorsun")

    gui._navigate_input_history(-1)
    gui._navigate_input_history(-1)

    assert gui._message_input.text == "selam"


def test_gui_history_next_loads_newer_message() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._message_input = _FakeMessageInput()
    gui._record_input_history("selam")
    gui._record_input_history("neler yapabiliyorsun")

    gui._navigate_input_history(-1)
    gui._navigate_input_history(-1)
    gui._navigate_input_history(1)

    assert gui._message_input.text == "neler yapabiliyorsun"


def test_gui_history_next_clears_input_at_end() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._message_input = _FakeMessageInput()
    gui._record_input_history("selam")

    gui._navigate_input_history(-1)
    gui._navigate_input_history(1)

    assert gui._message_input.text == ""


def test_gui_send_message_resets_input_history_index() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="naber")
    gui._input_history = ["selam"]
    gui._input_history_index = 0

    gui.send_message()

    assert gui._input_history_index == 2


def test_gui_history_navigation_does_not_run_when_input_disabled() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._message_input = _FakeMessageInput(state="disabled")
    gui._record_input_history("selam")

    gui._navigate_input_history(-1)

    assert gui._message_input.text == ""
    assert gui._input_history_index == 1


def test_fake_gui_memory_command_fast_response_resets_waiting_state() -> None:
    service = FakeConversationService(
        response_text="Tamam İlhan, bunu hatırlayacağım: kısa cevapları seviyorum."
    )
    gui = _create_test_gui(
        service,
        input_text="bunu hatırla: kısa cevapları seviyorum",
    )
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui.send_message()

    assert service.messages == ["bunu hatırla: kısa cevapları seviyorum"]
    assert gui.recorded_messages == [
        ("İlhan", "bunu hatırla: kısa cevapları seviyorum"),
        ("Lina", "Yazıyor..."),
        ("Lina", "Tamam İlhan, bunu hatırlayacağım: kısa cevapları seviyorum."),
    ]
    assert gui.waiting_states == [True, False]
    assert gui._is_waiting_for_response is False
    assert gui._status_updates[-1] == "Hazır"


def test_fake_gui_file_command_response_renders_normally() -> None:
    service = FakeConversationService(
        response_text="README.md dosyasının içeriği:\n\n# Lina"
    )
    gui = _create_test_gui(service, input_text="README dosyasını oku")

    gui.send_message()

    assert service.messages == ["README dosyasını oku"]
    assert gui.recorded_messages == [
        ("İlhan", "README dosyasını oku"),
        ("Lina", "Yazıyor..."),
        ("Lina", "README.md dosyasının içeriği:\n\n# Lina"),
    ]
    assert gui.waiting_states == [True, False]


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


def test_gui_shows_unexpected_errors_and_resets_waiting_state() -> None:
    service = FakeConversationService(unexpected_error=RuntimeError("sqlite thread error"))
    gui = _create_test_gui(service, input_text="bunu hatırla: kısa cevapları seviyorum")
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui.send_message()

    assert gui.recorded_messages == [
        ("İlhan", "bunu hatırla: kısa cevapları seviyorum"),
        ("Lina", "Yazıyor..."),
        ("Lina", format_unexpected_error_message()),
    ]
    assert gui.waiting_states == [True, False]
    assert gui._is_waiting_for_response is False
    assert gui._status_updates[-1] == "Hata oluştu"
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

    gui._append_message("Lina", "Lina: Lina: Ben Lina.")

    assert chat_log.inserted_text == "Lina:\nBen Lina.\n\n"
    assert gui._message_ranges == [("1.0", "1.0")]


def test_gui_append_message_keeps_identity_response_single_labeled() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    chat_log = _FakeChatLog()
    gui._chat_log = chat_log
    gui._append_message = LinaGui._append_message.__get__(gui, LinaGui)

    gui._append_message("Lina", "Ben Lina, İlhan'ın masaüstü asistanıyım.")

    assert chat_log.inserted_text == "Lina:\nBen Lina, İlhan'ın masaüstü asistanıyım.\n\n"
    assert "Lina:Lina:" not in chat_log.inserted_text


def test_gui_append_message_normalizes_error_response_in_render_path() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    chat_log = _FakeChatLog()
    gui._chat_log = chat_log
    gui._append_message = LinaGui._append_message.__get__(gui, LinaGui)

    gui._append_message("Lina", "Lina:Lina: Modele ulaşılamadı.")

    assert chat_log.inserted_text == "Lina:\nModele ulaşılamadı.\n\n"
    assert "Lina:Lina:" not in chat_log.inserted_text


def test_gui_show_response_replaces_typing_message_without_leaving_label() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    chat_log = _FakeTkTextLog()
    gui._chat_log = chat_log
    gui._append_message = LinaGui._append_message.__get__(gui, LinaGui)
    gui._remove_last_message = LinaGui._remove_last_message.__get__(gui, LinaGui)

    gui._append_message("Lina", "Yazıyor...")
    gui._show_response(ModelResponse(text="Lina: Merhaba İlhan."))

    assert chat_log.visible_text == "Lina:\nMerhaba İlhan.\n\n"
    assert "Yazıyor" not in chat_log.visible_text
    assert "Lina:\nLina:" not in chat_log.visible_text


def test_gui_show_unexpected_error_replaces_typing_message() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    chat_log = _FakeTkTextLog()
    gui._chat_log = chat_log
    gui._append_message = LinaGui._append_message.__get__(gui, LinaGui)
    gui._remove_last_message = LinaGui._remove_last_message.__get__(gui, LinaGui)

    gui._append_message("Lina", "Yazıyor...")
    gui._show_unexpected_error()

    assert chat_log.visible_text == f"Lina:\n{format_unexpected_error_message()}\n\n"
    assert "Yazıyor" not in chat_log.visible_text


def test_gui_single_send_appends_single_final_response() -> None:
    service = FakeConversationService()
    gui = _create_test_gui(service, input_text="Hello")

    gui.send_message()

    assert gui.recorded_messages.count(("Lina", "Response: Hello")) == 1


def test_gui_placeholder_feature_message_adds_assistant_message() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui._show_placeholder_feature_message("Mikrofon özelliği henüz aktif değil İlhan.")

    assert gui.recorded_messages == [
        ("Lina", "Mikrofon özelliği henüz aktif değil İlhan."),
    ]
    assert gui._last_response_text == "Mikrofon özelliği henüz aktif değil İlhan."
    assert gui._status_updates == ["Hazır"]


def test_gui_mic_with_noop_provider_shows_safe_unavailable_message() -> None:
    speech_service = SpeechService(NoOpSTTProvider(), NoOpTTSProvider())
    gui = _create_test_gui(
        FakeConversationService(),
        input_text="",
        speech_service=speech_service,
    )
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui._handle_mic()

    assert gui.recorded_messages == [
        (
            "Lina",
            "Mikrofon özelliği henüz hazır değil İlhan. Speech motoru "
            "bağlandığında konuşmanı metne çevirebileceğim.",
        )
    ]
    assert gui._status_updates == ["Speech kullanılamıyor"]
    assert gui._is_waiting_for_response is False


def test_gui_mic_writes_transcription_to_input_without_sending() -> None:
    provider = FakeSTTProvider()
    speech_service = SpeechService(provider, FakeTTSProvider())
    conversation_service = FakeConversationService()
    gui = _create_test_gui(
        conversation_service,
        input_text="",
        speech_service=speech_service,
    )
    gui._set_input_text = lambda text: setattr(gui, "transcribed_input", text)
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui._handle_mic()

    assert provider.call_count == 1
    assert gui.transcribed_input == "Merhaba Lina"
    assert conversation_service.messages == []
    assert gui.recorded_messages == [
        ("Lina", "Konuşmanı yazıya çevirdim İlhan. Kontrol edip gönderebilirsin.")
    ]
    assert gui.waiting_states == [True, False]
    assert gui._status_updates == ["Konuşma metne çevriliyor...", "Hazır"]
    assert gui._is_waiting_for_response is False


def test_gui_mic_error_resets_controls_and_status() -> None:
    provider = FakeSTTProvider(SpeechServiceError("transcription failed"))
    speech_service = SpeechService(provider, FakeTTSProvider())
    gui = _create_test_gui(
        FakeConversationService(),
        input_text="",
        speech_service=speech_service,
    )
    gui._status_updates = []
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui._handle_mic()

    assert gui.recorded_messages == [
        ("Lina", "Konuşma metne çevrilemedi. Tekrar deneyebilirsin İlhan.")
    ]
    assert gui.waiting_states == [True, False]
    assert gui._status_updates[-1] == "Speech hatası"
    assert gui._is_waiting_for_response is False
    assert gui.input_focus_count == 1


def test_gui_mic_ignores_click_while_another_operation_is_running() -> None:
    speech_service = SpeechService(FakeSTTProvider(), FakeTTSProvider())
    gui = _create_test_gui(
        FakeConversationService(),
        input_text="",
        speech_service=speech_service,
    )
    gui._is_waiting_for_response = True

    gui._handle_mic()

    assert gui.recorded_messages == []


def test_gui_new_chat_uses_clear_chat_flow() -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui.clear_count = 0
    gui._status_updates = []
    gui.clear_chat = lambda: setattr(gui, "clear_count", gui.clear_count + 1)
    gui._update_status_text = lambda text: gui._status_updates.append(text)

    gui._handle_new_chat()

    assert gui.clear_count == 1
    assert gui._status_updates == ["Yeni sohbet mevcut oturumu temizledi."]


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


# --- Branding tests ---


def test_gui_branding_assets_fallback_when_logo_files_are_missing(tmp_path, monkeypatch) -> None:
    gui = _create_test_gui(FakeConversationService(), input_text="")
    monkeypatch.setattr(gui_module, "BRANDING_LOGO_PATH", tmp_path / "missing-logo.png")
    monkeypatch.setattr(gui_module, "BRANDING_ICON_PATH", tmp_path / "missing-icon.png")

    gui._load_branding_assets()

    assert gui._logo_image is None
    assert gui._icon_image is None
    assert gui._root.icon_calls == []


def test_gui_branding_assets_load_existing_logo_and_icon(tmp_path, monkeypatch) -> None:
    logo_path = tmp_path / "lina-logo.png"
    icon_path = tmp_path / "lina-icon.png"
    logo_path.write_text("fake image", encoding="utf-8")
    icon_path.write_text("fake image", encoding="utf-8")
    gui = _create_test_gui(FakeConversationService(), input_text="")
    monkeypatch.setattr(gui_module, "BRANDING_LOGO_PATH", logo_path)
    monkeypatch.setattr(gui_module, "BRANDING_ICON_PATH", icon_path)
    monkeypatch.setattr(gui_module.tk, "PhotoImage", _FakePhotoImage)

    gui._load_branding_assets()

    assert gui._logo_image is not None
    assert gui._icon_image is not None
    assert gui._root.icon_calls == [(True, gui._icon_image)]


def test_gui_sidebar_branding_helper_uses_logo_when_available(monkeypatch) -> None:
    created_widgets: list[_FakePackedWidget] = []
    monkeypatch.setattr(gui_module.tk, "Frame", _make_fake_widget(created_widgets))
    monkeypatch.setattr(gui_module.tk, "Label", _make_fake_widget(created_widgets))
    gui = _create_test_gui(FakeConversationService(), input_text="")
    gui._logo_image = object()

    gui._build_sidebar_branding(_FakePackedWidget())

    assert any(widget.kwargs.get("image") is gui._logo_image for widget in created_widgets)


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


def _create_test_gui(
    service: FakeConversationService,
    input_text: str,
    speech_service: SpeechService | None = None,
):
    gui = LinaGui.__new__(LinaGui)
    gui._conversation_service = service
    gui._thread_factory = ImmediateThread
    gui._root = _FakeRoot()
    gui._is_waiting_for_response = False
    gui._diagnostics_service = None
    gui._speech_service = speech_service
    gui._last_response_text = ""
    gui._message_ranges = []
    gui._input_history = []
    gui._input_history_index = 0
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
    def __init__(self) -> None:
        self.icon_calls = []

    def after(self, delay_ms: int, callback, *args) -> None:
        callback(*args)

    def iconphoto(self, default: bool, image) -> None:
        self.icon_calls.append((default, image))


class _FakePhotoImage:
    def __init__(self, file: str) -> None:
        self.file = file
        self.subsample_calls: list[tuple[int, int]] = []

    def width(self) -> int:
        return 128

    def height(self) -> int:
        return 128

    def subsample(self, x: int, y: int):
        self.subsample_calls.append((x, y))
        return self


class _FakePackedWidget:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs
        self.pack_calls = []

    def pack(self, *args, **kwargs) -> None:
        self.pack_calls.append((args, kwargs))


def _make_fake_widget(created_widgets: list[_FakePackedWidget]):
    def create_widget(*args, **kwargs):
        widget = _FakePackedWidget(*args, **kwargs)
        created_widgets.append(widget)
        return widget

    return create_widget


class _FakeMessageInput:
    def __init__(self, text: str = "", state: str = "normal") -> None:
        self.text = text
        self._state = state

    def cget(self, key: str) -> str:
        if key == "state":
            return self._state
        return ""

    def delete(self, start: str, end: str) -> None:
        self.text = ""

    def insert(self, index: str, text: str) -> None:
        self.text = text


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


class _FakeTkTextLog:
    """Fake Tk Text widget with an implicit trailing newline."""

    def __init__(self) -> None:
        self._content = "\n"

    @property
    def visible_text(self) -> str:
        return self._content[:-1]

    def configure(self, **kwargs) -> None:
        pass

    def delete(self, start: str, end: str) -> None:
        start_index = int(start)
        end_index = int(end)
        self._content = self._content[:start_index] + self._content[end_index:]

    def insert(self, index: str, text: str) -> None:
        insert_index = self._resolve_index(index)
        self._content = self._content[:insert_index] + text + self._content[insert_index:]

    def index(self, idx: str) -> str:
        return str(self._resolve_index(idx))

    def see(self, idx: str) -> None:
        pass

    def _resolve_index(self, idx: str) -> int:
        if idx == "end-1c":
            return len(self._content) - 1
        return len(self._content)
