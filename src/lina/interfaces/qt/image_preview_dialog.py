"""Large in-memory preview for a session-local visual attachment."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QScrollArea, QPushButton, QVBoxLayout

from lina.screen.models import ScreenContext


class ImagePreviewDialog(QDialog):
    """Display an existing session image without reading its source again."""

    def __init__(self, context: ScreenContext, parent=None) -> None:
        super().__init__(parent)
        self._context = context
        self._pixmap = QPixmap()
        if not self._pixmap.loadFromData(context.image_bytes):
            raise ValueError("Image preview could not be created")
        self.setWindowTitle("Görsel Önizleme")
        self.setModal(True)
        self.setMinimumSize(640, 480)
        self._build_layout()
        self._fit_to_screen()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        title = QLabel("Görsel Önizleme", self)
        title.setStyleSheet("font-size: 15pt; font-weight: 700;")
        layout.addWidget(title)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setAccessibleName("Görsel önizlemesi")
        self._update_image()
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.image_label)
        layout.addWidget(scroll, 1)

        self.metadata_label = QLabel(
            f"{self._context.display_name} · {self._context.width}×{self._context.height} · "
            f"{self._context.estimated_byte_size} bytes",
            self,
        )
        self.metadata_label.setObjectName("mutedLabel")
        layout.addWidget(self.metadata_label)
        actions = QHBoxLayout()
        actions.addStretch(1)
        close_button = QPushButton("Kapat", self)
        close_button.setObjectName("secondaryButton")
        close_button.setAccessibleName("Görsel önizlemesini kapat")
        close_button.clicked.connect(self.reject)
        actions.addWidget(close_button)
        layout.addLayout(actions)

    def _update_image(self) -> None:
        self.image_label.setPixmap(
            self._pixmap.scaled(
                900,
                600,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _fit_to_screen(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(900, 650)
            return
        geometry = screen.availableGeometry()
        self.resize(min(1000, int(geometry.width() * 0.8)), min(760, int(geometry.height() * 0.8)))
