"""Selectable chat message bubble for Lina's Qt interface."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from lina.interfaces.qt.theme import TEXT_MUTED


class ChatMessageWidget(QWidget):
    """Render one user, assistant, or typing message."""

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        if role == "assistant":
            sender = QLabel("Lina", self)
            sender.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: 600;")
            layout.addWidget(sender)

        self.text_label = QLabel(text, self)
        self.text_label.setObjectName(
            "userBubble" if role == "user" else "assistantBubble"
        )
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
        layout.addWidget(self.text_label)

        metadata = QHBoxLayout()
        timestamp = QLabel(datetime.now().strftime("%H:%M"), self)
        timestamp.setObjectName("mutedLabel")
        metadata.addWidget(timestamp)
        metadata.addStretch(1)

        self.copy_button = QPushButton("Kopyala", self)
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setToolTip("Bu mesajı kopyala")
        self.copy_button.setAccessibleName("Mesajı kopyala")
        self.copy_button.clicked.connect(lambda: self.copy_requested.emit(self.raw_text))
        self.copy_button.setVisible(not typing)
        metadata.addWidget(self.copy_button)
        layout.addLayout(metadata)

    def set_message_font(self, family: str, size: int) -> None:
        """Update the visible message font for session accessibility controls."""
        self.text_label.setFont(QFont(family, size))

    def set_bubble_width(self, width: int) -> None:
        """Bound the bubble to a readable responsive width."""
        self.setMaximumWidth(max(320, width))
