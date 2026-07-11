"""PySide6 desktop window for Lina."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer, QThreadPool
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from lina.brain.model_provider import ModelResponse
from lina.interfaces.qt.formatting import (
    derive_session_title,
    format_welcome_message,
    friendly_error_message,
    normalize_assistant_text,
)
from lina.interfaces.qt.theme import (
    MESSAGE_FONT_DEFAULT,
    clamp_message_font_size,
    resolve_font_family,
)
from lina.interfaces.qt.widgets import ChatMessageWidget, ComposerWidget, SidebarWidget
from lina.interfaces.qt.worker import FunctionWorker
from lina.services.conversation_service import ConversationService
from lina.services.model_diagnostics_service import (
    DiagnosticsResult,
    ModelDiagnosticsService,
    ModelStatus,
    format_status_message,
)
from lina.speech.models import (
    SpeechServiceError,
    SpeechState,
    SpeechTranscriptionResult,
    SpeechUnavailableError,
)
from lina.speech.service import SpeechService


APP_VERSION = "v0.6.3-alpha"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
BRANDING_LOGO_PATH = PROJECT_ROOT / "assets" / "branding" / "lina-logo.png"
BRANDING_ICON_PATH = PROJECT_ROOT / "assets" / "branding" / "lina-icon.png"


class LinaMainWindow(QMainWindow):
    """Modern PySide6 chat interface backed by Lina's existing services."""

    def __init__(
        self,
        conversation_service: ConversationService,
        diagnostics_service: ModelDiagnosticsService | None = None,
        speech_service: SpeechService | None = None,
        thread_pool: QThreadPool | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._conversation_service = conversation_service
        self._diagnostics_service = diagnostics_service
        self._speech_service = speech_service
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._workers: set[FunctionWorker] = set()
        self._message_rows: list[QWidget] = []
        self._typing_message: ChatMessageWidget | None = None
        self._last_response_text = ""
        self._input_history: list[str] = []
        self._input_history_index = 0
        self._is_waiting = False
        self._is_speech_busy = False
        self._message_font_size = MESSAGE_FONT_DEFAULT
        self._font_family = resolve_font_family()
        self._session_title_text = "Yeni Sohbet"

        self.setWindowTitle("Lina")
        self.setMinimumSize(1040, 680)
        self.resize(1240, 780)
        self._apply_window_icon()
        self._build_layout()
        self._bind_shortcuts()
        self._append_assistant_message(format_welcome_message())
        self._composer.input.setFocus()
        self._run_initial_diagnostics()
        self._refresh_speech_status()

    def _build_layout(self) -> None:
        central = QWidget(self)
        central.setObjectName("centralWidget")
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        model_name = (
            self._diagnostics_service.configured_model
            if self._diagnostics_service is not None
            else "model bilinmiyor"
        )
        self._sidebar = SidebarWidget(
            logo_path=BRANDING_LOGO_PATH,
            version=APP_VERSION,
            model_name=model_name,
            parent=self,
        )
        root_layout.addWidget(self._sidebar)

        panel = QWidget(self)
        panel.setObjectName("chatPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(12)
        root_layout.addWidget(panel, 1)

        self._build_header(panel_layout)
        self._build_chat_area(panel_layout)
        self._build_footer(panel_layout)
        self.setCentralWidget(central)

        self._sidebar.new_chat_requested.connect(self.clear_chat)
        self._sidebar.collapse_requested.connect(self._sidebar.toggle)
        self._sidebar.font_decrease_requested.connect(lambda: self._change_font_size(-1))
        self._sidebar.font_increase_requested.connect(lambda: self._change_font_size(1))

    def _build_header(self, parent_layout: QVBoxLayout) -> None:
        header = QWidget(self)
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        titles = QVBoxLayout()
        self._session_title = QLabel(self._session_title_text, header)
        self._session_title.setStyleSheet("font-size: 15pt; font-weight: 700;")
        titles.addWidget(self._session_title)
        subtitle = QLabel("Lina ile yerel sohbet", header)
        subtitle.setObjectName("mutedLabel")
        titles.addWidget(subtitle)
        layout.addLayout(titles, 1)

        self._model_status = QLabel("Model kontrol ediliyor...", header)
        self._model_status.setObjectName("statusChip")
        layout.addWidget(self._model_status)

        self._speech_status = QLabel("Mic: hazırlanıyor", header)
        self._speech_status.setObjectName("statusChip")
        layout.addWidget(self._speech_status)
        parent_layout.addWidget(header)

    def _build_chat_area(self, parent_layout: QVBoxLayout) -> None:
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._message_container = QWidget(self._scroll)
        self._message_layout = QVBoxLayout(self._message_container)
        self._message_layout.setContentsMargins(4, 4, 4, 4)
        self._message_layout.setSpacing(14)
        self._message_layout.addStretch(1)
        self._scroll.setWidget(self._message_container)
        parent_layout.addWidget(self._scroll, 1)

    def _build_footer(self, parent_layout: QVBoxLayout) -> None:
        self._composer = ComposerWidget(
            font_family=self._font_family,
            font_size=self._message_font_size,
            parent=self,
        )
        parent_layout.addWidget(self._composer)

        footer = QWidget(self)
        footer.setObjectName("statusPanel")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        self._status_label = QLabel("Hazır", footer)
        self._status_label.setObjectName("mutedLabel")
        layout.addWidget(self._status_label, 1)

        clear_button = QPushButton("Temizle", footer)
        clear_button.setToolTip("Görünür sohbeti temizle")
        clear_button.clicked.connect(self.clear_chat)
        layout.addWidget(clear_button)

        copy_button = QPushButton("Son cevabı kopyala", footer)
        copy_button.clicked.connect(self.copy_last_response)
        layout.addWidget(copy_button)
        parent_layout.addWidget(footer)

        self._composer.send_requested.connect(self.send_message)
        self._composer.history_requested.connect(self._navigate_input_history)
        self._composer.attachment_requested.connect(
            lambda: self._set_status("Dosya ekleme henüz aktif değil.")
        )
        self._composer.screen_requested.connect(
            lambda: self._set_status("Ekran bağlamı henüz aktif değil.")
        )
        self._composer.mic_requested.connect(self.handle_mic_request)

    def _bind_shortcuts(self) -> None:
        focus_action = QAction(self)
        focus_action.setShortcut(QKeySequence("Ctrl+L"))
        focus_action.triggered.connect(self._composer.input.setFocus)
        self.addAction(focus_action)

        new_action = QAction(self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.clear_chat)
        self.addAction(new_action)

        clear_action = QAction(self)
        clear_action.setShortcut(QKeySequence("Ctrl+K"))
        clear_action.triggered.connect(self.clear_chat)
        self.addAction(clear_action)

    def send_message(self) -> None:
        """Send the current composer text through the conversation service."""
        if self._is_waiting:
            return
        message = self._composer.text()
        if not message:
            return

        self._record_input_history(message)
        self._update_session_title(message)
        self._composer.clear()
        self._append_user_message(message)
        self._show_typing_indicator()
        self._set_waiting_state(True)
        self._set_status("Cevap bekleniyor...")

        worker = FunctionWorker(self._conversation_service.handle_message, message)
        worker.signals.result.connect(self._handle_conversation_result)
        worker.signals.error.connect(self._handle_conversation_error)
        self._start_worker(worker)

    def clear_chat(self) -> None:
        """Clear visible session messages without resetting backend services."""
        if self._is_speech_busy and self._speech_service is not None:
            self._speech_service.stop_listening()
        for row in list(self._message_rows):
            row.setParent(None)
            row.deleteLater()
        self._message_rows.clear()
        self._typing_message = None
        self._last_response_text = ""
        self._input_history.clear()
        self._input_history_index = 0
        self._set_session_title("Yeni Sohbet")
        self._append_assistant_message(format_welcome_message())
        self._set_status("Hazır")

    def copy_last_response(self) -> None:
        """Copy the last assistant response to the system clipboard."""
        if not self._last_response_text:
            self._set_status("Kopyalanacak bir Lina cevabı yok.")
            return
        QApplication.clipboard().setText(self._last_response_text)
        self._set_status("Son cevap kopyalandı.")

    def handle_mic_request(self) -> None:
        """Start or stop an explicit push-to-talk transcription request."""
        if self._speech_service is None or not self._speech_service.is_stt_available():
            self._set_status("Mikrofon/STT şu anda hazır değil.")
            return
        state = self._speech_service.get_state()
        if state is SpeechState.LISTENING:
            self._speech_service.stop_listening()
            self._set_status("Kayıt durduruluyor...")
            return
        if self._is_speech_busy:
            return

        self._is_speech_busy = True
        self._composer.mic_button.setText("Durdur")
        self._composer.mic_button.setEnabled(True)
        self._set_status("Dinliyorum...")
        worker = FunctionWorker(self._speech_service.transcribe_once)
        worker.signals.result.connect(self._handle_transcription_result)
        worker.signals.error.connect(self._handle_transcription_error)
        worker.signals.finished.connect(self._reset_speech_ui)
        self._start_worker(worker)

    def _handle_conversation_result(self, response: object) -> None:
        self._remove_typing_indicator()
        text = response.text if isinstance(response, ModelResponse) else str(response)
        self._append_assistant_message(text)
        self._set_waiting_state(False)
        self._set_status("Hazır")

    def _handle_conversation_error(self, error: object) -> None:
        self._remove_typing_indicator()
        text = (
            friendly_error_message(error)
            if isinstance(error, Exception)
            else "Bir şey ters gitti İlhan. İstersen tekrar deneyebiliriz."
        )
        self._append_assistant_message(text)
        self._set_waiting_state(False)
        self._set_status("Hata oluştu.")

    def _handle_transcription_result(self, result: object) -> None:
        if not isinstance(result, SpeechTranscriptionResult):
            self._set_status("Konuşma sonucu okunamadı.")
            return
        text = result.text.strip()
        if not text:
            self._append_assistant_message(
                "Net bir konuşma algılayamadım İlhan. Tekrar deneyebilirsin."
            )
            self._set_status("Hazır")
            return
        if self._composer.append_transcription(text):
            self._append_assistant_message(
                "Konuşmanı yazıya çevirdim İlhan. Kontrol edip gönderebilirsin."
            )
            self._set_status("Hazır")
            return
        self._append_assistant_message(
            "Transkripsiyonu mesaj alanına yazamadım İlhan. Tekrar deneyebiliriz."
        )
        self._set_status("Hata oluştu.")

    def _handle_transcription_error(self, error: object) -> None:
        if isinstance(error, SpeechUnavailableError):
            text = "Mikrofon/STT şu anda hazır değil İlhan."
        elif isinstance(error, SpeechServiceError):
            text = "Konuşmayı yazıya çevirirken sorun yaşadım İlhan."
        else:
            text = "Mikrofon akışında beklenmeyen bir sorun oluştu İlhan."
        self._append_assistant_message(text)
        self._set_status("Hazır")

    def _reset_speech_ui(self) -> None:
        self._is_speech_busy = False
        self._composer.mic_button.setText("Mic")
        self._composer.mic_button.setEnabled(
            self._speech_service is not None and self._speech_service.is_stt_available()
        )
        self._refresh_speech_status()

    def _append_user_message(self, text: str) -> ChatMessageWidget:
        return self._append_message("user", text)

    def _append_assistant_message(self, text: str) -> ChatMessageWidget:
        normalized = normalize_assistant_text(text)
        self._last_response_text = normalized
        return self._append_message("assistant", normalized)

    def _append_message(
        self,
        role: str,
        text: str,
        typing: bool = False,
    ) -> ChatMessageWidget:
        was_near_bottom = self._is_scroll_near_bottom()
        message = ChatMessageWidget(
            role=role,
            text=text,
            font_family=self._font_family,
            font_size=self._message_font_size,
            typing=typing,
            parent=self._message_container,
        )
        message.copy_requested.connect(self._copy_text)
        row = QWidget(self._message_container)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        if role == "user":
            row_layout.addStretch(1)
            row_layout.addWidget(message)
        else:
            row_layout.addWidget(message)
            row_layout.addStretch(1)
        row._message_widget = message  # type: ignore[attr-defined]
        self._message_layout.insertWidget(self._message_layout.count() - 1, row)
        self._message_rows.append(row)
        self._update_message_widths()
        if was_near_bottom:
            QTimer.singleShot(0, self._scroll_to_bottom)
        return message

    def _show_typing_indicator(self) -> None:
        self._remove_typing_indicator()
        self._typing_message = self._append_message("assistant", "Yazıyor...", typing=True)

    def _remove_typing_indicator(self) -> None:
        if self._typing_message is None:
            return
        for row in list(self._message_rows):
            if getattr(row, "_message_widget", None) is self._typing_message:
                self._message_rows.remove(row)
                row.setParent(None)
                row.deleteLater()
                break
        self._typing_message = None

    def _copy_text(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        self._set_status("Mesaj kopyalandı.")

    def _record_input_history(self, message: str) -> None:
        if not self._input_history or self._input_history[-1] != message:
            self._input_history.append(message)
        self._input_history_index = len(self._input_history)

    def _navigate_input_history(self, direction: int) -> None:
        if not self._input_history:
            return
        self._input_history_index = max(
            0,
            min(len(self._input_history), self._input_history_index + direction),
        )
        if self._input_history_index == len(self._input_history):
            self._composer.set_text("")
        else:
            self._composer.set_text(self._input_history[self._input_history_index])

    def _update_session_title(self, message: str) -> None:
        if self._session_title_text != "Yeni Sohbet":
            return
        title = derive_session_title(message)
        if title != "Yeni Sohbet":
            self._set_session_title(title)

    def _set_session_title(self, title: str) -> None:
        self._session_title_text = title
        self._session_title.setText(title)
        self._sidebar.set_session_title(title)

    def _set_waiting_state(self, waiting: bool) -> None:
        self._is_waiting = waiting
        self._composer.set_waiting(waiting)

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _run_initial_diagnostics(self) -> None:
        if self._diagnostics_service is None:
            self._model_status.setText("Model: bilinmiyor")
            return
        worker = FunctionWorker(self._diagnostics_service.check_status)
        worker.signals.result.connect(self._handle_diagnostics_result)
        worker.signals.error.connect(
            lambda _error: self._model_status.setText("Model: kontrol edilemedi")
        )
        self._start_worker(worker)

    def _handle_diagnostics_result(self, result: object) -> None:
        if isinstance(result, DiagnosticsResult):
            self._model_status.setText(format_status_message(result))
            if result.status is not ModelStatus.READY:
                self._set_status(result.message)

    def _refresh_speech_status(self) -> None:
        if self._speech_service is None:
            self._speech_status.setText("Mic: yok")
            return
        if self._speech_service.is_stt_available():
            self._speech_status.setText("Mic: hazır")
            self._composer.mic_button.setEnabled(True)
        else:
            self._speech_status.setText("Mic: kapalı")
            self._composer.mic_button.setEnabled(False)

    def _start_worker(self, worker: FunctionWorker) -> None:
        self._workers.add(worker)
        worker.signals.finished.connect(lambda: self._workers.discard(worker))
        self._thread_pool.start(worker)

    def _change_font_size(self, delta: int) -> None:
        self._message_font_size = clamp_message_font_size(self._message_font_size + delta)
        self._composer.set_message_font(self._font_family, self._message_font_size)
        for row in self._message_rows:
            message = getattr(row, "_message_widget", None)
            if isinstance(message, ChatMessageWidget):
                message.set_message_font(self._font_family, self._message_font_size)

    def _update_message_widths(self) -> None:
        width = int(max(360, self._scroll.viewport().width() * 0.72))
        for row in self._message_rows:
            message = getattr(row, "_message_widget", None)
            if isinstance(message, ChatMessageWidget):
                message.set_bubble_width(width)

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._update_message_widths()

    def _is_scroll_near_bottom(self) -> bool:
        if not hasattr(self, "_scroll"):
            return True
        bar = self._scroll.verticalScrollBar()
        return bar.maximum() - bar.value() <= 48

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _apply_window_icon(self) -> None:
        if BRANDING_ICON_PATH.exists():
            icon = QIcon(str(BRANDING_ICON_PATH))
            if not icon.isNull():
                self.setWindowIcon(icon)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._speech_service is not None:
            self._speech_service.stop_listening()
        event.accept()
