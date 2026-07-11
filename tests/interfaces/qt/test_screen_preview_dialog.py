"""Tests for the screen capture preview dialog."""

from datetime import datetime

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog

from lina.interfaces.qt.screen_preview_dialog import PRIVACY_NOTICE, ScreenPreviewDialog
from lina.screen.models import ScreenContext


def _screen_context(width: int = 640, height: int = 360) -> ScreenContext:
    pixmap = QPixmap(width, height)
    pixmap.fill()
    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert pixmap.save(buffer, "PNG")
    buffer.close()
    image_bytes = bytes(data)
    return ScreenContext(
        image_bytes=image_bytes,
        width=width,
        height=height,
        captured_at=datetime(2026, 7, 11, 22, 5, 7),
        display_name="Display 2",
        estimated_byte_size=len(image_bytes),
    )


def test_preview_displays_image_metadata_and_privacy_notice(qtbot) -> None:
    dialog = ScreenPreviewDialog(_screen_context())
    qtbot.addWidget(dialog)

    preview = dialog.preview_label.pixmap()
    assert preview is not None
    assert preview.isNull() is False
    assert abs((preview.width() / preview.height()) - (640 / 360)) < 0.01
    assert "Display 2" in dialog.metadata_label.text()
    assert "640×360" in dialog.metadata_label.text()
    assert "22:05:07" in dialog.metadata_label.text()
    assert dialog.privacy_label.text() == PRIVACY_NOTICE


def test_preview_cancel_rejects_capture(qtbot) -> None:
    dialog = ScreenPreviewDialog(_screen_context())
    qtbot.addWidget(dialog)

    dialog.cancel_button.click()

    assert dialog.result() == QDialog.DialogCode.Rejected


def test_preview_add_accepts_capture(qtbot) -> None:
    dialog = ScreenPreviewDialog(_screen_context())
    qtbot.addWidget(dialog)

    dialog.add_button.click()

    assert dialog.result() == QDialog.DialogCode.Accepted


def test_preview_close_is_equivalent_to_cancel(qtbot) -> None:
    dialog = ScreenPreviewDialog(_screen_context())
    qtbot.addWidget(dialog)

    dialog.close()

    assert dialog.result() == QDialog.DialogCode.Rejected
