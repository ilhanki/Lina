"""Ephemeral QLabel/QImage live camera preview with change-region overlays."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCloseEvent, QImage, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from lina.vision.live.models import CameraConversationState, ChangeRegion, LiveVisionState


class CameraPreviewCanvas(QWidget):
    """Render one implicitly-shared QImage and normalized non-semantic boxes."""

    def __init__(self, parent=None, *, mirror_enabled: bool = True) -> None:
        super().__init__(parent)
        self._mirror_enabled = mirror_enabled
        self._image = QImage()
        self._regions: tuple[ChangeRegion, ...] = ()
        self.setMinimumSize(320, 180)
        self.setAccessibleName("Canlı kamera görüntüsü ve değişiklik bölgeleri")

    def set_frame(self, image: QImage) -> None:
        # Mirror only the local preview; model analysis keeps the original frame.
        self._image = (
            QImage(image).flipped(Qt.Orientation.Horizontal)
            if self._mirror_enabled else QImage(image)
        )
        self.update()

    def set_mirror_enabled(self, enabled: bool) -> None:
        if enabled != self._mirror_enabled and not self._image.isNull():
            self._image = self._image.flipped(Qt.Orientation.Horizontal)
        self._mirror_enabled = enabled
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
            rendered_x = _rendered_region_x(region, self._mirror_enabled)
            box = QRectF(
                target.x() + rendered_x * target.width(),
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
    automatic_commentary_toggled = Signal(bool)
    mute_toggled = Signal(bool)

    def __init__(self, device_name: str, session_id: str, parent=None, *, mirror_enabled: bool = True, automatic_commentary_enabled: bool = True, commentary_muted: bool = False) -> None:
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
        self.active_label = QLabel("● Konuşmalı Kamera", self)
        self.active_label.setAccessibleName("Kamera aktif gizlilik göstergesi")
        self.device_label = QLabel(device_name or "Kamera", self)
        self.status_label = QLabel("Kamera açılıyor", self)
        header.addWidget(self.active_label)
        header.addWidget(self.device_label, 1)
        header.addWidget(self.status_label)
        root.addLayout(header)
        self.canvas = CameraPreviewCanvas(self, mirror_enabled=mirror_enabled)
        root.addWidget(self.canvas, 1)
        note = QLabel("Kutular nesne kimliği değil, görüntü değişikliği bölgeleridir.", self)
        note.setObjectName("mutedLabel")
        root.addWidget(note)
        controls = QHBoxLayout()
        self.analyze_button = QPushButton("Şimdi Bak", self)
        self.pause_button = QPushButton("Duraklat", self)
        self.auto_commentary_button = QPushButton("Otomatik Yorum", self)
        self.auto_commentary_button.setCheckable(True)
        self.auto_commentary_button.setChecked(automatic_commentary_enabled)
        self.mute_button = QPushButton("Sessize Al", self)
        self.mute_button.setCheckable(True)
        self.mute_button.setChecked(commentary_muted)
        self.stop_button = QPushButton("Kamerayı Kapat", self)
        self.hide_button = QPushButton("Önizlemeyi Gizle", self)
        self.analyze_button.clicked.connect(self.analyze_requested)
        self.pause_button.clicked.connect(self.pause_requested)
        self.stop_button.clicked.connect(self.stop_requested)
        self.auto_commentary_button.toggled.connect(self.automatic_commentary_toggled)
        self.mute_button.toggled.connect(self._mute_changed)
        self.hide_button.clicked.connect(self.hide_preview)
        for button in (self.analyze_button, self.pause_button, self.auto_commentary_button, self.mute_button, self.stop_button, self.hide_button):
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
        self.status_label.setText(labels.get(state, "Durum güncelleniyor"))
        self.pause_button.setText("Devam Et" if state is LiveVisionState.PAUSED else "Duraklat")
        self.analyze_button.setEnabled(state not in {LiveVisionState.ANALYZING, LiveVisionState.PAUSED})

    def apply_conversation_state(self, state: CameraConversationState) -> None:
        self.status_label.setText({
            CameraConversationState.INACTIVE: "Kamera konuşması durduruldu",
            CameraConversationState.OBSERVING: "Kamerayı izliyorum",
            CameraConversationState.ANALYZING: "Görüntüyü analiz ediyorum",
            CameraConversationState.SPEAKING: "Cevap veriyorum",
            CameraConversationState.LISTENING: "Seni dinliyorum",
            CameraConversationState.PAUSED: "Otomatik yorum duraklatıldı",
            CameraConversationState.ERROR: "Görüntüyü şu anda yorumlayamıyorum",
        }[state])

    def _mute_changed(self, muted: bool) -> None:
        self.mute_button.setText("Sesi Aç" if muted else "Sessize Al")
        self.mute_toggled.emit(muted)

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


def _rendered_region_x(region: ChangeRegion, mirror_enabled: bool) -> float:
    return 1.0 - region.x - region.width if mirror_enabled else region.x
