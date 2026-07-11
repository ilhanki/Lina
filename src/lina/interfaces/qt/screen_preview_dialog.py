"""Modal preview for a user-requested temporary screen capture."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from lina.screen.models import ScreenCaptureError, ScreenContext


PRIVACY_NOTICE = (
    "Bu görüntü yalnız bu oturumda geçici olarak tutulur. "
    "Henüz modele gönderilmez ve diske kaydedilmez."
)


class ScreenPreviewDialog(QDialog):
    """Let the user approve or discard one in-memory screenshot."""

    PREVIEW_MAX_WIDTH = 820
    PREVIEW_MAX_HEIGHT = 460

    def __init__(self, context: ScreenContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._pixmap = QPixmap()
        if not self._pixmap.loadFromData(context.image_bytes, "PNG"):
            raise ScreenCaptureError("Screen preview could not be created.")

        self.setWindowTitle("Ekran Görüntüsü Önizleme")
        self.setModal(True)
        self.setMinimumSize(640, 480)
        self._build_layout()
        self._fit_to_available_screen()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Ekran Görüntüsü Önizleme", self)
        title.setStyleSheet("font-size: 15pt; font-weight: 700;")
        layout.addWidget(title)

        self.preview_label = QLabel(self)
        self.preview_label.setObjectName("screenPreviewImage")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setAccessibleName("Yakalanan ekran görüntüsü önizlemesi")
        self._update_preview_pixmap()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview_label)
        layout.addWidget(scroll, 1)

        self.metadata_label = QLabel(
            f"{self._context.display_name} · "
            f"{self._context.width}×{self._context.height} · "
            f"{self._context.captured_at:%H:%M:%S}",
            self,
        )
        self.metadata_label.setObjectName("mutedLabel")
        layout.addWidget(self.metadata_label)

        self.privacy_label = QLabel(PRIVACY_NOTICE, self)
        self.privacy_label.setObjectName("mutedLabel")
        self.privacy_label.setWordWrap(True)
        layout.addWidget(self.privacy_label)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.cancel_button = QPushButton("İptal", self)
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.reject)
        actions.addWidget(self.cancel_button)
        self.add_button = QPushButton("Sohbete Ekle", self)
        self.add_button.setObjectName("accentButton")
        self.add_button.clicked.connect(self.accept)
        actions.addWidget(self.add_button)
        layout.addLayout(actions)

    def _update_preview_pixmap(self) -> None:
        scaled = self._pixmap.scaled(
            self.PREVIEW_MAX_WIDTH,
            self.PREVIEW_MAX_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)
        self.preview_label.setMinimumSize(scaled.size())

    def _fit_to_available_screen(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(860, 620)
            return
        available = screen.availableGeometry()
        self.resize(
            min(920, int(available.width() * 0.82)),
            min(700, int(available.height() * 0.82)),
        )
