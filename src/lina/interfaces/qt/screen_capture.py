"""Qt adapter for explicit, in-memory screen capture."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPoint
from PySide6.QtGui import QCursor, QGuiApplication, QScreen

from lina.screen.models import ScreenCaptureError, ScreenContext


class QtScreenCaptureService:
    """Capture the cursor screen using Qt without persistent storage."""

    def __init__(
        self,
        screen_at: Callable[[QPoint], QScreen | None] | None = None,
        primary_screen: Callable[[], QScreen | None] | None = None,
        cursor_position: Callable[[], QPoint] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._screen_at = screen_at or QGuiApplication.screenAt
        self._primary_screen = primary_screen or QGuiApplication.primaryScreen
        self._cursor_position = cursor_position or QCursor.pos
        self._now = now or datetime.now

    def capture(self) -> ScreenContext:
        """Return a PNG-backed context for the cursor screen or primary screen."""
        screen = self._screen_at(self._cursor_position())
        if screen is None:
            screen = self._primary_screen()
        if screen is None:
            raise ScreenCaptureError("No screen is available for capture.")

        pixmap = screen.grabWindow(0)
        if pixmap.isNull():
            raise ScreenCaptureError("Screen capture returned an empty image.")

        image_data = QByteArray()
        buffer = QBuffer(image_data)
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            raise ScreenCaptureError("Screen capture buffer could not be opened.")
        try:
            if not pixmap.save(buffer, "PNG"):
                raise ScreenCaptureError("Screen capture could not be encoded.")
        finally:
            buffer.close()

        encoded = bytes(image_data)
        if not encoded:
            raise ScreenCaptureError("Screen capture returned empty image data.")
        return ScreenContext(
            image_bytes=encoded,
            width=pixmap.width(),
            height=pixmap.height(),
            captured_at=self._now(),
            display_name=screen.name() or "Screen",
            estimated_byte_size=len(encoded),
        )
