from datetime import datetime, timezone

import pytest

from lina.screen.models import ScreenCaptureError, ScreenContext
from lina.vision.live.frame_source import CameraFrameSource, RegionFrameSource, ScreenFrameSource
from lina.vision.live.models import LiveVisionError, LiveVisionSource


class Backend:
    device_name = "Test Camera"
    def __init__(self, available=True, error=None):
        self.available = available; self.error = error; self.started = 0; self.stopped = 0
    def is_available(self): return self.available
    def start(self):
        self.started += 1
        if self.error: raise self.error
    def capture(self): return b"png", 10, 20, "image/png"
    def stop(self): self.stopped += 1


def context(source="screen_capture_full"):
    return ScreenContext(b"png", 10, 20, datetime.now(timezone.utc), "Display", 3, source, "Display")


def test_camera_start_capture_duplicate_start_and_release():
    backend = Backend(); source = CameraFrameSource(backend)
    source.start(); source.start()
    result = source.capture()
    assert backend.started == 1
    assert result.source is LiveVisionSource.CAMERA and result.source_label == "Test Camera"
    source.stop(); source.stop()
    assert backend.stopped == 2


def test_camera_unavailable_and_permission_messages_are_safe():
    with pytest.raises(LiveVisionError, match="Kameraya erişilemiyor"):
        CameraFrameSource(Backend(False)).start()
    with pytest.raises(LiveVisionError, match="Kamera izni verilmedi"):
        CameraFrameSource(Backend(error=PermissionError())).start()


def test_screen_and_region_use_existing_capture_without_persistence():
    service = type("Service", (), {"capture": lambda self: context()})()
    screen = ScreenFrameSource(service); screen.start()
    assert screen.capture().source is LiveVisionSource.SCREEN
    region = RegionFrameSource(lambda: context("screen_capture_region")); region.start()
    assert region.capture().source is LiveVisionSource.REGION
    screen.stop(); region.stop()


def test_capture_failure_is_translated():
    def fail(): raise ScreenCaptureError("raw exception")
    source = RegionFrameSource(fail); source.start()
    with pytest.raises(LiveVisionError, match="Seçili bölge artık geçerli değil"):
        source.capture()
