"""Honest session sidebar for Lina's Qt interface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lina.conversations.models import ConversationSession


class SidebarWidget(QWidget):
    """Show branding, current session, and compact local status."""

    new_chat_requested = Signal()
    session_selected = Signal(int)
    session_rename_requested = Signal(int)
    session_delete_requested = Signal(int)

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
        layout.addWidget(self.session_panel)
        layout.addStretch(1)

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

    def set_session_title(self, title: str) -> None:
        self.session_title.setText(title)

    def set_sessions(
        self,
        sessions: tuple[ConversationSession, ...],
        active_id: int | None = None,
    ) -> None:
        """Render real persisted sessions in the sidebar."""
        while self.session_list_layout.count() > 1:
            item = self.session_list_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.session_note.setText(
            "Henüz kayıtlı sohbet yok." if not sessions else ""
        )
        for session in sessions:
            button = QPushButton(session.title, self.session_list)
            button.setObjectName("sessionButton")
            button.setToolTip(session.title)
            button.setCheckable(True)
            button.setChecked(session.id == active_id)
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda position, conversation_id=session.id: self._show_session_menu(
                    conversation_id or 0, button, position
                )
            )
            button.clicked.connect(
                lambda _checked=False, conversation_id=session.id: self.session_selected.emit(
                    conversation_id or 0
                )
            )
            self.session_list_layout.insertWidget(
                self.session_list_layout.count() - 1, button
            )

    def set_persistence_note(self, text: str) -> None:
        """Show a short persistence state without hiding the session list."""
        self.session_note.setText(text)

    def _show_session_menu(self, conversation_id: int, button: QPushButton, position) -> None:
        menu = QMenu(button)
        rename_action = menu.addAction("Yeniden Adlandır")
        delete_action = menu.addAction("Sil")
        selected = menu.exec(button.mapToGlobal(position))
        if selected is rename_action:
            self.session_rename_requested.emit(conversation_id)
        elif selected is delete_action:
            self.session_delete_requested.emit(conversation_id)
