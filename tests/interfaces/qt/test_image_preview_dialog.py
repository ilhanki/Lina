"""Tests for large in-memory image preview."""

from datetime import datetime

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QDialog

from lina.interfaces.qt.image_preview_dialog import ImagePreviewDialog
from lina.screen.models import ScreenContext


def _context() -> ScreenContext:
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill(0x336699)
    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    buffer.close()
    return ScreenContext(
        image_bytes=bytes(data),
        width=800,
        height=450,
        captured_at=datetime.now(),
        display_name="Preview",
        estimated_byte_size=len(data),
    )


def test_image_preview_shows_image_and_metadata(qtbot) -> None:
    dialog = ImagePreviewDialog(_context())
    qtbot.addWidget(dialog)

    assert dialog.image_label.pixmap().isNull() is False
    assert "800×450" in dialog.metadata_label.text()


def test_image_preview_closes_with_escape(qtbot) -> None:
    dialog = ImagePreviewDialog(_context())
    qtbot.addWidget(dialog)
    dialog.show()

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
