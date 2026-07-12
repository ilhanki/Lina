"""Honest session sidebar for Lina's Qt interface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QComboBox,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lina.conversations.models import ConversationSession
from lina.conversations.models import ConversationSearchResult
from lina.interfaces.qt.formatting import format_conversation_datetime


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

    WIDTH = 248

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

        self.logo_label = QLabel(self)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        if not pixmap.isNull():
            self.logo_label.setPixmap(
                pixmap.scaled(
                    56,
                    56,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.logo_label.setText("L")
        layout.addWidget(self.logo_label)

        title = QLabel("Lina", self)
        title.setStyleSheet("font-size: 17pt; font-weight: 700;")
        layout.addWidget(title)
        subtitle = QLabel("Local AI Assistant", self)
        subtitle.setObjectName("mutedLabel")
        layout.addWidget(subtitle)
        version_label = QLabel(version, self)
        version_label.setObjectName("mutedLabel")
        layout.addWidget(version_label)

        self.new_chat_button = QPushButton("Yeni Sohbet", self)
        self.new_chat_button.setObjectName("accentButton")
        self.new_chat_button.setAccessibleName("Yeni sohbet")
        layout.addWidget(self.new_chat_button)

        self.session_panel = QWidget(self)
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
        self.session_scroll.setWidgetResizable(True)
        self.session_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.session_list = QWidget(self.session_scroll)
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

        self.new_chat_button.clicked.connect(self.new_chat_requested)

        self.search_input = ConversationSearchInput(self)
        self.search_input.setObjectName("conversationSearchInput")
        self.search_input.setPlaceholderText("Sohbetlerde ara...")
        self.search_input.setAccessibleName("Sohbetlerde ara")
        layout.insertWidget(5, self.search_input)
        self.filter_combo = QComboBox(self)
        self.filter_combo.setObjectName("conversationFilter")
        self.filter_combo.setAccessibleName("Sohbet görünümü")
        self.filter_combo.addItem("Sohbetler", "chats")
        self.filter_combo.addItem("Sabitlenenler", "pinned")
        self.filter_combo.addItem("Arşiv", "archive")
        layout.insertWidget(6, self.filter_combo)
        self.search_input.textChanged.connect(self.search_changed)
        self.filter_combo.currentIndexChanged.connect(
            lambda _index: self.view_changed.emit(str(self.filter_combo.currentData()))
        )

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
            button.setMinimumHeight(64)
            button.setMaximumHeight(64)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            button._full_title = session.title  # type: ignore[attr-defined]
            button._activity_text = format_conversation_datetime(  # type: ignore[attr-defined]
                session.last_message_at or session.created_at
            )
            button._session = session  # type: ignore[attr-defined]
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
            button.setMinimumHeight(76)
            button.setMaximumHeight(76)
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
            button.setText(f"{elided_title}\n{activity}")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_session_button_titles()
