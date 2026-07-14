"""Click-through privacy border for screen and region monitoring."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCloseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget


class MonitoringBorderOverlay(QWidget):
    """Mandatory, non-interactive monitoring indicator outside the taskbar."""

    geometry_changed = Signal(object)
    closed_unexpectedly = Signal()

    def __init__(self, geometry_provider: Callable[[], QRect], label: str, parent=None) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        super().__init__(parent, flags)
        self._geometry_provider = geometry_provider
        self._label = label
        self._paused = False
        self._closing = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName(label)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh_geometry)
        self.refresh_geometry()

    @property
    def paused(self) -> bool:
        return self._paused

    def start(self) -> None:
        self.refresh_geometry()
        self.show()
        self._timer.start()

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        self.setWindowOpacity(0.55 if paused else 1.0)
        self.update()

    def refresh_geometry(self) -> None:
        geometry = self._geometry_provider()
        if not geometry.isValid() or geometry.width() <= 0 or geometry.height() <= 0:
            return
        if self.geometry() != geometry:
            self.setGeometry(geometry)
            self.geometry_changed.emit(QRect(geometry))

    def close_permanently(self) -> None:
        self._closing = True
        self._timer.stop()
        self.hide()
        self.close()
        self.deleteLater()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.accept()
        if not self._closing:
            self.closed_unexpectedly.emit()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(255, 255, 255), 3, Qt.PenStyle.DashLine if self._paused else Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(2, 2, -2, -2))
        label_rect = self.rect().adjusted(12, 10, -12, -10)
        label_rect.setWidth(min(230, label_rect.width()))
        label_rect.setHeight(30)
        painter.fillRect(label_rect, QColor(0, 0, 0, 195))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self._label + (" · Duraklatıldı" if self._paused else ""))
