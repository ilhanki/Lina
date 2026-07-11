"""Selectable chat message bubble for Lina's Qt interface."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lina.interfaces.qt.theme import SPACE_MD, SPACE_SM, TEXT_MUTED


MIN_BUBBLE_WIDTH = 380


class ChatMessageWidget(QWidget):
    """Render one user, assistant, or typing message as a cohesive bubble."""

    copy_requested = Signal(str)

    def __init__(
        self,
        role: str,
        text: str,
        font_family: str,
        font_size: int,
        typing: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.role = role
        self.raw_text = text
        self.typing = typing
        self.setObjectName("chatMessage")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE_SM)

        self.sender_label = QLabel("Lina", self)
        self.sender_label.setObjectName("senderLabel")
        self.sender_label.setVisible(role == "assistant")
        layout.addWidget(self.sender_label)

        self.bubble = QWidget(self)
        self.bubble.setObjectName("userBubble" if role == "user" else "assistantBubble")
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(16, 14, 16, 10)
        bubble_layout.setSpacing(SPACE_MD)
        layout.addWidget(self.bubble)

        self.text_label = QLabel(text, self.bubble)
        self.text_label.setObjectName("bubbleText")
        self.text_label.setWordWrap(True)
        self.text_label.setTextFormat(Qt.TextFormat.PlainText)
        self.text_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.text_label.setFont(QFont(font_family, font_size))
        self.text_label.setAccessibleName(
            "Kullanıcı mesajı" if role == "user" else "Lina mesajı"
        )
        bubble_layout.addWidget(self.text_label)

        metadata = QHBoxLayout()
        metadata.setContentsMargins(0, 0, 0, 0)
        metadata.setSpacing(SPACE_SM)
        self.timestamp_label = QLabel(datetime.now().strftime("%H:%M"), self.bubble)
        self.timestamp_label.setObjectName("mutedLabel")
        self.timestamp_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9pt;")
        metadata.addWidget(self.timestamp_label)
        metadata.addStretch(1)

        self.copy_button = QPushButton("Kopyala", self.bubble)
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setToolTip("Bu mesajı kopyala")
        self.copy_button.setAccessibleName("Mesajı kopyala")
        self.copy_button.clicked.connect(lambda: self.copy_requested.emit(self.raw_text))
        self.copy_button.setVisible(not typing)
        metadata.addWidget(self.copy_button)
        bubble_layout.addLayout(metadata)

    def set_message_font(self, family: str, size: int) -> None:
        """Update the visible message font for session accessibility controls."""
        self.text_label.setFont(QFont(family, size))

    def set_bubble_width(self, width: int) -> None:
        """Bound the bubble to a readable responsive width."""
        bounded_width = max(320, width)
        minimum_width = min(MIN_BUBBLE_WIDTH, bounded_width)
        self.setMaximumWidth(bounded_width)
        self.bubble.setMaximumWidth(bounded_width)
        self.setMinimumWidth(minimum_width)
        self.bubble.setMinimumWidth(minimum_width)
