"""Keyboard and mouse controlled screen region selection overlay."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


MIN_REGION_SIZE = 40


class RegionCaptureOverlay(QWidget):
    """Select one rectangle inside a single screen geometry."""

    region_selected = Signal(QRect)
    canceled = Signal()

    def __init__(self, geometry: QRect, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setGeometry(geometry)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._start: QPoint | None = None
        self._current: QPoint | None = None
        self._selection: QRect | None = None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.activateWindow()
        self.setFocus()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._cancel()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.position().toPoint()
            self._current = self._start
            self._selection = None
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._start is None:
            return
        self._current = event.position().toPoint()
        self._selection = QRect(self._start, self._current).normalized()
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._start is None:
            return
        self._current = event.position().toPoint()
        selection = QRect(self._start, self._current).normalized()
        if self._is_valid_selection(selection):
            self._selection = selection
            self.update()
            self.region_selected.emit(selection)
        else:
            self._selection = None
            self.update()

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._selection is not None:
            self._confirm()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm()
            return
        super().keyPressEvent(event)

    def _confirm(self) -> None:
        if self._selection is not None and self._is_valid_selection(self._selection):
            self.region_selected.emit(self._selection)

    def _cancel(self) -> None:
        self.canceled.emit()
        self.close()

    @staticmethod
    def _is_valid_selection(rectangle: QRect) -> bool:
        return (
            rectangle.width() >= MIN_REGION_SIZE
            and rectangle.height() >= MIN_REGION_SIZE
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        painter.setFont(QFont("Segoe UI", 12))
        painter.setPen(QColor("#f4f7fb"))
        painter.drawText(
            24,
            36,
            "Analiz edilecek alanı seç · Esc: İptal",
        )
        if self._selection is not None:
            selection = self._selection
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor("#7f9cff"), 2))
            painter.drawRect(selection)
            painter.setPen(QColor("#f4f7fb"))
            painter.drawText(
                selection.left(),
                max(54, selection.top() - 8),
                f"{selection.width()} × {selection.height()}",
            )
        painter.end()
