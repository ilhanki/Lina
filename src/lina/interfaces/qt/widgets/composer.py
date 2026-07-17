"""Multiline message composer for Lina's Qt interface."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont, QIcon, QKeyEvent, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lina.interfaces.qt.theme import SPACE_SM
from lina.ui.design import standard_icon


COMPOSER_INPUT_MIN_HEIGHT = 58
COMPOSER_INPUT_MAX_HEIGHT = 160
COMPOSER_BUTTON_HEIGHT = 38


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
    stop_requested = Signal()
    screen_context_remove_requested = Signal()
    screen_context_preview_requested = Signal()
    screen_context_change_requested = Signal()
    agent_mode_requested = Signal()
    task_templates_requested = Signal()

    def __init__(self, font_family: str, font_size: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("composerPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._initial_resize_done = False
        self._waiting = False
        self._compact = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        self.screen_context_chip = QWidget(self)
        self.screen_context_chip.setObjectName("screenContextChip")
        chip_layout = QHBoxLayout(self.screen_context_chip)
        chip_layout.setContentsMargins(10, 4, 6, 4)
        chip_layout.setSpacing(SPACE_SM)
        self.screen_context_thumbnail = QPushButton(self.screen_context_chip)
        self.screen_context_thumbnail.setObjectName("screenContextThumbnail")
        self.screen_context_thumbnail.setFixedSize(52, 52)
        self.screen_context_thumbnail.setIconSize(QPixmap(44, 44).size())
        self.screen_context_thumbnail.setAccessibleName("Görsel önizlemesini aç")
        self.screen_context_thumbnail.setToolTip("Görseli büyük önizlemede aç")
        self.screen_context_thumbnail.clicked.connect(
            self.screen_context_preview_requested
        )
        chip_layout.addWidget(self.screen_context_thumbnail)
        self.screen_context_label = QLabel(self.screen_context_chip)
        self.screen_context_label.setToolTip("Geçici ekran bağlamı")
        chip_layout.addWidget(self.screen_context_label)
        self.screen_context_note = QLabel(
            "Görsel analiz henüz aktif değil",
            self.screen_context_chip,
        )
        self.screen_context_note.setObjectName("mutedLabel")
        chip_layout.addWidget(self.screen_context_note, 1)
        self.screen_context_change_button = QPushButton("Değiştir", self.screen_context_chip)
        self.screen_context_change_button.setObjectName("screenContextChangeButton")
        self.screen_context_change_button.setAccessibleName("Görseli değiştir")
        self.screen_context_change_button.setToolTip("Başka bir görsel veya ekran seç")
        self.screen_context_change_button.clicked.connect(
            self.screen_context_change_requested
        )
        chip_layout.addWidget(self.screen_context_change_button)
        self.screen_context_remove_button = QPushButton("Kaldır", self.screen_context_chip)
        self.screen_context_remove_button.setObjectName("screenContextRemoveButton")
        self.screen_context_remove_button.setAccessibleName("Ekran bağlamını kaldır")
        self.screen_context_remove_button.setToolTip("Geçici ekran bağlamını kaldır")
        chip_layout.addWidget(self.screen_context_remove_button)
        self.screen_context_chip.hide()
        layout.addWidget(self.screen_context_chip)

        self.input = ComposerInput(self)
        self.input.setPlaceholderText("Mesaj yaz…")
        self.input.setMinimumHeight(COMPOSER_INPUT_MIN_HEIGHT)
        self.input.setMaximumHeight(COMPOSER_INPUT_MAX_HEIGHT)
        self.input.setFixedHeight(COMPOSER_INPUT_MIN_HEIGHT)
        self.input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input.setFont(QFont(font_family, font_size))
        self.input.setAccessibleName("Lina mesaj alanı")
        self.input.setAccessibleDescription("Enter gönderir, Shift Enter yeni satır ekler")
        layout.addWidget(self.input)

        action_row = QWidget(self)
        action_row.setObjectName("composerToolbar")
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(SPACE_SM)
        layout.addWidget(action_row)

        self.attachment_button = QPushButton("Dosya", self)
        self.attachment_button.setIcon(standard_icon(self, "file"))
        self._configure_action_button(self.attachment_button, tooltip="Görsel veya dosya ekle", accessible_name="Dosya ekle")
        self.attachment_button.setObjectName("composerUtilityButton")
        action_layout.addWidget(self.attachment_button)

        self.mic_button = QPushButton("Mikrofon", self)
        self.mic_button.setIcon(standard_icon(self, "microphone"))
        self._configure_action_button(
            self.mic_button,
            tooltip="Konuşmayı metne çevir",
            accessible_name="Mikrofon",
        )
        action_layout.addWidget(self.mic_button)

        self.screen_button = QPushButton("Ekran", self)
        self.screen_button.setIcon(standard_icon(self, "screen"))
        self._configure_action_button(
            self.screen_button,
            tooltip="Tam ekran veya seçili alan görüntüsü ekle",
            accessible_name="Ekran görüntüsü yakala",
        )
        action_layout.addWidget(self.screen_button)

        self.agent_button = QPushButton("Agent", self)
        self.agent_button.setIcon(standard_icon(self, "agent"))
        self._configure_action_button(
            self.agent_button,
            tooltip="Agent çalışma modunu aç veya kapat",
            accessible_name="Agent modu",
        )
        self.agent_button.hide()

        self.tools_button = QPushButton("", self)
        self.tools_button.setIcon(standard_icon(self, "more"))
        self._configure_action_button(
            self.tools_button,
            tooltip="Daha fazla araç",
            accessible_name="Daha fazla araç",
        )
        self.tools_button.setObjectName("composerUtilityButton")
        self.tools_menu = QMenu(self.tools_button)
        self.tools_menu.setAccessibleName("Mesaj araçları")
        self.mic_action = self.tools_menu.addAction("Mikrofon")
        self.mic_action.triggered.connect(self.mic_button.click)
        self.screen_menu = self.tools_menu.addMenu("Ekran görüntüsü")
        self.agent_action = self.tools_menu.addAction("Agent modu")
        self.agent_action.triggered.connect(self.agent_button.click)
        self.task_templates_action = self.tools_menu.addAction("Hazır görevler")
        self.task_templates_action.triggered.connect(self.task_templates_requested.emit)
        self.tools_button.setMenu(self.tools_menu)
        action_layout.addWidget(self.tools_button)
        self.input_hint = QLabel("Enter gönderir · Shift+Enter yeni satır", action_row)
        self.input_hint.setObjectName("composerHint")
        self.input_hint.hide()
        action_layout.addStretch(1)
        action_layout.addWidget(self.input_hint)

        self.send_button = QPushButton("", self)
        self.send_button.setIcon(standard_icon(self, "send"))
        self._configure_action_button(
            self.send_button,
            tooltip="Mesajı gönder",
            accessible_name="Mesajı gönder",
        )
        self.send_button.setObjectName("composerSendButton")
        self.send_button.setEnabled(False)
        action_layout.addWidget(self.send_button)

        self.input.send_requested.connect(self.send_requested)
        self.input.history_requested.connect(self.history_requested)
        self.input.textChanged.connect(self._handle_text_changed)
        self.attachment_button.clicked.connect(self.attachment_requested)
        self.mic_button.clicked.connect(self.mic_requested)
        self.screen_button.clicked.connect(self.screen_requested)
        self.agent_button.clicked.connect(self.agent_mode_requested)
        self.screen_context_remove_button.clicked.connect(
            self.screen_context_remove_requested
        )
        self.send_button.clicked.connect(self._handle_send_button_clicked)
        self._resize_input_to_content()
        QTimer.singleShot(0, self._resize_input_to_content)

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

    def set_screen_context(
        self,
        width: int,
        height: int,
        analysis_status: str = "Görsel analiz kontrol ediliyor",
        attachment_label: str = "Ekran",
        image_bytes: bytes | None = None,
    ) -> None:
        """Show one temporary visual attachment in the composer."""
        self.screen_context_label.setText(
            f"{attachment_label} · {width}×{height}"
        )
        self.screen_context_note.setText(analysis_status)
        pixmap = QPixmap()
        has_preview = bool(image_bytes) and pixmap.loadFromData(image_bytes)
        self.screen_context_thumbnail.setVisible(has_preview)
        if has_preview:
            self.screen_context_thumbnail.setIcon(
                QIcon(
                    pixmap.scaled(
                        44,
                        44,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            )
        self.screen_context_chip.show()

    def clear_screen_context(self) -> None:
        """Hide and clear the temporary screen attachment summary."""
        self.screen_context_label.clear()
        self.screen_context_thumbnail.setIcon(QIcon())
        self.screen_context_thumbnail.hide()
        self.screen_context_chip.hide()

    def set_waiting(self, waiting: bool) -> None:
        self._waiting = waiting
        self.input.setEnabled(True)
        self.send_button.setText("")
        self.send_button.setIcon(standard_icon(self, "stop" if waiting else "send"))
        self.send_button.setToolTip(
            "Yanıtı durdur" if waiting else "Mesajı gönder"
        )
        self.send_button.setAccessibleName(
            "Yanıtı durdur" if waiting else "Mesajı gönder"
        )
        self.send_button.setEnabled(True if waiting else bool(self.text()))
        self.input.setFocus()

    def set_message_font(self, family: str, size: int) -> None:
        self.input.setFont(QFont(family, size))
        self._resize_input_to_content()

    def set_compact(self, compact: bool) -> None:
        self._compact = compact
        self.input_hint.hide()
        self.mic_button.setVisible(not compact)
        self.screen_button.setVisible(not compact)
        labels = (
            (self.attachment_button, "", "Dosya"),
            (self.tools_button, "", ""),
        )
        for button, short, full in labels:
            button.setText(short if compact else full)

    def set_mic_state(self, state: str) -> None:
        """Update the visible microphone action state."""
        labels = {
            "idle": "Mikrofon",
            "listening": "Durdur",
            "transcribing": "Çevriliyor…",
        }
        label = labels.get(state, labels["idle"])
        self.mic_button.setText(label)
        self.mic_action.setText(label)
        self.tools_button.setToolTip(label if state != "idle" else "Daha fazla araç")

    def set_mic_enabled(self, enabled: bool) -> None:
        self.mic_button.setEnabled(enabled)
        self.mic_action.setEnabled(enabled)

    def set_screen_enabled(self, enabled: bool) -> None:
        self.screen_button.setEnabled(enabled)
        self.screen_menu.menuAction().setEnabled(enabled)

    def _configure_action_button(
        self,
        button: QPushButton,
        tooltip: str,
        accessible_name: str,
    ) -> None:
        button.setObjectName("composerActionButton")
        button.setToolTip(tooltip)
        button.setAccessibleName(accessible_name)
        button.setMinimumHeight(COMPOSER_BUTTON_HEIGHT)
        button.setMaximumHeight(COMPOSER_BUTTON_HEIGHT)

    def _handle_text_changed(self) -> None:
        self._resize_input_to_content()
        self._update_send_state()

    def _resize_input_to_content(self) -> None:
        self.input.document().setTextWidth(max(1, self.input.viewport().width()))
        document_height = int(
            self.input.document().documentLayout().documentSize().height()
        )
        line_height = self.input.fontMetrics().lineSpacing()
        explicit_line_height = (self.input.blockCount() * line_height) + 24
        content_height = max(document_height + 18, explicit_line_height)
        height = max(
            COMPOSER_INPUT_MIN_HEIGHT,
            min(COMPOSER_INPUT_MAX_HEIGHT, content_height),
        )
        self.input.setFixedHeight(height)
        policy = (
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
            if content_height > COMPOSER_INPUT_MAX_HEIGHT
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.input.setVerticalScrollBarPolicy(policy)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._initial_resize_done:
            self._initial_resize_done = True
            self._resize_input_to_content()
            QTimer.singleShot(0, self._resize_input_to_content)

    def _update_send_state(self) -> None:
        self.send_button.setEnabled(True if self._waiting else bool(self.text()))

    def _handle_send_button_clicked(self) -> None:
        if self._waiting:
            self.stop_requested.emit()
            return
        self.send_requested.emit()
