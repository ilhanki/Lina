"""Tests for Lina's PySide6 main window."""

from datetime import datetime

from PySide6.QtWidgets import QDialog

from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.interfaces.qt.main_window import LinaMainWindow
from lina.screen.models import ScreenCaptureError, ScreenContext
from lina.services.model_diagnostics_service import DiagnosticsResult, ModelStatus
from lina.speech.models import SpeechState, SpeechTranscriptionResult


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
    def __init__(self, response_text: str = "Yanıt", error: Exception | None = None) -> None:
        self.messages: list[str] = []
        self._response_text = response_text
        self._error = error

    def handle_message(self, message: str) -> ModelResponse:
        self.messages.append(message)
        if self._error is not None:
            raise self._error
        return ModelResponse(text=self._response_text)


class FakeDiagnosticsService:
    configured_model = "llama3"

    def check_status(self) -> DiagnosticsResult:
        return DiagnosticsResult(
            status=ModelStatus.READY,
            model_name="llama3",
            message="Model hazır.",
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


def _screen_context(width: int = 1920, height: int = 1080) -> ScreenContext:
    return ScreenContext(
        image_bytes=b"temporary-screen-bytes",
        width=width,
        height=height,
        captured_at=datetime(2026, 7, 11, 22, 30),
        display_name="Display 1",
        estimated_byte_size=22,
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


def test_main_window_builds_shell_and_welcome_message(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)

    assert window.windowTitle() == "Lina"
    assert "Merhaba İlhan" in _assistant_texts(window)[0]
    assert window._composer.mic_button.isEnabled() is False
    assert window._model_status.text() == "Model · hazır"
    assert window._speech_status.text() == "Mic · kapalı"


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
    assert window._typing_message is None
    assert "Yazıyor..." not in _assistant_texts(window)
    assert _assistant_texts(window)[-1] == "Selam İlhan"
    assert window._is_waiting is False
    assert window._composer.input.isEnabled() is True
    assert window._composer.send_button.text() == "Gönder"


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
    assert window._composer.send_button.text() == "Gönder"


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
    assert window._composer.send_button.text() == "Durdur"
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
    assert window._composer.send_button.text() == "Gönder"
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

    assert len(window._message_rows) == 1
    assert "Merhaba İlhan" in _assistant_texts(window)[0]


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
    qtbot.waitUntil(lambda: window._scroll.verticalScrollBar().maximum() > 0)
    window._scroll.verticalScrollBar().setValue(window._scroll.verticalScrollBar().maximum())

    window.clear_chat()
    qtbot.wait(75)

    assert window._scroll.verticalScrollBar().value() == window._scroll.verticalScrollBar().minimum()


def test_attachment_placeholder_uses_status_without_appending_chat(qtbot) -> None:
    window = LinaMainWindow(
        conversation_service=FakeConversationService(),
        diagnostics_service=FakeDiagnosticsService(),
        speech_service=FakeSpeechService(available=False),
        thread_pool=ImmediateThreadPool(),
    )
    qtbot.addWidget(window)
    initial_count = len(window._message_rows)

    window._composer.attachment_button.click()
    assert len(window._message_rows) == initial_count
    assert "Dosya yükleme" in window._status_label.text()


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

    window._composer.screen_button.click()

    assert capture.capture_count == 1
    assert dialog.exec_count == 1
    assert window._screen_context is capture.context
    assert window._composer.screen_context_chip.isVisibleTo(window)
    assert "1920×1080" in window._composer.screen_context_label.text()
    assert window._composer.screen_button.isEnabled() is True
    assert window._status_label.text() == "Ekran bağlamı eklendi"


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


def test_screen_context_is_not_sent_to_conversation_service(qtbot) -> None:
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
    assert window._screen_context is not None


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
    qtbot.waitUntil(lambda: window._scroll.verticalScrollBar().maximum() > 0)

    bar = window._scroll.verticalScrollBar()
    bar.setValue(0)
    window._update_auto_scroll_state()
    window._append_assistant_message("Konum korunmalı")
    qtbot.wait(50)

    assert bar.value() == 0
