"""Small theme-aware line icons for Lina's interface controls."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from lina.ui.design.tokens import resolve_palette


_ICON_NAMES = frozenset({
    "add", "agent", "archive", "close", "collapse", "compose", "copy",
    "delete", "details", "file", "history", "memory", "microphone", "more",
    "notifications", "pause", "pin", "resume", "screen", "search", "send",
    "settings", "status", "stop", "thumbs_down", "thumbs_up", "tools", "vision", "voice",
})
_ICON_CACHE: dict[tuple[str, str, int], QIcon] = {}


def standard_icon(widget: QWidget, name: str, size: int = 20) -> QIcon:
    """Return a crisp monochrome icon using the widget's current text color."""
    if name not in _ICON_NAMES:
        raise ValueError(f"Unknown interface icon: {name}")
    if size not in {16, 18, 20, 24}:
        raise ValueError("Interface icon size must be 16, 18, 20, or 24")
    color = _icon_color(widget)
    cache_key = (name, color.name(), size)
    cached = _ICON_CACHE.get(cache_key)
    if cached is not None:
        return cached
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 20.0, size / 20.0)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    _draw_icon(painter, name)
    painter.end()
    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon


def _icon_color(widget: QWidget) -> QColor:
    application = QApplication.instance()
    stylesheet = application.styleSheet() if application is not None else ""
    for theme in ("dark", "light"):
        palette = resolve_palette(theme)
        if palette.canvas in stylesheet:
            return QColor(palette.text_secondary)
    return widget.palette().windowText().color()


def _draw_icon(painter: QPainter, name: str) -> None:
    if name in {"add", "compose"}:
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
    elif name in {"details", "more", "tools"}:
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
    elif name in {"screen", "vision"}:
        painter.drawRoundedRect(QRectF(2.5, 3.5, 15, 11), 1.5, 1.5)
        painter.drawLine(QPointF(8, 17), QPointF(12, 17))
        painter.drawLine(QPointF(10, 14.5), QPointF(10, 17))
    elif name in {"microphone", "voice"}:
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
    elif name in {"settings", "status"}:
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
    elif name in {"file", "history", "memory", "archive"}:
        painter.drawRoundedRect(QRectF(4, 2.5, 12, 15), 1.5, 1.5)
        painter.drawLine(QPointF(7, 7), QPointF(13, 7))
        painter.drawLine(QPointF(7, 10), QPointF(13, 10))
        painter.drawLine(QPointF(7, 13), QPointF(11, 13))
    elif name == "pin":
        painter.drawLine(QPointF(10, 10), QPointF(10, 17))
        painter.drawLine(QPointF(6, 9), QPointF(14, 9))
        painter.drawLine(QPointF(7, 4), QPointF(13, 4))
        painter.drawLine(QPointF(7, 4), QPointF(6, 9))
        painter.drawLine(QPointF(13, 4), QPointF(14, 9))
    elif name == "delete":
        painter.drawRoundedRect(QRectF(5, 6, 10, 11), 1, 1)
        painter.drawLine(QPointF(4, 5), QPointF(16, 5))
        painter.drawLine(QPointF(8, 2.8), QPointF(12, 2.8))
    elif name == "copy":
        painter.drawRoundedRect(QRectF(6, 5, 10, 11), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(3.5, 2.5, 10, 11), 1.5, 1.5)
    elif name in {"pause", "resume"}:
        if name == "pause":
            painter.drawLine(QPointF(7, 5), QPointF(7, 15))
            painter.drawLine(QPointF(13, 5), QPointF(13, 15))
        else:
            path = QPainterPath(QPointF(7, 4.5))
            path.lineTo(QPointF(15, 10))
            path.lineTo(QPointF(7, 15.5))
            path.closeSubpath()
            painter.drawPath(path)
    elif name in {"thumbs_up", "thumbs_down"}:
        painter.drawRoundedRect(QRectF(8, 7, 8, 8), 1.5, 1.5)
        direction = -1 if name == "thumbs_up" else 1
        painter.drawLine(QPointF(8, 9), QPointF(5, 9 + 4 * direction))
        painter.drawLine(QPointF(5, 9 + 4 * direction), QPointF(3.5, 9))
