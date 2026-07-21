"""Honest session sidebar for Lina's Qt interface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QFrame,
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
from lina.ui.design import design_tokens


class ConversationSearchInput(QLineEdit):
    """Search field with an explicit Escape-to-clear interaction."""

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.clear()
            self.clearFocus()
            event.accept()
            return
        super().keyPressEvent(event)


class ConversationCard(QPushButton):
    """Keyboard-accessible session card with a stable visual hierarchy."""

    def __init__(self, session: ConversationSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sessionButton")
        self.setText("")
        self._full_title = session.title
        self._activity_text = format_conversation_datetime(
            session.last_message_at or session.created_at
        )
        self._preview_text = " ".join(session.preview.split())
        self._session = session
        self._is_pinned = session.is_pinned
        self.setCheckable(True)
        self.setMinimumHeight(design_tokens("dark").controls.sidebar_item)
        self.setMaximumHeight(design_tokens("dark").controls.sidebar_item)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        card_layout = QHBoxLayout(self)
        card_layout.setContentsMargins(8, 7, 10, 7)
        card_layout.setSpacing(9)
        self.accent = QFrame(self)
        self.accent.setObjectName("sessionAccent")
        self.accent.setFixedSize(3, 38)
        self.accent.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card_layout.addWidget(self.accent, 0, Qt.AlignmentFlag.AlignVCenter)

        self.icon_label = QLabel(self)
        self.icon_label.setObjectName("sessionCardIcon")
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_name = "pin" if session.is_pinned else "chat"
        self.icon_label.setPixmap(standard_icon(self, icon_name, 16).pixmap(16, 16))
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card_layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(3)
        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(6)
        self.title_label = QLabel(session.title, self)
        self.title_label.setObjectName("sessionCardTitle")
        self.activity_label = QLabel(self._activity_text, self)
        self.activity_label.setObjectName("sessionCardTime")
        heading.addWidget(self.title_label, 1)
        heading.addWidget(self.activity_label)
        content.addLayout(heading)
        self.preview_label = QLabel(self._preview_text or "Henüz mesaj yok", self)
        self.preview_label.setObjectName("sessionCardPreview")
        content.addWidget(self.preview_label)
        for label in (self.title_label, self.activity_label, self.preview_label):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card_layout.addLayout(content, 1)
        self._refresh_text()

    def _refresh_text(self) -> None:
        available = max(80, self.width() - 82 - self.activity_label.sizeHint().width())
        self.title_label.setText(
            QFontMetrics(self.title_label.font()).elidedText(
                self._full_title, Qt.TextElideMode.ElideRight, available
            )
        )
        preview_width = max(100, self.width() - 72)
        self.preview_label.setText(
            QFontMetrics(self.preview_label.font()).elidedText(
                self._preview_text or "Henüz mesaj yok",
                Qt.TextElideMode.ElideRight,
                preview_width,
            )
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_text()


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

    WIDTH = design_tokens("dark").layout.navigation_expanded
    COLLAPSED_WIDTH = design_tokens("dark").layout.navigation_collapsed

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
        layout.setContentsMargins(18, 22, 16, 16)
        layout.setSpacing(12)
        self._root_layout = layout

        self._collapsed = False
        brand_row = QWidget(self)
        brand_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        brand_layout = QHBoxLayout(brand_row)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(9)
        self._brand_layout = brand_layout
        self.logo_label = QLabel(brand_row)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        self._logo_pixmap = pixmap
        if not pixmap.isNull():
            self.logo_label.setPixmap(
                pixmap.scaled(
                    40,
                    40,
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
        self.collapse_button = QPushButton("", brand_row)
        self.collapse_button.setObjectName("sidebarCollapseButton")
        self.collapse_button.setAccessibleName("Sol navigasyonu daralt")
        self.collapse_button.setToolTip("Sol navigasyonu daralt")
        self.collapse_button.setFixedSize(32, 32)
        self.collapse_button.setIcon(standard_icon(self, "collapse"))
        brand_layout.addWidget(self.collapse_button)
        layout.addWidget(brand_row)

        self.subtitle_label = QLabel("Yerel çalışma alanı", self)
        self.subtitle_label.setObjectName("mutedLabel")
        self.subtitle_label.hide()
        layout.addWidget(self.subtitle_label)
        self.version_label = QLabel(version, self)
        self.version_label.setObjectName("mutedLabel")
        self.version_label.hide()

        self.new_chat_button = QPushButton("Yeni sohbet", self)
        self.new_chat_button.setObjectName("primaryNavigationButton")
        self.new_chat_button.setAccessibleName("Yeni sohbet")
        self.new_chat_button.setIcon(standard_icon(self, "add"))
        layout.addWidget(self.new_chat_button)

        self.session_panel = QWidget(self)
        self.session_panel.setObjectName("sidebarSessionPanel")
        session_layout = QVBoxLayout(self.session_panel)
        session_layout.setContentsMargins(0, 6, 0, 0)
        session_layout.setSpacing(4)
        section = QLabel("BU OTURUM", self.session_panel)
        section.setObjectName("mutedLabel")
        section.hide()
        session_layout.addWidget(section)
        self.session_title = QLabel("Yeni Sohbet", self.session_panel)
        self.session_title.setWordWrap(True)
        self.session_title.hide()
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
        mode_label = QLabel("● Yerel çalışma", self.status_panel)
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
        for button, name in (
            (self.agent_tasks_button, "Agent görevleri"),
            (self.notification_button, "Bildirimler"),
        ):
            button.setObjectName("sidebarShortcut")
            button.setToolTip(name)
            button.setAccessibleName(name)
            shortcut_layout.addWidget(button)
        self.agent_tasks_button.setIcon(standard_icon(self, "agent"))
        self.notification_button.setIcon(standard_icon(self, "notifications"))
        layout.addWidget(self.shortcuts)
        self.shortcuts.hide()

        self.settings_button = QPushButton("Ayarlar", self)
        self.settings_button.setObjectName("sidebarShortcut")
        self.settings_button.setIcon(standard_icon(self, "settings"))
        self.settings_button.setToolTip("Ayarlar · Ctrl+,")
        self.settings_button.setAccessibleName("Ayarlar")
        self.settings_button.setAccessibleDescription(
            "Tema, modeller, ses, görsel anlama ve gizlilik ayarlarını aç"
        )
        layout.addWidget(self.settings_button)

        self.new_chat_button.clicked.connect(self.new_chat_requested)

        self.search_input = ConversationSearchInput(self)
        self.search_input.setObjectName("conversationSearchInput")
        self.search_input.setPlaceholderText("Sohbetlerde ara…")
        self.search_input.setAccessibleName("Sohbetlerde ara")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(
            standard_icon(self, "search"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
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
        self._root_layout.setContentsMargins(
            7 if collapsed else 18,
            18 if collapsed else 22,
            7 if collapsed else 16,
            14 if collapsed else 16,
        )
        self._brand_layout.setSpacing(2 if collapsed else 9)
        for widget in (self.title_label, self.search_input, self.session_panel):
            widget.setVisible(not collapsed)
        self.subtitle_label.hide()
        self.filter_combo.hide()
        self.status_panel.hide()
        self.shortcuts.hide()
        self.logo_label.show()
        if not self._logo_pixmap.isNull():
            mark_size = 24 if collapsed else 40
            self.logo_label.setPixmap(
                self._logo_pixmap.scaled(
                    mark_size,
                    mark_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.logo_label.setFixedSize(mark_size, mark_size)
        self.collapse_button.setFixedSize(24 if collapsed else 32, 24 if collapsed else 32)
        self.collapse_button.setIcon(standard_icon(self, "expand" if collapsed else "collapse", 16))
        self.new_chat_button.setText("" if collapsed else "Yeni sohbet")
        self.new_chat_button.setToolTip("Yeni sohbet")
        self.collapse_button.setToolTip("Sol navigasyonu genişlet" if collapsed else "Sol navigasyonu daralt")
        self.collapse_button.setAccessibleName(self.collapse_button.toolTip())
        for button in (self.agent_tasks_button, self.notification_button):
            button.setText("" if collapsed else button.toolTip())
        self.settings_button.setText("" if collapsed else "Ayarlar")
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
        button = ConversationCard(session, self.session_list)
        button.setToolTip(session.title)
        button.setChecked(session.id == active_id)
        button.accent.setProperty("active", session.id == active_id)
        button.setAccessibleName(f"Sohbet: {session.title}")
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
        for button in self.session_list.findChildren(ConversationCard, "sessionButton"):
            button._refresh_text()
            if button._is_pinned:
                button.setToolTip(f"Sabitlenmiş sohbet\n{button._full_title}")
            else:
                button.setToolTip(button._full_title)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_session_button_titles()
