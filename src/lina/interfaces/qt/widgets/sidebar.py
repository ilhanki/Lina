"""Collapsible, honest session sidebar for Lina's Qt interface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SidebarWidget(QWidget):
    """Show branding, current session, and presentation controls."""

    new_chat_requested = Signal()
    collapse_requested = Signal()
    font_decrease_requested = Signal()
    font_increase_requested = Signal()

    EXPANDED_WIDTH = 270
    COLLAPSED_WIDTH = 72

    def __init__(
        self,
        logo_path: Path,
        version: str,
        model_name: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._expanded = True
        self.setFixedWidth(self.EXPANDED_WIDTH)
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
                    64,
                    64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.logo_label.setText("L")
        layout.addWidget(self.logo_label)

        self.details = QWidget(self)
        details_layout = QVBoxLayout(self.details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(6)
        title = QLabel("Lina", self.details)
        title.setStyleSheet("font-size: 18pt; font-weight: 700;")
        details_layout.addWidget(title)
        subtitle = QLabel("Local AI Assistant", self.details)
        subtitle.setObjectName("mutedLabel")
        details_layout.addWidget(subtitle)
        version_label = QLabel(version, self.details)
        version_label.setObjectName("mutedLabel")
        details_layout.addWidget(version_label)
        layout.addWidget(self.details)

        self.new_chat_button = QPushButton("Yeni Sohbet", self)
        self.new_chat_button.setObjectName("accentButton")
        self.new_chat_button.setAccessibleName("Yeni sohbet")
        layout.addWidget(self.new_chat_button)

        self.session_panel = QWidget(self)
        session_layout = QVBoxLayout(self.session_panel)
        session_layout.setContentsMargins(0, 12, 0, 0)
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
        self.local_status = QLabel(f"Local mode\n{model_name}\nVeriler yerelde işlenir", self)
        self.local_status.setObjectName("mutedLabel")
        self.local_status.setWordWrap(True)
        status_layout.addWidget(self.local_status)
        layout.addWidget(self.status_panel)

        controls = QHBoxLayout()
        self.font_decrease_button = QPushButton("A−", self)
        self.font_decrease_button.setToolTip("Yazıyı küçült")
        self.font_increase_button = QPushButton("A+", self)
        self.font_increase_button.setToolTip("Yazıyı büyüt")
        self.collapse_button = QPushButton("‹", self)
        self.collapse_button.setToolTip("Sidebar'ı daralt veya genişlet")
        controls.addWidget(self.font_decrease_button)
        controls.addWidget(self.font_increase_button)
        controls.addWidget(self.collapse_button)
        layout.addLayout(controls)

        self.new_chat_button.clicked.connect(self.new_chat_requested)
        self.font_decrease_button.clicked.connect(self.font_decrease_requested)
        self.font_increase_button.clicked.connect(self.font_increase_requested)
        self.collapse_button.clicked.connect(self.collapse_requested)

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def toggle(self) -> None:
        self._expanded = not self._expanded
        width = self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH
        self.setFixedWidth(width)
        self.details.setVisible(self._expanded)
        self.session_panel.setVisible(self._expanded)
        self.status_panel.setVisible(self._expanded)
        self.font_decrease_button.setVisible(self._expanded)
        self.font_increase_button.setVisible(self._expanded)
        self.new_chat_button.setText("Yeni Sohbet" if self._expanded else "+")
        self.collapse_button.setText("‹" if self._expanded else "›")

    def set_session_title(self, title: str) -> None:
        self.session_title.setText(title)
