"""Tests for Lina's PySide6 main window."""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRect
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtWidgets import QApplication, QDialog, QPushButton

from lina.brain.model_provider import EmptyModelResponseError, ModelProviderError, ModelResponse
from lina.interfaces.qt.main_window import (
    AUTO_SCROLL_THRESHOLD_PX,
    LinaMainWindow,
    _classify_voice_confirmation,
    _friendly_vision_error_message,
    clamp_window_geometry,
)
from lina.interfaces.qt.image_loader import ImageLoadError
from lina.services.conversation_models import ConversationResult
from lina.screen.models import LOCAL_FILE, ScreenCaptureError, ScreenContext
from lina.vision.models import PNG_SIGNATURE
from lina.services.model_diagnostics_service import (
    DiagnosticsResult,
    ModelStatus,
    VisionDiagnosticsResult,
    VisionStatus,
)
from lina.speech.models import SpeechState, SpeechTranscriptionResult
from lina.settings.models import UserSettings
from lina.voice.models import VoiceState
from lina.settings.repository import UserSettingsRepository
from lina.settings.service import UserSettingsService
from lina.interfaces.qt.theme import theme_palette


def test_direct_camera_question_empty_response_has_friendly_retry_message() -> None:
    assert _friendly_vision_error_message(EmptyModelResponseError("private")) == (
        "Görüntüyü şu anda yorumlayamadım. Birkaç saniye sonra tekrar deneyelim."
    )


def test_saved_window_geometry_is_clamped_to_visible_screen() -> None:
    available = (QRect(0, 0, 1920, 1080),)
    assert clamp_window_geometry(QRect(5000, 4000, 2400, 1400), available) == QRect(0, 0, 1920, 1080)
    assert clamp_window_geometry(QRect(100, 120, 1000, 700), available) == QRect(100, 120, 1000, 700)


class ImmediateThreadPool:
    def __init__(self) -> None:
        self.started = 0

    def start(self, worker) -> None:
        self.started += 1
        worker.run()


class DeferredThreadPool:
    def __init__(self) -> None:
        self.workers = []

    def start(self, worker) -> None:
        self.workers.append(worker)

    def run_next(self) -> None:
        self.workers.pop(0).run()


class FakeConversationService:
    def __init__(
        self,
        response_text: str = "Yanıt",
        error: Exception | None = None,
        consume_attachment: bool = True,
    ) -> None:
        self.messages: list[str] = []
        self._response_text = response_text
        self._error = error
        self._consume_attachment = consume_attachment
        self.inputs = []

    def handle_message(self, message: str) -> ModelResponse:
        self.messages.append(message)
        if self._error is not None:
            raise self._error
        return ModelResponse(text=self._response_text)

    def handle_input(self, conversation_input) -> ConversationResult:
        self.inputs.append(conversation_input)
        self.messages.append(conversation_input.text)
        if self._error is not None:
            raise self._error
        return ConversationResult(
            response=ModelResponse(text=self._response_text),
            attachment_consumed=self._consume_attachment,
        )


class FakeDiagnosticsService:
    configured_model = "llama3"

    def check_status(self) -> DiagnosticsResult:
        return DiagnosticsResult(
            status=ModelStatus.READY,
            model_name="llama3",
            message="Model hazır.",
        )


class FakeVisionDiagnosticsService:
    configured_model = "qwen3-vl:2b"

    def __init__(self, status: VisionStatus = VisionStatus.READY) -> None:
        self.status = status

    def check_status(self) -> VisionDiagnosticsResult:
        return VisionDiagnosticsResult(
            status=self.status,
            model_name=self.configured_model,
            message="Vision hazır." if self.status is VisionStatus.READY else "Vision yok.",
        )


class FakeSpeechService:
    def __init__(self, text: str = "Merhaba Lina", available: bool = True) -> None:
        self._text = text
        self._available = available
        self.stop_count = 0
        self.transcribe_count = 0

    def is_stt_available(self) -> bool:
        return self._available

    def get_state(self) -> SpeechState:
        return SpeechState.IDLE

    def transcribe_once(self) -> SpeechTranscriptionResult:
        self.transcribe_count += 1
        return SpeechTranscriptionResult(
            text=self._text,
            confidence=0.9,
            source="fake",
            is_final=True,
        )

    def stop_listening(self) -> None:
        self.stop_count += 1


class FakeVoiceController:
    def __init__(self) -> None:
        self.state = VoiceState.IDLE
        self.settings = None
        self.spoken: list[str] = []
        self.listeners = []

    @property
    def wake_word_available(self):
        return False

    def list_voices(self):
        return ()

    def subscribe(self, listener):
        self.listeners.append(listener)

    def configure(self, settings):
        self.settings = settings

    def speak(self, text):
        if self.settings is None or not self.settings.responses_enabled:
            return False
        self.spoken.append(text)
        return True

    @property
    def responses_enabled(self):
        return bool(self.settings and self.settings.responses_enabled)

    def begin_thinking(self):
        self.state = VoiceState.THINKING

    def finish_interaction(self):
        self.state = VoiceState.IDLE

    def stop(self):
        return False

    def shutdown(self):
        return None


def test_voice_confirmation_variants_are_conservative():
    for text in ("evet", "Onayla!", "tamam", "oluştur", "kaydet"):
        assert _classify_voice_confirmation(text) == "yes"
    for text in ("hayır", "iptal", "vazgeç", "boşver", "gerek yok"):
        assert _classify_voice_confirmation(text) == "no"
    assert _classify_voice_confirmation("belki") is None
    assert _classify_voice_confirmation("evet ama") is None


def test_hands_free_voice_states_have_visible_text_indicators(qtbot):
    window = LinaMainWindow(FakeConversationService(), thread_pool=ImmediateThreadPool())
    qtbot.addWidget(window)
    window.show()
    qtbot.wait(10)
    expected = {
        VoiceState.WAKE_LISTENING: "Hey Lina bekleniyor",
        VoiceState.WAKE_DETECTED: "Dinliyorum",
        VoiceState.COMMAND_LISTENING: "Dinliyorum",
        VoiceState.TRANSCRIBING: "Yazıya çeviriyor",
        VoiceState.THINKING: "Düşünüyor",
        VoiceState.SPEAKING: "Konuşuyor",
        VoiceState.COOLDOWN: "Beklemeye alındı",
        VoiceState.DISABLED: "kapalı",
    }
    for state, label in expected.items():
        window._apply_voice_state(state)
        assert label in window._voice_status.text()


def _valid_png() -> bytes:
    image = QImage(16, 9, QImage.Format.Format_RGB32)
    image.fill(0x336699)
    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def _screen_context(
    width: int = 1920,
    height: int = 1080,
    source: str = "screen_capture",
) -> ScreenContext:
    image_bytes = _valid_png()
    return ScreenContext(
        image_bytes=image_bytes,
        width=width,
        height=height,
        captured_at=datetime(2026, 7, 11, 22, 30),
        display_name="selected.png" if source == LOCAL_FILE else "Display 1",
        estimated_byte_size=len(image_bytes),
        source=source,
    )


class FakeScreenCaptureService:
    def __init__(
        self,
        context: ScreenContext | None = None,
        error: Exception | None = None,
    ) -> None:
        self.context = context or _screen_context()
        self.error = error
        self.capture_count = 0

    def capture(self) -> ScreenContext:
        self.capture_count += 1
        if self.error is not None:
            raise self.error
        return self.context

    def capture_region(self, rectangle, screen) -> ScreenContext:
        self.capture_count += 1
        return _screen_context(source="screen_capture_region")


class FakeImageLoader:
    def __init__(
        self,
        context: ScreenContext | None = None,
        error: Exception | None = None,
    ) -> None:
        self.context = context or _screen_context(source=LOCAL_FILE)
        self.error = error
        self.paths: list[Path] = []

    def load(self, path: Path) -> ScreenContext:
        self.paths.append(path)
        if self.error is not None:
            raise self.error
        return self.context


class FakePreviewDialog:
    def __init__(self, result: QDialog.DialogCode) -> None:
        self._result = result
        self.exec_count = 0

    def exec(self) -> QDialog.DialogCode:
        self.exec_count += 1
        return self._result


def _assistant_texts(window: LinaMainWindow) -> list[str]:
    texts: list[str] = []
    for row in window._message_rows:
        message = getattr(row, "_message_widget", None)
        if getattr(message, "role", None) == "assistant":
            texts.append(message.text_label.text())
    return texts


def _user_messages(window: LinaMainWindow) -> list[object]:
    messages = []
    for row in window._message_rows:
        message = getattr(row, "_message_widget", None)
        if getattr(message, "role", None) == "user":
            messages.append(message)
    return messages


def test_final_normal_chat_response_uses_common_voice_path(qtbot, tmp_path) -> None:
    settings_service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    enabled = UserSettings.from_dict({"speech": {"voice_responses_enabled": True}})
    settings_service.update(enabled)
    voice = FakeVoiceController()
    window = LinaMainWindow(
        FakeConversationService(response_text="Final yanıt"),
        speech_service=FakeSpeechService(available=False),
        user_settings_service=settings_service,
        voice_controller=voice,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._composer.set_text("Merhaba")
    window.send_message()
    assert voice.spoken == ["Final yanıt"]
    qtbot.wait(20)
    window._force_exit = True
    window.close()


def test_voice_disabled_skips_final_response(qtbot) -> None:
    voice = FakeVoiceController()
    window = LinaMainWindow(
        FakeConversationService(response_text="Sessiz yanıt"),
        speech_service=FakeSpeechService(available=False),
        voice_controller=voice,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._composer.set_text("Merhaba")
    window.send_message()
    assert voice.spoken == []
    qtbot.wait(20)
    window._force_exit = True
    window.close()


def test_settings_apply_updates_runtime_voice_controller(qtbot, tmp_path) -> None:
    voice = FakeVoiceController()
    settings_service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    window = LinaMainWindow(
        FakeConversationService(),
        speech_service=FakeSpeechService(available=False),
        user_settings_service=settings_service,
        voice_controller=voice,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.open_settings()
    window._settings_dialog._voice_responses.setChecked(True)
    window._settings_dialog._apply()
    assert voice.settings.responses_enabled
    assert settings_service.current.speech.voice_responses_enabled
    window._settings_dialog.close()
    qtbot.wait(20)
    window._force_exit = True
    window.close()


def test_short_tool_result_uses_common_voice_path(qtbot) -> None:
    voice = FakeVoiceController()
    window = LinaMainWindow(
        FakeConversationService(),
        speech_service=FakeSpeechService(available=False),
        voice_controller=voice,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._apply_user_settings(
        UserSettings.from_dict({"speech": {"voice_responses_enabled": True}})
    )
    window._finish_routed_intent("Saat kaç?", "Saat 12:30.", datetime.now())
    assert voice.spoken == ["Saat 12:30."]
    qtbot.wait(20)
    window._force_exit = True
    window.close()


def test_cancelled_stale_response_does_not_start_tts(qtbot) -> None:
    voice = FakeVoiceController()
    pool = DeferredThreadPool()
    window = LinaMainWindow(
        FakeConversationService(response_text="Geç yanıt"),
        speech_service=FakeSpeechService(available=False),
        voice_controller=voice,
        thread_pool=pool,
    )
    qtbot.addWidget(window)
    window._apply_user_settings(
        UserSettings.from_dict({"speech": {"voice_responses_enabled": True}})
    )
    while pool.workers:
        pool.run_next()
    window._composer.set_text("Merhaba")
    window.send_message()
    window.cancel_active_response()
    pool.run_next()
    assert voice.spoken == []
    qtbot.wait(20)
    window._force_exit = True
    window.close()


def test_settings_toggle_disables_speech_and_vision_controls(qtbot, tmp_path) -> None:
    settings_service = UserSettingsService(
        UserSettingsRepository(tmp_path / "settings.json")
    )
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(),
        user_settings_service=settings_service,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    updated = UserSettings.from_dict({"speech": {"enabled": False}, "vision": {"enabled": False}})

    window._apply_user_settings(updated)

    assert window._composer.mic_button.isEnabled() is False
    assert window._composer.attachment_button.isEnabled() is False
    assert window._composer.screen_button.isEnabled() is False


def test_runtime_light_theme_refreshes_open_settings_dialog(qtbot, tmp_path) -> None:
    settings_service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    window = LinaMainWindow(FakeConversationService(), user_settings_service=settings_service, thread_pool=ImmediateThreadPool())
    qtbot.addWidget(window)
    window.open_settings()
    updated = UserSettings.from_dict({"appearance": {"theme": "light", "font_scale": 1.35}})
    window._apply_user_settings(updated)
    stylesheet = QApplication.instance().styleSheet()
    assert theme_palette("light")["app_bg"] in stylesheet
    assert "font-size: 15pt" in stylesheet
    assert window._settings_dialog.isVisible()
    window._settings_dialog.close()
    window._force_exit = True
    window.close()
    qtbot.wait(300)


def test_main_window_builds_shell_and_welcome_message(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    assert window.windowTitle() == "Lina"
    assert window._welcome_state is not None
    assert "İlhan" in window._welcome_state.greeting_label.text()
    assert _assistant_texts(window) == []
    assert window._composer.mic_button.isEnabled() is False
    assert window._model_status.text() == "Model · hazır"
    assert window._speech_status.text() == "Mic · kapalı"
    assert window._scroll.objectName() == "chatTimelineScroll"
    assert window._scroll.viewport().objectName() == "chatTimelineViewport"
    assert window._message_container.objectName() == "chatTimeline"
    assert window._status_button.text() == "Hazır"
    assert window._inspector_button.text() == "Araçlar"
    assert window._inspector.isHidden()
    tools = window._build_tools_menu()
    assert [action.text() for action in tools.actions() if not action.isSeparator()] == [
        "Komut paleti", "Agent ile çalış", "Hazır görevler", "Agent Görev Merkezi",
        "Sohbet görünümü", "Sistem ayrıntıları"
    ]


def test_send_message_removes_typing_and_normalizes_lina_prefix(qtbot) -> None:
    service = FakeConversationService(response_text="Lina:Lina: Selam İlhan")
    window = LinaMainWindow(
        conversation_service=service,
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.show()

    window._composer.set_text("selam")
    window.send_message()

    assert service.messages == ["selam"]
    assert window._welcome_state is None
    assert len(window._message_rows) >= 2
    assert window._typing_message is None
    assert "Yazıyor..." not in _assistant_texts(window)
    assert _assistant_texts(window)[-1] == "Selam İlhan"
    assert window._is_waiting is False
    assert window._composer.input.isEnabled() is True
    assert window._composer.send_button.text() == ""
    assert window._composer.send_button.accessibleName() == "Mesajı gönder"


def test_send_message_error_resets_ui(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(error=ModelProviderError("ollama down")),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.show()

    window._composer.set_text("merhaba")
    window.send_message()

    assert window._typing_message is None
    assert window._is_waiting is False
    assert "Modele ulaşılamadı" in _assistant_texts(window)[-1]
    assert window._composer.input.isEnabled() is True
    assert window._composer.send_button.text() == ""
    assert window._composer.send_button.accessibleName() == "Mesajı gönder"


def test_waiting_response_keeps_input_enabled_and_send_button_becomes_stop(qtbot) -> None:
    pool = DeferredThreadPool()
    window = LinaMainWindow(
        conversation_service=FakeConversationService(response_text="Geç cevap"),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=pool,
    )
    qtbot.addWidget(window)

    window._composer.set_text("merhaba")
    window.send_message()

    assert window._is_waiting is True
    assert window._composer.input.isEnabled() is True
    assert window._composer.send_button.text() == ""
    assert window._composer.send_button.accessibleName() == "Yanıtı durdur"
    assert window._composer.text() == ""


def test_stop_button_ignores_late_conversation_result(qtbot) -> None:
    pool = DeferredThreadPool()
    window = LinaMainWindow(
        conversation_service=FakeConversationService(response_text="Bu görünmemeli"),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=pool,
    )
    qtbot.addWidget(window)

    window._composer.set_text("uzun cevap ver")
    window.send_message()
    window._composer.send_button.click()

    assert window._is_waiting is False
    assert window._typing_message is None
    assert window._composer.input.isEnabled() is True
    assert window._composer.send_button.text() == ""
    assert window._composer.send_button.accessibleName() == "Mesajı gönder"
    assert "Yanıt durduruldu" in window._status_label.text()

    pool.run_next()

    assert "Bu görünmemeli" not in _assistant_texts(window)


def test_speech_transcription_writes_input_without_sending(qtbot) -> None:
    service = FakeConversationService()
    speech = FakeSpeechService(text="Merhaba Lina")
    window = LinaMainWindow(
        conversation_service=service,
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=speech,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window.handle_mic_request()

    assert window._composer.text() == "Merhaba Lina"
    assert service.messages == []
    assert speech.transcribe_count == 1
    assert "Konuşmanı yazıya çevirdim" in _assistant_texts(window)[-1]


def test_empty_speech_transcription_does_not_show_success(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(text="   "),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window.handle_mic_request()

    assert window._composer.text() == ""
    assert "Net bir konuşma algılayamadım" in _assistant_texts(window)[-1]


def test_clear_chat_resets_visible_session(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._append_assistant_message("Ek mesaj")

    window.clear_chat()

    assert len(window._message_rows) == 0
    assert window._welcome_state is not None


def test_clear_chat_scrolls_to_top(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.resize(1040, 640)
    window.show()

    for index in range(30):
        window._append_assistant_message(f"Uzun mesaj {index}\n" * 5)
    qtbot.waitUntil(
        lambda: window._scroll.verticalScrollBar().maximum() > AUTO_SCROLL_THRESHOLD_PX
    )
    window._scroll.verticalScrollBar().setValue(window._scroll.verticalScrollBar().maximum())

    window.clear_chat()
    qtbot.wait(75)

    assert window._scroll.verticalScrollBar().value() == window._scroll.verticalScrollBar().minimum()


def test_bottom_action_buttons_are_removed_without_removing_status(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    button_texts = {button.text() for button in window.findChildren(QPushButton)}

    assert "Temizle" not in button_texts
    assert "Son cevabı kopyala" not in button_texts
    assert window._status_label.text() == "Hazır"


def test_attachment_button_loads_user_selected_image(qtbot, monkeypatch) -> None:
    loader = FakeImageLoader()
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        image_loader=loader,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    monkeypatch.setattr(
        "lina.interfaces.qt.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("C:/selected.png", "Images"),
    )

    window._composer.attachment_button.click()

    assert loader.paths == [Path("C:/selected.png")]
    assert window._screen_context is loader.context
    assert "selected.png" in window._composer.screen_context_label.text()
    assert window._status_label.text() == "Görsel analize hazır"


def test_attachment_picker_cancel_keeps_existing_state(qtbot, monkeypatch) -> None:
    loader = FakeImageLoader()
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        image_loader=loader,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    monkeypatch.setattr(
        "lina.interfaces.qt.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("", ""),
    )

    window.handle_image_upload()

    assert loader.paths == []
    assert window._screen_context is None


def test_attachment_load_error_is_user_friendly(qtbot, monkeypatch) -> None:
    loader = FakeImageLoader(error=ImageLoadError("invalid"))
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        image_loader=loader,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    monkeypatch.setattr(
        "lina.interfaces.qt.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("C:/broken.png", "Images"),
    )

    window.handle_image_upload()

    assert window._screen_context is None
    assert window._status_label.text() == "Seçilen görsel yüklenemedi."


def test_screen_capture_acceptance_adds_temporary_context(qtbot) -> None:
    capture = FakeScreenCaptureService()
    dialog = FakePreviewDialog(QDialog.DialogCode.Accepted)
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        screen_capture_service=capture,
        screen_preview_factory=lambda context, parent: dialog,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window._screen_menu.actions()[0].trigger()

    assert capture.capture_count == 1
    assert dialog.exec_count == 1
    assert window._screen_context is capture.context
    assert window._composer.screen_context_chip.isVisibleTo(window)
    assert "1920×1080" in window._composer.screen_context_label.text()
    assert window._composer.screen_button.isEnabled() is True
    assert window._status_label.text() == "Ekran bağlamı eklendi"


def test_screen_menu_contains_full_and_region_capture_actions(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    actions = [action.text() for action in window._screen_menu.actions()]

    assert actions == ["Tüm Ekranı Yakala", "Alan Seçerek Yakala"]
    assert window._composer.screen_button.toolTip() == (
        "Tam ekran veya seçili alan görüntüsü ekle"
    )


def test_region_capture_opens_overlay_and_cancel_restores_ui(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window.handle_region_capture()

    assert window._region_overlay is not None
    assert window._is_screen_capture_busy is True
    window._cancel_region_capture()
    assert window._region_overlay is None
    assert window._is_screen_capture_busy is False
    assert window._composer.screen_button.isEnabled() is True
    assert window._status_label.text() == "Alan seçimi iptal edildi."


def test_region_capture_uses_same_preview_and_adds_region_context(qtbot) -> None:
    capture = FakeScreenCaptureService()
    dialog = FakePreviewDialog(QDialog.DialogCode.Accepted)
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        screen_capture_service=capture,
        screen_preview_factory=lambda context, parent: dialog,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._is_screen_capture_busy = True
    window._composer.screen_button.setEnabled(False)
    screen = QGuiApplication.primaryScreen()

    window._finish_region_capture(screen, QRect(10, 10, 100, 80))

    assert dialog.exec_count == 1
    assert window._screen_context is not None
    assert window._screen_context.source == "screen_capture_region"
    assert window._is_screen_capture_busy is False
    assert window._composer.screen_button.isEnabled() is True


def test_ready_vision_status_is_shown_on_screen_attachment(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        vision_diagnostics_service=FakeVisionDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window._set_screen_context(_screen_context())

    assert window._composer.screen_context_note.text() == "Analize hazır"


def test_screen_capture_cancel_does_not_add_context(qtbot) -> None:
    capture = FakeScreenCaptureService()
    dialog = FakePreviewDialog(QDialog.DialogCode.Rejected)
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        screen_capture_service=capture,
        screen_preview_factory=lambda context, parent: dialog,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window.handle_screen_request()

    assert window._screen_context is None
    assert window._composer.screen_context_chip.isHidden()
    assert window._composer.screen_button.isEnabled() is True
    assert window._status_label.text() == "Hazır"


def test_screen_capture_error_restores_button_without_stale_context(qtbot) -> None:
    capture = FakeScreenCaptureService(error=ScreenCaptureError("no screen"))
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        screen_capture_service=capture,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window.handle_screen_request()

    assert window._screen_context is None
    assert window._composer.screen_button.isEnabled() is True
    assert window._is_screen_capture_busy is False
    assert window._status_label.text() == "Ekran görüntüsü alınamadı."


def test_duplicate_screen_request_is_ignored_while_capture_is_busy(qtbot) -> None:
    capture = FakeScreenCaptureService()
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        screen_capture_service=capture,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._is_screen_capture_busy = True

    window.handle_screen_request()

    assert capture.capture_count == 0


def test_screen_context_can_be_removed_and_replaced(qtbot) -> None:
    first = _screen_context(1280, 720)
    second = _screen_context(2560, 1440)
    capture = FakeScreenCaptureService(first)
    dialog = FakePreviewDialog(QDialog.DialogCode.Accepted)
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        screen_capture_service=capture,
        screen_preview_factory=lambda context, parent: dialog,
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window.handle_screen_request()
    capture.context = second
    window.handle_screen_request()

    assert window._screen_context is second
    assert "2560×1440" in window._composer.screen_context_label.text()

    window._composer.screen_context_remove_button.click()

    assert window._screen_context is None
    assert window._composer.screen_context_chip.isHidden()
    assert window._status_label.text() == "Ekran bağlamı kaldırıldı"


def test_visual_message_can_restore_attachment_without_sending(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    context = _screen_context()
    message = window._append_user_message(
        "Bu görseli açıkla",
        image_bytes=context.image_bytes,
        visual_context=context,
    )

    message.reanalyze_button.click()

    assert window._screen_context is context
    assert window._composer.screen_context_chip.isVisibleTo(window)
    assert window._composer.text() == ""


def test_screen_context_is_sent_once_and_consumed_after_success(qtbot) -> None:
    conversation = FakeConversationService()
    window = LinaMainWindow(
        conversation_service=conversation,
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        screen_capture_service=FakeScreenCaptureService(),
        screen_preview_factory=lambda context, parent: FakePreviewDialog(
            QDialog.DialogCode.Accepted
        ),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.handle_screen_request()

    window._composer.set_text("Merhaba")
    window.send_message()

    assert conversation.messages == ["Merhaba"]
    assert conversation.inputs[0].image_attachment.data.startswith(PNG_SIGNATURE)
    assert window._screen_context is None
    assert window._composer.screen_context_chip.isHidden()
    assert window._status_label.text() == "Ekran görüntüsü analiz edildi"
    user_message = _user_messages(window)[-1]
    assert user_message.image_label is not None
    assert user_message.image_label.pixmap().isNull() is False


def test_screen_context_is_retained_after_vision_failure(qtbot) -> None:
    conversation = FakeConversationService(error=ModelProviderError("request timed out"))
    context = _screen_context()
    window = LinaMainWindow(
        conversation_service=conversation,
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._set_screen_context(context)

    window._composer.set_text("Bu ekranı açıkla")
    window.send_message()

    assert window._screen_context is context
    assert window._composer.screen_context_chip.isHidden() is False
    assert "zaman aşımına uğradı" in _assistant_texts(window)[-1]
    assert window._is_waiting is False


def test_empty_vision_response_shows_specific_error(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    window._handle_conversation_error(
        ModelProviderError("Ollama response contains empty text content"),
        vision_request=True,
    )

    assert "boş cevap döndürdü" in _assistant_texts(window)[-1]


def test_screen_context_with_empty_input_is_not_sent(qtbot) -> None:
    conversation = FakeConversationService()
    window = LinaMainWindow(
        conversation_service=conversation,
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._set_screen_context(_screen_context())

    window.send_message()

    assert conversation.inputs == []
    assert window._screen_context is not None
    assert window._status_label.text() == "Ekran görüntüsü hakkında bir soru yaz."


def test_vision_request_uses_screen_typing_indicator(qtbot) -> None:
    pool = DeferredThreadPool()
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=pool,
    )
    qtbot.addWidget(window)
    window._set_screen_context(_screen_context())
    window._composer.set_text("Bu ekranda ne var?")

    window.send_message()

    assert window._typing_message is not None
    assert window._typing_message.text_label.text() == "Lina ekranı inceliyor..."


def test_removed_context_is_not_restored_by_pending_vision_result(qtbot) -> None:
    pool = DeferredThreadPool()
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=pool,
    )
    qtbot.addWidget(window)
    window._set_screen_context(_screen_context())
    window._composer.set_text("Bu ekranda ne var?")
    window.send_message()

    window.remove_screen_context()
    pool.run_next()

    assert window._screen_context is None
    assert window._composer.screen_context_chip.isHidden()


def test_clear_chat_removes_screen_context(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._set_screen_context(_screen_context())

    window.clear_chat()

    assert window._screen_context is None
    assert window._composer.screen_context_chip.isHidden()


def test_close_removes_screen_context(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window._set_screen_context(_screen_context())

    window.close()

    assert window._screen_context is None
    assert window._composer.screen_context_chip.isHidden()


def test_auto_scroll_goes_to_bottom_when_bottom_mode_is_active(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.resize(1040, 640)
    window.show()

    for index in range(30):
        window._append_assistant_message(f"Uzun mesaj {index}\n" * 5)
    qtbot.waitUntil(lambda: window._scroll.verticalScrollBar().maximum() > 0)

    bar = window._scroll.verticalScrollBar()
    bar.setValue(bar.maximum())
    window._append_assistant_message("En altta kalmalı")
    qtbot.waitUntil(lambda: bar.value() == bar.maximum())


def test_auto_scroll_retries_for_long_assistant_messages(qtbot) -> None:
    service = FakeConversationService(response_text=("Uzun cevap\n" * 80))
    window = LinaMainWindow(
        conversation_service=service,
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.resize(1040, 640)
    window.show()

    window._composer.set_text("uzun cevap ver")
    window.send_message()

    bar = window._scroll.verticalScrollBar()
    qtbot.waitUntil(lambda: bar.maximum() > 0)
    qtbot.waitUntil(lambda: bar.value() == bar.maximum())


def test_auto_scroll_tracks_assistant_bubble_growth_after_initial_scroll(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.resize(1040, 640)
    window.show()

    message = window._append_assistant_message("Kısa cevap")
    bar = window._scroll.verticalScrollBar()
    qtbot.wait(30)

    message.text_label.setText("Geç büyüyen Lina cevabı\n" * 120)
    message.raw_text = message.text_label.text()
    window._message_container.layout().activate()
    window._schedule_scroll_to_bottom()

    qtbot.waitUntil(lambda: bar.maximum() > 0)
    qtbot.waitUntil(lambda: bar.value() == bar.maximum())


def test_auto_scroll_preserves_position_when_user_reads_old_messages(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    window.resize(1040, 640)
    window.show()

    for index in range(30):
        window._append_assistant_message(f"Uzun mesaj {index}\n" * 5)
    qtbot.waitUntil(
        lambda: window._scroll.verticalScrollBar().maximum() > AUTO_SCROLL_THRESHOLD_PX
    )

    bar = window._scroll.verticalScrollBar()
    bar.setValue(0)
    window._update_auto_scroll_state()
    window._append_assistant_message("Konum korunmalı")
    qtbot.wait(50)

    assert bar.value() == 0
