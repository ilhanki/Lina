"""Ephemeral QLabel/QImage live camera preview with change-region overlays."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCloseEvent, QImage, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from lina.vision.live.models import ChangeRegion, LiveVisionState


class CameraPreviewCanvas(QWidget):
    """Render one implicitly-shared QImage and normalized non-semantic boxes."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._image = QImage()
        self._regions: tuple[ChangeRegion, ...] = ()
        self.setMinimumSize(320, 180)
        self.setAccessibleName("Canlı kamera görüntüsü ve değişiklik bölgeleri")

    def set_frame(self, image: QImage) -> None:
        self._image = QImage(image)
        self.update()

    def set_regions(self, regions: tuple[ChangeRegion, ...]) -> None:
        self._regions = regions
        self.update()

    def clear_frame(self) -> None:
        self._image = QImage()
        self._regions = ()
        self.update()

    @property
    def regions(self) -> tuple[ChangeRegion, ...]:
        return self._regions

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(11, 13, 18))
        if self._image.isNull():
            painter.setPen(QColor(244, 247, 251))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Kamera açılıyor…")
            return
        target = _fit_rect(self.width(), self.height(), self._image.width(), self._image.height())
        painter.drawImage(target, self._image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for region in self._regions:
            box = QRectF(
                target.x() + region.x * target.width(),
                target.y() + region.y * target.height(),
                region.width * target.width(),
                region.height * target.height(),
            )
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(box)
            label = QRectF(box.x(), max(target.y(), box.y() - 22), 86, 22)
            painter.fillRect(label, QColor(0, 0, 0, 190))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(label, Qt.AlignmentFlag.AlignCenter, "Değişiklik")


class CameraPreviewWindow(QWidget):
    analyze_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    hidden = Signal()

    def __init__(self, device_name: str, session_id: str, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Tool)
        self.session_id = session_id
        self._programmatic_close = False
        self._region_generation = 0
        self._region_timer = QTimer(self)
        self._region_timer.setSingleShot(True)
        self._region_timer.timeout.connect(self._expire_current_regions)
        self.setWindowTitle("Lina Kamera")
        self.resize(680, 500)
        self.setMinimumSize(420, 320)
        root = QVBoxLayout(self)
        header = QHBoxLayout()
        self.active_label = QLabel("● Kamera aktif", self)
        self.active_label.setAccessibleName("Kamera aktif gizlilik göstergesi")
        self.device_label = QLabel(device_name or "Kamera", self)
        self.status_label = QLabel("Kamera açılıyor", self)
        header.addWidget(self.active_label)
        header.addWidget(self.device_label, 1)
        header.addWidget(self.status_label)
        root.addLayout(header)
        self.canvas = CameraPreviewCanvas(self)
        root.addWidget(self.canvas, 1)
        note = QLabel("Kutular nesne kimliği değil, görüntü değişikliği bölgeleridir.", self)
        note.setObjectName("mutedLabel")
        root.addWidget(note)
        controls = QHBoxLayout()
        self.analyze_button = QPushButton("Şimdi Analiz Et", self)
        self.pause_button = QPushButton("Duraklat", self)
        self.stop_button = QPushButton("Takibi Durdur", self)
        self.hide_button = QPushButton("Preview’i Gizle", self)
        self.analyze_button.clicked.connect(self.analyze_requested)
        self.pause_button.clicked.connect(self.pause_requested)
        self.stop_button.clicked.connect(self.stop_requested)
        self.hide_button.clicked.connect(self.hide_preview)
        for button in (self.analyze_button, self.pause_button, self.stop_button, self.hide_button):
            controls.addWidget(button)
        root.addLayout(controls)

    def set_frame(self, image: QImage, session_id: str) -> bool:
        if session_id != self.session_id:
            return False
        self.canvas.set_frame(image)
        return True

    def set_change_regions(self, regions: tuple[ChangeRegion, ...], session_id: str) -> bool:
        if session_id != self.session_id:
            return False
        self._region_generation += 1
        self.canvas.set_regions(regions)
        if regions:
            self._region_timer.start(2500)
        else:
            self._region_timer.stop()
        return True

    def apply_state(self, state: LiveVisionState) -> None:
        labels = {
            LiveVisionState.STARTING: "Kamera açılıyor",
            LiveVisionState.MONITORING: "Takip ediliyor",
            LiveVisionState.CHANGE_DETECTED: "Değişiklik algılandı",
            LiveVisionState.ANALYZING: "Analiz ediliyor",
            LiveVisionState.PAUSED: "Duraklatıldı",
        }
        self.status_label.setText(labels.get(state, state.value))
        self.pause_button.setText("Devam Et" if state is LiveVisionState.PAUSED else "Duraklat")
        self.analyze_button.setEnabled(state not in {LiveVisionState.ANALYZING, LiveVisionState.PAUSED})

    def hide_preview(self) -> None:
        self.hide()
        self.hidden.emit()

    def close_permanently(self) -> None:
        self._programmatic_close = True
        self._region_timer.stop()
        self.canvas.clear_frame()
        self.close()
        self.deleteLater()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._programmatic_close:
            event.accept()
            return
        event.ignore()
        self.hide_preview()

    def _expire_regions(self, generation: int) -> None:
        if generation == self._region_generation:
            self.canvas.set_regions(())

    def _expire_current_regions(self) -> None:
        self._expire_regions(self._region_generation)


def _fit_rect(container_width: int, container_height: int, image_width: int, image_height: int) -> QRectF:
    scale = min(container_width / image_width, container_height / image_height)
    width = image_width * scale
    height = image_height * scale
    return QRectF((container_width - width) / 2, (container_height - height) / 2, width, height)
