"""Small theme-aware line icons for Lina's interface controls."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from lina.ui.design.tokens import resolve_palette


_ICON_NAMES = frozenset({
    "add", "agent", "close", "collapse", "details", "microphone",
    "notifications", "screen", "search", "send", "settings", "stop",
})


def standard_icon(widget: QWidget, name: str) -> QIcon:
    """Return a crisp monochrome icon using the widget's current text color."""
    if name not in _ICON_NAMES:
        raise ValueError(f"Unknown interface icon: {name}")
    pixmap = QPixmap(20, 20)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(_icon_color(widget), 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    _draw_icon(painter, name)
    painter.end()
    return QIcon(pixmap)


def _icon_color(widget: QWidget) -> QColor:
    application = QApplication.instance()
    stylesheet = application.styleSheet() if application is not None else ""
    for theme in ("dark", "light"):
        palette = resolve_palette(theme)
        if palette.canvas in stylesheet:
            return QColor(palette.text_secondary)
    return widget.palette().windowText().color()


def _draw_icon(painter: QPainter, name: str) -> None:
    if name == "add":
        painter.drawLine(QPointF(10, 4), QPointF(10, 16))
        painter.drawLine(QPointF(4, 10), QPointF(16, 10))
    elif name == "search":
        painter.drawEllipse(QRectF(3.5, 3.5, 10, 10))
        painter.drawLine(QPointF(12.5, 12.5), QPointF(16.5, 16.5))
    elif name == "close":
        painter.drawLine(QPointF(5, 5), QPointF(15, 15))
        painter.drawLine(QPointF(15, 5), QPointF(5, 15))
    elif name == "collapse":
        painter.drawLine(QPointF(6, 4), QPointF(6, 16))
        painter.drawLine(QPointF(14, 6), QPointF(10, 10))
        painter.drawLine(QPointF(10, 10), QPointF(14, 14))
    elif name == "details":
        for x in (5.0, 10.0, 15.0):
            painter.drawEllipse(QPointF(x, 10), 0.8, 0.8)
    elif name == "send":
        path = QPainterPath(QPointF(3.5, 4))
        path.lineTo(QPointF(16.5, 10))
        path.lineTo(QPointF(3.5, 16))
        path.lineTo(QPointF(6, 10))
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(6, 10), QPointF(16, 10))
    elif name == "stop":
        painter.drawRoundedRect(QRectF(5, 5, 10, 10), 1.5, 1.5)
    elif name == "screen":
        painter.drawRoundedRect(QRectF(2.5, 3.5, 15, 11), 1.5, 1.5)
        painter.drawLine(QPointF(8, 17), QPointF(12, 17))
        painter.drawLine(QPointF(10, 14.5), QPointF(10, 17))
    elif name == "microphone":
        painter.drawRoundedRect(QRectF(7, 2.5, 6, 10), 3, 3)
        painter.drawArc(QRectF(4.5, 7, 11, 9), 180 * 16, 180 * 16)
        painter.drawLine(QPointF(10, 16), QPointF(10, 18))
    elif name == "notifications":
        path = QPainterPath(QPointF(5, 14.5))
        path.quadTo(QPointF(6.5, 13), QPointF(6.5, 9))
        path.quadTo(QPointF(6.5, 4.5), QPointF(10, 4.5))
        path.quadTo(QPointF(13.5, 4.5), QPointF(13.5, 9))
        path.quadTo(QPointF(13.5, 13), QPointF(15, 14.5))
        painter.drawPath(path)
        painter.drawLine(QPointF(5, 14.5), QPointF(15, 14.5))
        painter.drawArc(QRectF(8, 13.5, 4, 4), 180 * 16, 180 * 16)
    elif name == "settings":
        painter.drawEllipse(QRectF(3.5, 3.5, 13, 13))
        painter.drawEllipse(QRectF(7.5, 7.5, 5, 5))
        painter.drawLine(QPointF(10, 1.8), QPointF(10, 4))
        painter.drawLine(QPointF(10, 16), QPointF(10, 18.2))
        painter.drawLine(QPointF(1.8, 10), QPointF(4, 10))
        painter.drawLine(QPointF(16, 10), QPointF(18.2, 10))
    elif name == "agent":
        points = (QPointF(10, 3.5), QPointF(4.5, 14.5), QPointF(15.5, 14.5))
        painter.drawLine(points[0], points[1])
        painter.drawLine(points[0], points[2])
        painter.drawLine(points[1], points[2])
        for point in points:
            painter.drawEllipse(point, 1.7, 1.7)
