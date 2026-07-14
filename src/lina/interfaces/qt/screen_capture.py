"""Qt adapter for explicit, in-memory screen capture."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPoint, QRect
from PySide6.QtGui import QCursor, QGuiApplication, QScreen

from lina.screen.models import (
    SCREEN_CAPTURE_FULL,
    SCREEN_CAPTURE_REGION,
    ScreenCaptureError,
    ScreenContext,
)


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

        return self._build_context(
            screen.grabWindow(0),
            screen,
            SCREEN_CAPTURE_FULL,
            screen.name(),
        )

    def capture_screen(self, screen: QScreen) -> ScreenContext:
        """Capture an explicitly selected screen without consulting cursor state."""
        if screen is None:
            raise ScreenCaptureError("No screen is available for capture.")
        return self._build_context(
            screen.grabWindow(0),
            screen,
            SCREEN_CAPTURE_FULL,
            screen.name(),
        )

    def capture_region(
        self,
        rectangle: QRect,
        screen: QScreen | None = None,
    ) -> ScreenContext:
        """Capture a logical-pixel rectangle from the selected screen."""
        target_screen = screen or self._screen_at(self._cursor_position())
        if target_screen is None:
            target_screen = self._primary_screen()
        if target_screen is None:
            raise ScreenCaptureError("No screen is available for capture.")

        pixmap = target_screen.grabWindow(0)
        if pixmap.isNull():
            raise ScreenCaptureError("Screen capture returned an empty image.")
        geometry = target_screen.geometry()
        device_ratio = pixmap.devicePixelRatio()
        local = rectangle.translated(-geometry.topLeft())
        crop = QRect(
            round(local.x() * device_ratio),
            round(local.y() * device_ratio),
            round(local.width() * device_ratio),
            round(local.height() * device_ratio),
        ).intersected(pixmap.rect())
        if crop.width() <= 0 or crop.height() <= 0:
            raise ScreenCaptureError("Selected screen region is empty.")
        return self._build_context(
            pixmap.copy(crop),
            target_screen,
            SCREEN_CAPTURE_REGION,
            target_screen.name(),
            "Seçili Ekran Alanı",
        )

    def _build_context(
        self,
        pixmap,
        screen: QScreen,
        source: str,
        source_screen_name: str | None,
        display_name: str | None = None,
    ) -> ScreenContext:
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
            display_name=display_name or screen.name() or "Screen",
            estimated_byte_size=len(encoded),
            source=source,
            source_screen_name=source_screen_name,
        )
