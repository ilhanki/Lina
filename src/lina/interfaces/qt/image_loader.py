"""Qt adapter for explicit, in-memory image file loading."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImageReader

from lina.screen.models import ScreenContext


MAX_SOURCE_FILE_BYTES = 32 * 1024 * 1024
MAX_PIXEL_COUNT = 40_000_000


class ImageLoadError(RuntimeError):
    """Raised when a user-selected image cannot be loaded safely."""


class QtImageLoader:
    """Load one explicitly selected image and normalize it to in-memory PNG."""

    def load(self, path: Path) -> ScreenContext:
        """Return a temporary image context without writing to disk."""
        try:
            source_size = path.stat().st_size
        except OSError as error:
            raise ImageLoadError("Selected image could not be accessed.") from error
        if source_size <= 0:
            raise ImageLoadError("Selected image is empty.")
        if source_size > MAX_SOURCE_FILE_BYTES:
            raise ImageLoadError("Selected image file is too large.")

        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        size = reader.size()
        if size.isValid() and size.width() * size.height() > MAX_PIXEL_COUNT:
            raise ImageLoadError("Selected image dimensions are too large.")
        image = reader.read()
        if image.isNull():
            raise ImageLoadError("Selected file is not a supported image.")
        if image.width() * image.height() > MAX_PIXEL_COUNT:
            raise ImageLoadError("Selected image dimensions are too large.")

        encoded_data = QByteArray()
        buffer = QBuffer(encoded_data)
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            raise ImageLoadError("Image buffer could not be opened.")
        try:
            if not image.save(buffer, "PNG"):
                raise ImageLoadError("Selected image could not be encoded.")
        finally:
            buffer.close()

        image_bytes = bytes(encoded_data)
        if not image_bytes:
            raise ImageLoadError("Selected image produced empty data.")
        return ScreenContext(
            image_bytes=image_bytes,
            width=image.width(),
            height=image.height(),
            captured_at=datetime.now(),
            display_name=path.name,
            estimated_byte_size=len(image_bytes),
            source="file_upload",
        )
