"""Honest session sidebar for Lina's Qt interface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class SidebarWidget(QWidget):
    """Show branding, current session, and compact local status."""

    new_chat_requested = Signal()

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
        note = QLabel("Kalıcı sohbet geçmişi henüz aktif değil.", self.session_panel)
        note.setWordWrap(True)
        note.setObjectName("mutedLabel")
        session_layout.addWidget(note)
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
