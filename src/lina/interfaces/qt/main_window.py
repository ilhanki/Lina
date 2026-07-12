"""PySide6 desktop window for Lina."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer, QThreadPool
from PySide6.QtGui import QAction, QCloseEvent, QCursor, QGuiApplication, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
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
from lina.interfaces.qt.image_loader import ImageLoadError, QtImageLoader
from lina.interfaces.qt.image_preview_dialog import ImagePreviewDialog
from lina.interfaces.qt.screen_capture import QtScreenCaptureService
from lina.interfaces.qt.screen_preview_dialog import ScreenPreviewDialog
from lina.interfaces.qt.region_capture_overlay import RegionCaptureOverlay
from lina.interfaces.qt.theme import MESSAGE_FONT_DEFAULT, resolve_font_family
from lina.interfaces.qt.widgets import ChatMessageWidget, ComposerWidget, SidebarWidget
from lina.interfaces.qt.worker import FunctionWorker
from lina.services.conversation_service import ConversationService
from lina.conversations.models import ConversationSession
from lina.services.conversation_models import ConversationInput, ConversationResult
from lina.screen.capture_service import ScreenCaptureService
from lina.screen.models import LOCAL_FILE, ScreenCaptureError, ScreenContext
from lina.services.model_diagnostics_service import (
    DiagnosticsResult,
    ModelDiagnosticsService,
    ModelStatus,
    VisionDiagnosticsResult,
    VisionDiagnosticsService,
    VisionStatus,
)
from lina.speech.models import (
    SpeechServiceError,
    SpeechState,
    SpeechTranscriptionResult,
    SpeechUnavailableError,
)
from lina.speech.service import SpeechService
from lina.vision.models import ImageAttachment, VisionRequestError


APP_VERSION = "v0.8.0-alpha"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
BRANDING_LOGO_PATH = PROJECT_ROOT / "assets" / "branding" / "lina-logo.png"
BRANDING_ICON_PATH = PROJECT_ROOT / "assets" / "branding" / "lina-icon.png"
AUTO_SCROLL_THRESHOLD_PX = 110


class LinaMainWindow(QMainWindow):
    """Modern PySide6 chat interface backed by Lina's existing services."""

    def __init__(
        self,
        conversation_service: ConversationService,
        diagnostics_service: ModelDiagnosticsService | None = None,
        vision_diagnostics_service: VisionDiagnosticsService | None = None,
        speech_service: SpeechService | None = None,
        screen_capture_service: ScreenCaptureService | None = None,
        image_loader: QtImageLoader | None = None,
        screen_preview_factory: Callable[[ScreenContext, QWidget | None], QDialog]
        | None = None,
        thread_pool: QThreadPool | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._conversation_service = conversation_service
        self._diagnostics_service = diagnostics_service
        self._vision_diagnostics_service = vision_diagnostics_service
        self._speech_service = speech_service
        self._screen_capture_service = screen_capture_service or QtScreenCaptureService()
        self._image_loader = image_loader or QtImageLoader()
        self._screen_preview_factory = screen_preview_factory or ScreenPreviewDialog
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._workers: set[FunctionWorker] = set()
        self._message_rows: list[QWidget] = []
        self._typing_message: ChatMessageWidget | None = None
        self._last_response_text = ""
        self._input_history: list[str] = []
        self._input_history_index = 0
        self._is_waiting = False
        self._active_request_id = 0
        self._cancelled_request_ids: set[int] = set()
        self._is_speech_busy = False
        self._is_screen_capture_busy = False
        self._region_overlay: RegionCaptureOverlay | None = None
        self._screen_context: ScreenContext | None = None
        self._vision_status: VisionDiagnosticsResult | None = None
        self._request_screen_contexts: dict[int, ScreenContext] = {}
        self._auto_scroll_enabled = True
        self._pending_scroll_to_bottom = False
        self._pending_scroll_to_top = False
        self._scroll_retry_count = 0
        self._is_programmatic_scroll = False
        self._message_font_size = MESSAGE_FONT_DEFAULT
        self._font_family = resolve_font_family()
        self._session_title_text = "Yeni Sohbet"
        self._conversation_history_service = (
            conversation_service.conversation_history_service
            if hasattr(conversation_service, "conversation_history_service")
            else None
        )

        self.setWindowTitle("Lina")
        self.setMinimumSize(1040, 640)
        self.resize(1240, 780)
        self._apply_window_icon()
        self._build_layout()
        self._bind_shortcuts()
        self._restore_initial_conversation()
        self._composer.input.setFocus()
        self._run_initial_diagnostics()
        self._run_initial_vision_diagnostics()
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
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(12)
        root_layout.addWidget(panel, 1)

        self._build_header(panel_layout)
        self._build_chat_area(panel_layout)
        self._build_footer(panel_layout)
        self.setCentralWidget(central)

        self._sidebar.new_chat_requested.connect(self.start_new_chat)
        self._sidebar.session_selected.connect(self.load_conversation)
        self._sidebar.session_rename_requested.connect(self.rename_conversation)
        self._sidebar.session_delete_requested.connect(self.delete_conversation)

    def _build_header(self, parent_layout: QVBoxLayout) -> None:
        header = QWidget(self)
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 9, 14, 9)
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

        self._speech_status = QLabel("Mic · hazırlanıyor", header)
        self._speech_status.setObjectName("statusChip")
        layout.addWidget(self._speech_status)
        parent_layout.addWidget(header)

    def _build_chat_area(self, parent_layout: QVBoxLayout) -> None:
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._message_container = QWidget(self._scroll)
        self._message_layout = QVBoxLayout(self._message_container)
        self._message_layout.setContentsMargins(24, 14, 24, 14)
        self._message_layout.setSpacing(14)
        self._message_layout.addStretch(1)
        self._scroll.setWidget(self._message_container)
        self._scroll.verticalScrollBar().valueChanged.connect(self._update_auto_scroll_state)
        self._scroll.verticalScrollBar().rangeChanged.connect(self._handle_scroll_range_changed)
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
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(8)

        self._status_label = QLabel("Hazır", footer)
        self._status_label.setObjectName("mutedLabel")
        layout.addWidget(self._status_label, 1)

        clear_button = QPushButton("Temizle", footer)
        clear_button.setObjectName("secondaryButton")
        clear_button.setToolTip("Görünür sohbeti temizle")
        clear_button.clicked.connect(self.clear_chat_with_confirmation)
        layout.addWidget(clear_button)

        copy_button = QPushButton("Son cevabı kopyala", footer)
        copy_button.setObjectName("secondaryButton")
        copy_button.clicked.connect(self.copy_last_response)
        layout.addWidget(copy_button)
        parent_layout.addWidget(footer)

        self._composer.send_requested.connect(self.send_message)
        self._composer.stop_requested.connect(self.cancel_active_response)
        self._composer.history_requested.connect(self._navigate_input_history)
        self._composer.attachment_requested.connect(self.handle_image_upload)
        self._screen_menu = QMenu(self)
        self._screen_menu.setAccessibleName("Ekran yakalama seçenekleri")
        full_screen_action = self._screen_menu.addAction("Tüm Ekranı Yakala")
        full_screen_action.setToolTip("Tüm ekranı yakala")
        full_screen_action.triggered.connect(self.handle_screen_request)
        region_action = self._screen_menu.addAction("Alan Seçerek Yakala")
        region_action.setToolTip("Ekranda alan seçerek yakala")
        region_action.triggered.connect(self.handle_region_capture)
        self._composer.screen_button.setMenu(self._screen_menu)
        self._composer.screen_context_remove_requested.connect(
            self.remove_screen_context
        )
        self._composer.screen_context_preview_requested.connect(
            self.preview_active_attachment
        )
        self._composer.screen_context_change_requested.connect(
            self.change_active_attachment
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
            if self._screen_context is not None:
                self._set_status("Ekran görüntüsü hakkında bir soru yaz.")
            return

        self._record_input_history(message)
        self._update_session_title(message)
        self._composer.clear()
        request_screen_context = self._screen_context
        self._auto_scroll_enabled = True
        user_message = self._append_user_message(
            message,
            image_bytes=(
                request_screen_context.image_bytes
                if request_screen_context is not None
                else None
            ),
            visual_context=request_screen_context,
        )
        if request_screen_context is not None:
            user_message.set_visual_status("Analiz ediliyor")
        self._show_typing_indicator(
            "Lina ekranı inceliyor..."
            if request_screen_context is not None
            else "Yazıyor..."
        )
        self._set_waiting_state(True)
        self._set_status("Cevap bekleniyor...")

        self._active_request_id += 1
        request_id = self._active_request_id
        if request_screen_context is not None:
            self._request_screen_contexts[request_id] = request_screen_context
        worker = FunctionWorker(
            self._run_conversation_request,
            request_id,
            message,
            request_screen_context,
        )
        worker.signals.result.connect(self._handle_conversation_worker_result)
        worker.signals.error.connect(self._handle_conversation_error)
        self._start_worker(worker)

    def cancel_active_response(self) -> None:
        """Stop rendering the active response and keep the composer usable."""
        if not self._is_waiting:
            return
        self._cancelled_request_ids.add(self._active_request_id)
        self._request_screen_contexts.pop(self._active_request_id, None)
        self._remove_typing_indicator()
        self._set_waiting_state(False)
        self._set_status("Yanıt durduruldu.")
        self._composer.input.setFocus()

    def clear_chat(self) -> None:
        """Clear the active conversation and its visible messages."""
        if self._is_speech_busy and self._speech_service is not None:
            self._speech_service.stop_listening()
        if self._conversation_history_service is not None:
            self._conversation_service.clear_session()
        self._clear_visible_messages()
        self._clear_screen_context()
        self._set_session_title("Yeni Sohbet")
        self._refresh_conversation_sidebar()
        self._append_assistant_message(format_welcome_message())
        self._set_status("Hazır")
        self._schedule_scroll_to_top()

    def clear_chat_with_confirmation(self) -> None:
        """Ask before deleting all messages from the active conversation."""
        if self._is_waiting:
            return
        result = QMessageBox.question(
            self,
            "Sohbeti temizle",
            "Bu sohbetteki tüm mesajlar silinecek. Bu işlem geri alınamaz.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel,
        )
        if result == QMessageBox.StandardButton.Ok:
            self.clear_chat()

    def start_new_chat(self) -> None:
        """Create a new persisted session without deleting the old one."""
        if self._is_waiting:
            self._set_status("Önce devam eden yanıtı durdurmalısın.")
            return
        if self._conversation_history_service is not None:
            self._conversation_service.start_new_session()
        self._clear_visible_messages()
        self._clear_screen_context()
        self._set_session_title("Yeni Sohbet")
        self._refresh_conversation_sidebar()
        self._append_assistant_message(format_welcome_message())
        self._set_status("Hazır")
        self._schedule_scroll_to_top()

    def load_conversation(self, conversation_id: int) -> None:
        """Load a persisted conversation without mixing session history."""
        if self._is_waiting:
            self._set_status("Önce devam eden yanıtı durdurmalısın.")
            return
        if self._conversation_history_service is None:
            return
        try:
            self._conversation_service.load_session(conversation_id)
            session = self._conversation_history_service.active_session
            self._clear_visible_messages()
            self._clear_screen_context()
            if session is not None:
                self._set_session_title(session.title)
            for message in self._conversation_history_service.loaded_messages():
                text = message.content
                if message.had_image:
                    text = f"▣ {_visual_placeholder(message.image_source)}\n{text}"
                self._append_message(
                    message.role,
                    text,
                    visual_context=None,
                )
            if not self._message_rows:
                self._append_assistant_message(format_welcome_message())
            self._refresh_conversation_sidebar()
            self._set_status("Sohbet yüklendi")
            self._schedule_scroll_to_bottom()
        except Exception:
            self._set_status("Sohbet geçmişi yüklenemedi.")

    def rename_conversation(self, conversation_id: int) -> None:
        """Rename a conversation through a bounded local dialog."""
        if self._conversation_history_service is None or self._is_waiting:
            return
        session = next(
            (item for item in self._conversation_history_service.list_sessions() if item.id == conversation_id),
            None,
        )
        if session is None:
            return
        title, accepted = QInputDialog.getText(self, "Sohbeti yeniden adlandır", "Başlık:", text=session.title)
        if not accepted or not title.strip():
            return
        if self._conversation_history_service.active_session and self._conversation_history_service.active_session.id == conversation_id:
            renamed = self._conversation_history_service.rename(title)
            self._set_session_title(renamed.title)
        else:
            self._conversation_history_service.rename_session(conversation_id, title)
        self._refresh_conversation_sidebar()

    def delete_conversation(self, conversation_id: int) -> None:
        """Delete one conversation after explicit confirmation."""
        if self._conversation_history_service is None or self._is_waiting:
            return
        session = next(
            (item for item in self._conversation_history_service.list_sessions() if item.id == conversation_id),
            None,
        )
        if session is None:
            return
        result = QMessageBox.question(
            self,
            "Sohbeti sil",
            f'“{session.title}” sohbeti kalıcı olarak silinsin mi?',
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel,
        )
        if result != QMessageBox.StandardButton.Ok:
            return
        was_active = self._conversation_history_service.delete(conversation_id)
        if was_active:
            self.start_new_chat()
        self._refresh_conversation_sidebar()

    def _clear_visible_messages(self) -> None:
        for row in list(self._message_rows):
            row.setParent(None)
            row.deleteLater()
        self._message_rows.clear()
        self._typing_message = None
        self._last_response_text = ""
        self._input_history.clear()
        self._input_history_index = 0

    def _restore_initial_conversation(self) -> None:
        if self._conversation_history_service is None:
            self._append_assistant_message(format_welcome_message())
            return
        session = self._conversation_history_service.active_session
        if session is None:
            self._append_assistant_message(format_welcome_message())
            return
        self._set_session_title(session.title)
        messages = self._conversation_history_service.loaded_messages()
        if not messages:
            self._append_assistant_message(format_welcome_message())
        else:
            for message in messages:
                text = message.content
                if message.had_image:
                    text = f"▣ {_visual_placeholder(message.image_source)}\n{text}"
                self._append_message(message.role, text)
        self._refresh_conversation_sidebar()

    def _refresh_conversation_sidebar(self) -> None:
        if self._conversation_history_service is None:
            self._sidebar.set_persistence_note("Kalıcı sohbet geçmişi kapalı.")
            return
        sessions = self._conversation_history_service.list_sessions()
        active_id = (
            self._conversation_history_service.active_session.id
            if self._conversation_history_service.active_session is not None
            else None
        )
        self._sidebar.set_sessions(sessions, active_id=active_id)

    def handle_screen_request(self) -> None:
        """Capture and preview one screen after an explicit user action."""
        if self._is_screen_capture_busy:
            return
        self._is_screen_capture_busy = True
        self._composer.screen_button.setEnabled(False)
        self._set_status("Ekran yakalanıyor...")
        try:
            context = self._screen_capture_service.capture()
            dialog = self._screen_preview_factory(context, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._set_screen_context(context)
            else:
                self._set_status("Hazır")
        except ScreenCaptureError:
            self._set_status("Ekran görüntüsü alınamadı.")
        except Exception:
            self._set_status("Ekran önizlemesi oluşturulamadı.")
        finally:
            self._is_screen_capture_busy = False
            self._composer.screen_button.setEnabled(True)

    def handle_image_upload(self) -> None:
        """Load one image explicitly selected by the user into temporary context."""
        selected_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Görsel Seç",
            "",
            "Görseller (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not selected_path:
            return
        try:
            context = self._image_loader.load(Path(selected_path))
        except ImageLoadError:
            self._set_status("Seçilen görsel yüklenemedi.")
            return
        self._set_screen_context(context)
        self._set_status("Görsel analize hazır")

    def handle_region_capture(self) -> None:
        """Start an explicit region selection on the cursor screen."""
        if self._is_screen_capture_busy:
            return
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            self._set_status("Ekran bulunamadı.")
            return
        self._is_screen_capture_busy = True
        self._composer.screen_button.setEnabled(False)
        self._set_status("Analiz edilecek alanı seç...")
        overlay = RegionCaptureOverlay(screen.geometry())
        self._region_overlay = overlay
        overlay.region_selected.connect(
            lambda rectangle: self._finish_region_capture(screen, rectangle)
        )
        overlay.canceled.connect(self._cancel_region_capture)
        overlay.show()

    def _finish_region_capture(self, screen, rectangle) -> None:
        overlay = self._region_overlay
        self._region_overlay = None
        if overlay is not None:
            overlay.close()
            overlay.deleteLater()
        try:
            context = self._screen_capture_service.capture_region(rectangle, screen)
            dialog = self._screen_preview_factory(context, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._set_screen_context(context)
            else:
                self._set_status("Hazır")
        except ScreenCaptureError:
            self._set_status("Ekran alanı yakalanamadı.")
        except Exception:
            self._set_status("Ekran önizlemesi oluşturulamadı.")
        finally:
            self._is_screen_capture_busy = False
            self._composer.screen_button.setEnabled(True)

    def _cancel_region_capture(self) -> None:
        overlay = self._region_overlay
        self._region_overlay = None
        if overlay is not None:
            overlay.close()
            overlay.deleteLater()
        self._is_screen_capture_busy = False
        self._composer.screen_button.setEnabled(True)
        self._set_status("Alan seçimi iptal edildi.")

    def remove_screen_context(self) -> None:
        """Remove the active temporary screenshot from the GUI session."""
        if self._screen_context is None:
            return
        self._clear_screen_context()
        self._set_status("Ekran bağlamı kaldırıldı")

    def _set_screen_context(self, context: ScreenContext) -> None:
        self._screen_context = context
        self._composer.set_screen_context(
            context.width,
            context.height,
            self._vision_attachment_status_text(),
            (
                f"Görsel · {context.display_name}"
                if context.source == LOCAL_FILE
                else "Ekran"
            ),
            image_bytes=context.image_bytes,
        )
        self._set_status("Ekran bağlamı eklendi")

    def preview_active_attachment(self) -> None:
        """Open the active attachment from its in-memory session data."""
        if self._screen_context is None:
            return
        try:
            dialog = ImagePreviewDialog(self._screen_context, self)
            dialog.exec()
        except Exception:
            self._set_status("Görsel önizlemesi oluşturulamadı.")

    def change_active_attachment(self) -> None:
        """Replace the current local image or screen capture."""
        if self._screen_context is not None and self._screen_context.source == LOCAL_FILE:
            self.handle_image_upload()
            return
        self._screen_menu.popup(self._composer.screen_button.mapToGlobal(
            self._composer.screen_button.rect().bottomLeft()
        ))

    def _clear_screen_context(self) -> None:
        self._screen_context = None
        self._composer.clear_screen_context()

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
        self._composer.set_mic_state("listening")
        self._composer.mic_button.setEnabled(True)
        self._set_status("Dinliyorum...")
        worker = FunctionWorker(self._speech_service.transcribe_once)
        worker.signals.result.connect(self._handle_transcription_result)
        worker.signals.error.connect(self._handle_transcription_error)
        worker.signals.finished.connect(self._reset_speech_ui)
        self._start_worker(worker)

    def _run_conversation_request(
        self,
        request_id: int,
        message: str,
        screen_context: ScreenContext | None,
    ) -> tuple[int, str, object]:
        try:
            if screen_context is None:
                response: object = self._conversation_service.handle_message(message)
            else:
                response = self._conversation_service.handle_input(
                    ConversationInput(
                        text=message,
                        image_attachment=ImageAttachment(
                            mime_type="image/png",
                            data=screen_context.image_bytes,
                            width=screen_context.width,
                            height=screen_context.height,
                            captured_at=screen_context.captured_at,
                            source=screen_context.source,
                            display_name=screen_context.display_name,
                        ),
                    )
                )
        except Exception as error:
            return (request_id, "error", error)
        return (request_id, "success", response)

    def _handle_conversation_worker_result(self, result: object) -> None:
        if not isinstance(result, tuple) or len(result) != 3:
            self._handle_conversation_error(RuntimeError("Invalid conversation result"))
            return
        request_id, status, payload = result
        if not isinstance(request_id, int):
            self._handle_conversation_error(RuntimeError("Invalid conversation request"))
            return
        if request_id in self._cancelled_request_ids:
            self._cancelled_request_ids.discard(request_id)
            self._request_screen_contexts.pop(request_id, None)
            return
        if request_id != self._active_request_id:
            self._request_screen_contexts.pop(request_id, None)
            return
        if status == "error":
            request_screen_context = self._request_screen_contexts.pop(request_id, None)
            self._handle_conversation_error(
                payload,
                vision_request=request_screen_context is not None,
                request_screen_context=request_screen_context,
            )
            return
        request_screen_context = self._request_screen_contexts.pop(request_id, None)
        self._handle_conversation_result(payload, request_screen_context)

    def _handle_conversation_result(
        self,
        result: object,
        request_screen_context: ScreenContext | None = None,
    ) -> None:
        self._remove_typing_indicator()
        if isinstance(result, ConversationResult):
            response: object = result.response
            consumed = result.attachment_consumed
        else:
            response = result
            consumed = False
        text = response.text if isinstance(response, ModelResponse) else str(response)
        self._auto_scroll_enabled = True
        self._append_assistant_message(text)
        self._set_visual_status_for_context(request_screen_context, "Analiz edildi")
        self._refresh_conversation_sidebar()
        self._set_waiting_state(False)
        if (
            consumed
            and request_screen_context is not None
            and self._screen_context is request_screen_context
        ):
            self._clear_screen_context()
            self._set_status("Ekran görüntüsü analiz edildi")
        else:
            self._set_status("Hazır")
        self._composer.input.setFocus()
        QTimer.singleShot(0, self._composer.input.setFocus)

    def _handle_conversation_error(
        self,
        error: object,
        vision_request: bool = False,
        request_screen_context: ScreenContext | None = None,
    ) -> None:
        self._remove_typing_indicator()
        if vision_request and isinstance(error, Exception):
            text = _friendly_vision_error_message(error)
        else:
            text = (
                friendly_error_message(error)
                if isinstance(error, Exception)
                else "Bir şey ters gitti İlhan. İstersen tekrar deneyebiliriz."
            )
        self._auto_scroll_enabled = True
        self._append_assistant_message(text)
        self._set_visual_status_for_context(
            request_screen_context,
            "Analiz başarısız · Tekrar dene",
        )
        self._refresh_conversation_sidebar()
        self._set_waiting_state(False)
        self._set_status("Hata oluştu.")
        self._composer.input.setFocus()
        QTimer.singleShot(0, self._composer.input.setFocus)

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
            self._set_status("Metne çevrildi.")
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
        self._composer.set_mic_state("idle")
        self._composer.mic_button.setEnabled(
            self._speech_service is not None and self._speech_service.is_stt_available()
        )
        self._refresh_speech_status()

    def _append_user_message(
        self,
        text: str,
        image_bytes: bytes | None = None,
        visual_context: ScreenContext | None = None,
    ) -> ChatMessageWidget:
        return self._append_message(
            "user",
            text,
            image_bytes=image_bytes,
            visual_context=visual_context,
        )

    def _append_assistant_message(self, text: str) -> ChatMessageWidget:
        normalized = normalize_assistant_text(text)
        self._last_response_text = normalized
        return self._append_message("assistant", normalized)

    def _append_message(
        self,
        role: str,
        text: str,
        typing: bool = False,
        image_bytes: bytes | None = None,
        visual_context: ScreenContext | None = None,
    ) -> ChatMessageWidget:
        should_scroll = self._auto_scroll_enabled or self._is_scroll_near_bottom()
        message = ChatMessageWidget(
            role=role,
            text=text,
            font_family=self._font_family,
            font_size=self._message_font_size,
            typing=typing,
            image_bytes=image_bytes,
            visual_context=visual_context,
            parent=self._message_container,
        )
        message.copy_requested.connect(self._copy_text)
        message.image_preview_requested.connect(self._show_image_preview)
        message.reanalyze_requested.connect(self.reanalyze_visual_context)
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
        if should_scroll:
            self._schedule_scroll_to_bottom()
        return message

    def _show_image_preview(self, context: object) -> None:
        if not isinstance(context, ScreenContext):
            return
        try:
            ImagePreviewDialog(context, self).exec()
        except Exception:
            self._set_status("Görsel önizlemesi oluşturulamadı.")

    def reanalyze_visual_context(self, context: object) -> None:
        """Restore a previous image to the composer without sending it."""
        if not isinstance(context, ScreenContext) or self._is_waiting:
            return
        self._set_screen_context(context)
        self._set_status("Görsel yeniden analize hazır")

    def _set_visual_status_for_context(
        self,
        context: ScreenContext | None,
        status: str,
    ) -> None:
        if context is None:
            return
        for row in self._message_rows:
            message = getattr(row, "_message_widget", None)
            if isinstance(message, ChatMessageWidget) and message.visual_context is context:
                message.set_visual_status(status)
                return

    def _show_typing_indicator(self, text: str = "Yazıyor...") -> None:
        self._remove_typing_indicator()
        self._typing_message = self._append_message("assistant", text, typing=True)

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
            self._model_status.setText(_format_model_status_chip(result))
            if result.status is not ModelStatus.READY:
                self._set_status(result.message)

    def _run_initial_vision_diagnostics(self) -> None:
        if self._vision_diagnostics_service is None:
            return
        worker = FunctionWorker(self._vision_diagnostics_service.check_status)
        worker.signals.result.connect(self._handle_vision_diagnostics_result)
        self._start_worker(worker)

    def _handle_vision_diagnostics_result(self, result: object) -> None:
        if not isinstance(result, VisionDiagnosticsResult):
            return
        self._vision_status = result
        if self._screen_context is not None:
            self._composer.set_screen_context(
                self._screen_context.width,
                self._screen_context.height,
                self._vision_attachment_status_text(),
                (
                    f"Görsel · {self._screen_context.display_name}"
                    if self._screen_context.source == LOCAL_FILE
                    else "Ekran"
                ),
            )

    def _vision_attachment_status_text(self) -> str:
        if self._vision_status is None:
            return "Vision kontrol ediliyor"
        labels = {
            VisionStatus.READY: "Analize hazır",
            VisionStatus.DISABLED: "Vision kapalı",
            VisionStatus.MODEL_NOT_AVAILABLE: "Vision modeli hazır değil",
            VisionStatus.VISION_NOT_SUPPORTED: "Model görüntü desteklemiyor",
            VisionStatus.TIMEOUT: "Vision kontrolü zaman aşımına uğradı",
            VisionStatus.OLLAMA_UNREACHABLE: "Ollama ulaşılamıyor",
            VisionStatus.INVALID_RESPONSE: "Vision durumu doğrulanamadı",
        }
        return labels[self._vision_status.status]

    def _refresh_speech_status(self) -> None:
        if self._speech_service is None:
            self._speech_status.setText("Mic · yok")
            return
        if self._speech_service.is_stt_available():
            self._speech_status.setText("Mic · hazır")
            self._composer.mic_button.setEnabled(True)
        else:
            self._speech_status.setText("Mic · kapalı")
            self._composer.mic_button.setEnabled(False)

    def _start_worker(self, worker: FunctionWorker) -> None:
        self._workers.add(worker)
        worker.signals.finished.connect(lambda: self._workers.discard(worker))
        self._thread_pool.start(worker)

    def _update_message_widths(self) -> None:
        width = int(min(780, max(340, self._scroll.viewport().width() * 0.70)))
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
        return bar.maximum() - bar.value() <= AUTO_SCROLL_THRESHOLD_PX

    def _update_auto_scroll_state(self) -> None:
        if self._is_programmatic_scroll:
            return
        self._auto_scroll_enabled = self._is_scroll_near_bottom()
        if not self._auto_scroll_enabled and not self._pending_scroll_to_top:
            self._pending_scroll_to_bottom = False
            self._scroll_retry_count = 0

    def _handle_scroll_range_changed(self, _minimum: int, _maximum: int) -> None:
        if self._pending_scroll_to_top:
            QTimer.singleShot(0, self._scroll_to_top)
            return
        if self._pending_scroll_to_bottom:
            QTimer.singleShot(0, self._scroll_to_bottom)

    def _schedule_scroll_to_bottom(self) -> None:
        self._pending_scroll_to_bottom = True
        self._pending_scroll_to_top = False
        self._scroll_retry_count = 8
        self._message_container.layout().activate()
        QTimer.singleShot(0, self._scroll_to_bottom)
        QTimer.singleShot(25, self._scroll_to_bottom)
        QTimer.singleShot(75, self._scroll_to_bottom)
        QTimer.singleShot(150, self._scroll_to_bottom)
        QTimer.singleShot(250, self._scroll_to_bottom)

    def _schedule_scroll_to_top(self) -> None:
        self._pending_scroll_to_top = True
        self._pending_scroll_to_bottom = False
        self._message_container.layout().activate()
        QTimer.singleShot(0, self._scroll_to_top)
        QTimer.singleShot(25, self._scroll_to_top)

    def _scroll_to_bottom(self) -> None:
        if not self._pending_scroll_to_bottom:
            return
        bar = self._scroll.verticalScrollBar()
        if bar.maximum() == 0 and self._scroll_retry_count > 0:
            self._scroll_retry_count -= 1
            QTimer.singleShot(25, self._scroll_to_bottom)
            return
        self._is_programmatic_scroll = True
        try:
            bar.setValue(bar.maximum())
        finally:
            self._is_programmatic_scroll = False
        if self._scroll_retry_count <= 0:
            self._pending_scroll_to_bottom = False
            self._scroll_retry_count = 0
            self._auto_scroll_enabled = True
            return
        self._scroll_retry_count -= 1
        QTimer.singleShot(25, self._scroll_to_bottom)

    def _scroll_to_top(self) -> None:
        bar = self._scroll.verticalScrollBar()
        self._is_programmatic_scroll = True
        try:
            bar.setValue(bar.minimum())
        finally:
            self._is_programmatic_scroll = False
        self._pending_scroll_to_top = False
        self._auto_scroll_enabled = self._is_scroll_near_bottom()

    def _apply_window_icon(self) -> None:
        if BRANDING_ICON_PATH.exists():
            icon = QIcon(str(BRANDING_ICON_PATH))
            if not icon.isNull():
                self.setWindowIcon(icon)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._clear_screen_context()
        if self._speech_service is not None:
            self._speech_service.stop_listening()
        event.accept()


def _format_model_status_chip(result: DiagnosticsResult) -> str:
    if result.status is ModelStatus.READY:
        return "Model · hazır"
    if result.status is ModelStatus.CONNECTING:
        return "Model · bağlanıyor"
    if result.status is ModelStatus.TIMEOUT:
        return "Model · timeout"
    if result.status is ModelStatus.MODEL_NOT_AVAILABLE:
        return "Model · yok"
    if result.status is ModelStatus.MODEL_NOT_CONFIGURED:
        return "Model · ayarsız"
    return "Model · kapalı"


def _friendly_vision_error_message(error: Exception) -> str:
    message = str(error).casefold()
    if isinstance(error, VisionRequestError):
        return str(error)
    if "size limit" in message:
        return "Ekran görüntüsü analiz için fazla büyük."
    if "empty text content" in message:
        return (
            "Vision modeli boş cevap döndürdü. Görseli daha kısa bir soruyla "
            "tekrar deneyebilirsin."
        )
    if "missing text content" in message or "invalid response" in message:
        return "Vision modelinden geçerli bir cevap alınamadı. Tekrar deneyebilirsin."
    if "valid png" in message or "image attachment" in message:
        return "Ekran görüntüsü doğrulanamadı."
    if "timed out" in message or "timeout" in message:
        return "Ekran analizi zaman aşımına uğradı. Daha küçük bir görüntüyle tekrar deneyebilirsin."
    if "network error" in message or "connection refused" in message:
        return "Lina yerel modele ulaşamadı. Ollama'nın çalıştığını kontrol et."
    if "http error: 404" in message or "not found" in message:
        return "Görüntü analizi için vision modeli kurulu değil."
    return "Ekran görüntüsü analiz edilirken bir sorun oluştu."


def _visual_placeholder(source: str | None) -> str:
    labels = {
        "screen_full": "Ekran görüntüsü kullanıldı · Görsel güvenlik nedeniyle saklanmadı",
        "screen_region": "Seçili ekran alanı kullanıldı · Görsel güvenlik nedeniyle saklanmadı",
        "local_image": "Yerel görsel kullanıldı · Görsel güvenlik nedeniyle saklanmadı",
    }
    return labels.get(
        source,
        "Görsel eklendi · Görsel güvenlik nedeniyle saklanmadı",
    )
