"""UI-only welcome state for an empty conversation."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from lina.interfaces.qt.formatting import build_welcome_message


class WelcomeStateWidget(QWidget):
    """Render a non-persistent welcome experience for an empty session."""

    prompt_selected = Signal(str)

    def __init__(
        self,
        logo_path: Path,
        conversation_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("welcomeState")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)
        layout.addStretch(2)

        self.logo_label = QLabel(self)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        if not pixmap.isNull():
            self.logo_label.setPixmap(
                pixmap.scaled(
                    76,
                    76,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.logo_label.setText("L")
            self.logo_label.setObjectName("welcomeFallbackLogo")
        layout.addWidget(self.logo_label)

        self.greeting_label = QLabel(self)
        self.greeting_label.setObjectName("welcomeGreeting")
        self.greeting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.greeting_label)

        self.subtitle_label = QLabel(self)
        self.subtitle_label.setObjectName("welcomeSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setText(
            "Bir şey sorabilir, ekran görüntüsü gösterebilir veya dosyalar hakkında konuşabilirsin."
        )
        layout.addWidget(self.subtitle_label)
        self._suggestions = QGridLayout()
        self._suggestions.setSpacing(8)
        self._suggestion_buttons: list[QPushButton] = []
        self._suggestions_compact: bool | None = None
        for text in (
            "Bugün neye odaklanmalıyım?",
            "Yapay zekâ ajanını açıkla",
            "Bir ekran görüntüsünü incele",
        ):
            button = QPushButton(text, self)
            button.setObjectName("suggestionButton")
            button.setAccessibleName(f"Öneri: {text}")
            button.clicked.connect(lambda _checked=False, prompt=text: self.prompt_selected.emit(prompt))
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._suggestion_buttons.append(button)
        layout.addLayout(self._suggestions)
        # Start with the narrow-safe layout so the widget never imposes a wide
        # minimum size on its containing scroll area before its first resize.
        self._layout_suggestions(compact=True)
        layout.addStretch(3)
        self.refresh(conversation_id)

    def _layout_suggestions(self, *, compact: bool) -> None:
        if self._suggestions_compact is compact:
            return
        self._suggestions_compact = compact
        columns = 1 if compact else len(self._suggestion_buttons)
        for index, button in enumerate(self._suggestion_buttons):
            self._suggestions.addWidget(button, index // columns, index % columns)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_suggestions(compact=self.width() < 1100)

    def refresh(self, conversation_id: int | None = None) -> None:
        """Refresh deterministic time-aware greeting text."""
        greeting, prompt = build_welcome_message(conversation_id=conversation_id)
        self.greeting_label.setText(f"{greeting}\n{prompt}")
