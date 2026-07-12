"""Tests for explicit Qt image file loading."""

from pathlib import Path

import pytest
from PySide6.QtGui import QImage

from lina.interfaces.qt.image_loader import ImageLoadError, QtImageLoader
from lina.screen.models import LOCAL_FILE
from lina.vision.models import PNG_SIGNATURE


def test_image_loader_normalizes_selected_image_to_memory_png(tmp_path: Path) -> None:
    path = tmp_path / "selected.jpg"
    image = QImage(320, 180, QImage.Format.Format_RGB32)
    image.fill(0x336699)
    assert image.save(str(path), "JPEG")

    context = QtImageLoader().load(path)

    assert context.image_bytes.startswith(PNG_SIGNATURE)
    assert context.width == 320
    assert context.height == 180
    assert context.display_name == "selected.jpg"
    assert context.source == LOCAL_FILE
    assert context.estimated_byte_size == len(context.image_bytes)


def test_image_loader_rejects_unsupported_file(tmp_path: Path) -> None:
    path = tmp_path / "not-an-image.txt"
    path.write_text("not an image", encoding="utf-8")

    with pytest.raises(ImageLoadError, match="supported image"):
        QtImageLoader().load(path)


def test_image_loader_rejects_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.png"
    path.touch()

    with pytest.raises(ImageLoadError, match="empty"):
        QtImageLoader().load(path)
