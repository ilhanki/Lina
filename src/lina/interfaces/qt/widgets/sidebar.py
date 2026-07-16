"""Honest session sidebar for Lina's Qt interface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from lina.conversations.models import ConversationSession
from lina.conversations.models import ConversationSearchResult
from lina.interfaces.qt.formatting import format_conversation_datetime
from lina.ui.design import standard_icon


class ConversationSearchInput(QLineEdit):
    """Search field with an explicit Escape-to-clear interaction."""

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.clear()
            self.clearFocus()
            event.accept()
            return
        super().keyPressEvent(event)


class SidebarWidget(QWidget):
    """Show branding, current session, and compact local status."""

    new_chat_requested = Signal()
    session_selected = Signal(int)
    session_rename_requested = Signal(int)
    session_delete_requested = Signal(int)
    session_pin_requested = Signal(int, bool)
    session_archive_requested = Signal(int, bool)
    search_changed = Signal(str)
    view_changed = Signal(str)
    collapsed_changed = Signal(bool)
    agent_tasks_requested = Signal()
    notifications_requested = Signal()
    settings_requested = Signal()
    local_status_requested = Signal()

    WIDTH = 264
    COLLAPSED_WIDTH = 64

    def __init__(
        self,
        logo_path: Path,
        version: str,
        model_name: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(self.WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self._collapsed = False
        brand_row = QWidget(self)
        brand_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        brand_layout = QHBoxLayout(brand_row)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(8)
        self.logo_label = QLabel(brand_row)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        if not pixmap.isNull():
            self.logo_label.setPixmap(
                pixmap.scaled(
                    32,
                    32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.logo_label.setText("L")
        brand_layout.addWidget(self.logo_label)

        self.title_label = QLabel("Lina", brand_row)
        self.title_label.setObjectName("sidebarTitle")
        brand_layout.addWidget(self.title_label, 1)
        self.collapse_button = QPushButton("‹", brand_row)
        self.collapse_button.setObjectName("sidebarCollapseButton")
        self.collapse_button.setAccessibleName("Sol navigasyonu daralt")
        self.collapse_button.setToolTip("Sol navigasyonu daralt")
        self.collapse_button.setFixedSize(32, 32)
        brand_layout.addWidget(self.collapse_button)
        layout.addWidget(brand_row)

        self.subtitle_label = QLabel("Yerel çalışma alanı", self)
        self.subtitle_label.setObjectName("mutedLabel")
        self.subtitle_label.hide()
        layout.addWidget(self.subtitle_label)
        self.version_label = QLabel(version, self)
        self.version_label.setObjectName("mutedLabel")
        self.version_label.hide()

        self.new_chat_button = QPushButton("Yeni Sohbet", self)
        self.new_chat_button.setObjectName("accentButton")
        self.new_chat_button.setAccessibleName("Yeni sohbet")
        self.new_chat_button.setIcon(standard_icon(self, "add"))
        layout.addWidget(self.new_chat_button)

        self.session_panel = QWidget(self)
        self.session_panel.setObjectName("sidebarSessionPanel")
        session_layout = QVBoxLayout(self.session_panel)
        session_layout.setContentsMargins(0, 12, 0, 0)
        session_layout.setSpacing(6)
        section = QLabel("BU OTURUM", self.session_panel)
        section.setObjectName("mutedLabel")
        session_layout.addWidget(section)
        self.session_title = QLabel("Yeni Sohbet", self.session_panel)
        self.session_title.setWordWrap(True)
        session_layout.addWidget(self.session_title)
        self.session_note = QLabel("Henüz kayıtlı sohbet yok.", self.session_panel)
        self.session_note.setWordWrap(True)
        self.session_note.setObjectName("mutedLabel")
        session_layout.addWidget(self.session_note)

        self.session_scroll = QScrollArea(self.session_panel)
        self.session_scroll.setObjectName("sidebarConversationScroll")
        self.session_scroll.viewport().setObjectName("sidebarConversationViewport")
        self.session_scroll.setWidgetResizable(True)
        self.session_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.session_list = QWidget(self.session_scroll)
        self.session_list.setObjectName("sidebarConversationList")
        self.session_list_layout = QVBoxLayout(self.session_list)
        self.session_list_layout.setContentsMargins(0, 4, 0, 0)
        self.session_list_layout.setSpacing(4)
        self.session_list_layout.addStretch(1)
        self.session_scroll.setWidget(self.session_list)
        session_layout.addWidget(self.session_scroll, 1)
        self.session_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        layout.addWidget(self.session_panel, 1)

        self.status_panel = QWidget(self)
        self.status_panel.setObjectName("sidebarStatusPanel")
        status_layout = QVBoxLayout(self.status_panel)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)
        mode_label = QLabel("● Local Mode", self.status_panel)
        mode_label.setObjectName("mutedLabel")
        status_layout.addWidget(mode_label)
        self.local_status = QLabel(f"{model_name}\nVeriler cihazında işlenir", self)
        self.local_status.setObjectName("mutedLabel")
        self.local_status.setWordWrap(True)
        status_layout.addWidget(self.local_status)
        layout.addWidget(self.status_panel)
        self.status_panel.hide()

        self._collapsed_spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        layout.addItem(self._collapsed_spacer)

        self.shortcuts = QWidget(self)
        self.shortcuts.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        shortcut_layout = QVBoxLayout(self.shortcuts)
        shortcut_layout.setContentsMargins(0, 0, 0, 0)
        shortcut_layout.setSpacing(4)
        self.agent_tasks_button = QPushButton("Agent görevleri", self.shortcuts)
        self.notification_button = QPushButton("Bildirimler", self.shortcuts)
        self.settings_button = QPushButton("Ayarlar", self.shortcuts)
        for button, name in (
            (self.agent_tasks_button, "Agent görevleri"),
            (self.notification_button, "Bildirimler"),
            (self.settings_button, "Ayarlar"),
        ):
            button.setObjectName("sidebarShortcut")
            button.setToolTip(name)
            button.setAccessibleName(name)
            shortcut_layout.addWidget(button)
        self.agent_tasks_button.setIcon(standard_icon(self, "agent"))
        self.notification_button.setIcon(standard_icon(self, "notifications"))
        self.settings_button.setIcon(standard_icon(self, "settings"))
        layout.addWidget(self.shortcuts)
        self.shortcuts.hide()

        self.new_chat_button.clicked.connect(self.new_chat_requested)

        self.search_input = ConversationSearchInput(self)
        self.search_input.setObjectName("conversationSearchInput")
        self.search_input.setPlaceholderText("Sohbetlerde ara...")
        self.search_input.setAccessibleName("Sohbetlerde ara")
        layout.insertWidget(3, self.search_input)
        self.filter_combo = QComboBox(self)
        self.filter_combo.setObjectName("conversationFilter")
        self.filter_combo.setAccessibleName("Sohbet görünümü")
        self.filter_combo.addItem("Sohbetler", "chats")
        self.filter_combo.addItem("Sabitlenenler", "pinned")
        self.filter_combo.addItem("Arşiv", "archive")
        self.filter_combo.hide()
        layout.insertWidget(4, self.filter_combo)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(
            lambda: self.search_changed.emit(self.search_input.text())
        )
        self.search_input.textChanged.connect(lambda _text: self._search_timer.start())
        self.filter_combo.currentIndexChanged.connect(
            lambda _index: self.view_changed.emit(str(self.filter_combo.currentData()))
        )
        self.collapse_button.clicked.connect(self.toggle_collapsed)
        self.agent_tasks_button.clicked.connect(self.agent_tasks_requested)
        self.notification_button.clicked.connect(self.notifications_requested)
        self.settings_button.clicked.connect(self.settings_requested)
        self.status_panel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_panel.mousePressEvent = lambda _event: self.local_status_requested.emit()  # type: ignore[method-assign]

    @property
    def collapsed(self) -> bool:
        return self._collapsed

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed
        self._collapsed_spacer.changeSize(
            0,
            1 if collapsed else 0,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding if collapsed else QSizePolicy.Policy.Minimum,
        )
        self.layout().invalidate()
        self.setFixedWidth(self.COLLAPSED_WIDTH if collapsed else self.WIDTH)
        for widget in (self.title_label, self.search_input, self.session_panel):
            widget.setVisible(not collapsed)
        self.subtitle_label.hide()
        self.filter_combo.hide()
        self.status_panel.hide()
        self.shortcuts.hide()
        self.logo_label.setVisible(not collapsed)
        self.new_chat_button.setText("" if collapsed else "Yeni Sohbet")
        self.new_chat_button.setToolTip("Yeni sohbet")
        self.collapse_button.setText("›" if collapsed else "‹")
        self.collapse_button.setToolTip("Sol navigasyonu genişlet" if collapsed else "Sol navigasyonu daralt")
        self.collapse_button.setAccessibleName(self.collapse_button.toolTip())
        for button in (self.agent_tasks_button, self.notification_button, self.settings_button):
            button.setText("" if collapsed else button.toolTip())
        self.collapsed_changed.emit(collapsed)

    def set_session_title(self, title: str) -> None:
        self.session_title.setText(title)

    def set_sessions(
        self,
        sessions: tuple[ConversationSession, ...],
        active_id: int | None = None,
        groups: tuple[tuple[str, tuple[ConversationSession, ...]], ...] = (),
    ) -> None:
        """Render real persisted sessions in the sidebar."""
        while self.session_list_layout.count():
            item = self.session_list_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.session_note.setText(
            "Henüz kayıtlı sohbet yok." if not sessions else ""
        )
        if not groups:
            groups = (("Sohbetler", sessions),)
        for group_label, group_sessions in groups:
            if not group_sessions:
                continue
            heading = QLabel(group_label, self.session_list)
            heading.setObjectName("conversationGroupHeading")
            self.session_list_layout.addWidget(heading)
            for session in group_sessions:
                self._add_session_button(session, active_id)
        self.session_list_layout.addStretch(1)
        self._refresh_session_button_titles()

    def _add_session_button(
        self,
        session: ConversationSession,
        active_id: int | None,
    ) -> None:
            button = QPushButton(session.title, self.session_list)
            button.setObjectName("sessionButton")
            button.setToolTip(session.title)
            button.setMinimumHeight(56)
            button.setMaximumHeight(56)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            button._full_title = session.title  # type: ignore[attr-defined]
            button._activity_text = format_conversation_datetime(  # type: ignore[attr-defined]
                session.last_message_at or session.created_at
            )
            button._session = session  # type: ignore[attr-defined]
            button._is_pinned = session.is_pinned  # type: ignore[attr-defined]
            button.setCheckable(True)
            button.setChecked(session.id == active_id)
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda position, conversation=session: self._show_session_menu(
                    conversation, button, position
                )
            )
            button.clicked.connect(
                lambda _checked=False, conversation_id=session.id: self.session_selected.emit(
                    conversation_id or 0
                )
            )
            self.session_list_layout.addWidget(button)

    def set_search_results(
        self,
        results: tuple[ConversationSearchResult, ...],
    ) -> None:
        """Render plain-text conversation search results."""
        while self.session_list_layout.count():
            item = self.session_list_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        if not results:
            empty = QLabel("Sonuç bulunamadı.", self.session_list)
            empty.setObjectName("conversationEmptyState")
            empty.setWordWrap(True)
            self.session_list_layout.addWidget(empty)
        for result in results:
            button = QPushButton(self.session_list)
            button.setObjectName("conversationSearchResult")
            button.setMinimumHeight(68)
            button.setMaximumHeight(68)
            button.setToolTip(result.title)
            button.setText(
                f"{result.title}\n{result.snippet}\n"
                f"{format_conversation_datetime(result.last_activity_at)}"
            )
            button.clicked.connect(
                lambda _checked=False, conversation_id=result.conversation_id: self.session_selected.emit(
                    conversation_id
                )
            )
            self.session_list_layout.addWidget(button)
        self.session_list_layout.addStretch(1)

    def reset_view_controls(self) -> None:
        self.search_input.clear()
        self.filter_combo.setCurrentIndex(0)

    def set_persistence_note(self, text: str) -> None:
        """Show a short persistence state without hiding the session list."""
        self.session_note.setText(text)

    def _show_session_menu(
        self,
        session: ConversationSession,
        button: QPushButton,
        position,
    ) -> None:
        menu = QMenu(button)
        rename_action = menu.addAction("Yeniden Adlandır")
        pin_action = menu.addAction(
            "Sabitlemeyi Kaldır" if session.is_pinned else "Sabitle"
        )
        archive_action = menu.addAction(
            "Arşivden Çıkar" if session.is_archived else "Arşivle"
        )
        menu.addSeparator()
        delete_action = menu.addAction("Sil")
        selected = menu.exec(button.mapToGlobal(position))
        if selected is rename_action:
            self.session_rename_requested.emit(session.id or 0)
        elif selected is pin_action:
            self.session_pin_requested.emit(session.id or 0, not session.is_pinned)
        elif selected is archive_action:
            self.session_archive_requested.emit(session.id or 0, not session.is_archived)
        elif selected is delete_action:
            self.session_delete_requested.emit(session.id or 0)

    def _refresh_session_button_titles(self) -> None:
        available_width = max(120, self.session_list.width() - 24)
        for button in self.session_list.findChildren(QPushButton, "sessionButton"):
            title = getattr(button, "_full_title", button.text())
            elided_title = QFontMetrics(button.font()).elidedText(
                title,
                Qt.TextElideMode.ElideRight,
                available_width,
            )
            activity = getattr(button, "_activity_text", "")
            prefix = "● " if getattr(button, "_is_pinned", False) else ""
            button.setText(f"{prefix}{elided_title}\n{activity}")
            if getattr(button, "_is_pinned", False):
                button.setToolTip(f"Sabitlenmiş sohbet\n{title}")
            else:
                button.setToolTip(title)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_session_button_titles()
