"""PySide6 desktop window for Lina."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PySide6.QtCore import QRect, QTimer, QThreadPool, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QCursor, QFont, QGuiApplication, QIcon, QImage, QKeySequence
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
    QSystemTrayIcon,
)

from lina.brain.model_provider import EmptyModelResponseError, ModelResponse
from lina.agent import AgentController, AgentSessionStatus, ApprovalDecision, parse_approval
from lina.agent.errors import AgentError
from lina.brain.routing.models import IntentRequest, IntentType as RoutingIntentType, RequestContext, ToolResult
from lina.brain.routing.models import ToolStatus
from lina.brain.routing.router import IntentRouter
from lina.interfaces.qt.formatting import (
    build_welcome_message,
    derive_session_title,
    format_conversation_datetime,
    format_welcome_message,
    friendly_error_message,
    normalize_assistant_text,
)
from lina.interfaces.qt.image_loader import ImageLoadError, QtImageLoader
from lina.interfaces.qt.image_preview_dialog import ImagePreviewDialog
from lina.interfaces.qt.screen_capture import QtScreenCaptureService
from lina.interfaces.qt.screen_preview_dialog import ScreenPreviewDialog
from lina.interfaces.qt.region_capture_overlay import RegionCaptureOverlay
from lina.interfaces.qt.theme import MESSAGE_FONT_DEFAULT, build_stylesheet, resolve_font_family
from lina.interfaces.qt.widgets import ChatMessageWidget, ComposerWidget, SidebarWidget
from lina.interfaces.qt.widgets.tool_activity_card import ToolActivityCard
from lina.interfaces.qt.agent_panel import AgentPanel
from lina.interfaces.qt.worker import FunctionWorker
from lina.services.conversation_service import ConversationService
from lina.conversations.models import ConversationSession
from lina.services.conversation_models import ConversationInput, ConversationResult
from lina.interfaces.qt.widgets.welcome_state import WelcomeStateWidget
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
from lina.settings.models import UserSettings
from lina.settings.service import UserSettingsService
from lina.interfaces.qt.settings_dialog import SettingsDialog
from lina.interfaces.qt.notification_center import NotificationCenterDialog
from lina.interfaces.qt.reminder_dialog import ReminderDialog
from lina.notifications.presenter import QtNotificationPresenter
from lina.notifications.scheduler import NotificationScheduler
from lina.notifications.service import NotificationService
from lina.vision.models import ImageAttachment, VisionRequestError
from lina.voice.controller import VoiceController
from lina.voice.hands_free import HandsFreeConversationService
from lina.voice.models import VoiceSettings, VoiceState
from lina.inference.service import InferenceDiagnosticsService, ModelLifecycleService
from lina.interfaces.qt.camera_source import QtCameraBackend
from lina.interfaces.qt.camera_preview import CameraPreviewWindow
from lina.interfaces.qt.live_vision import QtCaptureInvoker
from lina.interfaces.qt.monitoring_overlay import MonitoringBorderOverlay
from lina.vision.live import (
    CameraConversationState, CameraFrameSource, ChangeRegionsEvent, ChangeSensitivity, LiveVisionConfig,
    LiveVisionController, LiveVisionError, LiveVisionSession, LiveVisionSnapshot,
    LiveVisionSource, LiveVisionState, OverlayGeometry, PreviewFrameEvent,
    RegionFrameSource, ScreenFrameSource, SessionStoppedEvent,
)


APP_VERSION = "v0.12.0-alpha"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
BRANDING_LOGO_PATH = PROJECT_ROOT / "assets" / "branding" / "lina-logo.png"
BRANDING_ICON_PATH = PROJECT_ROOT / "assets" / "branding" / "lina-icon.png"
AUTO_SCROLL_THRESHOLD_PX = 110
LIVE_CAMERA_CONTEXT = "live_camera"


def _is_camera_question(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    return any(phrase in normalized for phrase in (
        "ne görüyorsun", "ne goruyorsun", "elimde ne var", "bu ne renk",
        "bunu tarif et", "şu an ne yapıyorum", "su an ne yapiyorum",
    ))


class LinaMainWindow(QMainWindow):
    """Modern PySide6 chat interface backed by Lina's existing services."""

    voice_state_changed = Signal(object)
    speech_state_changed = Signal(object)
    hands_free_command_received = Signal(str)
    hands_free_feedback_received = Signal(str)
    live_vision_snapshot_received = Signal(object)
    live_preview_frame_received = Signal(object)
    live_change_regions_received = Signal(object)
    live_session_stopped_received = Signal(object)

    def __init__(
        self,
        conversation_service: ConversationService,
        diagnostics_service: ModelDiagnosticsService | None = None,
        vision_diagnostics_service: VisionDiagnosticsService | None = None,
        speech_service: SpeechService | None = None,
        user_settings_service: UserSettingsService | None = None,
        notification_service: NotificationService | None = None,
        intent_router: IntentRouter | None = None,
        screen_capture_service: ScreenCaptureService | None = None,
        image_loader: QtImageLoader | None = None,
        voice_controller: VoiceController | None = None,
        inference_diagnostics_service: InferenceDiagnosticsService | None = None,
        model_lifecycle_service: ModelLifecycleService | None = None,
        hands_free_service: HandsFreeConversationService | None = None,
        live_vision_controller: LiveVisionController | None = None,
        agent_controller: AgentController | None = None,
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
        self._voice_controller = voice_controller
        self._inference_diagnostics_service = inference_diagnostics_service
        self._model_lifecycle_service = model_lifecycle_service
        self._hands_free_service = hands_free_service
        self._live_vision_controller = live_vision_controller
        self._agent_controller = agent_controller
        self._agent_enabled = bool(
            user_settings_service and user_settings_service.current.agent.agent_mode_enabled
        )
        self._agent_notified_sessions: set[str] = set()
        self._live_vision_enabled = True
        self._pending_region_monitor_focus: str | None = None
        self._live_capture_invoker: QtCaptureInvoker | None = None
        self._camera_preview: CameraPreviewWindow | None = None
        self._camera_backend: QtCameraBackend | None = None
        self._monitoring_overlay: MonitoringBorderOverlay | None = None
        self._live_session_id: str | None = None
        self._speech_enabled = True
        self._voice_responses_enabled = False
        self._hands_free_enabled = False
        self._transcription_mode = "insert"
        self._vision_enabled = True
        self._user_settings_service = user_settings_service
        self._settings_dialog: SettingsDialog | None = None
        self._notification_service = notification_service
        self._notification_dialog: NotificationCenterDialog | None = None
        self._notification_scheduler: NotificationScheduler | None = None
        self._intent_router = intent_router
        self._routing_session_key = -1
        self._active_confirmation_cancel: Callable[[], None] | None = None
        self._active_confirmation_confirm: Callable[[], None] | None = None
        self._active_confirmation_card: ToolActivityCard | None = None
        self._tray_icon: QSystemTrayIcon | None = None
        self._force_exit = False
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
        self._welcome_state: WelcomeStateWidget | None = None
        self._conversation_history_service = (
            conversation_service.conversation_history_service
            if hasattr(conversation_service, "conversation_history_service")
            else None
        )
        self._conversation_view = "chats"
        self._conversation_query = ""

        self.setWindowTitle("Lina")
        self.setMinimumSize(1040, 640)
        self.resize(1240, 780)
        self._apply_window_icon()
        self._build_layout()
        self.voice_state_changed.connect(self._apply_voice_state)
        self.speech_state_changed.connect(self._apply_speech_state)
        self.hands_free_command_received.connect(self._submit_hands_free_command)
        self.hands_free_feedback_received.connect(self._handle_hands_free_feedback)
        self.live_vision_snapshot_received.connect(self._apply_live_vision_snapshot)
        self.live_preview_frame_received.connect(self._apply_live_preview_event)
        self.live_change_regions_received.connect(self._apply_live_change_regions)
        self.live_session_stopped_received.connect(self._handle_live_session_stopped)
        if self._live_vision_controller is not None:
            self._live_vision_controller.subscribe(self.live_vision_snapshot_received.emit)
            if hasattr(self._live_vision_controller, "subscribe_preview_frame"):
                self._live_vision_controller.subscribe_preview_frame(self.live_preview_frame_received.emit)
            if hasattr(self._live_vision_controller, "subscribe_change_regions"):
                self._live_vision_controller.subscribe_change_regions(self.live_change_regions_received.emit)
            if hasattr(self._live_vision_controller, "subscribe_session_stopped"):
                self._live_vision_controller.subscribe_session_stopped(self.live_session_stopped_received.emit)
        if self._hands_free_service is not None:
            self._hands_free_service.bind(
                self.hands_free_command_received.emit,
                self.hands_free_feedback_received.emit,
            )
        if self._voice_controller is not None:
            self._voice_controller.subscribe(self.voice_state_changed.emit)
        if self._speech_service is not None and hasattr(self._speech_service, "subscribe_state"):
            self._speech_service.subscribe_state(self.speech_state_changed.emit)
        if self._user_settings_service is not None:
            self._apply_user_settings(self._user_settings_service.current)
        self._setup_system_tray()
        self._setup_notifications()
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
        panel_layout.setSpacing(8)
        root_layout.addWidget(panel, 1)

        self._build_header(panel_layout)
        self._build_chat_area(panel_layout)
        self._build_agent_panel(panel_layout)
        self._build_live_vision_panel(panel_layout)
        self._build_footer(panel_layout)
        self.setCentralWidget(central)

        self._sidebar.new_chat_requested.connect(self.start_new_chat)
        self._sidebar.session_selected.connect(self.load_conversation)
        self._sidebar.session_rename_requested.connect(self.rename_conversation)
        self._sidebar.session_delete_requested.connect(self.delete_conversation)
        self._sidebar.session_pin_requested.connect(self.set_conversation_pinned)
        self._sidebar.session_archive_requested.connect(self.set_conversation_archived)
        self._sidebar.search_changed.connect(self._handle_conversation_search)
        self._sidebar.view_changed.connect(self._handle_conversation_view_changed)

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
        self._session_date_label = QLabel("", header)
        self._session_date_label.setObjectName("sessionDateLabel")
        titles.addWidget(self._session_date_label)
        layout.addLayout(titles, 1)

        self._model_status = QLabel("Model kontrol ediliyor...", header)
        self._model_status.setObjectName("statusChip")
        layout.addWidget(self._model_status)

        self._speech_status = QLabel("Mic · hazırlanıyor", header)
        self._speech_status.setObjectName("statusChip")
        layout.addWidget(self._speech_status)
        self._voice_status = QLabel("Ses · kapalı", header)
        self._voice_status.setObjectName("statusChip")
        layout.addWidget(self._voice_status)
        if self._hands_free_service is not None:
            self._hands_free_toggle = QPushButton("Hands-free Kapalı", header)
            self._hands_free_toggle.setAccessibleName("Hands-free conversation aç veya kapat")
            self._hands_free_toggle.clicked.connect(self._toggle_hands_free_from_tray)
            layout.addWidget(self._hands_free_toggle)
            self._hands_free_pause = QPushButton("Dinlemeyi Duraklat", header)
            self._hands_free_pause.setAccessibleName("Hands-free dinlemeyi duraklat veya sürdür")
            self._hands_free_pause.clicked.connect(self._toggle_hands_free_pause)
            self._hands_free_pause.setEnabled(False)
            layout.addWidget(self._hands_free_pause)
        if self._user_settings_service is not None:
            if self._notification_service is not None:
                self._notification_button = QPushButton("🔔", header)
                self._notification_button.setObjectName("notificationButton")
                self._notification_button.clicked.connect(self.open_notifications)
                layout.addWidget(self._notification_button)
            self._settings_button = QPushButton("Ayarlar", header)
            self._settings_button.setToolTip("Ayarlar")
            self._settings_button.clicked.connect(self.open_settings)
            layout.addWidget(self._settings_button)
        parent_layout.addWidget(header)

    def _build_chat_area(self, parent_layout: QVBoxLayout) -> None:
        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("chatTimelineScroll")
        self._scroll.viewport().setObjectName("chatTimelineViewport")
        self._scroll.setWidgetResizable(True)
        self._message_container = QWidget(self._scroll)
        self._message_container.setObjectName("chatTimeline")
        self._message_layout = QVBoxLayout(self._message_container)
        self._message_layout.setContentsMargins(24, 14, 24, 14)
        self._message_layout.setSpacing(14)
        self._message_layout.addStretch(1)
        self._scroll.setWidget(self._message_container)
        self._scroll.verticalScrollBar().valueChanged.connect(self._update_auto_scroll_state)
        self._scroll.verticalScrollBar().rangeChanged.connect(self._handle_scroll_range_changed)
        parent_layout.addWidget(self._scroll, 1)

    def _build_live_vision_panel(self, parent_layout: QVBoxLayout) -> None:
        panel = QWidget(self)
        panel.setObjectName("liveVisionPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 6, 10, 6)
        self._live_indicator = QLabel("◉ Live Vision · Kapalı", panel)
        self._live_indicator.setObjectName("statusChip")
        self._live_indicator.setAccessibleName("Live Vision gizlilik göstergesi")
        layout.addWidget(self._live_indicator)
        self._live_result = QLabel("Kamera veya ekran takibi etkin değil.", panel)
        self._live_result.setObjectName("mutedLabel")
        self._live_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._live_result, 1)
        self._live_analyze = QPushButton("Şimdi Analiz Et", panel)
        self._live_pause = QPushButton("Duraklat", panel)
        self._live_stop = QPushButton("Durdur", panel)
        self._live_show_preview = QPushButton("Preview’i Göster", panel)
        self._live_analyze.clicked.connect(self._live_analyze_now)
        self._live_pause.clicked.connect(self._toggle_live_pause)
        self._live_stop.clicked.connect(self._stop_live_vision)
        self._live_show_preview.clicked.connect(self._show_existing_camera_preview)
        for button in (self._live_analyze, self._live_pause, self._live_stop, self._live_show_preview):
            button.setEnabled(False)
            layout.addWidget(button)
        parent_layout.addWidget(panel)

    def _build_agent_panel(self, parent_layout: QVBoxLayout) -> None:
        self._agent_panel = AgentPanel(self)
        self._agent_panel.mode_toggle_requested.connect(self._toggle_agent_mode)
        self._agent_panel.start_requested.connect(self._start_agent_plan)
        self._agent_panel.approve_requested.connect(lambda: self._decide_agent_step(ApprovalDecision.APPROVE))
        self._agent_panel.skip_requested.connect(lambda: self._decide_agent_step(ApprovalDecision.SKIP))
        self._agent_panel.modify_requested.connect(lambda: self._decide_agent_step(ApprovalDecision.MODIFY))
        self._agent_panel.pause_requested.connect(self._pause_agent)
        self._agent_panel.resume_requested.connect(self._resume_agent)
        self._agent_panel.cancel_requested.connect(self._cancel_agent)
        self._agent_panel.render(self._agent_controller.session if self._agent_controller else None, enabled=self._agent_enabled)
        self._agent_panel.setVisible(self._agent_controller is not None)
        parent_layout.addWidget(self._agent_panel)

    def _build_footer(self, parent_layout: QVBoxLayout) -> None:
        self._composer = ComposerWidget(
            font_family=self._font_family,
            font_size=self._message_font_size,
            parent=self,
        )
        parent_layout.addWidget(self._composer)

        footer = QWidget(self)
        footer.setObjectName("statusPanel")
        footer.setMaximumHeight(24)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(4, 0, 4, 2)
        layout.setSpacing(0)

        self._status_label = QLabel("Hazır", footer)
        self._status_label.setObjectName("mutedLabel")
        layout.addWidget(self._status_label, 1)
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

        search_action = QAction(self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(self._sidebar.search_input.setFocus)
        self.addAction(search_action)

        new_action = QAction(self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.clear_chat)
        self.addAction(new_action)

        clear_action = QAction(self)
        clear_action.setShortcut(QKeySequence("Ctrl+K"))
        clear_action.triggered.connect(self.clear_chat)

        settings_action = QAction(self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)

    def open_settings(self) -> None:
        """Open one settings dialog instance and focus it when already open."""
        if self._user_settings_service is None:
            return
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(
                self._user_settings_service,
                model_diagnostics=self._diagnostics_service,
                vision_diagnostics=self._vision_diagnostics_service,
                voice_controller=self._voice_controller,
                inference_diagnostics=self._inference_diagnostics_service,
                parent=self,
            )
            self._settings_dialog.settings_applied.connect(self._apply_user_settings)
            self._settings_dialog.finished.connect(self._clear_settings_dialog)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def _setup_system_tray(self) -> None:
        if self._user_settings_service is None or not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray_icon = QSystemTrayIcon(self.windowIcon(), self)
        menu = QMenu(self)
        open_action = menu.addAction("Lina'yı Aç")
        open_action.triggered.connect(self._show_from_tray)
        new_action = menu.addAction("Yeni Sohbet")
        new_action.triggered.connect(self._new_chat_from_tray)
        if self._notification_service is not None:
            reminder_action = menu.addAction("Yeni Hatırlatıcı")
            reminder_action.triggered.connect(self.create_reminder)
            notifications_action = menu.addAction("Bildirimler")
            notifications_action.triggered.connect(self.open_notifications)
        settings_action = menu.addAction("Ayarlar")
        settings_action.triggered.connect(self.open_settings)
        stop_voice_action = menu.addAction("Sesi Durdur")
        stop_voice_action.triggered.connect(self.stop_voice)
        if self._hands_free_service is not None:
            self._tray_hands_free_action = menu.addAction("Hands-free Aç/Kapat")
            self._tray_hands_free_action.triggered.connect(self._toggle_hands_free_from_tray)
            self._tray_pause_action = menu.addAction("Dinlemeyi Duraklat")
            self._tray_pause_action.triggered.connect(self._toggle_hands_free_pause)
        if self._live_vision_controller is not None:
            menu.addSeparator()
            self._tray_live_status_action = menu.addAction("Live Vision Durumu: Kapalı")
            self._tray_live_status_action.setEnabled(False)
            self._tray_live_analyze_action = menu.addAction("Şimdi Analiz Et")
            self._tray_live_analyze_action.triggered.connect(self._live_analyze_now)
            self._tray_live_pause_action = menu.addAction("Takibi Duraklat")
            self._tray_live_pause_action.triggered.connect(self._toggle_live_pause)
            self._tray_live_stop_action = menu.addAction("Takibi Durdur")
            self._tray_live_stop_action.triggered.connect(self._stop_live_vision)
            self._tray_camera_action = menu.addAction("Kamerayı Aç")
            self._tray_camera_action.triggered.connect(lambda: self._confirm_tray_live_start(LiveVisionSource.CAMERA))
            self._tray_screen_action = menu.addAction("Ekranı Takip Et")
            self._tray_screen_action.triggered.connect(lambda: self._confirm_tray_live_start(LiveVisionSource.SCREEN))
            self._update_live_tray_actions(LiveVisionState.IDLE)
        if self._agent_controller is not None:
            menu.addSeparator()
            self._tray_agent_mode_action = menu.addAction("Agent Modu Aç/Kapat")
            self._tray_agent_mode_action.triggered.connect(self._toggle_agent_mode)
            self._tray_agent_show_action = menu.addAction("Aktif Görevi Göster")
            self._tray_agent_show_action.triggered.connect(self._show_agent_from_tray)
            self._tray_agent_pause_action = menu.addAction("Agent Görevini Duraklat")
            self._tray_agent_pause_action.triggered.connect(self._toggle_agent_pause)
            self._tray_agent_cancel_action = menu.addAction("Agent Görevini İptal Et")
            self._tray_agent_cancel_action.triggered.connect(self._cancel_agent)
            self._update_agent_ui()
        menu.addSeparator()
        exit_action = menu.addAction("Çıkış")
        exit_action.triggered.connect(self._exit_from_tray)
        self._tray_icon.setContextMenu(menu)
        self._tray_icon.setToolTip("Lina")
        self._tray_icon.show()

    def _setup_notifications(self) -> None:
        if self._notification_service is None:
            return
        presenter = QtNotificationPresenter(self._tray_icon)
        provider = (lambda: self._user_settings_service.current.system) if self._user_settings_service else None
        self._notification_scheduler = NotificationScheduler(self._notification_service._repository, presenter.present, settings_provider=provider)
        self._notification_scheduler.process_missed()
        self._notification_scheduler.start()
        self._refresh_notification_badge()

    def _refresh_notification_badge(self) -> None:
        if hasattr(self, "_notification_button") and self._notification_service is not None:
            count = self._notification_service.unread_count()
            self._notification_button.setText(f"🔔 {count}" if count else "🔔")

    def open_notifications(self) -> None:
        if self._notification_service is None:
            return
        if self._notification_dialog is None:
            self._notification_dialog = NotificationCenterDialog(self._notification_service, self)
            self._notification_dialog.finished.connect(lambda _result: self._clear_notification_dialog())
        else:
            self._notification_dialog.reload()
        self._notification_dialog.show(); self._notification_dialog.raise_(); self._notification_dialog.activateWindow()
        self._refresh_notification_badge()

    def _clear_notification_dialog(self) -> None:
        self._notification_dialog = None
        self._refresh_notification_badge()

    def create_reminder(self) -> None:
        if self._notification_service is None:
            return
        dialog = ReminderDialog(parent=self)
        if dialog.exec():
            created = self._notification_service.create(
                dialog.title_edit.text().strip(), dialog.due_at, dialog.recurrence
            )
            if self._notification_dialog is not None:
                self._notification_dialog._filter.setCurrentIndex(0)
                self._notification_dialog.reload(created.id)
            # Creating a reminder does not create a notification event. Reading
            # the event count keeps the badge unchanged and authoritative.
            self._refresh_notification_badge()

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _new_chat_from_tray(self) -> None:
        self.start_new_chat()
        self._show_from_tray()

    def _exit_from_tray(self) -> None:
        self._force_exit = True
        self.close()

    def _toggle_hands_free_from_tray(self) -> None:
        if self._user_settings_service is None:
            return
        current = self._user_settings_service.current
        enabled = not current.speech.hands_free_enabled
        if enabled and not self._confirm_hands_free_privacy():
            return
        updated = replace(
            current,
            speech=replace(
                current.speech,
                hands_free_enabled=enabled,
                wake_word_enabled=enabled,
            ),
        )
        self._user_settings_service.update(updated)
        self._apply_user_settings(updated)

    def _toggle_hands_free_pause(self) -> None:
        if self._hands_free_service is None or self._voice_controller is None:
            return
        if self._voice_controller.hands_free_paused:
            resumed = self._hands_free_service.resume()
            self._set_status("Hands-free dinleme devam ediyor." if resumed else "Wake-word algılama şu anda kullanılamıyor.")
        else:
            self._hands_free_service.pause()
            self._set_status("Sesli konuşma durduruldu.")

    def _confirm_hands_free_privacy(self) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle("Hands-free conversation")
        box.setText(
            "Hands-free modunda Lina, “Hey Lina” ifadesini algılamak için mikrofonu "
            "yerel olarak dinler. Ses kayıtları saklanmaz ve cloud’a gönderilmez."
        )
        enable = box.addButton("Etkinleştir", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Vazgeç", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        return box.clickedButton() is enable

    def _clear_settings_dialog(self, _result: int) -> None:
        self._settings_dialog = None

    def _apply_user_settings(self, settings: UserSettings) -> None:
        """Apply settings that are safe to reflect in the current window."""
        if not settings.general.intent_routing_enabled and self._intent_router is not None:
            self._intent_router.cancel_pending()
            self._active_confirmation_cancel = None
            self._active_confirmation_confirm = None
            if self._active_confirmation_card is not None:
                self._active_confirmation_card.hide()
                self._active_confirmation_card = None
        application = QApplication.instance()
        if application is not None:
            application.setFont(QFont(self._font_family, round(11 * settings.appearance.font_scale)))
            application.setStyleSheet(
                build_stylesheet(
                    self._font_family,
                    theme=settings.appearance.theme,
                    font_scale=settings.appearance.font_scale,
                )
            )
            for widget in application.topLevelWidgets():
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
        if settings.general.welcome_enabled and self._welcome_state is None and not self._message_rows:
            self._show_welcome_state()
        elif not settings.general.welcome_enabled:
            self._hide_welcome_state()
        self._speech_enabled = settings.speech.enabled
        self._voice_responses_enabled = settings.speech.voice_responses_enabled
        hands_free_was_enabled = self._hands_free_enabled
        self._hands_free_enabled = settings.speech.hands_free_enabled
        if hands_free_was_enabled and not self._hands_free_enabled and self._hands_free_service is not None:
            self._hands_free_service.cancel_active()
        self._wake_indicator_enabled = settings.speech.wake_word_indicator_enabled
        self._transcription_mode = settings.speech.transcription_mode
        if self._speech_service is not None and hasattr(self._speech_service, "set_microphone_device"):
            self._speech_service.set_microphone_device(settings.speech.microphone_device_id)
        if self._voice_controller is not None:
            self._voice_controller.configure(
                VoiceSettings(
                    enabled=settings.speech.enabled,
                    responses_enabled=settings.speech.voice_responses_enabled,
                    voice_id=settings.speech.system_voice,
                    rate=settings.speech.speech_rate,
                    volume=settings.speech.volume,
                    barge_in_enabled=settings.speech.barge_in_enabled,
                    hands_free_enabled=settings.speech.hands_free_enabled,
                    wake_word_enabled=settings.speech.wake_word_enabled,
                    wake_phrase=settings.speech.wake_phrase,
                    return_to_wake_listening=settings.speech.return_to_wake_listening,
                    voice_confirmation_enabled=settings.speech.voice_confirmation_enabled,
                    microphone_device_id=settings.speech.microphone_device_id,
                )
            )
            if settings.speech.voice_responses_enabled:
                self._apply_voice_state(self._voice_controller.state)
            else:
                self._voice_status.setText("Sesli yanıt · kapalı")
        self._vision_enabled = settings.vision.enabled
        self._agent_enabled = settings.agent.agent_mode_enabled
        if self._agent_controller is not None:
            self._agent_controller.auto_start_read_only_plans = settings.agent.auto_start_read_only_plans
            self._agent_controller.always_show_plan = settings.agent.always_show_plan
            self._agent_controller.policy.max_steps = settings.agent.max_agent_steps
            self._agent_controller.policy.max_replans = settings.agent.max_agent_replans
        self._update_agent_ui()
        self._live_vision_enabled = settings.live_vision.enabled and settings.vision.enabled
        if self._camera_preview is not None:
            self._camera_preview.canvas.set_mirror_enabled(settings.live_vision.mirror_camera_preview)
            self._camera_preview.auto_commentary_button.setChecked(settings.live_vision.automatic_camera_commentary_enabled)
            self._camera_preview.mute_button.setChecked(not settings.live_vision.speak_semantic_changes)
        if hasattr(self, "_hands_free_toggle"):
            self._hands_free_toggle.setText("Hands-free Açık" if settings.speech.hands_free_enabled else "Hands-free Kapalı")
            self._hands_free_pause.setEnabled(settings.speech.hands_free_enabled)
        self._composer.attachment_button.setEnabled(self._vision_enabled)
        self._set_vision_controls_enabled(self._vision_enabled)
        if not self._vision_enabled and self._screen_context is not None:
            self._clear_screen_context()
        if not self._live_vision_enabled and self._live_vision_controller is not None:
            self._live_vision_controller.stop()
        self._refresh_speech_status()
        self._set_status("Ayarlar uygulandı")

    def _set_vision_controls_enabled(self, enabled: bool) -> None:
        self._composer.screen_button.setEnabled(enabled and not self._is_screen_capture_busy)

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
        request_created_at = datetime.now(timezone.utc)
        self._hide_welcome_state()
        self._auto_scroll_enabled = True
        user_message = self._append_user_message(
            message,
            image_bytes=(
                request_screen_context.image_bytes
                if request_screen_context is not None
                else None
            ),
            visual_context=request_screen_context,
            created_at=request_created_at,
        )
        if request_screen_context is not None:
            user_message.set_visual_status("Analiz ediliyor")
        if self._active_confirmation_cancel is not None:
            confirmation = _classify_voice_confirmation(message)
            if confirmation == "yes" and self._active_confirmation_confirm is not None:
                self._active_confirmation_confirm()
                return
            if confirmation == "no":
                self._active_confirmation_cancel()
                return
            if self._voice_controller is not None and self._voice_controller.hands_free_enabled:
                prompt = "Onaylıyor musun, iptal mi ediyorsun?"
                self._append_assistant_message(prompt)
                self._voice_controller.request_confirmation_listening()
                self.speak_assistant_response(prompt)
                return
        if self._agent_controller is not None and self._agent_controller.active_session is not None:
            agent_session = self._agent_controller.active_session
            decision = parse_approval(message)
            if agent_session.status is AgentSessionStatus.AWAITING_PLAN_APPROVAL and decision is ApprovalDecision.APPROVE:
                self._start_agent_plan()
                self._finish_routed_intent(message, self._agent_controller.result_summary(), request_created_at)
                return
            if agent_session.status is AgentSessionStatus.AWAITING_STEP_APPROVAL and decision is not ApprovalDecision.AMBIGUOUS:
                self._decide_agent_step(decision)
                self._finish_routed_intent(message, self._agent_controller.result_summary(), request_created_at)
                return
        if _is_camera_question(message) and not self._camera_is_active():
            self._finish_routed_intent(
                message,
                "Kamera şu anda açık değil.",
                request_created_at,
            )
            return
        if self._intent_router is not None:
            routed = self._intent_router.route(
                message, self._routing_session_key, self._active_request_id
            )
            if routed.intent is not RoutingIntentType.CHAT:
                self._handle_routed_intent(routed, message, request_created_at)
                return
        if request_screen_context is None:
            request_screen_context = self._capture_live_camera_context(message)
            if request_screen_context is not None:
                user_message.set_visual_status("Canlı kamera karesi analiz ediliyor")
        self._show_typing_indicator(
            "Lina ekranı inceliyor..."
            if request_screen_context is not None
            else "Yazıyor..."
        )
        self._set_waiting_state(True)
        self._set_status("Cevap bekleniyor...")
        if (
            self._voice_controller is not None
            and self._voice_controller.responses_enabled
            and self._voice_controller.state is VoiceState.IDLE
        ):
            self._voice_controller.begin_thinking()

        self._active_request_id += 1
        request_id = self._active_request_id
        if request_screen_context is not None:
            self._request_screen_contexts[request_id] = request_screen_context
        worker = FunctionWorker(
            self._run_conversation_request,
            request_id,
            message,
            request_screen_context,
            request_created_at,
        )
        worker.signals.result.connect(self._handle_conversation_worker_result)
        worker.signals.error.connect(self._handle_conversation_error)
        self._start_worker(worker)

    def _handle_routed_intent(self, request: IntentRequest, user_text: str, created_at: datetime) -> None:
        if request.intent in {
            RoutingIntentType.AGENT_EXECUTE, RoutingIntentType.AGENT_PLAN,
            RoutingIntentType.AGENT_PAUSE, RoutingIntentType.AGENT_RESUME,
            RoutingIntentType.AGENT_CANCEL, RoutingIntentType.AGENT_STATUS,
            RoutingIntentType.AGENT_MODIFY_PLAN,
        }:
            self._handle_agent_intent(request, user_text, created_at)
            return
        clarification = self._intent_router.clarification_message(request)
        if clarification:
            self._finish_routed_intent(user_text, clarification, created_at)
            return
        if request.intent is RoutingIntentType.UNSAFE:
            self._finish_routed_intent(user_text, "Bu işlem Lina’nın mevcut yetkileri dışında.", created_at)
            return
        if request.intent is RoutingIntentType.UNSUPPORTED:
            self._finish_routed_intent(user_text, "Bu işlem şu anda desteklenmiyor.", created_at)
            return
        if request.intent is RoutingIntentType.CANCEL:
            self._finish_routed_intent(user_text, "İşlem iptal edildi.", created_at)
            return
        if request.intent in {RoutingIntentType.ANALYZE_SCREEN, RoutingIntentType.ANALYZE_REGION, RoutingIntentType.ANALYZE_IMAGE}:
            card = self._add_tool_card("Görsel analiz", "Vision hazırlanıyor.")
            card.set_status(ToolStatus.RUNNING)
            message = self._run_vision_intent(request.intent)
            unavailable = any(term in message for term in ("kapalı", "ulaşılamadığı", "uygun değil", "seçmelisin"))
            card.set_status(ToolStatus.UNAVAILABLE if unavailable else ToolStatus.SUCCESS, message, retryable=unavailable)
            if unavailable:
                card.retry_requested.connect(lambda: self._retry_vision_intent(request.intent, card))
            self._finish_routed_intent(user_text, message, created_at)
            return
        if request.requires_confirmation:
            self._show_confirmation_card(request, user_text, created_at)
            return
        self._execute_routed_tool(request, user_text, created_at, confirmed=True)

    def _handle_agent_intent(self, request: IntentRequest, user_text: str, created_at: datetime) -> None:
        controller = self._agent_controller
        if controller is None:
            self._finish_routed_intent(user_text, "Agent Mode şu anda kullanılamıyor.", created_at)
            return
        try:
            if request.intent is RoutingIntentType.AGENT_STATUS:
                progress = controller.status()
                message = "Aktif Agent görevi yok." if progress is None else f"Agent durumu: {progress.status.value}; ilerleme {progress.current}/{progress.total}. {progress.summary}"
            elif request.intent is RoutingIntentType.AGENT_PAUSE:
                session = controller.active_session
                message = "Aktif Agent görevi yok." if session is None else (controller.pause(session.session_id) and "Agent görevi duraklatıldı.")
            elif request.intent is RoutingIntentType.AGENT_RESUME:
                session = controller.active_session
                message = "Aktif Agent görevi yok." if session is None else (controller.resume(session.session_id) and controller.result_summary())
            elif request.intent is RoutingIntentType.AGENT_CANCEL:
                session = controller.active_session
                message = "Aktif Agent görevi yok." if session is None else (controller.cancel(session.session_id) and "Agent görevi iptal edildi. Tamamlanan kalıcı işlemler geri alınmadı.")
            elif request.intent is RoutingIntentType.AGENT_MODIFY_PLAN:
                message = "Plan düzenleme isteği kaydedildi; mevcut plan çalıştırılmadı. Yeni isteğini Agent modunda açıkça yaz."
            else:
                session = controller.create_session(user_text, self._routing_session_key, self._active_request_id)
                plan = controller.plan()
                self._agent_enabled = True
                message = f"{len(plan.steps)} adımlı plan hazır. İnceleyip Planı Başlat seçeneğiyle onayla."
                if session.status is AgentSessionStatus.COMPLETED:
                    message = controller.result_summary()
            self._update_agent_ui()
            self._finish_routed_intent(user_text, message, created_at)
        except AgentError as error:
            self._update_agent_ui()
            self._finish_routed_intent(user_text, str(error), created_at)

    def _toggle_agent_mode(self) -> None:
        self._agent_enabled = not self._agent_enabled
        if not self._agent_enabled and self._agent_controller and self._agent_controller.active_session:
            self._agent_controller.cancel(self._agent_controller.active_session.session_id)
        if self._user_settings_service is not None:
            current = self._user_settings_service.current
            self._user_settings_service.update(replace(current, agent=replace(current.agent, agent_mode_enabled=self._agent_enabled)))
        self._update_agent_ui()

    def _start_agent_plan(self) -> None:
        if not self._agent_controller or not self._agent_controller.active_session:
            return
        try:
            session = self._agent_controller.active_session
            self._agent_controller.approve_plan(session.session_id, session.generation_id)
            self._agent_controller.run(self._routing_session_key)
        except AgentError as error:
            self._set_status(str(error))
        self._update_agent_ui()

    def _decide_agent_step(self, decision: ApprovalDecision) -> None:
        if not self._agent_controller or not self._agent_controller.active_session:
            return
        try:
            session = self._agent_controller.active_session
            self._agent_controller.approve_step(session.session_id, decision, session.generation_id)
        except AgentError as error:
            self._set_status(str(error))
        self._update_agent_ui()

    def _pause_agent(self) -> None:
        if self._agent_controller and self._agent_controller.active_session:
            try:
                self._agent_controller.pause(self._agent_controller.active_session.session_id)
            except AgentError as error:
                self._set_status(str(error))
        self._update_agent_ui()

    def _resume_agent(self) -> None:
        if self._agent_controller and self._agent_controller.active_session:
            try:
                self._agent_controller.resume(self._agent_controller.active_session.session_id)
            except AgentError as error:
                self._set_status(str(error))
        self._update_agent_ui()

    def _cancel_agent(self) -> None:
        if self._agent_controller and self._agent_controller.active_session:
            self._agent_controller.cancel(self._agent_controller.active_session.session_id)
        if self._voice_controller is not None:
            self.stop_voice()
        self._update_agent_ui()

    def _toggle_agent_pause(self) -> None:
        session = self._agent_controller.active_session if self._agent_controller else None
        if session is None:
            return
        if session.status is AgentSessionStatus.PAUSED:
            self._resume_agent()
        else:
            self._pause_agent()

    def _show_agent_from_tray(self) -> None:
        self._show_from_tray()
        self._agent_panel.setFocus()

    def _update_agent_ui(self) -> None:
        if not hasattr(self, "_agent_panel"):
            return
        session = self._agent_controller.session if self._agent_controller else None
        self._agent_panel.render(session, enabled=self._agent_enabled)
        active = bool(self._agent_controller and self._agent_controller.active_session)
        if hasattr(self, "_tray_agent_pause_action"):
            self._tray_agent_show_action.setEnabled(active)
            self._tray_agent_pause_action.setEnabled(active)
            self._tray_agent_cancel_action.setEnabled(active)
            paused = bool(active and self._agent_controller.active_session.status is AgentSessionStatus.PAUSED)
            self._tray_agent_pause_action.setText("Agent Görevine Devam Et" if paused else "Agent Görevini Duraklat")
        if self._tray_icon is not None and active:
            progress = self._agent_controller.status()
            if progress.status in {AgentSessionStatus.AWAITING_PLAN_APPROVAL, AgentSessionStatus.AWAITING_STEP_APPROVAL}:
                self._tray_icon.setToolTip("Lina — Agent onay bekliyor")
            elif progress.status is AgentSessionStatus.PAUSED:
                self._tray_icon.setToolTip("Lina — Agent duraklatıldı")
            else:
                self._tray_icon.setToolTip(f"Lina — Agent görevi çalışıyor: {progress.current}/{progress.total}")
        if self._tray_icon is not None and session and session.terminal and session.session_id not in self._agent_notified_sessions:
            settings = self._user_settings_service.current.agent if self._user_settings_service else None
            if settings is None or settings.notify_agent_completion:
                title = "Agent görevi tamamlandı" if session.status in {AgentSessionStatus.COMPLETED, AgentSessionStatus.PARTIALLY_COMPLETED} else "Agent görevi sona erdi"
                self._tray_icon.showMessage(title, self._agent_controller.result_summary())
            self._agent_notified_sessions.add(session.session_id)

    def _execute_routed_tool(self, request: IntentRequest, user_text: str, created_at: datetime, confirmed: bool, card: ToolActivityCard | None = None) -> None:
        live_intents = {
            RoutingIntentType.CAMERA_OPEN, RoutingIntentType.CAMERA_ANALYZE,
            RoutingIntentType.CAMERA_MONITOR, RoutingIntentType.SCREEN_MONITOR,
            RoutingIntentType.REGION_MONITOR, RoutingIntentType.LIVE_VISION_PAUSE,
            RoutingIntentType.LIVE_VISION_RESUME, RoutingIntentType.LIVE_VISION_STOP,
            RoutingIntentType.LIVE_VISION_STATUS,
        }
        if request.intent in live_intents:
            activity = card or self._add_tool_card(self._tool_title(request), "Live Vision hazırlanıyor.")
            activity.set_status(ToolStatus.RUNNING)
            result = self._execute_live_intent(request)
            activity.set_status(ToolStatus.SUCCESS if result.success else ToolStatus.UNAVAILABLE, result.user_message, result.retryable)
            self._finish_routed_intent(user_text, result.user_message, created_at)
            return
        activity = card or self._add_tool_card(self._tool_title(request), "İşlem hazırlanıyor.")
        activity.set_status(ToolStatus.RUNNING)
        result = self._intent_router.execute(
            request,
            RequestContext(
                self._routing_session_key,
                generation_id=self._active_request_id,
                confirmed=confirmed,
            ),
        )
        if result.success:
            activity.set_status(ToolStatus.SUCCESS, result.user_message)
        else:
            status = ToolStatus.UNAVAILABLE if result.error_code == "unavailable" else ToolStatus.FAILURE
            activity.set_status(status, result.user_message, result.retryable)
            if result.retryable:
                activity.retry_requested.connect(lambda: self._retry_readonly_tool(request, activity))
        self._finish_routed_intent(user_text, result.user_message, created_at)
        if result.success and request.intent is RoutingIntentType.CREATE_REMINDER:
            if self._notification_dialog is not None:
                self._notification_dialog.reload()

    def _show_confirmation_card(self, request: IntentRequest, user_text: str, created_at: datetime) -> None:
        card = self._add_tool_card(
            self._tool_title(request),
            self._intent_router.confirmation_message(request),
            self._tool_arguments(request),
            risk="Kalıcı değişiklik",
            confirmation=True,
        )
        handled = {"value": False}

        def confirm() -> None:
            if handled["value"]:
                return
            handled["value"] = True
            self._active_confirmation_cancel = None
            self._active_confirmation_confirm = None
            self._active_confirmation_card = None
            self._execute_routed_tool(request, user_text, created_at, confirmed=True, card=card)

        def cancel() -> None:
            if handled["value"]:
                return
            handled["value"] = True
            self._active_confirmation_cancel = None
            self._active_confirmation_confirm = None
            self._active_confirmation_card = None
            self._intent_router.cancel_pending(self._routing_session_key)
            card.set_status(ToolStatus.CANCELLED, "İşlemden vazgeçildi.")
            self._finish_routed_intent(user_text, "İşlemden vazgeçildi.", created_at)

        card.confirmed.connect(confirm)
        card.cancelled.connect(cancel)
        self._active_confirmation_cancel = cancel
        self._active_confirmation_confirm = confirm
        self._active_confirmation_card = card
        confirmation_text = self._intent_router.confirmation_message(request)
        if self._voice_controller is not None and self._voice_controller.request_confirmation_listening():
            self.speak_assistant_response(confirmation_text)
            QTimer.singleShot(25_000, lambda: self._expire_voice_confirmation(card, cancel))

    def _retry_readonly_tool(self, request: IntentRequest, card: ToolActivityCard) -> None:
        card.set_status(ToolStatus.RUNNING, "İşlem tekrar deneniyor.")
        result = self._intent_router.retry(
            request,
            RequestContext(self._routing_session_key, generation_id=self._active_request_id, confirmed=True),
        )
        status = ToolStatus.SUCCESS if result.success else ToolStatus.UNAVAILABLE if result.error_code == "unavailable" else ToolStatus.FAILURE
        card.set_status(status, result.user_message, result.retryable)
        self._append_assistant_message(result.user_message)
        if self._conversation_history_service is not None:
            self._conversation_history_service.record_assistant_message(result.user_message)

    def _retry_vision_intent(self, intent: RoutingIntentType, card: ToolActivityCard) -> None:
        card.set_status(ToolStatus.RUNNING, "Vision tekrar deneniyor.")
        message = self._run_vision_intent(intent)
        unavailable = any(term in message for term in ("kapalı", "ulaşılamadığı", "uygun değil", "seçmelisin"))
        card.set_status(ToolStatus.UNAVAILABLE if unavailable else ToolStatus.SUCCESS, message, retryable=unavailable)
        self._append_assistant_message(message)
        if self._conversation_history_service is not None:
            self._conversation_history_service.record_assistant_message(message)

    def _add_tool_card(self, title: str, description: str, arguments: str = "", risk: str = "Düşük", confirmation: bool = False) -> ToolActivityCard:
        card = ToolActivityCard(title, description, arguments, risk, confirmation, self._message_container)
        row = QWidget(self._message_container)
        row_layout = QHBoxLayout(row); row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(card); row_layout.addStretch(1)
        self._message_layout.insertWidget(self._message_layout.count() - 1, row)
        self._message_rows.append(row)
        self._schedule_scroll_to_bottom()
        return card

    @staticmethod
    def _tool_title(request: IntentRequest) -> str:
        return {
            RoutingIntentType.CREATE_REMINDER: "Hatırlatıcı oluştur",
            RoutingIntentType.LIST_REMINDERS: "Hatırlatıcıları listele",
            RoutingIntentType.READ_FILE: "Dosyayı oku",
            RoutingIntentType.MEMORY_STORE: "Hafızaya kaydet",
            RoutingIntentType.MEMORY_RECALL: "Hafızada ara",
            RoutingIntentType.CAMERA_OPEN: "Kamerayı aç",
            RoutingIntentType.CAMERA_ANALYZE: "Kamerayı analiz et",
            RoutingIntentType.CAMERA_MONITOR: "Kamerayı takip et",
            RoutingIntentType.SCREEN_MONITOR: "Ekranı takip et",
            RoutingIntentType.REGION_MONITOR: "Bölgeyi takip et",
            RoutingIntentType.LIVE_VISION_PAUSE: "Takibi duraklat",
            RoutingIntentType.LIVE_VISION_RESUME: "Takibe devam et",
            RoutingIntentType.LIVE_VISION_STOP: "Takibi durdur",
            RoutingIntentType.LIVE_VISION_STATUS: "Live Vision durumu",
        }.get(request.intent, "Araç işlemi")

    @staticmethod
    def _tool_arguments(request: IntentRequest) -> str:
        if request.intent is RoutingIntentType.CREATE_REMINDER:
            due = request.extracted_arguments.get("due_at")
            title = request.extracted_arguments.get("title", "")
            return f"{due.astimezone().strftime('%d.%m.%Y · %H:%M')}\n“{title}”" if due else f"“{title}”"
        if request.intent is RoutingIntentType.MEMORY_STORE:
            return f"“{request.extracted_arguments.get('content', '')}”"
        return ""

    def _execute_live_intent(self, request: IntentRequest) -> ToolResult:
        controller = self._live_vision_controller
        if controller is None or not self._live_vision_enabled:
            return ToolResult(False, "Live Vision şu anda kapalı.", error_code="unavailable")
        intent = request.intent
        if intent is RoutingIntentType.LIVE_VISION_PAUSE:
            success = controller.pause()
            return ToolResult(success, "Canlı takip duraklatıldı." if success else "Duraklatılacak aktif takip yok.")
        if intent is RoutingIntentType.LIVE_VISION_RESUME:
            success = controller.resume()
            if not success and controller.snapshot.source is LiveVisionSource.CAMERA:
                success = controller.set_automatic_commentary(True)
            return ToolResult(success, "Canlı takip devam ediyor." if success else "Devam ettirilecek takip yok.")
        if intent is RoutingIntentType.LIVE_VISION_STOP:
            success = controller.stop()
            return ToolResult(success, "Canlı takip durduruldu." if success else "Durdurulacak aktif takip yok.")
        if intent is RoutingIntentType.LIVE_VISION_STATUS:
            snapshot = controller.snapshot
            if snapshot.state is LiveVisionState.IDLE:
                return ToolResult(True, "Şu anda aktif bir takip yok.")
            return ToolResult(True, f"{self._live_source_label(snapshot.source)} takip ediliyor; durum: {snapshot.state.value}.")
        focus = str(request.extracted_arguments.get("user_focus", ""))
        if intent is RoutingIntentType.REGION_MONITOR:
            self._pending_region_monitor_focus = focus
            self.handle_region_capture()
            return ToolResult(True, "Takip etmek istediğin ekran bölgesini seç.")
        try:
            if intent in {RoutingIntentType.CAMERA_OPEN, RoutingIntentType.CAMERA_ANALYZE, RoutingIntentType.CAMERA_MONITOR}:
                settings = self._user_settings_service.current.live_vision if self._user_settings_service else None
                backend = QtCameraBackend(settings.camera_device_id if settings else None)
                source = CameraFrameSource(backend)
                session_id = self._start_live_source(
                    source, focus,
                    analyze_immediately=True,
                    single_shot=intent is RoutingIntentType.CAMERA_ANALYZE,
                )
                self._camera_backend = backend
                backend.subscribe_preview(lambda image, sid=session_id: self._apply_camera_image(image, sid))
                backend.subscribe_error(lambda message, sid=session_id: self._handle_camera_preview_error(message, sid))
                self._show_camera_preview(backend.device_name, session_id)
                return ToolResult(True, "Kamera tek kare analiz için açıldı." if intent is RoutingIntentType.CAMERA_ANALYZE else "Kamera takibi aktif.")
            screen = self._selected_live_screen()
            if screen is None:
                return ToolResult(False, "Ekran görüntüsü alınamadı.", error_code="unavailable")
            self._start_screen_monitor(screen, focus)
            return ToolResult(True, "Ekran takibi aktif.")
        except LiveVisionError as error:
            return ToolResult(False, str(error), error_code="unavailable", retryable=True)

    def _live_config(self, source: LiveVisionSource | None = None) -> LiveVisionConfig:
        settings = self._user_settings_service.current.live_vision if self._user_settings_service else None
        if settings is None:
            return LiveVisionConfig()
        return LiveVisionConfig(
            capture_interval_seconds=settings.capture_interval_seconds,
            minimum_analysis_interval_seconds=(
                settings.camera_analysis_interval_seconds
                if source is LiveVisionSource.CAMERA else settings.minimum_analysis_interval_seconds
            ),
            duration_seconds=(settings.monitor_duration_minutes * 60.0) if settings.monitor_duration_minutes else None,
            sensitivity=ChangeSensitivity(settings.change_sensitivity),
            voice_feedback_enabled=settings.voice_live_vision_enabled and settings.speak_semantic_changes,
            speak_only_meaningful_changes=settings.speak_only_meaningful_changes,
            repeat_speech_cooldown_seconds=settings.commentary_cooldown_seconds,
            automatic_commentary_enabled=settings.automatic_camera_commentary_enabled,
        )

    def _selected_live_screen(self):
        screens = QGuiApplication.screens()
        settings = self._user_settings_service.current.live_vision if self._user_settings_service else None
        preferred = settings.default_screen_name if settings else None
        if preferred:
            selected = next((screen for screen in screens if screen.name() == preferred), None)
            if selected is not None:
                return selected
        return QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()

    def _start_screen_monitor(self, screen, focus: str) -> str:
        self._cleanup_live_visuals()
        capture = (
            lambda: self._screen_capture_service.capture_screen(screen)
            if hasattr(self._screen_capture_service, "capture_screen")
            else self._screen_capture_service.capture()
        )
        invoker = QtCaptureInvoker(capture, self)
        source = ScreenFrameSource(invoker)
        overlay = MonitoringBorderOverlay(screen.geometry, "Lina ekranı izliyor")
        overlay.geometry_changed.connect(lambda geometry: self._publish_overlay_geometry(geometry, screen.name()))
        overlay.closed_unexpectedly.connect(self._stop_live_vision)
        self._live_capture_invoker = invoker
        self._monitoring_overlay = overlay
        overlay.start()
        if not overlay.isVisible():
            self._cleanup_live_visuals()
            raise LiveVisionError("Ekran takip çerçevesi gösterilemedi.")
        session = LiveVisionSession(source.source, focus, self._live_config(source.source))
        try:
            session_id = self._live_vision_controller.start(source, session, analyze_immediately=True)
        except Exception:
            self._cleanup_live_visuals()
            raise
        self._live_session_id = session_id
        self._publish_overlay_geometry(screen.geometry(), screen.name())
        return session_id

    def _start_region_monitor(self, screen, local_rectangle: QRect, focus: str) -> str:
        self._cleanup_live_visuals()

        def monitored_geometry() -> QRect:
            screen_geometry = screen.geometry()
            global_rectangle = QRect(local_rectangle).translated(screen_geometry.topLeft())
            return global_rectangle.intersected(screen_geometry)

        def capture_selected_region():
            current = monitored_geometry()
            if current.size() != local_rectangle.size():
                raise ScreenCaptureError("Selected screen geometry changed.")
            return self._screen_capture_service.capture_region(current, screen)

        invoker = QtCaptureInvoker(capture_selected_region, self)
        source = RegionFrameSource(invoker.capture)
        overlay = MonitoringBorderOverlay(monitored_geometry, "Lina bu bölgeyi izliyor")
        overlay.geometry_changed.connect(lambda geometry: self._publish_overlay_geometry(geometry, screen.name()))
        overlay.closed_unexpectedly.connect(self._stop_live_vision)
        self._live_capture_invoker = invoker
        self._monitoring_overlay = overlay
        overlay.start()
        if not overlay.isVisible():
            self._cleanup_live_visuals()
            raise LiveVisionError("Ekran takip çerçevesi gösterilemedi.")
        session = LiveVisionSession(source.source, focus, self._live_config(source.source))
        try:
            session_id = self._live_vision_controller.start(source, session, analyze_immediately=True)
        except Exception:
            self._cleanup_live_visuals()
            raise
        self._live_session_id = session_id
        self._publish_overlay_geometry(monitored_geometry(), screen.name())
        return session_id

    def _start_live_source(self, source, focus: str = "", *, analyze_immediately: bool = False, single_shot: bool = False) -> str:
        self._cleanup_live_visuals()
        session = LiveVisionSession(source.source, focus, self._live_config(source.source))
        session_id = self._live_vision_controller.start(source, session, analyze_immediately=analyze_immediately, single_shot=single_shot)
        self._live_session_id = session_id
        return session_id

    def _show_camera_preview(self, device_name: str, session_id: str) -> None:
        if self._camera_preview is not None:
            self._camera_preview.close_permanently()
        settings = self._user_settings_service.current.live_vision if self._user_settings_service else None
        preview = CameraPreviewWindow(
            device_name,
            session_id,
            mirror_enabled=settings.mirror_camera_preview if settings else True,
            automatic_commentary_enabled=settings.automatic_camera_commentary_enabled if settings else True,
            commentary_muted=not settings.speak_semantic_changes if settings else False,
        )
        preview.analyze_requested.connect(self._live_analyze_now)
        preview.pause_requested.connect(self._toggle_live_pause)
        preview.stop_requested.connect(self._stop_live_vision)
        preview.automatic_commentary_toggled.connect(self._set_camera_auto_commentary)
        preview.mute_toggled.connect(self._set_camera_commentary_muted)
        preview.hidden.connect(lambda: self._live_show_preview.setEnabled(True))
        self._camera_preview = preview
        self._live_show_preview.setEnabled(False)
        preview.show()

    def _show_existing_camera_preview(self) -> None:
        if self._camera_preview is not None:
            self._camera_preview.show()
            self._camera_preview.raise_()
            self._camera_preview.activateWindow()
            self._live_show_preview.setEnabled(False)

    def _apply_camera_image(self, image: object, session_id: str) -> None:
        if session_id != self._live_session_id or self._camera_preview is None or not isinstance(image, QImage):
            return
        if self._live_vision_controller is not None and self._live_vision_controller.snapshot.state is LiveVisionState.PAUSED:
            return
        self._camera_preview.set_frame(image, session_id)

    def _capture_live_camera_context(self, question: str = "") -> ScreenContext | None:
        """Attach the current in-memory camera frame to an ordinary chat question."""
        controller = self._live_vision_controller
        if controller is None or not hasattr(controller, "capture_current_frame"):
            return None
        settings = self._user_settings_service.current.live_vision if self._user_settings_service else None
        if settings is not None and not settings.realtime_camera_conversation_enabled:
            return None
        snapshot = controller.snapshot
        if snapshot.source is not LiveVisionSource.CAMERA or snapshot.state in {
            LiveVisionState.IDLE,
            LiveVisionState.PAUSED,
            LiveVisionState.STOPPING,
            LiveVisionState.UNAVAILABLE,
        }:
            return None
        frame = controller.capture_current_frame(question)
        if frame is None:
            return None
        return ScreenContext(
            image_bytes=frame.data,
            width=frame.width,
            height=frame.height,
            captured_at=frame.captured_at,
            display_name=frame.source_label or snapshot.source_label or "Kamera",
            estimated_byte_size=len(frame.data),
            source=LIVE_CAMERA_CONTEXT,
        )

    def _camera_is_active(self) -> bool:
        if self._live_vision_controller is None:
            return False
        snapshot = self._live_vision_controller.snapshot
        return snapshot.source is LiveVisionSource.CAMERA and snapshot.state not in {
            LiveVisionState.IDLE,
            LiveVisionState.STOPPING,
            LiveVisionState.UNAVAILABLE,
        }

    def _set_camera_auto_commentary(self, enabled: bool) -> None:
        if self._live_vision_controller is not None:
            self._live_vision_controller.set_automatic_commentary(enabled)
        if self._camera_preview is not None and not enabled:
            self._camera_preview.apply_conversation_state(CameraConversationState.PAUSED)

    def _set_camera_commentary_muted(self, muted: bool) -> None:
        if self._live_vision_controller is not None:
            self._live_vision_controller.set_commentary_muted(muted)

    def _apply_live_preview_event(self, event: object) -> None:
        if not isinstance(event, PreviewFrameEvent) or event.session_id != self._live_session_id:
            return
        if self._camera_preview is not None and event.frame.source is LiveVisionSource.CAMERA:
            image = QImage.fromData(event.frame.data)
            if not image.isNull():
                self._camera_preview.set_frame(image, event.session_id)

    def _apply_live_change_regions(self, event: object) -> None:
        if not isinstance(event, ChangeRegionsEvent) or event.session_id != self._live_session_id:
            return
        if self._camera_preview is not None:
            self._camera_preview.set_change_regions(event.regions, event.session_id)

    def _handle_camera_preview_error(self, message: str, session_id: str) -> None:
        if session_id != self._live_session_id:
            return
        self._set_status(message)
        if self._live_vision_controller is not None:
            self._live_vision_controller.stop()

    def _publish_overlay_geometry(self, geometry: QRect, screen_name: str) -> None:
        controller = self._live_vision_controller
        if controller is None or not hasattr(controller, "update_overlay_geometry"):
            return
        controller.update_overlay_geometry(
            OverlayGeometry(geometry.x(), geometry.y(), geometry.width(), geometry.height(), screen_name)
        )

    def _handle_live_session_stopped(self, event: object) -> None:
        if isinstance(event, SessionStoppedEvent) and event.session_id == self._live_session_id:
            self._cleanup_live_visuals()

    def _cleanup_live_visuals(self) -> None:
        backend = self._camera_backend
        self._camera_backend = None
        if backend is not None:
            backend.clear_listeners()
        preview = self._camera_preview
        self._camera_preview = None
        if preview is not None:
            preview.close_permanently()
        overlay = self._monitoring_overlay
        self._monitoring_overlay = None
        if overlay is not None:
            overlay.close_permanently()
        self._live_capture_invoker = None
        self._live_session_id = None
        if hasattr(self, "_live_show_preview"):
            self._live_show_preview.setEnabled(False)

    def _live_analyze_now(self) -> None:
        if self._live_vision_controller is not None:
            self._start_worker(FunctionWorker(self._live_vision_controller.analyze_now))

    def _toggle_live_pause(self) -> None:
        if self._live_vision_controller is None:
            return
        if self._live_vision_controller.snapshot.state is LiveVisionState.PAUSED:
            self._live_vision_controller.resume()
        else:
            self._live_vision_controller.pause()

    def _stop_live_vision(self) -> None:
        if self._live_vision_controller is not None:
            self._live_vision_controller.stop()

    def _apply_live_vision_snapshot(self, snapshot: object) -> None:
        if not isinstance(snapshot, LiveVisionSnapshot):
            return
        active = snapshot.state not in {LiveVisionState.IDLE, LiveVisionState.DISABLED, LiveVisionState.UNAVAILABLE}
        label = self._live_source_label(snapshot.source)
        state_labels = {
            LiveVisionState.STARTING: "Başlatılıyor", LiveVisionState.MONITORING: "Takip ediliyor",
            LiveVisionState.CHANGE_DETECTED: "Değişiklik algılandı", LiveVisionState.ANALYZING: "Analiz ediliyor",
            LiveVisionState.PAUSED: "Duraklatıldı", LiveVisionState.ERROR: "Hata",
            LiveVisionState.UNAVAILABLE: "Kullanılamıyor", LiveVisionState.IDLE: "Kapalı",
            LiveVisionState.STOPPING: "Durduruluyor", LiveVisionState.SPEAKING: "Seslendiriliyor",
            LiveVisionState.DISABLED: "Kapalı",
        }
        self._live_indicator.setText(f"◉ {label} · {state_labels.get(snapshot.state, snapshot.state.value)}" if active else "◉ Live Vision · Kapalı")
        self._live_result.setText(snapshot.last_result or snapshot.user_message or "Kamera veya ekran takibi etkin değil.")
        self._live_analyze.setEnabled(active and snapshot.state is not LiveVisionState.ANALYZING)
        self._live_pause.setEnabled(active and snapshot.state is not LiveVisionState.ANALYZING)
        self._live_pause.setText("Devam Et" if snapshot.state is LiveVisionState.PAUSED else "Duraklat")
        self._live_stop.setEnabled(active)
        if self._camera_preview is not None and snapshot.session_id == self._live_session_id:
            self._camera_preview.apply_state(snapshot.state)
            if (
                snapshot.source is LiveVisionSource.CAMERA
                and self._live_vision_controller is not None
                and hasattr(self._live_vision_controller, "camera_context")
            ):
                self._camera_preview.apply_conversation_state(self._live_vision_controller.camera_context.state)
            self._live_show_preview.setEnabled(not self._camera_preview.isVisible())
        if self._monitoring_overlay is not None and snapshot.session_id == self._live_session_id:
            self._monitoring_overlay.set_paused(snapshot.state is LiveVisionState.PAUSED)
        self._update_live_tray_actions(snapshot.state, label)
        if snapshot.state in {LiveVisionState.IDLE, LiveVisionState.DISABLED, LiveVisionState.UNAVAILABLE, LiveVisionState.ERROR}:
            self._cleanup_live_visuals()

    @staticmethod
    def _live_source_label(source: LiveVisionSource | None) -> str:
        return {LiveVisionSource.CAMERA: "Kamera", LiveVisionSource.SCREEN: "Ekran", LiveVisionSource.REGION: "Bölge"}.get(source, "Live Vision")

    def _update_live_tray_actions(self, state: LiveVisionState, label: str = "Live Vision") -> None:
        if not hasattr(self, "_tray_live_status_action"):
            return
        active = state not in {LiveVisionState.IDLE, LiveVisionState.DISABLED, LiveVisionState.UNAVAILABLE}
        self._tray_live_status_action.setText(f"Live Vision Durumu: {label if active else 'Kapalı'}")
        self._tray_live_analyze_action.setEnabled(active)
        self._tray_live_pause_action.setEnabled(active)
        self._tray_live_pause_action.setText("Takibe Devam Et" if state is LiveVisionState.PAUSED else "Takibi Duraklat")
        self._tray_live_stop_action.setEnabled(active)
        if self._tray_icon is not None:
            self._tray_icon.setToolTip(f"Lina — {label} takibi aktif" if active else "Lina")

    def _confirm_tray_live_start(self, source: LiveVisionSource) -> None:
        message = "Lina kamera görüntüsünü yalnız yerel analiz için kullanır. Görüntüler kalıcı olarak saklanmaz veya cloud'a gönderilmez." if source is LiveVisionSource.CAMERA else "Lina ekran görüntüsünü yalnız yerel analiz için kullanır. Görüntüler kalıcı olarak saklanmaz."
        if QMessageBox.question(self, "Live Vision Gizlilik Onayı", message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        intent = RoutingIntentType.CAMERA_MONITOR if source is LiveVisionSource.CAMERA else RoutingIntentType.SCREEN_MONITOR
        self._execute_live_intent(IntentRequest(intent, 1.0, message, {"user_focus": ""}, True))

    def _run_vision_intent(self, intent: RoutingIntentType) -> str:
        if not self._vision_enabled:
            return "Vision özelliği Ayarlar’dan kapalı."
        if self._vision_status is not None and self._vision_status.status is not VisionStatus.READY:
            if self._vision_status.status is VisionStatus.DISABLED:
                return "Vision şu anda kapalı. Ayarlar’dan açabilirsin."
            if self._vision_status.status in {VisionStatus.MODEL_NOT_AVAILABLE, VisionStatus.VISION_NOT_SUPPORTED, VisionStatus.INVALID_RESPONSE}:
                if self._vision_status.status is VisionStatus.VISION_NOT_SUPPORTED:
                    return "Seçili model görüntü analizi desteklemiyor. Ayarlardan bir vision modeli seç."
                return "Seçili Vision modeli görsel analiz için uygun değil."
            if self._vision_status.status in {VisionStatus.OLLAMA_UNREACHABLE, VisionStatus.TIMEOUT}:
                return "Ollama’ya ulaşılamadığı için görsel analiz yapılamıyor."
        if intent is RoutingIntentType.ANALYZE_SCREEN:
            self.handle_screen_request()
            return "Ekran görüntüsü analize hazır. Ekranda neye bakmamı istersin?"
        if intent is RoutingIntentType.ANALYZE_REGION:
            self.handle_region_capture()
            return "Analiz etmek istediğin ekran bölgesini seç."
        if self._screen_context is None:
            self.handle_image_upload()
        return "Görsel analize hazır." if self._screen_context is not None else "Analiz için bir görsel seçmelisin."

    def _finish_routed_intent(self, user_text: str, assistant_text: str, created_at: datetime) -> None:
        self._append_assistant_message(assistant_text)
        self.speak_assistant_response(assistant_text)
        if self._hands_free_service is not None:
            self._hands_free_service.mark_response_completed()
        if self._conversation_history_service is not None:
            self._conversation_history_service.record_user_message(user_text, created_at=created_at)
            self._conversation_history_service.record_assistant_message(assistant_text)
        self._refresh_conversation_sidebar()
        self._set_status("Hazır")
        self._composer.input.setFocus()

    def cancel_active_response(self) -> None:
        """Stop rendering the active response and keep the composer usable."""
        self.stop_voice()
        if (
            self._voice_controller is not None
            and self._voice_controller.state is VoiceState.THINKING
        ):
            self._voice_controller.finish_interaction()
        if self._model_lifecycle_service is not None:
            self._model_lifecycle_service.cancel_active()
        elif self._inference_diagnostics_service is not None:
            self._inference_diagnostics_service.cancel()
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
        if self._is_waiting:
            self.cancel_active_response()
        else:
            self.stop_voice()
        if self._is_speech_busy and self._speech_service is not None:
            self._speech_service.stop_listening()
        self._cancel_hands_free_command()
        if self._conversation_history_service is not None:
            self._conversation_service.clear_session()
        self._clear_visible_messages()
        self._clear_screen_context()
        if self._intent_router is not None:
            self._intent_router.cancel_pending()
        self._active_confirmation_cancel = None
        self._active_confirmation_confirm = None
        self._active_confirmation_card = None
        self._set_session_title("Yeni Sohbet")
        self._update_session_date()
        self._refresh_conversation_sidebar()
        self._show_welcome_state()
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
        self._cancel_hands_free_command()
        if self._intent_router is not None:
            self._intent_router.cancel_pending()
        self._active_confirmation_cancel = None
        self._active_confirmation_confirm = None
        self._active_confirmation_card = None
        self._routing_session_key -= 1
        self._conversation_view = "chats"
        self._conversation_query = ""
        self._sidebar.reset_view_controls()
        self._clear_visible_messages()
        self._clear_screen_context()
        self._set_session_title("Yeni Sohbet")
        self._update_session_date()
        self._refresh_conversation_sidebar()
        self._show_welcome_state()
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
            self._cancel_hands_free_command()
            if self._intent_router is not None:
                self._intent_router.cancel_pending()
            self._active_confirmation_cancel = None
            self._active_confirmation_confirm = None
            self._active_confirmation_card = None
            self._routing_session_key = conversation_id
            self._conversation_view = "chats"
            self._conversation_query = ""
            self._sidebar.reset_view_controls()
            self._conversation_service.load_session(conversation_id)
            session = self._conversation_history_service.active_session
            self._clear_visible_messages()
            self._clear_screen_context()
            if session is not None:
                self._set_session_title(session.title)
            self._update_session_date()
            for message in self._conversation_history_service.loaded_messages():
                text = message.content
                if message.had_image:
                    text = f"▣ {_visual_placeholder(message.image_source)}\n{text}"
                self._append_message(
                    message.role,
                    text,
                    visual_context=None,
                    created_at=message.created_at,
                )
            if not self._message_rows:
                self._show_welcome_state()
            self._refresh_conversation_sidebar()
            self._set_status("Sohbet yüklendi")
            self._schedule_scroll_to_bottom()
        except Exception:
            self._set_status("Sohbet geçmişi yüklenemedi.")

    def _cancel_hands_free_command(self) -> None:
        if self._hands_free_service is not None:
            self._hands_free_service.cancel_active()
        if self._voice_controller is not None and getattr(self._voice_controller, "hands_free_enabled", False):
            self._voice_controller.finish_interaction()

    def rename_conversation(self, conversation_id: int) -> None:
        """Rename a conversation through a bounded local dialog."""
        if self._conversation_history_service is None or self._is_waiting:
            return
        sessions = self._conversation_history_service.list_sessions(view="chats")
        sessions += self._conversation_history_service.list_sessions(view="archive")
        session = next((item for item in sessions if item.id == conversation_id), None)
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
        sessions = self._conversation_history_service.list_sessions(view="chats")
        sessions += self._conversation_history_service.list_sessions(view="archive")
        session = next((item for item in sessions if item.id == conversation_id), None)
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
            if self._intent_router is not None:
                self._intent_router.cancel_pending()
            self._active_confirmation_cancel = None
            self._active_confirmation_confirm = None
            self._active_confirmation_card = None
            active_session = self._conversation_history_service.active_session
            if active_session is not None and active_session.id is not None:
                self.load_conversation(active_session.id)
            else:
                self.start_new_chat()
        self._refresh_conversation_sidebar()

    def set_conversation_pinned(self, conversation_id: int, pinned: bool) -> None:
        if self._conversation_history_service is None or self._is_waiting:
            return
        if self._conversation_history_service.set_pinned(conversation_id, pinned) is None:
            self._set_status("Sohbet yönetimi şu anda kullanılamıyor.")
            return
        self._refresh_conversation_sidebar()
        self._set_status("Sohbet sabitlendi" if pinned else "Sohbet sabitlemesi kaldırıldı")

    def set_conversation_archived(self, conversation_id: int, archived: bool) -> None:
        if self._conversation_history_service is None or self._is_waiting:
            return
        was_active = self._conversation_history_service.set_archived(
            conversation_id, archived
        )
        if not self._conversation_history_service.persistence_available:
            self._set_status("Sohbet yönetimi şu anda kullanılamıyor.")
            return
        if was_active:
            if self._intent_router is not None:
                self._intent_router.cancel_pending()
            self._active_confirmation_cancel = None
            self._active_confirmation_confirm = None
            self._active_confirmation_card = None
            active_session = self._conversation_history_service.active_session
            if active_session is not None and active_session.id is not None:
                self.load_conversation(active_session.id)
            else:
                self._clear_visible_messages()
                self._clear_screen_context()
                self._set_session_title("Yeni Sohbet")
                self._update_session_date()
                self._show_welcome_state()
        self._refresh_conversation_sidebar()
        self._set_status(
            "Sohbet arşivlendi" if archived else "Sohbet arşivden çıkarıldı"
        )

    def _handle_conversation_search(self, query: str) -> None:
        self._conversation_query = query.strip()
        self._refresh_conversation_sidebar()

    def _handle_conversation_view_changed(self, view: str) -> None:
        self._conversation_view = view
        self._refresh_conversation_sidebar()

    def _clear_visible_messages(self) -> None:
        self._hide_welcome_state()
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
            self._show_welcome_state()
            return
        session = self._conversation_history_service.active_session
        if session is None:
            self._show_welcome_state()
            return
        self._set_session_title(session.title)
        self._update_session_date()
        messages = self._conversation_history_service.loaded_messages()
        if not messages:
            self._show_welcome_state()
        else:
            for message in messages:
                text = message.content
                if message.had_image:
                    text = f"▣ {_visual_placeholder(message.image_source)}\n{text}"
                self._append_message(message.role, text, created_at=message.created_at)
        self._refresh_conversation_sidebar()

    def _show_welcome_state(self) -> None:
        self._hide_welcome_state()
        conversation_id = (
            self._conversation_history_service.active_session.id
            if self._conversation_history_service is not None
            and self._conversation_history_service.active_session is not None
            else None
        )
        self._welcome_state = WelcomeStateWidget(
            BRANDING_LOGO_PATH,
            conversation_id=conversation_id,
            parent=self._message_container,
        )
        self._message_layout.insertWidget(0, self._welcome_state)

    def _hide_welcome_state(self) -> None:
        if self._welcome_state is None:
            return
        self._welcome_state.setParent(None)
        self._welcome_state.deleteLater()
        self._welcome_state = None

    def _refresh_conversation_sidebar(self) -> None:
        if self._conversation_history_service is None:
            self._sidebar.set_persistence_note("Kalıcı sohbet geçmişi kapalı.")
            return
        if len(self._conversation_query) >= 2:
            self._sidebar.set_search_results(
                self._conversation_history_service.search(
                    self._conversation_query,
                    view=self._conversation_view,
                )
            )
            return
        sessions = self._conversation_history_service.list_sessions(
            view=self._conversation_view
        )
        active_id = (
            self._conversation_history_service.active_session.id
            if self._conversation_history_service.active_session is not None
            else None
        )
        groups = self._conversation_history_service.group_sessions(sessions)
        if self._conversation_view == "chats":
            pinned = tuple(session for session in sessions if session.is_pinned)
            unpinned = tuple(session for session in sessions if not session.is_pinned)
            groups = (("Sabitlenenler", pinned),) + self._conversation_history_service.group_sessions(unpinned)
        self._sidebar.set_sessions(sessions, active_id=active_id, groups=groups)
        self._update_session_date()

    def _update_session_date(self) -> None:
        if self._conversation_history_service is None:
            self._session_date_label.clear()
            return
        session = self._conversation_history_service.active_session
        if session is None:
            self._session_date_label.clear()
            return
        self._session_date_label.setText(
            format_conversation_datetime(session.last_message_at or session.created_at)
        )

    def handle_screen_request(self) -> None:
        """Capture and preview one screen after an explicit user action."""
        if not self._vision_enabled:
            return
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
            self._set_vision_controls_enabled(self._vision_enabled)

    def handle_image_upload(self) -> None:
        """Load one image explicitly selected by the user into temporary context."""
        if not self._vision_enabled:
            return
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
        if not self._vision_enabled:
            return
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
        if self._pending_region_monitor_focus is not None:
            focus = self._pending_region_monitor_focus
            self._pending_region_monitor_focus = None
            try:
                self._start_region_monitor(screen, QRect(rectangle), focus)
                self._set_status("Bölge takibi aktif")
            except LiveVisionError as error:
                self._set_status(str(error))
            finally:
                self._is_screen_capture_busy = False
                self._set_vision_controls_enabled(self._vision_enabled)
            return
        try:
            global_rectangle = QRect(rectangle).translated(screen.geometry().topLeft())
            context = self._screen_capture_service.capture_region(global_rectangle, screen)
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
            self._set_vision_controls_enabled(self._vision_enabled)

    def _cancel_region_capture(self) -> None:
        overlay = self._region_overlay
        self._region_overlay = None
        self._pending_region_monitor_focus = None
        if overlay is not None:
            overlay.close()
            overlay.deleteLater()
        self._is_screen_capture_busy = False
        self._set_vision_controls_enabled(self._vision_enabled)
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
        if (
            self._voice_controller is not None
            and self._voice_controller.state is VoiceState.SPEAKING
            and not self._voice_controller.begin_listening()
        ):
            return
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
        if self._voice_controller is not None:
            self._voice_controller.begin_listening()
        self._composer.set_mic_state("listening")
        self._composer.mic_button.setEnabled(True)
        self._set_status("Dinliyorum...")
        worker = FunctionWorker(self._speech_service.transcribe_once)
        worker.signals.result.connect(self._handle_transcription_result)
        worker.signals.error.connect(self._handle_transcription_error)
        worker.signals.finished.connect(self._reset_speech_ui)
        self._start_worker(worker)

    def _submit_hands_free_command(self, text: str) -> None:
        if self._is_waiting:
            self._handle_hands_free_feedback("Beklemeye alındı.")
            if self._voice_controller is not None:
                self._voice_controller.finish_interaction()
            return
        self._composer.input.setPlainText(text)
        self.send_message()

    def _handle_hands_free_feedback(self, message: str) -> None:
        self._set_status(message)
        if message not in {"Dinliyorum.", "Beklemeye alındı."}:
            self._append_assistant_message(message)

    def _expire_voice_confirmation(self, card: ToolActivityCard, cancel: Callable[[], None]) -> None:
        if self._active_confirmation_card is card:
            cancel()

    def _run_conversation_request(
        self,
        request_id: int,
        message: str,
        screen_context: ScreenContext | None,
        created_at: datetime,
    ) -> tuple[int, str, object]:
        try:
            if screen_context is None:
                response: object = self._conversation_service.handle_input(
                    ConversationInput(text=message, created_at=created_at)
                )
            else:
                response = self._conversation_service.handle_input(
                    ConversationInput(
                        text=message,
                        created_at=created_at,
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
            assistant_created_at = result.assistant_created_at
        else:
            response = result
            consumed = False
            assistant_created_at = None
        text = response.text if isinstance(response, ModelResponse) else str(response)
        self._auto_scroll_enabled = True
        self._append_assistant_message(text, created_at=assistant_created_at)
        if request_screen_context is not None and request_screen_context.source == LIVE_CAMERA_CONTEXT:
            live_speaker = getattr(self._voice_controller, "speak_live_vision", None)
            if callable(live_speaker):
                live_speaker(text)
            else:
                self.speak_assistant_response(text)
        else:
            self.speak_assistant_response(text)
        if self._hands_free_service is not None:
            self._hands_free_service.mark_response_completed()
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
            if self._transcription_mode == "send":
                if self._voice_controller is not None:
                    self._voice_controller.begin_thinking()
                self._reset_speech_ui()
                self.send_message()
                return
            self._append_assistant_message(
                "Konuşmanı yazıya çevirdim İlhan. Kontrol edip gönderebilirsin."
            )
            self._set_status("Metne çevrildi.")
            return
        self._append_assistant_message(
            "Transkripsiyonu mesaj alanına yazamadım İlhan. Tekrar deneyebiliriz."
        )
        self._set_status("Hata oluştu.")

    def stop_voice(self) -> None:
        """Stop local speech playback without removing written content."""
        if self._voice_controller is not None and self._voice_controller.stop():
            self._set_status("Ses durduruldu.")

    def speak_assistant_response(self, text: str) -> bool:
        """Speak one finalized assistant response through the single safe runtime path."""
        if self._voice_controller is None:
            return False
        return self._voice_controller.speak(text)

    def _apply_voice_state(self, state: object) -> None:
        labels = {
            VoiceState.IDLE: "Ses · hazır",
            VoiceState.LISTENING: "Dinliyor",
            VoiceState.WAKE_LISTENING: "🎙 Hey Lina bekleniyor",
            VoiceState.WAKE_DETECTED: "🎙 Dinliyorum",
            VoiceState.COMMAND_LISTENING: "🎙 Dinliyorum",
            VoiceState.TRANSCRIBING: "Yazıya çeviriyor",
            VoiceState.THINKING: "Düşünüyor",
            VoiceState.SPEAKING: "Konuşuyor · Sesi Durdur",
            VoiceState.INTERRUPTED: "Durduruldu",
            VoiceState.COOLDOWN: "Beklemeye alındı",
            VoiceState.ERROR: "Ses kullanılamıyor",
            VoiceState.DISABLED: "Ses · kapalı",
        }
        label = labels.get(state, "Ses · hazır")
        if state is VoiceState.WAKE_LISTENING and not getattr(self, "_wake_indicator_enabled", True):
            label = "🎙 Mikrofon aktif"
        self._voice_status.setText(label)
        if (
            self._camera_preview is not None
            and self._live_vision_controller is not None
            and self._live_vision_controller.snapshot.source is LiveVisionSource.CAMERA
        ):
            if state in {VoiceState.LISTENING, VoiceState.COMMAND_LISTENING, VoiceState.TRANSCRIBING}:
                self._camera_preview.apply_conversation_state(CameraConversationState.LISTENING)
            elif state is VoiceState.SPEAKING:
                self._camera_preview.apply_conversation_state(CameraConversationState.SPEAKING)
            elif self._live_vision_controller.snapshot.state is LiveVisionState.MONITORING:
                self._camera_preview.apply_conversation_state(CameraConversationState.OBSERVING)
        if hasattr(self, "_hands_free_pause") and self._voice_controller is not None:
            self._hands_free_pause.setText("Dinlemeye Devam Et" if self._voice_controller.hands_free_paused else "Dinlemeyi Duraklat")
        if self._tray_icon is not None:
            self._tray_icon.setToolTip(f"Lina · {labels.get(state, 'Hazır')}")

    def _apply_speech_state(self, state: object) -> None:
        if self._voice_controller is None:
            return
        if (
            state is SpeechState.LISTENING
            and self._voice_controller.state not in {VoiceState.LISTENING, VoiceState.COMMAND_LISTENING}
        ):
            self._voice_controller.begin_listening()
        elif (
            state is SpeechState.TRANSCRIBING
            and self._voice_controller.state in {VoiceState.LISTENING, VoiceState.COMMAND_LISTENING}
        ):
            self._voice_controller.begin_transcribing()
        elif state is SpeechState.IDLE and self._voice_controller.state in {
            VoiceState.LISTENING,
            VoiceState.COMMAND_LISTENING,
            VoiceState.TRANSCRIBING,
        }:
            self._voice_controller.finish_interaction()

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
        if (
            self._voice_controller is not None
            and self._transcription_mode != "send"
            and self._voice_controller.state
            in {VoiceState.LISTENING, VoiceState.TRANSCRIBING, VoiceState.ERROR}
        ):
            self._voice_controller.finish_interaction()
        self._composer.set_mic_state("idle")
        self._composer.mic_button.setEnabled(
            self._speech_enabled
            and self._speech_service is not None
            and self._speech_service.is_stt_available()
        )
        self._refresh_speech_status()

    def _append_user_message(
        self,
        text: str,
        image_bytes: bytes | None = None,
        visual_context: ScreenContext | None = None,
        created_at: datetime | None = None,
    ) -> ChatMessageWidget:
        return self._append_message(
            "user",
            text,
            image_bytes=image_bytes,
            visual_context=visual_context,
            created_at=created_at,
        )

    def _append_assistant_message(
        self,
        text: str,
        created_at: datetime | None = None,
    ) -> ChatMessageWidget:
        normalized = normalize_assistant_text(text)
        self._last_response_text = normalized
        return self._append_message("assistant", normalized, created_at=created_at)

    def _append_message(
        self,
        role: str,
        text: str,
        typing: bool = False,
        image_bytes: bytes | None = None,
        visual_context: ScreenContext | None = None,
        created_at: datetime | None = None,
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
            created_at=created_at,
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
        if self._speech_enabled and self._speech_service.is_stt_available():
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
        if not self._force_exit and self._user_settings_service is not None:
            behavior = self._user_settings_service.current.system.close_behavior
            if behavior == "tray" and self._tray_icon is not None:
                self.hide()
                event.ignore()
                return
            if behavior == "ask":
                result = QMessageBox.question(
                    self,
                    "Lina",
                    "Lina kapatılsın mı, sistem tepsisinde çalışmaya devam mı etsin?",
                    QMessageBox.StandardButton.Cancel
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Yes,
                    QMessageBox.StandardButton.Cancel,
                )
                if result == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
                if result == QMessageBox.StandardButton.No and self._tray_icon is not None:
                    self.hide()
                    event.ignore()
                    return
        self._clear_screen_context()
        if self._live_vision_controller is not None:
            self._live_vision_controller.shutdown()
        if self._agent_controller is not None:
            self._agent_controller.shutdown()
        self._cleanup_live_visuals()
        if self._intent_router is not None:
            self._intent_router.cancel_pending()
        self._active_confirmation_cancel = None
        self._active_confirmation_confirm = None
        self._active_confirmation_card = None
        if self._hands_free_service is not None:
            self._hands_free_service.shutdown()
        if self._speech_service is not None:
            if hasattr(self._speech_service, "shutdown"):
                self._speech_service.shutdown()
            else:
                self._speech_service.stop_listening()
        if self._voice_controller is not None:
            self._voice_controller.shutdown()
        if self._inference_diagnostics_service is not None:
            self._inference_diagnostics_service.cancel()
        if self._model_lifecycle_service is not None:
            self._model_lifecycle_service.shutdown()
        if self._notification_scheduler is not None:
            self._notification_scheduler.stop()
        if self._tray_icon is not None:
            self._tray_icon.hide()
        self._pending_scroll_to_bottom = False
        self._pending_scroll_to_top = False
        event.accept()


def _classify_voice_confirmation(text: str) -> str | None:
    normalized = " ".join(text.casefold().split()).strip(" .!?,;:")
    if normalized in {"evet", "onayla", "tamam", "oluştur", "kaydet"}:
        return "yes"
    if normalized in {"hayır", "iptal", "vazgeç", "boşver", "gerek yok"}:
        return "no"
    return None


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
    if isinstance(error, EmptyModelResponseError):
        return "Görüntüyü şu anda yorumlayamadım. Birkaç saniye sonra tekrar deneyelim."
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
