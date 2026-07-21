"""PySide6 desktop window for Lina."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
from typing import Any

from PySide6.QtCore import QRect, QTimer, QThreadPool, Qt, Signal, QUrl
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QCursor,
    QDesktopServices,
    QFont,
    QGuiApplication,
    QIcon,
    QImage,
    QKeySequence,
)
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
from lina.files import AttachmentService, DocumentAttachment
from lina.files.models import (DocumentExtractionError, FileTooLargeError,
                               ForbiddenFilePathError, UnsupportedFileTypeError)
from lina.agent import (
    AgentContext,
    AgentController,
    AgentPlanEditor,
    AgentMessageKind,
    AgentResponseQuality,
    AgentSessionStatus,
    AgentTaskCenter,
    ApprovalDecision,
    parse_approval,
    render_plan_diff,
)
from lina.agent.errors import AgentError
from lina.codex import (CodexBridge, CodexClientUnavailableError, CodexTransportError, WorkspaceAccessError,
                         validate_codex_request_scope)
from lina.codex.intent import classify_codex_intent
from lina.codex.voice import confirmation_prompt, route_codex_control
from lina.codex.changes import CodexReviewDecision
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
from lina.interfaces.qt.codex_panel import CodexInspector
from lina.interfaces.qt.codex_diff_review import CodexDiffReviewDialog
from lina.interfaces.qt.status_labels import codex_status_label
from lina.interfaces.qt.agent_task_center import (
    AgentInspectorV2,
    AgentStepArgumentsDialog,
    AgentTaskCenterDialog,
    PlanReviewWidget,
    TaskTemplateBrowserDialog,
    TaskTemplateParameterDialog,
)
from lina.interfaces.qt.worker import FunctionWorker
from lina.interfaces.qt.context_inspector import DrawerScrim
from lina.interfaces.qt.view_state import ApplicationViewState, ResponsiveMode, RightPanelSection
from lina.interfaces.qt.workspace import CommandPalette, DetailsInspector, PaletteAction
from lina.ui.design import design_tokens, standard_icon
from lina.interfaces.status import StatusPriority, UnifiedStatusController
from lina.services.conversation_service import ConversationService
from lina.services.local_storage_service import LocalStorageService, LocalStorageSnapshot
from lina.memory.service import MemoryService
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


APP_VERSION = "v0.13.2-alpha"
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


def clamp_window_geometry(saved: QRect, available: tuple[QRect, ...]) -> QRect:
    """Clamp a saved window to a visible screen without assuming positive coordinates."""
    if not available:
        return saved
    target = next((screen for screen in available if screen.intersects(saved)), available[0])
    width = min(max(720, saved.width()), target.width())
    height = min(max(560, saved.height()), target.height())
    x = max(target.left(), min(saved.x(), target.right() - width + 1))
    y = max(target.top(), min(saved.y(), target.bottom() - height + 1))
    return QRect(x, y, width, height)


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
    codex_event_received = Signal(object, str)

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
        attachment_service: AttachmentService | None = None,
        voice_controller: VoiceController | None = None,
        inference_diagnostics_service: InferenceDiagnosticsService | None = None,
        model_lifecycle_service: ModelLifecycleService | None = None,
        hands_free_service: HandsFreeConversationService | None = None,
        live_vision_controller: LiveVisionController | None = None,
        agent_controller: AgentController | None = None,
        memory_service: MemoryService | None = None,
        local_storage_service: LocalStorageService | None = None,
        screen_preview_factory: Callable[[ScreenContext, QWidget | None], QDialog]
        | None = None,
        thread_pool: QThreadPool | None = None,
        parent: QWidget | None = None,
        codex_bridge: CodexBridge | None = None,
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
        self._codex_bridge = codex_bridge
        self._codex_refresh_pending = False
        self.codex_event_received.connect(self._handle_codex_event_ui)
        if self._codex_bridge is not None:
            self._codex_bridge.subscribe(
                lambda event, message: self.codex_event_received.emit(event, message)
            )
        self._pending_codex_request: str | None = None
        self._memory_service = memory_service
        self._local_storage_service = local_storage_service
        self._agent_enabled = bool(
            user_settings_service and user_settings_service.current.agent.agent_mode_enabled
        )
        self._agent_notified_sessions: set[str] = set()
        self._agent_notification_events: set[str] = set()
        self._agent_response_quality = AgentResponseQuality()
        self._agent_task_center_dialog: AgentTaskCenterDialog | None = None
        self._task_template_dialog: TaskTemplateBrowserDialog | None = None
        self._plan_review_dialog: QDialog | None = None
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
        self._window_state_restored = False
        self._screen_capture_service = screen_capture_service or QtScreenCaptureService()
        self._image_loader = image_loader or QtImageLoader()
        self._attachment_service = attachment_service or AttachmentService()
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
        self._unified_status = UnifiedStatusController()
        self._cancelled_request_ids: set[int] = set()
        self._is_speech_busy = False
        self._is_screen_capture_busy = False
        self._region_overlay: RegionCaptureOverlay | None = None
        self._screen_context: ScreenContext | None = None
        self._document_attachment: DocumentAttachment | None = None
        self._vision_status: VisionDiagnosticsResult | None = None
        self._request_screen_contexts: dict[int, ScreenContext] = {}
        self._request_document_attachments: dict[int, DocumentAttachment] = {}
        self._auto_scroll_enabled = True
        self._pending_scroll_to_bottom = False
        self._pending_scroll_to_top = False
        self._scroll_retry_count = 0
        self._is_programmatic_scroll = False
        self._message_font_size = MESSAGE_FONT_DEFAULT
        self._interface_density = "comfortable"
        self._compact_chrome = False
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
        self._view_state = ApplicationViewState()
        self._responsive_mode = ResponsiveMode.LARGE
        self._right_panel_requested_visible = True
        self._right_panel_width = design_tokens("dark").layout.inspector_width
        self._message_width = design_tokens("dark").layout.chat_readable
        self._storage_snapshot: LocalStorageSnapshot | None = None

        self.setWindowTitle("Lina")
        metrics = design_tokens("dark").layout
        self.setMinimumSize(metrics.minimum_window_width, metrics.minimum_window_height)
        self.resize(1440, 900)
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
        self._setup_agent_recovery_notice()
        self._bind_shortcuts()
        self._restore_initial_conversation()
        self._composer.input.setFocus()
        self._run_initial_diagnostics()
        self._run_initial_vision_diagnostics()
        self._refresh_speech_status()
        self._refresh_local_storage()

    def _build_layout(self) -> None:
        central = QWidget(self)
        central.setObjectName("centralWidget")
        self._central = central
        root_layout = QHBoxLayout(central)
        self._root_layout = root_layout
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
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        root_layout.addWidget(panel, 1)

        self._inspector = DetailsInspector(self._memory_service, model_name, central)
        self._inspector.setFixedWidth(self._right_panel_width)
        self._inspector.closed.connect(self._close_inspector)
        self._inspector.tool_requested.connect(self._handle_context_tool)
        self._inspector.memory_requested.connect(self._show_memory_inspector)
        self._inspector.data_folder_requested.connect(self._open_local_data_folder)
        root_layout.addWidget(self._inspector)

        self._drawer_scrim = DrawerScrim(central)
        self._drawer_scrim.clicked.connect(self._close_inspector)
        self._drawer_scrim.hide()

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
        self._sidebar.settings_requested.connect(self.open_settings)
        self._sidebar.notifications_requested.connect(self.open_notifications)
        self._sidebar.agent_tasks_requested.connect(self._show_agent_task_center)
        self._sidebar.local_status_requested.connect(self._show_system_inspector)

    def _build_header(self, parent_layout: QVBoxLayout) -> None:
        header = QWidget(self)
        header.setObjectName("header")
        header.setMinimumHeight(design_tokens("dark").layout.header_height)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 10, 24, 10)
        layout.setSpacing(10)

        titles = QVBoxLayout()
        self._session_title = QLabel(self._session_title_text, header)
        self._session_title.setObjectName("conversationTitle")
        titles.addWidget(self._session_title)
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_dot = QLabel("●", header)
        status_dot.setObjectName("readyStatusDot")
        status_dot.setAccessibleName("Hazır")
        status_row.addWidget(status_dot)
        self._header_status_label = QLabel("Hazır", header)
        self._header_status_label.setObjectName("conversationSubtitle")
        status_row.addWidget(self._header_status_label)
        status_row.addStretch(1)
        titles.addLayout(status_row)
        self._session_date_label = QLabel("", header)
        self._session_date_label.setObjectName("sessionDateLabel")
        self._session_date_label.hide()
        layout.addLayout(titles, 1)

        self._status_button = QPushButton("", header)
        self._status_button.setObjectName("unifiedStatusButton")
        self._status_button.setIcon(standard_icon(self, "status"))
        self._status_button.setAccessibleName("Lina Durumu ve sistem ayrıntıları")
        self._status_button.setToolTip("Model, mikrofon, ses, Agent ve Vision durumlarını göster")
        self._status_button.clicked.connect(self._show_status_menu)
        layout.addWidget(self._status_button)

        # Diagnostic labels remain as state sinks; details are progressively disclosed.
        self._model_status = QLabel("Model kontrol ediliyor...", header)
        self._model_status.setObjectName("statusChip")
        self._model_status.hide()

        self._speech_status = QLabel("Mic · hazırlanıyor", header)
        self._speech_status.setObjectName("statusChip")
        self._speech_status.hide()
        self._voice_status = QLabel("Ses · kapalı", header)
        self._voice_status.setObjectName("statusChip")
        self._voice_status.hide()
        if self._hands_free_service is not None:
            self._hands_free_toggle = QPushButton("Hands-free Kapalı", header)
            self._hands_free_toggle.setAccessibleName("Hands-free conversation aç veya kapat")
            self._hands_free_toggle.setObjectName("modeChip")
            self._hands_free_toggle.clicked.connect(self._toggle_hands_free_from_tray)
            self._hands_free_toggle.hide()
            layout.addWidget(self._hands_free_toggle)
            self._hands_free_pause = QPushButton("Dinlemeyi Duraklat", header)
            self._hands_free_pause.setAccessibleName("Hands-free dinlemeyi duraklat veya sürdür")
            self._hands_free_pause.clicked.connect(self._toggle_hands_free_pause)
            self._hands_free_pause.setEnabled(False)
            self._hands_free_pause.hide()
        if self._user_settings_service is not None:
            if self._notification_service is not None:
                self._notification_button = QPushButton("Bildirimler", header)
                self._notification_button.setObjectName("notificationButton")
                self._notification_button.setToolTip("Bildirim merkezini aç")
                self._notification_button.setAccessibleName("Bildirimler")
                self._notification_button.setIcon(standard_icon(self, "notifications"))
                self._notification_button.clicked.connect(self.open_notifications)
                self._notification_button.hide()
                layout.addWidget(self._notification_button)
        self._inspector_button = QPushButton("", header)
        self._inspector_button.setObjectName("iconButton")
        self._inspector_button.setToolTip("Bağlamsal araçları aç veya kapat")
        self._inspector_button.setAccessibleName("Bağlamsal araçlar")
        self._inspector_button.setIcon(standard_icon(self, "tools"))
        self._inspector_button.clicked.connect(self._toggle_inspector)
        layout.addWidget(self._inspector_button)
        parent_layout.addWidget(header)

    def _build_chat_area(self, parent_layout: QVBoxLayout) -> None:
        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("chatTimelineScroll")
        self._scroll.viewport().setObjectName("chatTimelineViewport")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._message_container = QWidget(self._scroll)
        self._message_container.setObjectName("chatTimeline")
        self._message_layout = QVBoxLayout(self._message_container)
        self._message_layout.setContentsMargins(20, 22, 20, 20)
        self._message_layout.setSpacing(design_tokens("dark").layout.message_spacing)
        self._message_layout.addStretch(1)
        self._scroll.setWidget(self._message_container)
        self._scroll.verticalScrollBar().valueChanged.connect(self._update_auto_scroll_state)
        self._scroll.verticalScrollBar().rangeChanged.connect(self._handle_scroll_range_changed)
        parent_layout.addWidget(self._scroll, 1)

    def _build_live_vision_panel(self, parent_layout: QVBoxLayout) -> None:
        panel = QWidget(self)
        self._live_panel = panel
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
        self._live_details = QPushButton("Ayrıntılar", panel)
        self._live_analyze.clicked.connect(self._live_analyze_now)
        self._live_pause.clicked.connect(self._toggle_live_pause)
        self._live_stop.clicked.connect(self._stop_live_vision)
        self._live_show_preview.clicked.connect(self._show_existing_camera_preview)
        self._live_details.clicked.connect(self._show_vision_inspector)
        for button in (self._live_analyze, self._live_pause, self._live_stop, self._live_show_preview, self._live_details):
            button.setEnabled(False)
            layout.addWidget(button)
        panel.hide()
        panel.setMaximumWidth(design_tokens("dark").layout.composer_maximum)
        parent_layout.addWidget(panel, 0, Qt.AlignmentFlag.AlignHCenter)

    def _build_agent_panel(self, parent_layout: QVBoxLayout) -> None:
        self._agent_panel = AgentPanel(self)
        self._agent_panel.mode_toggle_requested.connect(self._toggle_agent_mode)
        self._agent_panel.start_requested.connect(self._start_agent_plan)
        self._agent_panel.approve_requested.connect(lambda: self._decide_agent_step(ApprovalDecision.APPROVE))
        self._agent_panel.skip_requested.connect(lambda: self._decide_agent_step(ApprovalDecision.SKIP))
        self._agent_panel.modify_requested.connect(self._show_plan_review)
        self._agent_panel.pause_requested.connect(self._pause_agent)
        self._agent_panel.resume_requested.connect(self._resume_agent)
        self._agent_panel.cancel_requested.connect(self._cancel_agent)
        self._agent_panel.details_requested.connect(self._show_agent_inspector)
        self._agent_panel.render(self._agent_controller.session if self._agent_controller else None, enabled=self._agent_enabled)
        self._agent_panel.setVisible(bool(self._agent_controller and self._agent_controller.session))
        self._agent_panel.setMaximumWidth(design_tokens("dark").layout.composer_maximum)
        parent_layout.addWidget(self._agent_panel, 0, Qt.AlignmentFlag.AlignHCenter)

    def _build_footer(self, parent_layout: QVBoxLayout) -> None:
        self._composer = ComposerWidget(
            font_family=self._font_family,
            font_size=self._message_font_size,
            parent=self,
        )
        composer_row = QWidget(self)
        composer_row.setObjectName("composerRow")
        composer_layout = QHBoxLayout(composer_row)
        composer_layout.setContentsMargins(24, 12, 24, 18)
        composer_layout.addStretch(1)
        self._composer.setMaximumWidth(design_tokens("dark").layout.composer_maximum)
        composer_layout.addWidget(self._composer, 8)
        composer_layout.addStretch(1)
        parent_layout.addWidget(composer_row)

        footer = QWidget(self)
        footer.setObjectName("statusPanel")
        footer.setMaximumHeight(28)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(4, 0, 4, 2)
        layout.setSpacing(0)

        self._status_label = QLabel("Hazır", footer)
        self._status_label.setObjectName("mutedLabel")
        self._status_label.setAccessibleName("Lina Durumu")
        self._status_label.hide()
        layout.addWidget(self._status_label)
        disclaimer = QLabel("Lina hata yapabilir. Önemli bilgileri doğrulayın.", footer)
        disclaimer.setObjectName("composerDisclaimer")
        layout.addWidget(disclaimer, 1)
        model_name = (
            self._diagnostics_service.configured_model
            if self._diagnostics_service is not None
            else "yerel model"
        )
        self._composer_model_label = QLabel(f"Yerel · {model_name}", footer)
        self._composer_model_label.setObjectName("composerModelLabel")
        layout.addWidget(self._composer_model_label)
        parent_layout.addWidget(footer)

        self._composer.send_requested.connect(self.send_message)
        self._composer.stop_requested.connect(self.cancel_active_response)
        self._composer.task_templates_requested.connect(self._show_task_templates)
        self._composer.history_requested.connect(self._navigate_input_history)
        self._composer.attachment_requested.connect(self.handle_image_upload)
        self._screen_menu = self._composer.screen_menu
        self._screen_menu.setAccessibleName("Ekran yakalama seçenekleri")
        full_screen_action = self._screen_menu.addAction("Tüm Ekranı Yakala")
        full_screen_action.setToolTip("Tüm ekranı yakala")
        full_screen_action.triggered.connect(self.handle_screen_request)
        region_action = self._screen_menu.addAction("Alan Seçerek Yakala")
        region_action.setToolTip("Ekranda alan seçerek yakala")
        region_action.triggered.connect(self.handle_region_capture)
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
        self._composer.agent_mode_requested.connect(self._toggle_agent_mode)

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
        clear_action.triggered.connect(self._show_command_palette)
        self.addAction(clear_action)

        palette_action = QAction(self)
        palette_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        palette_action.triggered.connect(self._show_command_palette)
        self.addAction(palette_action)

        settings_action = QAction(self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)

        escape_action = QAction(self)
        escape_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        escape_action.triggered.connect(self._handle_escape)
        self.addAction(escape_action)

    def _handle_escape(self) -> None:
        if self._inspector.isVisible() and self._responsive_mode is not ResponsiveMode.LARGE:
            self._close_inspector()
            return
        if self._sidebar.search_input.text():
            self._sidebar.search_input.clear()
            return
        self._composer.input.setFocus()

    def _palette_actions(self) -> tuple[PaletteAction, ...]:
        return (
            PaletteAction("new_chat", "Yeni sohbet", "sohbet temizle", self.start_new_chat),
            PaletteAction("search", "Sohbetlerde ara", "geçmiş bul", self._sidebar.search_input.setFocus),
            PaletteAction("agent", "Agent görev ayrıntıları", "plan görev", self._show_agent_inspector, self._agent_controller is not None),
            PaletteAction("agent_templates", "Hazır Agent görevleri", "şablon template görev", self._show_task_templates, self._template_registry() is not None),
            PaletteAction("agent_tasks", "Agent Görev Merkezi", "geçmiş recovery yarım", self._show_agent_task_center, self._agent_controller is not None),
            PaletteAction("codex_analyze", "Codex ile analiz et", "proje incele analiz", self._create_codex_task, self._codex_bridge is not None),
            PaletteAction("codex_create", "Codex görevi oluştur", "plan görev", self._create_codex_task, self._codex_bridge is not None),
            PaletteAction("codex_active", "Aktif Codex görevini göster", "durum progress", self._show_codex_inspector, self._codex_bridge is not None),
            PaletteAction("codex_history", "Codex geçmişi", "görev sonuç", self._show_codex_inspector, self._codex_bridge is not None),
            PaletteAction("codex_stop", "Codex görevini durdur", "iptal stop", self._stop_codex_task, self._codex_bridge is not None),
            PaletteAction("codex_resume", "Codex görevini sürdür", "devam resume recovery", self._resume_codex_task, self._codex_bridge is not None),
            PaletteAction("codex_changes", "Codex değişikliklerini göster", "diff inceleme review", self._show_codex_diff_review, self._codex_bridge is not None),
            PaletteAction("codex_settings", "Codex ayarları", "güvenlik workspace", self.open_settings, self._user_settings_service is not None),
            PaletteAction("notifications", "Bildirimleri aç", "hatırlatıcı", self.open_notifications, self._notification_service is not None),
            PaletteAction("settings", "Ayarları aç", "tema ses model", self.open_settings, self._user_settings_service is not None),
            PaletteAction("inspector", "Ayrıntılar panelini aç", "durum sistem", self._show_system_inspector),
        )

    def _show_command_palette(self) -> None:
        if not hasattr(self, "_command_palette") or self._command_palette is None:
            self._command_palette = CommandPalette(self._palette_actions(), self)
        self._command_palette.open_focused()

    def _toggle_inspector(self) -> None:
        if self._inspector.isVisible():
            self._close_inspector()
        else:
            self._inspector.show_home()
            self._view_state = replace(
                self._view_state,
                right_panel_section=RightPanelSection.TOOLS,
            )
            self._present_inspector()

    def _close_inspector(self) -> None:
        self._inspector.hide()
        self._drawer_scrim.hide()
        self._right_panel_requested_visible = False
        self._view_state = replace(self._view_state, right_panel_visible=False)
        self._set_inspector_button_state(opened=False)
        self._inspector_button.setFocus()

    def _set_inspector_button_state(self, *, opened: bool) -> None:
        self._inspector_button.setProperty("opened", opened)
        self._inspector_button.setToolTip(
            "Bağlamsal araçları kapat" if opened else "Bağlamsal araçları aç"
        )
        self._inspector_button.style().unpolish(self._inspector_button)
        self._inspector_button.style().polish(self._inspector_button)

    def _present_inspector(self) -> None:
        self._right_panel_requested_visible = True
        self._view_state = replace(self._view_state, right_panel_visible=True)
        if self._responsive_mode is ResponsiveMode.LARGE:
            self._dock_inspector()
        else:
            self._undock_inspector()
        self._inspector.show()
        self._inspector.raise_()
        self._set_inspector_button_state(opened=True)

    def _dock_inspector(self) -> None:
        self._drawer_scrim.hide()
        if self._root_layout.indexOf(self._inspector) < 0:
            self._inspector.hide()
            self._inspector.setParent(self._central)
            self._root_layout.addWidget(self._inspector)
        self._inspector.display_mode = "docked"
        self._inspector.setFixedWidth(self._right_panel_width)

    def _undock_inspector(self) -> None:
        if self._root_layout.indexOf(self._inspector) >= 0:
            self._root_layout.removeWidget(self._inspector)
            self._inspector.setParent(self._central)
        self._inspector.display_mode = "drawer"
        self._position_inspector_drawer()
        self._drawer_scrim.setGeometry(self._central.rect())
        self._drawer_scrim.show()
        self._drawer_scrim.raise_()
        self._inspector.raise_()

    def _position_inspector_drawer(self) -> None:
        available = self._central.width()
        width = min(self._right_panel_width, max(280, available - 48))
        self._inspector.setGeometry(available - width, 0, width, self._central.height())

    def _apply_responsive_layout(self) -> None:
        tokens = design_tokens("dark").layout
        previous = self._responsive_mode
        derived = self._view_state.for_width(self.width(), tokens)
        self._responsive_mode = derived.responsive_mode
        compact = (
            self._interface_density == "compact"
            or self._responsive_mode is ResponsiveMode.COMPACT
        )
        self._sidebar.set_collapsed(compact)
        self._composer.set_compact(compact)
        self._update_responsive_chrome(compact)
        if self._responsive_mode is ResponsiveMode.LARGE:
            self._dock_inspector()
            self._inspector.setVisible(self._right_panel_requested_visible)
            self._drawer_scrim.hide()
        else:
            if previous is ResponsiveMode.LARGE:
                self._inspector.hide()
            if self._inspector.isVisible():
                self._undock_inspector()
            else:
                self._drawer_scrim.hide()
        self._view_state = replace(
            derived,
            right_panel_visible=self._inspector.isVisible(),
        )

    def _show_system_inspector(self) -> None:
        details = "\n".join((self._model_status.text(), self._speech_status.text(), self._voice_status.text()))
        self._inspector.show_details("Lina Durumu", details)
        self._view_state = replace(self._view_state, right_panel_section=RightPanelSection.SYSTEM)
        self._present_inspector()

    def _show_agent_inspector(self) -> None:
        session = self._agent_controller.session if self._agent_controller else None
        inspector = AgentInspectorV2(self._inspector)
        inspector.render(session)
        self._inspector.show_widget("Agent Görevi", inspector)
        self._view_state = replace(self._view_state, right_panel_section=RightPanelSection.AGENT)
        self._present_inspector()

    def _show_codex_inspector(self) -> None:
        inspector = CodexInspector(self._inspector)
        session = self._codex_bridge.session if self._codex_bridge else None
        history = self._codex_bridge.repository.list() if self._codex_bridge else ()
        change_set = (self._codex_bridge.review_change_set(session.session_id)
                      if self._codex_bridge and session else None)
        recovery = self._codex_bridge.repository.recovery_items() if self._codex_bridge else ()
        inspector.render(
            session, history, self._codex_bridge.client_info if self._codex_bridge else None,
            change_set, recovery,
        )
        inspector.approve_requested.connect(self._approve_codex_task)
        inspector.deny_requested.connect(self._deny_codex_task)
        inspector.edit_requested.connect(self._edit_codex_task)
        inspector.workspace_select_requested.connect(self._select_codex_workspace)
        inspector.workspace_cancel_requested.connect(self._cancel_codex_workspace)
        inspector.refresh_requested.connect(self._refresh_codex_status)
        inspector.login_requested.connect(lambda: self._login_codex(False))
        inspector.device_login_requested.connect(lambda: self._login_codex(True))
        inspector.logout_requested.connect(self._logout_codex)
        inspector.stop_requested.connect(self._stop_codex_task)
        inspector.diagnostics_requested.connect(self._show_codex_diagnostics)
        inspector.installation_guide_requested.connect(self._open_codex_installation_guide)
        inspector.terminal_requested.connect(self._open_codex_terminal)
        inspector.review_requested.connect(self._show_codex_diff_review)
        inspector.resume_requested.connect(self._resume_codex_task)
        inspector.recovery_inspect_requested.connect(self._inspect_codex_recovery)
        inspector.recovery_restart_requested.connect(self._restart_codex_recovery)
        inspector.recovery_remove_requested.connect(self._remove_codex_recovery)
        if self._pending_codex_request and (session is None or session.terminal):
            inspector.render_workspace_required(self._pending_codex_request)
        self._inspector.show_widget("Codex", inspector)
        self._view_state = replace(self._view_state, right_panel_section=RightPanelSection.CODEX)
        self._present_inspector()

    def _show_memory_inspector(self) -> None:
        if self._memory_service is None:
            summary = "Bellek bu çalışma alanında etkin değil."
        else:
            memories = tuple(
                item.content
                for item in self._memory_service.list_memories()
                if not self._memory_service.is_sensitive_content(item.content)
            )
            summary = "\n\n".join(f"• {item}" for item in memories) or "Henüz kayıtlı bir bilgi yok."
        self._inspector.show_details("Bellek", summary)
        self._view_state = replace(self._view_state, right_panel_section=RightPanelSection.MEMORY)
        self._present_inspector()

    def _show_voice_inspector(self) -> None:
        details = "\n".join((self._speech_status.text(), self._voice_status.text()))
        self._inspector.show_details("Sesli Mod", details)
        self._view_state = replace(self._view_state, right_panel_section=RightPanelSection.VOICE)
        self._present_inspector()

    def _handle_context_tool(self, tool_id: str) -> None:
        if tool_id == "chat":
            if self._responsive_mode is not ResponsiveMode.LARGE:
                self._close_inspector()
            self._composer.input.setFocus()
        elif tool_id == "voice":
            self._show_voice_inspector()
        elif tool_id == "vision":
            self._show_vision_inspector()
        elif tool_id == "file":
            self.handle_image_upload()
        elif tool_id == "agent":
            self._show_agent_inspector()
        elif tool_id == "codex":
            self._show_codex_inspector()
        elif tool_id == "memory":
            self._show_memory_inspector()

    def _should_route_codex(self, message: str) -> bool:
        if self._codex_bridge is None:
            return False
        if classify_codex_intent(message).operational:
            return True
        lowered = message.casefold()
        return bool(
            self._user_settings_service
            and self._user_settings_service.current.codex.automatic_analysis_suggestions
            and any(subject in lowered for subject in ("bu proje", "projeyi", "bu dosya"))
            and any(action in lowered for action in ("incele", "analiz et", "optimize et", "hataları bul"))
        )

    def _handle_codex_control_message(self, message: str) -> bool:
        control = route_codex_control(message)
        if not control.matched:
            return False
        if self._codex_bridge is None:
            self._append_assistant_message("Codex Bridge şu anda etkin değil.")
            return True
        if control.action.value == "stop":
            self._stop_codex_task()
        elif control.action.value == "resume":
            self._resume_codex_task(control.instruction)
        elif control.action.value == "show_changes":
            self._show_codex_diff_review()
        else:
            session = self._codex_bridge.session
            if session is None:
                self._append_assistant_message("Aktif Codex görevi yok.")
            else:
                self._append_assistant_message(
                    f"Codex görev durumu: {codex_status_label(session.status)}. "
                    f"İlerleme: %{session.progress}."
                )
            self._show_codex_inspector()
        return True

    def _create_codex_task(self) -> None:
        request = self._composer.text()
        if not request:
            request, accepted = QInputDialog.getText(
                self, "Codex görevi", "Codex ile ne yapmak istiyorsun?")
            if not accepted or not request.strip():
                return
        self._prepare_codex_request(request)

    def _prepare_codex_request(self, request: str) -> None:
        if self._codex_bridge is None:
            self._append_assistant_message("Codex Bridge şu anda yapılandırılmamış.")
            return
        try:
            validate_codex_request_scope(request)
        except WorkspaceAccessError as error:
            self._append_assistant_message(str(error))
            return
        self._pending_codex_request = request
        self._append_assistant_message(
            "Codex ile analiz yapabilmem için önce çalışma klasörünü seçmelisin."
        )
        self._speak_codex_status("Codex görevi hazır. Çalışma alanını seçmeni bekliyorum.")
        self._show_codex_inspector()

    def _select_codex_workspace(self) -> None:
        request = self._pending_codex_request
        if self._codex_bridge is None or not request:
            return
        workspace = QFileDialog.getExistingDirectory(
            self, "Codex çalışma klasörünü seç", str(Path.home()))
        if not workspace:
            return
        try:
            context = self._codex_bridge.select_workspace(Path(workspace))
            session = self._codex_bridge.prepare(request, context)
        except (OSError, ValueError, PermissionError) as error:
            self._append_assistant_message(
                str(error) if isinstance(error, WorkspaceAccessError)
                else "Codex görevi güvenli biçimde hazırlanamadı."
            )
            return
        self._pending_codex_request = None
        task = session.task
        actions = "\n".join(
            f"{index}. {action.purpose}" for index, action in enumerate(task.requested_actions, 1)
        ) if task else ""
        self._append_assistant_message(
            f"{confirmation_prompt()}\n\nPlan:\n{actions}\n\nWorkspace: {context.root_path.name}")
        self._speak_codex_status("Codex görevi hazır. Onayını bekliyorum.")
        self._show_codex_inspector()

    def _cancel_codex_workspace(self) -> None:
        if self._pending_codex_request is None:
            return
        self._pending_codex_request = None
        self._append_assistant_message("Codex görevi iptal edildi; çalışma alanı seçilmedi.")
        self._show_codex_inspector()

    def _approve_codex_task(self) -> None:
        if self._codex_bridge is None or self._codex_bridge.session is None:
            return
        session = self._codex_bridge.session
        self._append_assistant_message("Codex çalışıyor. Sonuç tamamlandığında doğrulayacağım.")
        self._speak_codex_status("Codex çalışıyor.")
        worker = FunctionWorker(lambda: self._codex_bridge.start(session.session_id, approved=True))
        worker.signals.result.connect(self._handle_codex_result)
        worker.signals.error.connect(self._handle_codex_error)
        self._start_worker(worker)
        self._show_codex_inspector()

    def _handle_codex_result(self, _result: object) -> None:
        session = self._codex_bridge.session if self._codex_bridge else None
        if session and session.review_pending:
            self._append_assistant_message(
                f"Codex {session.changed_file_count} dosyada değişiklik yaptı. "
                f"+{session.additions} / -{session.deletions}. Değişiklikler incelemeni bekliyor."
            )
        else:
            self._append_assistant_message(
                session.result_summary if session and session.result_summary else "Codex görevi tamamlandı."
            )
        if session and self._codex_bridge:
            self._codex_bridge.mark_result_surfaced(session.session_id)
        self._speak_codex_status(
            "Değişiklikler incelemeni bekliyor." if session and session.review_pending
            else "Analiz tamamlandı." if session and session.status.value == "completed"
            else "Görev doğrulanamadı."
        )
        self._show_codex_inspector()

    def _handle_codex_event_ui(self, _event: object, _message: str) -> None:
        # The event originated in a worker thread; this Qt signal queues the UI refresh.
        if self._codex_refresh_pending:
            return
        self._codex_refresh_pending = True
        QTimer.singleShot(100, self._flush_codex_event_ui)

    def _flush_codex_event_ui(self) -> None:
        self._codex_refresh_pending = False
        self._show_codex_inspector()

    def _handle_codex_error(self, error: object) -> None:
        session = self._codex_bridge.session if self._codex_bridge else None
        if isinstance(error, (CodexClientUnavailableError, CodexTransportError)) and session:
            text = session.result_summary or getattr(error, "user_message", "Codex görevi tamamlanamadı.")
        else:
            text = "Codex görevi güvenli biçimde tamamlanamadı. Ayrıntılar kullanıcıya açılmadı."
        self._append_assistant_message(text)
        self._speak_codex_status(
            "Codex oturumu gerekli."
            if session and session.error_code in {"login_required", "not_authenticated"}
            else "Görev doğrulanamadı."
        )
        self._show_codex_inspector()

    def _speak_codex_status(self, text: str) -> None:
        if self._voice_controller is None or not self._voice_controller.responses_enabled:
            return
        # Only fixed, short status phrases cross the TTS boundary. Never pass CLI output,
        # paths, diffs, file names, diagnostics, or exception text here.
        allowed = {
            "Codex görevi hazır. Çalışma alanını seçmeni bekliyorum.",
            "Codex görevi hazır. Onayını bekliyorum.",
            "Codex çalışıyor.", "Analiz tamamlandı.",
            "Codex oturumu gerekli.", "Görev doğrulanamadı.",
            "Değişiklikler incelemeni bekliyor.",
        }
        if text in allowed:
            self._voice_controller.speak(text)

    def _refresh_codex_status(self) -> None:
        if self._codex_bridge is None:
            return
        worker = FunctionWorker(self._codex_bridge.refresh_client_info)
        worker.signals.result.connect(lambda _info: self._show_codex_inspector())
        worker.signals.error.connect(lambda _error: self._append_assistant_message(
            "Codex CLI durumu kontrol edilemedi."))
        self._start_worker(worker)

    def _login_codex(self, device_auth: bool) -> None:
        if self._codex_bridge is None:
            return
        answer = QMessageBox.question(
            self, "Codex oturumu",
            "Resmi Codex CLI giriş akışı ayrı bir terminalde başlatılacak. Devam edilsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._codex_bridge.launch_login(device_auth=device_auth)
            self._append_assistant_message("Resmi Codex CLI giriş akışı başlatıldı. Tamamlayınca durumu yenile.")
        except (CodexClientUnavailableError, CodexTransportError):
            self._append_assistant_message("Codex giriş akışı başlatılamadı.")

    def _logout_codex(self) -> None:
        if self._codex_bridge is None:
            return
        answer = QMessageBox.warning(
            self, "Codex oturumunu kapat",
            "Bu işlem Codex CLI oturumunu bu cihazda kapatacak.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        worker = FunctionWorker(lambda: self._codex_bridge.logout(confirmed=True))
        worker.signals.result.connect(lambda _info: self._show_codex_inspector())
        worker.signals.error.connect(lambda _error: self._append_assistant_message(
            "Codex oturumu güvenli biçimde kapatılamadı."))
        self._start_worker(worker)

    def _stop_codex_task(self) -> None:
        if self._codex_bridge is not None:
            self._codex_bridge.cancel()
            self._append_assistant_message("Codex görevi iptal edildi.")
            self._show_codex_inspector()

    def _show_codex_diff_review(self) -> None:
        if self._codex_bridge is None or self._codex_bridge.session is None:
            return
        session = self._codex_bridge.session
        change_set = self._codex_bridge.review_change_set(session.session_id)
        if change_set is None:
            self._append_assistant_message("İncelenecek Codex değişikliği bulunmuyor.")
            return
        dialog = CodexDiffReviewDialog(
            change_set, task_title=session.task_summary,
            workspace_name=session.project_context.root_path.name, parent=self,
        )
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.decision_requested.connect(self._handle_codex_review_decision)
        dialog.review_completed.connect(self._complete_codex_review)
        self._codex_diff_dialog = dialog
        dialog.open()

    def _handle_codex_review_decision(self, decision: CodexReviewDecision) -> None:
        if self._codex_bridge is None or self._codex_bridge.session is None:
            return
        session = self._codex_bridge.session
        summary = self._codex_bridge.decide_review(session.session_id, decision)
        dialog = getattr(self, "_codex_diff_dialog", None)
        if dialog is not None:
            change_set = self._codex_bridge.review_change_set(session.session_id)
            if change_set is not None:
                dialog.render(change_set)
        if decision.action == "reject":
            self._append_assistant_message(
                "Reddetme kararı kaydedildi. Hiçbir dosya otomatik geri alınmadı veya silinmedi."
            )
        elif decision.action in {"request_explanation", "send_back"}:
            self._append_assistant_message(
                "İnceleme talebi kaydedildi; yeni Codex görevi ayrıca onay gerektirecek."
            )
        if summary.approved_for_continue:
            self._complete_codex_review()
        self._show_codex_inspector()

    def _complete_codex_review(self) -> None:
        if self._codex_bridge is None or self._codex_bridge.session is None:
            return
        try:
            self._codex_bridge.complete_review(self._codex_bridge.session.session_id)
        except PermissionError:
            return
        self._append_assistant_message("Codex değişiklik incelemesi tamamlandı.")
        self._show_codex_inspector()

    def _resume_codex_task(self, instruction: str = "") -> None:
        instruction = instruction if isinstance(instruction, str) else ""
        if self._codex_bridge is None or self._codex_bridge.session is None:
            self._append_assistant_message(
                "Önceki görevi sürdürmek için aynı workspace'i seçip açıkça onaylamalısın."
            )
            return
        session = self._codex_bridge.session
        reference = session.remote_session
        if reference is None or not reference.resumable:
            self._append_assistant_message(
                "Bu görev güvenli resume metadata'sına sahip değil. Yeni görev olarak başlatabilirsin."
            )
            return
        answer = QMessageBox.question(
            self, "Codex görevini sürdür",
            "Aynı workspace ve doğrulanmış CLI oturumuyla göreve devam edilsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            session = self._codex_bridge.prepare_resume(session.session_id, instruction)
        except (RuntimeError, ValueError) as error:
            self._append_assistant_message(str(error))
            return
        worker = FunctionWorker(lambda: self._codex_bridge.start(
            session.session_id, approved=True, resume_reference=reference
        ))
        worker.signals.result.connect(self._handle_codex_result)
        worker.signals.error.connect(self._handle_codex_error)
        self._start_worker(worker)

    def _inspect_codex_recovery(self, item: object) -> None:
        if item is None:
            return
        details = (
            f"Görev: {getattr(item, 'task_summary', 'Bilinmiyor')}\n"
            f"Workspace: {getattr(item, 'workspace_display_name', 'Bilinmiyor')}\n"
            f"Durum: {codex_status_label(getattr(item, 'status', 'unknown'))}\n"
            f"Son olay: {getattr(item, 'last_event', 'unknown')}\n"
            f"Doğrulama: {getattr(item, 'verification', 'unverified')}"
        )
        self._inspector.show_details("Codex Görev Kurtarma", details)

    def _restart_codex_recovery(self, item: object) -> None:
        if item is None:
            return
        self._composer.input.setPlainText(str(getattr(item, "task_summary", "")))
        self._composer.input.setFocus()
        self._append_assistant_message(
            "Önceki görev özeti yeni görev taslağına alındı; workspace ve plan yeniden onaylanacak."
        )

    def _remove_codex_recovery(self, item: object) -> None:
        if self._codex_bridge is None or item is None:
            return
        self._codex_bridge.repository.delete(str(getattr(item, "session_id", "")))
        self._append_assistant_message("Codex görev kaydı geçmişten kaldırıldı; workspace dosyalarına dokunulmadı.")
        self._show_codex_inspector()

    def _show_codex_diagnostics(self) -> None:
        if self._codex_bridge is None:
            return
        worker = FunctionWorker(self._codex_bridge.diagnostics_report)
        worker.signals.result.connect(
            lambda report: self._inspector.show_details("Codex CLI Ayrıntıları", str(report))
        )
        worker.signals.error.connect(
            lambda _error: self._append_assistant_message("Codex CLI diagnostics alınamadı.")
        )
        self._start_worker(worker)

    @staticmethod
    def _open_codex_installation_guide() -> None:
        QDesktopServices.openUrl(QUrl("https://developers.openai.com/codex/cli"))

    def _open_codex_terminal(self) -> None:
        workspace = (self._codex_bridge.session.project_context.root_path
                     if self._codex_bridge and self._codex_bridge.session else Path.home())
        terminal = shutil.which("wt.exe")
        if terminal is None:
            self._append_assistant_message(
                "Windows Terminal bulunamadı. Terminali açıp çalışma klasörüne elle geçebilirsin."
            )
            return
        subprocess.Popen((terminal, "-d", str(workspace)), shell=False)

    def _deny_codex_task(self) -> None:
        if self._codex_bridge is None or self._codex_bridge.session is None:
            return
        self._codex_bridge.deny(self._codex_bridge.session.session_id)
        self._append_assistant_message("Codex görevi iptal edildi; hiçbir değişiklik uygulanmadı.")
        self._show_codex_inspector()

    def _edit_codex_task(self) -> None:
        if self._codex_bridge is None or self._codex_bridge.session is None:
            return
        task = self._codex_bridge.session.task
        if task is not None:
            self._composer.input.setPlainText(task.objective)
            self._composer.input.setFocus()

    def _refresh_local_storage(self) -> None:
        if self._local_storage_service is None:
            return
        worker = FunctionWorker(self._local_storage_service.measure)
        worker.signals.result.connect(self._apply_local_storage_snapshot)
        self._start_worker(worker)

    def _apply_local_storage_snapshot(self, result: object) -> None:
        if isinstance(result, LocalStorageSnapshot):
            self._storage_snapshot = result
            self._inspector.set_storage_snapshot(result)

    def _open_local_data_folder(self) -> None:
        snapshot = self._storage_snapshot
        locations = snapshot.locations if snapshot is not None else ()
        target = next((path for path in locations if path.exists()), None)
        if target is None:
            self._set_status("Yerel veri klasörü bulunamadı.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _template_registry(self):
        return self._agent_controller.planner.template_registry if self._agent_controller else None

    def _available_agent_tools(self) -> set[str]:
        if self._agent_controller is None:
            return set()
        return {
            item.name
            for item in self._agent_controller.policy.capability_snapshot(self._agent_controller.executor.registry)
            if item.available
        }

    def _show_task_templates(self) -> None:
        registry = self._template_registry()
        if registry is None:
            self._set_status("Hazır Agent görevleri şu anda kullanılamıyor.")
            return
        dialog = TaskTemplateBrowserDialog(registry, self._available_agent_tools(), self)
        dialog.template_selected.connect(self._prepare_task_template)
        dialog.finished.connect(lambda _result: setattr(self, "_task_template_dialog", None))
        self._task_template_dialog = dialog
        dialog.show()
        dialog.raise_()

    def _prepare_task_template(self, template_id: str) -> None:
        registry = self._template_registry()
        if registry is None or self._agent_controller is None:
            return
        template = registry.get(template_id)
        if template is None:
            return
        dialog = TaskTemplateParameterDialog(template, self)
        if not dialog.exec():
            return
        try:
            session = self._agent_controller.create_from_template(
                template_id,
                dialog.parameters(),
                self._routing_session_key,
                self._active_request_id,
            )
        except AgentError as error:
            self._set_status(str(error))
            return
        self._agent_enabled = True
        self._update_agent_ui()
        self._set_status(f"{session.plan.title} hazır; çalıştırılmadan önce plan onayı bekliyor.")
        self._show_plan_review()

    def _show_agent_task_center(self) -> None:
        controller = self._agent_controller
        if controller is None or controller.repository is None:
            self._show_agent_inspector()
            return
        if self._agent_task_center_dialog is None:
            dialog = AgentTaskCenterDialog(AgentTaskCenter(controller.repository), self)
            dialog.open_requested.connect(self._open_agent_task)
            dialog.restart_requested.connect(self._restart_agent_task)
            dialog.finished.connect(lambda _result: setattr(self, "_agent_task_center_dialog", None))
            self._agent_task_center_dialog = dialog
        else:
            self._agent_task_center_dialog.reload()
        self._agent_task_center_dialog.show()
        self._agent_task_center_dialog.raise_()
        self._agent_task_center_dialog.activateWindow()

    def _open_agent_task(self, session_id: str) -> None:
        current = self._agent_controller.session if self._agent_controller else None
        if current is not None and current.session_id == session_id:
            self._show_agent_inspector()
            return
        center = AgentTaskCenter(self._agent_controller.repository) if self._agent_controller and self._agent_controller.repository else None
        task = center.get(session_id) if center else None
        if task is not None:
            self._inspector.show_details(task.title, task.last_summary)
            self._view_state = replace(self._view_state, right_panel_section=RightPanelSection.AGENT)
            self._present_inspector()

    def _restart_agent_task(self, session_id: str) -> None:
        controller = self._agent_controller
        current = controller.session if controller else None
        if controller is None or current is None or current.session_id != session_id:
            center = AgentTaskCenter(controller.repository) if controller and controller.repository else None
            task = center.get(session_id) if center else None
            if task is not None and task.template_id and self._template_registry() is not None:
                self._set_status("Geçmiş görev gizlilik nedeniyle otomatik yürütülmeyecek; bilgileri yeniden doğrula.")
                self._prepare_task_template(task.template_id)
            else:
                self._set_status("Bu geçmiş görev gizlilik nedeniyle otomatik yeniden kurulmadı; şablonu açıp bilgileri yeniden doğrula.")
            return
        try:
            controller.safe_restart(session_id)
        except AgentError as error:
            self._set_status(str(error))
            return
        self._update_agent_ui()
        self._set_status("Görev güvenli bir kopya olarak yeniden hazırlandı.")
        if self._agent_task_center_dialog is not None:
            self._agent_task_center_dialog.reload()

    def _show_vision_inspector(self) -> None:
        snapshot = self._live_vision_controller.snapshot if self._live_vision_controller else None
        summary = "Aktif Vision oturumu yok."
        if snapshot is not None:
            summary = f"Kaynak: {snapshot.source.value}\nDurum: {snapshot.state.value}\n{snapshot.last_result or snapshot.user_message}"
        self._inspector.show_details("Vision Oturumu", summary)
        self._view_state = replace(self._view_state, right_panel_section=RightPanelSection.VISION)
        self._present_inspector()

    def _show_status_menu(self) -> None:
        menu = QMenu(self)
        for text in (self._model_status.text(), self._speech_status.text(), self._voice_status.text()):
            action = menu.addAction(text)
            action.setEnabled(False)
        menu.addSeparator()
        details = menu.addAction("Tüm ayrıntıları göster")
        selected = menu.exec(self._status_button.mapToGlobal(self._status_button.rect().bottomLeft()))
        if selected is details:
            self._show_system_inspector()

    def _show_tools_menu(self) -> None:
        self._tools_menu = self._build_tools_menu()
        self._tools_menu.exec(
            self._inspector_button.mapToGlobal(self._inspector_button.rect().bottomLeft())
        )

    def _build_tools_menu(self) -> QMenu:
        menu = QMenu(self)
        palette_action = menu.addAction("Komut paleti")
        palette_action.triggered.connect(self._show_command_palette)
        agent_action = menu.addAction("Agent ile çalış")
        agent_action.setEnabled(self._agent_controller is not None)
        agent_action.triggered.connect(self._show_agent_inspector)
        templates_action = menu.addAction("Hazır görevler")
        templates_action.setEnabled(self._template_registry() is not None)
        templates_action.triggered.connect(self._show_task_templates)
        task_center_action = menu.addAction("Agent Görev Merkezi")
        task_center_action.setEnabled(self._agent_controller is not None)
        task_center_action.triggered.connect(self._show_agent_task_center)
        conversations = menu.addMenu("Sohbet görünümü")
        for label, view in (("Sohbetler", "chats"), ("Sabitlenenler", "pinned"), ("Arşiv", "archive")):
            action = conversations.addAction(label)
            action.triggered.connect(lambda _checked=False, target=view: self._set_conversation_view(target))
        if self._notification_service is not None:
            notification_action = menu.addAction("Bildirimler")
            notification_action.triggered.connect(self.open_notifications)
        menu.addSeparator()
        details_action = menu.addAction("Sistem ayrıntıları")
        details_action.triggered.connect(self._show_system_inspector)
        if self._user_settings_service is not None:
            settings_action = menu.addAction("Ayarlar")
            settings_action.triggered.connect(self.open_settings)
        return menu

    def _set_conversation_view(self, view: str) -> None:
        index = self._sidebar.filter_combo.findData(view)
        if index >= 0:
            self._sidebar.filter_combo.setCurrentIndex(index)

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
                speech_service=self._speech_service,
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
            self._notification_button.setText(str(count) if count else "")
            self._notification_button.setVisible(count > 0)
            self._notification_button.setToolTip(
                f"Bildirim merkezini aç ({count} okunmamış)" if count else "Bildirim merkezini aç"
            )

    def _setup_agent_recovery_notice(self) -> None:
        controller = self._agent_controller
        settings = self._user_settings_service.current.agent if self._user_settings_service else None
        if (
            controller is None
            or controller.repository is None
            or settings is not None and not settings.notify_interrupted_tasks_on_startup
        ):
            return
        notice = AgentTaskCenter(controller.repository).recovery_notice()
        if notice is None:
            return
        self._notify_agent_event("recovery", "Yarım Agent görevi", notice.message)
        self._set_status(notice.message)

    def _notify_agent_event(self, event_id: str, title: str, message: str) -> None:
        if event_id in self._agent_notification_events:
            return
        self._agent_notification_events.add(event_id)
        if self._tray_icon is not None:
            self._tray_icon.showMessage(title, message)

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
        if not self._window_state_restored:
            self._restore_window_state(settings)
            self._window_state_restored = True
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
        self._interface_density = settings.appearance.density
        self._right_panel_width = settings.appearance.right_panel_width
        self._message_width = settings.appearance.message_width
        self._right_panel_requested_visible = settings.appearance.right_panel_visible
        section = RightPanelSection(settings.appearance.right_panel_section)
        self._view_state = replace(
            self._view_state,
            theme=settings.appearance.theme,
            sidebar_collapsed=settings.appearance.sidebar_collapsed,
            right_panel_visible=settings.appearance.right_panel_visible,
            right_panel_section=section,
        )
        self._inspector.setFixedWidth(self._right_panel_width)
        self._apply_responsive_layout()
        self._voice_responses_enabled = settings.speech.voice_responses_enabled
        hands_free_was_enabled = self._hands_free_enabled
        self._hands_free_enabled = settings.speech.hands_free_enabled
        if hands_free_was_enabled and not self._hands_free_enabled and self._hands_free_service is not None:
            self._hands_free_service.cancel_active()
        self._wake_indicator_enabled = settings.speech.wake_word_indicator_enabled
        self._transcription_mode = settings.speech.transcription_mode
        if self._speech_service is not None and hasattr(self._speech_service, "set_microphone_device"):
            self._speech_service.set_microphone_device(settings.speech.microphone_device_id)
            self._speech_service.configure_microphone(
                settings.speech.input_sensitivity,
                settings.speech.calibrated_noise_threshold,
            )
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
            if self._agent_controller.repository is not None:
                try:
                    self._agent_controller.repository.cleanup(settings.agent.agent_history_retention_days)
                except (OSError, ValueError, TypeError):
                    pass
        if hasattr(self._composer, "task_templates_action"):
            self._composer.task_templates_action.setVisible(settings.agent.show_task_template_suggestions)
        self._update_agent_ui()
        self._live_vision_enabled = settings.live_vision.enabled and settings.vision.enabled
        if self._camera_preview is not None:
            self._camera_preview.canvas.set_mirror_enabled(settings.live_vision.mirror_camera_preview)
            self._camera_preview.auto_commentary_button.setChecked(settings.live_vision.automatic_camera_commentary_enabled)
            self._camera_preview.mute_button.setChecked(not settings.live_vision.speak_semantic_changes)
        if hasattr(self, "_hands_free_toggle"):
            self._hands_free_toggle.setText("Hands-free Açık" if settings.speech.hands_free_enabled else "Hands-free Kapalı")
            self._hands_free_pause.setEnabled(settings.speech.hands_free_enabled)
        self._composer.attachment_button.setEnabled(True)
        self._set_vision_controls_enabled(self._vision_enabled)
        if not self._vision_enabled and self._screen_context is not None:
            self._clear_screen_context()
        if not self._live_vision_enabled and self._live_vision_controller is not None:
            self._live_vision_controller.stop()
        self._refresh_speech_status()
        self._set_status("Ayarlar uygulandı")

    def _restore_window_state(self, settings: UserSettings) -> None:
        system = settings.system
        screens = tuple(screen.availableGeometry() for screen in QGuiApplication.screens())
        primary = screens[0] if screens else QRect(0, 0, 1240, 780)
        x = system.window_x if system.window_x is not None else primary.center().x() - system.window_width // 2
        y = system.window_y if system.window_y is not None else primary.center().y() - system.window_height // 2
        geometry = clamp_window_geometry(QRect(x, y, system.window_width, system.window_height), screens)
        self.setGeometry(geometry)
        if system.window_maximized:
            self.showMaximized()

    def _persist_window_state(self) -> None:
        if self._user_settings_service is None:
            return
        current = self._user_settings_service.current
        geometry = self.normalGeometry() if self.isMaximized() else self.geometry()
        system = replace(
            current.system,
            window_x=geometry.x(), window_y=geometry.y(),
            window_width=max(720, geometry.width()), window_height=max(560, geometry.height()),
            window_maximized=self.isMaximized(),
        )
        appearance = replace(
            current.appearance,
            sidebar_collapsed=self._sidebar.collapsed,
            right_panel_visible=self._right_panel_requested_visible,
            right_panel_section=self._view_state.right_panel_section.value,
            right_panel_width=self._right_panel_width,
            message_width=self._message_width,
        )
        if system != current.system or appearance != current.appearance:
            try:
                self._user_settings_service.update(
                    replace(current, system=system, appearance=appearance)
                )
            except OSError:
                pass

    def _set_vision_controls_enabled(self, enabled: bool) -> None:
        self._composer.set_screen_enabled(enabled and not self._is_screen_capture_busy)

    def send_message(self) -> None:
        """Send the current composer text through the conversation service."""
        if self._is_waiting:
            return
        message = self._composer.text()
        if not message:
            if self._screen_context is not None:
                self._set_status("Ekran görüntüsü hakkında bir soru yaz.")
            elif self._document_attachment is not None:
                self._set_status("Belge hakkında bir soru yaz.")
            return

        self._record_input_history(message)
        self._update_session_title(message)
        self._composer.clear()
        request_screen_context = self._screen_context
        request_document_attachment = self._document_attachment
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
        if self._handle_codex_control_message(message):
            return
        if self._should_route_codex(message):
            self._prepare_codex_request(message)
            return
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
            if agent_session.status is AgentSessionStatus.AWAITING_INPUT:
                try:
                    plan = self._agent_controller.provide_input(
                        agent_session.session_id,
                        message,
                        self._routing_session_key,
                        agent_session.generation_id,
                    )
                    response = f"{plan.title} hazır. {len(plan.steps)} adımı inceleyip başlatabilirsin."
                except AgentError as error:
                    response = str(error)
                response = self._prepare_agent_text(response, self._agent_controller.session)
                self._update_agent_ui()
                self._finish_routed_intent(message, response, request_created_at)
                return
            decision = parse_approval(message)
            if agent_session.status is AgentSessionStatus.AWAITING_PLAN_APPROVAL and decision is ApprovalDecision.APPROVE:
                self._start_agent_plan()
                self._finish_routed_intent(message, self._agent_controller.result_summary(), request_created_at)
                return
            if agent_session.status is AgentSessionStatus.AWAITING_STEP_APPROVAL and decision is not ApprovalDecision.AMBIGUOUS:
                self._decide_agent_step(decision)
                self._finish_routed_intent(message, self._agent_controller.result_summary(), request_created_at)
                return
        if self._agent_enabled and self._agent_controller is not None and self._agent_controller.active_session is None:
            capabilities = self._agent_controller.policy.capability_snapshot(self._agent_controller.executor.registry)
            match = self._agent_controller.planner.match_template(
                AgentContext.bounded(message, capabilities=capabilities)
            )
            if match is not None and (match.template_id is not None or match.ambiguous):
                try:
                    session = self._agent_controller.create_session(
                        message, self._routing_session_key, self._active_request_id
                    )
                    plan = self._agent_controller.plan(capabilities=capabilities)
                    response = f"{plan.title} hazır. {len(plan.steps)} adımı inceleyip başlatabilirsin."
                except AgentError as error:
                    response = str(error)
                response = self._prepare_agent_text(response, self._agent_controller.session)
                self._update_agent_ui()
                active = self._agent_controller.session
                if active is not None:
                    self._speak_agent_event(
                        active.session_id,
                        active.status.value,
                        response,
                        approval=active.status in {AgentSessionStatus.AWAITING_PLAN_APPROVAL, AgentSessionStatus.AWAITING_STEP_APPROVAL},
                    )
                self._finish_routed_intent(message, response, request_created_at)
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
        if request_document_attachment is not None:
            self._request_document_attachments[request_id] = request_document_attachment
        worker = FunctionWorker(
            self._run_conversation_request,
            request_id,
            message,
            request_screen_context,
            request_document_attachment,
            request_created_at,
        )
        worker.signals.result.connect(self._handle_conversation_worker_result)
        worker.signals.error.connect(self._handle_conversation_error)
        self._start_worker(worker)

    def _handle_routed_intent(self, request: IntentRequest, user_text: str, created_at: datetime) -> None:
        if request.intent is RoutingIntentType.CODEX_OPERATIONAL:
            if self._handle_codex_control_message(user_text):
                return
            self._prepare_codex_request(user_text)
            return
        if request.intent in {
            RoutingIntentType.AGENT_EXECUTE, RoutingIntentType.AGENT_PLAN,
            RoutingIntentType.AGENT_PAUSE, RoutingIntentType.AGENT_RESUME,
            RoutingIntentType.AGENT_CANCEL, RoutingIntentType.AGENT_STATUS,
            RoutingIntentType.AGENT_MODIFY_PLAN, RoutingIntentType.AGENT_TEMPLATE_LIST,
            RoutingIntentType.AGENT_TEMPLATE_USE, RoutingIntentType.AGENT_TASK_HISTORY,
            RoutingIntentType.AGENT_TASK_RESTART, RoutingIntentType.AGENT_TASK_RECOVERY,
            RoutingIntentType.AGENT_PLAN_EDIT, RoutingIntentType.AGENT_STEP_SKIP,
            RoutingIntentType.AGENT_RETRY_READ_ONLY, RoutingIntentType.AGENT_CHECK_UNCERTAIN_RESULT,
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
                message = "Aktif Agent görevi yok." if progress is None else f"Agent ilerlemesi {progress.current}/{progress.total}. {progress.summary}"
            elif request.intent in {RoutingIntentType.AGENT_TEMPLATE_LIST, RoutingIntentType.AGENT_TEMPLATE_USE}:
                self._show_task_templates()
                message = "Kullanılabilir hazır Agent görevlerini açtım. Bir şablon seçtiğinde önce plan hazırlanacak."
            elif request.intent in {RoutingIntentType.AGENT_TASK_HISTORY, RoutingIntentType.AGENT_TASK_RECOVERY}:
                self._show_agent_task_center()
                message = "Agent Görev Merkezi açıldı. Yarım görevler otomatik olarak devam ettirilmez."
            elif request.intent in {RoutingIntentType.AGENT_PLAN_EDIT, RoutingIntentType.AGENT_MODIFY_PLAN, RoutingIntentType.AGENT_STEP_SKIP}:
                self._show_plan_review()
                message = "Plan incelemesini açtım. Değişiklikler yeniden doğrulanıp onay bekleyecek."
            elif request.intent in {RoutingIntentType.AGENT_TASK_RESTART, RoutingIntentType.AGENT_RETRY_READ_ONLY}:
                session = controller.session
                if session is None:
                    message = "Yeniden başlatılabilecek Agent görevi yok."
                else:
                    controller.safe_restart(session.session_id)
                    self._update_agent_ui()
                    message = "Görev güvenli bir kopya olarak yeniden hazırlandı. Eski onaylar kullanılmadı."
            elif request.intent is RoutingIntentType.AGENT_CHECK_UNCERTAIN_RESULT:
                self._show_agent_inspector()
                message = "Belirsiz sonucu yeniden çalıştırmadan inceleme ekranını açtım."
            elif request.intent is RoutingIntentType.AGENT_PAUSE:
                session = controller.active_session
                message = "Aktif Agent görevi yok." if session is None else (controller.pause(session.session_id) and "Agent görevi duraklatıldı.")
            elif request.intent is RoutingIntentType.AGENT_RESUME:
                session = controller.active_session
                message = "Aktif Agent görevi yok." if session is None else (controller.resume(session.session_id) and controller.result_summary())
            elif request.intent is RoutingIntentType.AGENT_CANCEL:
                session = controller.active_session
                message = "Aktif Agent görevi yok." if session is None else (controller.cancel(session.session_id) and "Agent görevi iptal edildi. Tamamlanan kalıcı işlemler geri alınmadı.")
            else:
                session = controller.create_session(user_text, self._routing_session_key, self._active_request_id)
                plan = controller.plan()
                self._agent_enabled = True
                message = f"{len(plan.steps)} adımlı plan hazır. İnceleyip Planı Başlat seçeneğiyle onayla."
                if session.status is AgentSessionStatus.COMPLETED:
                    message = controller.result_summary()
            self._update_agent_ui()
            active = controller.active_session or controller.session
            if active is not None:
                approval = active.status in {AgentSessionStatus.AWAITING_PLAN_APPROVAL, AgentSessionStatus.AWAITING_STEP_APPROVAL}
                completion = active.status in {AgentSessionStatus.COMPLETED, AgentSessionStatus.PARTIALLY_COMPLETED, AgentSessionStatus.FAILED}
                message = self._prepare_agent_text(message, active, approval=approval)
                self._speak_agent_event(active.session_id, active.status.value, message, approval=approval, completion=completion)
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

    def _show_plan_review(self) -> None:
        controller = self._agent_controller
        session = controller.session if controller else None
        if controller is None or session is None or session.plan is None:
            return
        dialog = QDialog(self)
        dialog.setObjectName("agentPlanReviewDialog")
        dialog.setWindowTitle("Agent Planını İncele")
        dialog.setMinimumSize(700, 520)
        layout = QVBoxLayout(dialog)
        review = PlanReviewWidget(dialog)
        review.render(session.plan)
        layout.addWidget(review)
        definitions = controller.executor.registry.definitions()
        editor = AgentPlanEditor(
            controller.policy,
            {item.name for item in definitions if item.available()},
            {item.name: dict(item.input_schema) for item in definitions},
        )

        def apply_edit(callback) -> None:
            current = controller.session
            if current is None or current.plan is None:
                return
            try:
                edited, difference = callback(current.plan)
                controller.apply_edited_plan(current.session_id, edited, current.generation_id)
            except AgentError as error:
                self._set_status(str(error))
                return
            review.render(edited)
            self._set_status(render_plan_diff(difference))
            self._update_agent_ui()

        def move_step(step_id: str, direction: int) -> None:
            current = controller.session
            if current is None or current.plan is None:
                return
            order = [step.step_id for step in current.plan.steps]
            index = order.index(step_id)
            target = index + direction
            if target < 0 or target >= len(order):
                return
            order[index], order[target] = order[target], order[index]
            apply_edit(lambda plan: editor.reorder(plan, order))

        review.skip_requested.connect(lambda step_id: apply_edit(lambda plan: editor.skip_step(plan, step_id)))
        review.remove_requested.connect(lambda step_id: apply_edit(lambda plan: editor.remove_optional_step(plan, step_id)))
        review.move_requested.connect(move_step)

        def edit_arguments(step_id: str) -> None:
            current = controller.session
            if current is None or current.plan is None:
                return
            step = next((item for item in current.plan.steps if item.step_id == step_id), None)
            definition = controller.executor.registry.get_by_name(step.tool_name) if step is not None else None
            if step is None or definition is None:
                self._set_status("Bu adım için düzenlenebilir typed schema bulunamadı.")
                return
            dialog = AgentStepArgumentsDialog(step.title, definition.input_schema, step.typed_arguments, self)
            if dialog.exec():
                apply_edit(lambda plan: editor.update_arguments(plan, step_id, dialog.arguments()))

        review.arguments_requested.connect(edit_arguments)

        def regenerate() -> None:
            current = controller.session
            if current is None:
                return
            try:
                difference = controller.regenerate_plan(current.session_id, current.generation_id)
            except AgentError as error:
                self._set_status(str(error))
                return
            review.render(controller.session.plan)
            self._set_status(render_plan_diff(difference))
            self._update_agent_ui()

        review.regenerate_requested.connect(regenerate)
        review.cancel_requested.connect(lambda: (self._cancel_agent(), dialog.reject()))
        review.start_requested.connect(lambda: (self._start_agent_plan(), dialog.accept()))
        dialog.finished.connect(lambda _result: setattr(self, "_plan_review_dialog", None))
        self._plan_review_dialog = dialog
        dialog.show()
        dialog.raise_()

    def _start_agent_plan(self) -> None:
        if not self._agent_controller or not self._agent_controller.active_session:
            return
        try:
            session = self._agent_controller.active_session
            self._agent_controller.approve_plan(session.session_id, session.generation_id)
            self._agent_controller.run(self._routing_session_key)
            current = self._agent_controller.session
            if current is not None:
                text = self._agent_controller.result_summary()
                self._speak_agent_event(current.session_id, current.status.value, text, approval=current.status is AgentSessionStatus.AWAITING_STEP_APPROVAL, completion=current.terminal)
        except AgentError as error:
            self._set_status(str(error))
        self._update_agent_ui()

    def _decide_agent_step(self, decision: ApprovalDecision) -> None:
        if not self._agent_controller or not self._agent_controller.active_session:
            return
        try:
            session = self._agent_controller.active_session
            self._agent_controller.approve_step(session.session_id, decision, session.generation_id)
            current = self._agent_controller.session
            if current is not None:
                self._speak_agent_event(current.session_id, current.status.value, self._agent_controller.result_summary(), approval=current.status is AgentSessionStatus.AWAITING_STEP_APPROVAL, completion=current.terminal)
        except AgentError as error:
            self._set_status(str(error))
        self._update_agent_ui()

    def _pause_agent(self) -> None:
        if self._agent_controller and self._agent_controller.active_session:
            try:
                self._agent_controller.pause(self._agent_controller.active_session.session_id)
                session = self._agent_controller.session
                self._speak_agent_event(session.session_id, "paused", "Agent görevi duraklatıldı.")
            except AgentError as error:
                self._set_status(str(error))
        self._update_agent_ui()

    def _resume_agent(self) -> None:
        if self._agent_controller and self._agent_controller.active_session:
            try:
                self._agent_controller.resume(self._agent_controller.active_session.session_id)
                session = self._agent_controller.session
                self._speak_agent_event(session.session_id, "resumed", "Agent görevi devam ediyor.")
            except AgentError as error:
                self._set_status(str(error))
        self._update_agent_ui()

    def _cancel_agent(self) -> None:
        if self._agent_controller and self._agent_controller.active_session:
            session_id = self._agent_controller.active_session.session_id
            self._agent_controller.cancel(session_id)
            self._speak_agent_event(session_id, "cancelled", "Agent görevi iptal edildi.")
        if self._voice_controller is not None:
            self.stop_voice()
        self._update_agent_ui()

    def _speak_agent_event(self, session_id: str, event_id: str, text: str, *, approval: bool = False, completion: bool = False) -> None:
        if self._voice_controller is None or self._user_settings_service is None:
            return
        settings = self._user_settings_service.current.agent
        allowed = (
            (approval and settings.speak_agent_approvals)
            or (completion and settings.speak_agent_completion)
            or (not approval and not completion and settings.speak_important_agent_events)
        )
        if not allowed:
            return
        session = self._agent_controller.session if self._agent_controller else None
        kind = self._agent_message_kind(session, approval=approval, completion=completion)
        spoken = self._agent_response_quality.for_speech(text, kind)
        try:
            self._voice_controller.speak_agent(spoken, session_id=session_id, event_id=f"{session_id}:{event_id}", approval=approval)
        except Exception:
            return

    def _prepare_agent_text(self, text: str, session=None, *, approval: bool = False) -> str:
        kind = self._agent_message_kind(session, approval=approval, completion=bool(session and session.terminal))
        return self._agent_response_quality.prepare(text, kind).text

    @staticmethod
    def _agent_message_kind(session=None, *, approval: bool = False, completion: bool = False) -> AgentMessageKind:
        if approval:
            return AgentMessageKind.APPROVAL
        if session is not None:
            if session.status is AgentSessionStatus.AWAITING_INPUT:
                return AgentMessageKind.CLARIFICATION
            if session.status is AgentSessionStatus.COMPLETED:
                return AgentMessageKind.COMPLETION
            if session.status is AgentSessionStatus.PARTIALLY_COMPLETED:
                return AgentMessageKind.PARTIAL
            if session.status in {AgentSessionStatus.FAILED, AgentSessionStatus.BLOCKED, AgentSessionStatus.UNCERTAIN}:
                return AgentMessageKind.FAILURE
            if session.status is AgentSessionStatus.INTERRUPTED:
                return AgentMessageKind.RECOVERY
            if session.status is AgentSessionStatus.AWAITING_PLAN_APPROVAL:
                return AgentMessageKind.PLAN_READY
        return AgentMessageKind.COMPLETION if completion else AgentMessageKind.PROGRESS

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
        self._agent_panel.setVisible(session is not None)
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
                self._notify_agent_event(
                    f"{progress.session_id}:{progress.status.value}:{progress.current}",
                    "Agent onay bekliyor",
                    "Bir Agent planı veya kalıcı adım açık onayını bekliyor.",
                )
            elif progress.status is AgentSessionStatus.PAUSED:
                self._tray_icon.setToolTip("Lina — Agent duraklatıldı")
            else:
                self._tray_icon.setToolTip(f"Lina — Agent görevi çalışıyor: {progress.current}/{progress.total}")
        if self._tray_icon is not None and session and session.terminal and session.session_id not in self._agent_notified_sessions:
            settings = self._user_settings_service.current.agent if self._user_settings_service else None
            if settings is None or settings.notify_agent_completion:
                title = "Agent görevi tamamlandı" if session.status in {AgentSessionStatus.COMPLETED, AgentSessionStatus.PARTIALLY_COMPLETED} else "Agent görevi sona erdi"
                self._notify_agent_event(
                    f"{session.session_id}:{session.status.value}",
                    title,
                    self._agent_controller.result_summary(),
                )
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
        self._live_panel.setVisible(active)
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
        self._request_document_attachments.pop(self._active_request_id, None)
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
        self._welcome_state.prompt_selected.connect(self._use_welcome_prompt)
        self._message_layout.insertWidget(0, self._welcome_state)

    def _use_welcome_prompt(self, prompt: str) -> None:
        self._composer.set_text(prompt)
        self._composer.input.setFocus()

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
        self._composer.set_screen_enabled(False)
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
        """Load one explicitly selected image or supported document."""
        selected_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Görsel veya Belge Seç",
            "",
            "Desteklenen dosyalar (*.png *.jpg *.jpeg *.webp *.bmp *.txt *.md *.py *.json *.csv *.pdf *.docx *.xlsx);;"
            "Görseller (*.png *.jpg *.jpeg *.webp *.bmp);;"
            "Belgeler (*.txt *.md *.py *.json *.csv *.pdf *.docx *.xlsx)",
        )
        if not selected_path:
            return
        path = Path(selected_path)
        if path.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            try:
                attachment = self._attachment_service.load(path)
            except FileTooLargeError:
                self._set_status("Belge boyut sınırını aşıyor.")
            except UnsupportedFileTypeError:
                self._set_status("Bu belge türü desteklenmiyor.")
            except ForbiddenFilePathError:
                self._set_status("Kimlik bilgisi veya anahtar dosyası eklenemez.")
            except DocumentExtractionError:
                self._set_status("Belgeden okunabilir içerik çıkarılamadı.")
            else:
                self._clear_screen_context()
                self._document_attachment = attachment
                self._composer.set_document_context(
                    attachment.display_name, attachment.format, attachment.truncated
                )
                self._set_status("Belge soruna eklenmeye hazır")
            return
        if not self._vision_enabled:
            self._set_status("Görsel eklemek için Vision özelliğini aç.")
            return
        try:
            context = self._image_loader.load(path)
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
        self._composer.set_screen_enabled(False)
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
        self._document_attachment = None
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
        if self._document_attachment is not None:
            QMessageBox.information(
                self, self._document_attachment.display_name,
                self._document_attachment.text[:4000],
            )
            return
        if self._screen_context is None:
            return
        try:
            dialog = ImagePreviewDialog(self._screen_context, self)
            dialog.exec()
        except Exception:
            self._set_status("Görsel önizlemesi oluşturulamadı.")

    def change_active_attachment(self) -> None:
        """Replace the current local image or screen capture."""
        if self._document_attachment is not None:
            self.handle_image_upload()
            return
        if self._screen_context is not None and self._screen_context.source == LOCAL_FILE:
            self.handle_image_upload()
            return
        self._screen_menu.popup(self._composer.screen_button.mapToGlobal(
            self._composer.screen_button.rect().bottomLeft()
        ))

    def _clear_screen_context(self) -> None:
        self._screen_context = None
        self._document_attachment = None
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
        self._composer.set_mic_enabled(True)
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
        document_attachment: DocumentAttachment | None,
        created_at: datetime,
    ) -> tuple[int, str, object]:
        try:
            if screen_context is None:
                response: object = self._conversation_service.handle_input(
                    ConversationInput(
                        text=message, created_at=created_at,
                        document_attachment=document_attachment,
                    )
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
            self._request_document_attachments.pop(request_id, None)
            return
        if request_id != self._active_request_id:
            self._request_screen_contexts.pop(request_id, None)
            self._request_document_attachments.pop(request_id, None)
            return
        if status == "error":
            request_screen_context = self._request_screen_contexts.pop(request_id, None)
            self._request_document_attachments.pop(request_id, None)
            self._handle_conversation_error(
                payload,
                vision_request=request_screen_context is not None,
                request_screen_context=request_screen_context,
            )
            return
        request_screen_context = self._request_screen_contexts.pop(request_id, None)
        request_document_attachment = self._request_document_attachments.pop(request_id, None)
        self._handle_conversation_result(
            payload, request_screen_context, request_document_attachment
        )

    def _handle_conversation_result(
        self,
        result: object,
        request_screen_context: ScreenContext | None = None,
        request_document_attachment: DocumentAttachment | None = None,
    ) -> None:
        self._remove_typing_indicator()
        if isinstance(result, ConversationResult):
            response: object = result.response
            consumed = result.attachment_consumed
            assistant_created_at = result.assistant_created_at
            response_safe_for_speech = result.response_safe_for_speech
        else:
            response = result
            consumed = False
            assistant_created_at = None
            response_safe_for_speech = True
        text = response.text if isinstance(response, ModelResponse) else str(response)
        self._auto_scroll_enabled = True
        self._append_assistant_message(text, created_at=assistant_created_at)
        if not response_safe_for_speech:
            pass
        elif request_screen_context is not None and request_screen_context.source == LIVE_CAMERA_CONTEXT:
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
        elif (
            consumed
            and request_document_attachment is not None
            and self._document_attachment is request_document_attachment
        ):
            self._clear_screen_context()
            self._set_status("Belge işlendi")
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
        self._composer.set_mic_enabled(
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
        preserved_scroll_value = self._scroll.verticalScrollBar().value()
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
        message.retry_requested.connect(self._retry_last_response)
        message.read_aloud_requested.connect(self._read_message_aloud)
        message.stop_speech_requested.connect(self.stop_voice)
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
        else:
            self._scroll.verticalScrollBar().setValue(preserved_scroll_value)
            QTimer.singleShot(
                0,
                lambda value=preserved_scroll_value: self._restore_scroll_position(value),
            )
        return message

    def _retry_last_response(self) -> None:
        if self._is_waiting or not self._input_history:
            return
        self._composer.set_text(self._input_history[-1])
        self.send_message()

    def _read_message_aloud(self, text: str) -> None:
        if self._voice_controller is None or not self._voice_controller.speak_response(text):
            self._set_status("Sesli yanıt başlatılamadı; yazılı cevap hazır.")

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

    def _set_status(self, text: str, *, generation: int | None = None, priority: StatusPriority = StatusPriority.ACTIVE) -> None:
        if self._unified_status.publish(text, generation=generation, priority=priority):
            self._status_label.setText(text)
            if hasattr(self, "_header_status_label"):
                self._header_status_label.setText(text)
            if hasattr(self, "_status_button"):
                self._status_button.setToolTip(
                    f"Lina Durumu: {text}. Model, mikrofon, ses, Agent ve Vision ayrıntılarını göster"
                )

    def _update_responsive_chrome(self, compact: bool) -> None:
        self._compact_chrome = compact
        self._set_inspector_button_state(opened=self._inspector.isVisible())
        if hasattr(self, "_notification_button"):
            self._refresh_notification_badge()

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
            self._composer.set_mic_enabled(True)
        else:
            self._speech_status.setText("Mic · kapalı")
            self._composer.set_mic_enabled(False)

    def _start_worker(self, worker: FunctionWorker) -> None:
        if getattr(self, "_closing", False):
            worker.cancel()
            return
        self._workers.add(worker)
        worker.signals.finished.connect(lambda: self._workers.discard(worker))
        self._thread_pool.start(worker)

    def _update_message_widths(self) -> None:
        viewport_width = self._scroll.viewport().width()
        width = int(min(self._message_width, max(320, viewport_width * 0.86)))
        outer_margin = max(0, (viewport_width - width) // 2)
        for row in self._message_rows:
            if row.layout() is not None:
                row.layout().setContentsMargins(outer_margin, 0, outer_margin, 0)
            message = getattr(row, "_message_widget", None)
            if isinstance(message, ChatMessageWidget):
                message.set_bubble_width(width)

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_sidebar"):
            self._apply_responsive_layout()
        self._update_message_widths()

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
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

    def _restore_scroll_position(self, value: int) -> None:
        if self._auto_scroll_enabled or self._pending_scroll_to_bottom:
            return
        self._is_programmatic_scroll = True
        try:
            self._scroll.verticalScrollBar().setValue(value)
        finally:
            self._is_programmatic_scroll = False

    def _handle_scroll_range_changed(self, _minimum: int, _maximum: int) -> None:
        if self._pending_scroll_to_top:
            QTimer.singleShot(0, self._scroll_to_top)
            return
        if self._pending_scroll_to_bottom:
            QTimer.singleShot(0, self._scroll_to_bottom)

    def _schedule_scroll_to_bottom(self) -> None:
        self._pending_scroll_to_bottom = True
        self._pending_scroll_to_top = False
        self._scroll_retry_count = 0
        self._message_container.layout().activate()
        for delay in (0, 25, 75, 150, 300, 600, 1000):
            QTimer.singleShot(delay, self._scroll_to_bottom)
        QTimer.singleShot(1100, self._finish_scroll_to_bottom)

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
        self._is_programmatic_scroll = True
        try:
            bar.setValue(bar.maximum())
        finally:
            self._is_programmatic_scroll = False

    def _finish_scroll_to_bottom(self) -> None:
        if not self._pending_scroll_to_bottom:
            return
        self._scroll_to_bottom()
        self._pending_scroll_to_bottom = False
        self._scroll_retry_count = 0
        self._auto_scroll_enabled = True

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
        self._persist_window_state()
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
        self._closing = True
        for worker in tuple(self._workers):
            worker.cancel()
        self._clear_screen_context()
        if self._live_vision_controller is not None:
            self._live_vision_controller.shutdown()
        if self._agent_controller is not None:
            self._agent_controller.shutdown()
        if self._codex_bridge is not None:
            self._codex_bridge.shutdown()
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
        wait_for_done = getattr(self._thread_pool, "waitForDone", None)
        if callable(wait_for_done):
            wait_for_done(1500)
        self._workers.clear()
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
