"""Multiline message composer for Lina's Qt interface."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent, QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QWidget


class ComposerInput(QPlainTextEdit):
    """Multiline editor with chat send and bounded history behavior."""

    send_requested = Signal()
    history_requested = Signal(int)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
                return
            self.send_requested.emit()
            event.accept()
            return
        if key == Qt.Key.Key_Up and self._cursor_on_first_line():
            self.history_requested.emit(-1)
            event.accept()
            return
        if key == Qt.Key.Key_Down and self._cursor_on_last_line():
            self.history_requested.emit(1)
            event.accept()
            return
        super().keyPressEvent(event)

    def _cursor_on_first_line(self) -> bool:
        return self.textCursor().blockNumber() == 0

    def _cursor_on_last_line(self) -> bool:
        return self.textCursor().blockNumber() == self.blockCount() - 1


class ComposerWidget(QWidget):
    """Compose text and expose Lina's primary GUI actions."""

    send_requested = Signal()
    attachment_requested = Signal()
    mic_requested = Signal()
    screen_requested = Signal()
    history_requested = Signal(int)

    def __init__(self, font_family: str, font_size: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("composerPanel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.attachment_button = QPushButton("+", self)
        self.attachment_button.setToolTip("Dosya ekle - henüz aktif değil")
        self.attachment_button.setAccessibleName("Dosya ekle")
        layout.addWidget(self.attachment_button)

        self.input = ComposerInput(self)
        self.input.setPlaceholderText("Lina'ya bir mesaj yaz...")
        self.input.setMinimumHeight(64)
        self.input.setMaximumHeight(150)
        self.input.setFont(QFont(font_family, font_size))
        self.input.setAccessibleName("Lina mesaj alanı")
        self.input.setAccessibleDescription("Enter gönderir, Shift Enter yeni satır ekler")
        layout.addWidget(self.input, 1)

        self.mic_button = QPushButton("Mic", self)
        self.mic_button.setToolTip("Konuşmayı metne çevir")
        self.mic_button.setAccessibleName("Mikrofon")
        layout.addWidget(self.mic_button)

        self.screen_button = QPushButton("Screen", self)
        self.screen_button.setToolTip("Ekran bağlamı - henüz aktif değil")
        self.screen_button.setAccessibleName("Ekran bağlamı")
        layout.addWidget(self.screen_button)

        self.send_button = QPushButton("Gönder", self)
        self.send_button.setObjectName("accentButton")
        self.send_button.setToolTip("Mesajı gönder")
        self.send_button.setAccessibleName("Mesajı gönder")
        self.send_button.setEnabled(False)
        layout.addWidget(self.send_button)

        self.input.send_requested.connect(self.send_requested)
        self.input.history_requested.connect(self.history_requested)
        self.input.textChanged.connect(self._update_send_state)
        self.attachment_button.clicked.connect(self.attachment_requested)
        self.mic_button.clicked.connect(self.mic_requested)
        self.screen_button.clicked.connect(self.screen_requested)
        self.send_button.clicked.connect(self.send_requested)

    def text(self) -> str:
        return self.input.toPlainText().strip()

    def set_text(self, text: str) -> None:
        self.input.setPlainText(text)
        cursor = self.input.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.input.setTextCursor(cursor)

    def append_transcription(self, text: str) -> bool:
        transcription = text.strip()
        if not transcription:
            return False
        current = self.text()
        self.set_text(f"{current} {transcription}".strip())
        self.input.setFocus()
        return self.text() == f"{current} {transcription}".strip()

    def clear(self) -> None:
        self.input.clear()

    def set_waiting(self, waiting: bool) -> None:
        self.input.setEnabled(not waiting)
        self.send_button.setEnabled(not waiting and bool(self.text()))

    def set_message_font(self, family: str, size: int) -> None:
        self.input.setFont(QFont(family, size))

    def _update_send_state(self) -> None:
        self.send_button.setEnabled(self.input.isEnabled() and bool(self.text()))
