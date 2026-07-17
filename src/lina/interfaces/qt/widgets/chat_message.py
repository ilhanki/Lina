"""Selectable chat message bubble for Lina's Qt interface."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lina.interfaces.qt.theme import SPACE_MD, SPACE_SM
from lina.interfaces.qt.formatting import format_message_time
from lina.screen.models import ScreenContext


MIN_ASSISTANT_WIDTH = 520
MAX_ASSISTANT_WIDTH = 720
MIN_USER_WIDTH = 320
MAX_USER_WIDTH = 560
MAX_PREVIEW_WIDTH = 560
MAX_PREVIEW_HEIGHT = 320


class ChatMessageWidget(QWidget):
    """Render one user, assistant, or typing message as a cohesive bubble."""

    copy_requested = Signal(str)
    retry_requested = Signal()
    read_aloud_requested = Signal(str)
    stop_speech_requested = Signal()
    image_preview_requested = Signal(object)
    reanalyze_requested = Signal(object)

    def __init__(
        self,
        role: str,
        text: str,
        font_family: str,
        font_size: int,
        typing: bool = False,
        image_bytes: bytes | None = None,
        visual_context: ScreenContext | None = None,
        created_at: datetime | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.role = role
        self.raw_text = text
        self.typing = typing
        self.visual_context = visual_context
        self.created_at = created_at or datetime.now().astimezone()
        self.setObjectName("chatMessage")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE_SM)

        self.sender_label = QLabel("Lina düşünüyor" if typing else "Lina", self)
        self.sender_label.setObjectName("senderLabel")
        self.sender_label.setVisible(role == "assistant" and typing)
        layout.addWidget(self.sender_label)

        self.bubble = QWidget(self)
        self.bubble.setObjectName("userBubble" if role == "user" else "assistantBubble")
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(18, 14, 18, 11)
        bubble_layout.setSpacing(SPACE_MD)
        layout.addWidget(self.bubble)

        self.image_label: QLabel | None = None
        self._preview_pixmap: QPixmap | None = None
        if image_bytes:
            source_pixmap = QPixmap()
            if source_pixmap.loadFromData(image_bytes):
                self._preview_pixmap = source_pixmap.scaled(
                    MAX_PREVIEW_WIDTH,
                    MAX_PREVIEW_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.image_label = QLabel(self.bubble)
                self.image_label.setObjectName("messageImagePreview")
                self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.image_label.setAccessibleName("Mesaja eklenen görsel önizlemesi")
                self.image_label.setPixmap(self._preview_pixmap)
                self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)
                self.image_label.mousePressEvent = self._handle_image_click  # type: ignore[method-assign]
                bubble_layout.addWidget(self.image_label)

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

        self.action_bar = QWidget(self.bubble)
        self.action_bar.setObjectName("messageActions")
        metadata = QHBoxLayout(self.action_bar)
        metadata.setContentsMargins(0, 0, 0, 0)
        metadata.setSpacing(SPACE_SM)
        self.timestamp_label = QLabel(format_message_time(self.created_at), self.bubble)
        self.timestamp_label.setObjectName("messageTimestamp")
        metadata.addWidget(self.timestamp_label)
        metadata.addStretch(1)

        self.copy_button = QPushButton("Kopyala", self.action_bar)
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setToolTip("Bu mesajı kopyala")
        self.copy_button.setAccessibleName("Mesajı kopyala")
        self.copy_button.clicked.connect(lambda: self.copy_requested.emit(self.raw_text))
        self.copy_button.setVisible(not typing)
        metadata.addWidget(self.copy_button)
        self.retry_button = QPushButton("Yeniden dene", self.action_bar)
        self.retry_button.setObjectName("copyButton")
        self.retry_button.setToolTip("Son isteği yeniden gönder")
        self.retry_button.setAccessibleName("Yanıtı yeniden dene")
        self.retry_button.setVisible(role == "assistant" and not typing)
        self.retry_button.clicked.connect(self.retry_requested)
        metadata.addWidget(self.retry_button)
        self.read_aloud_button = QPushButton("Seslendir", self.action_bar)
        self.read_aloud_button.setObjectName("copyButton")
        self.read_aloud_button.setToolTip("Bu yanıtı seslendir")
        self.read_aloud_button.setAccessibleName("Yanıtı seslendir")
        self.read_aloud_button.setVisible(role == "assistant" and not typing)
        self.read_aloud_button.clicked.connect(lambda: self.read_aloud_requested.emit(self.raw_text))
        metadata.addWidget(self.read_aloud_button)
        self.stop_speech_button = QPushButton("Sesi durdur", self.action_bar)
        self.stop_speech_button.setObjectName("copyButton")
        self.stop_speech_button.setToolTip("Seslendirmeyi durdur")
        self.stop_speech_button.setAccessibleName("Sesi durdur")
        self.stop_speech_button.setVisible(role == "assistant" and not typing)
        self.stop_speech_button.clicked.connect(self.stop_speech_requested)
        metadata.addWidget(self.stop_speech_button)
        self.visual_status_label = QLabel(self.bubble)
        self.visual_status_label.setObjectName("mutedLabel")
        self.visual_status_label.setVisible(visual_context is not None)
        self.visual_status_label.setText("Analiz bekleniyor")
        metadata.insertWidget(1, self.visual_status_label)
        self.reanalyze_button = QPushButton("Yeniden analiz et", self.bubble)
        self.reanalyze_button.setObjectName("copyButton")
        self.reanalyze_button.setToolTip("Bu görseli composer alanına geri yükle")
        self.reanalyze_button.setAccessibleName("Görseli yeniden analize hazırla")
        self.reanalyze_button.setVisible(visual_context is not None)
        self.reanalyze_button.clicked.connect(
            lambda: self.reanalyze_requested.emit(self.visual_context)
        )
        metadata.addWidget(self.reanalyze_button)
        self.action_bar.setVisible(not typing and role == "user")
        bubble_layout.addWidget(self.action_bar)

    def enterEvent(self, event) -> None:
        if not self.typing:
            self.action_bar.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self.role == "assistant":
            self.action_bar.hide()
        super().leaveEvent(event)

    def _handle_image_click(self, _event) -> None:
        if self.visual_context is not None:
            self.image_preview_requested.emit(self.visual_context)

    def set_visual_status(self, status: str) -> None:
        """Update the session-local analysis status shown below an image."""
        self.visual_status_label.setText(status)

    def set_message_font(self, family: str, size: int) -> None:
        """Update the visible message font for session accessibility controls."""
        self.text_label.setFont(QFont(family, size))

    def set_bubble_width(self, width: int) -> None:
        """Bound the bubble to a readable responsive width."""
        maximum = MAX_ASSISTANT_WIDTH if self.role == "assistant" else MAX_USER_WIDTH
        minimum = MIN_ASSISTANT_WIDTH if self.role == "assistant" else MIN_USER_WIDTH
        bounded_width = max(280, min(maximum, width))
        minimum_width = min(minimum, bounded_width)
        self.setMaximumWidth(bounded_width)
        self.bubble.setMaximumWidth(bounded_width)
        self.setMinimumWidth(minimum_width)
        self.bubble.setMinimumWidth(minimum_width)
        if self.image_label is not None and self._preview_pixmap is not None:
            preview = self._preview_pixmap.scaled(
                max(1, bounded_width - 32),
                MAX_PREVIEW_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(preview)

    def update_stream_preview(self, text: str) -> None:
        """Update only the transient widget; persistence remains owned by the service."""
        if not self.typing:
            return
        self.raw_text = text
        self.text_label.setText(text)
        self.sender_label.setText("Lina yanıtlıyor")

    def finalize_stream(self, text: str) -> None:
        self.raw_text = text
        self.text_label.setText(text)
        self.typing = False
        self.sender_label.setText("Lina")
        self.copy_button.show()
