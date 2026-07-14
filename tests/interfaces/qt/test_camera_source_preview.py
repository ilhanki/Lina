import pytest
from PySide6.QtGui import QImage

from lina.interfaces.qt.camera_source import QtCameraBackend
from lina.vision.live.models import LiveVisionError


class Frame:
    def __init__(self, image): self.image = image
    def isValid(self): return True
    def toImage(self): return self.image


def test_backend_delivers_qimage_without_encoding_or_persistence():
    backend = QtCameraBackend()
    images = []
    backend.subscribe_preview(images.append)
    image = QImage(32, 18, QImage.Format.Format_RGB32)
    backend._receive_frame(Frame(image))
    assert len(images) == 1
    assert images[0].size() == image.size()
    backend.clear_listeners()
    backend._receive_frame(Frame(image))
    assert len(images) == 1


def test_device_error_wakes_capture_and_uses_safe_message():
    backend = QtCameraBackend(frame_timeout=.01)
    errors = []
    backend.subscribe_error(errors.append)
    backend._camera_error(None, "raw driver exception")
    with pytest.raises(LiveVisionError, match="Kameraya erişilemiyor"):
        backend.capture()
    assert errors == ["Kameraya erişilemiyor."]
