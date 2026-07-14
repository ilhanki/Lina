"""Frame-source contracts and adapters over existing capture services."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Protocol

from lina.screen.models import ScreenCaptureError, ScreenContext
from lina.vision.live.models import LiveVisionError, LiveVisionFrame, LiveVisionSource


class FrameSource(Protocol):
    source: LiveVisionSource
    label: str
    def is_available(self) -> bool: ...
    def start(self) -> None: ...
    def capture(self) -> LiveVisionFrame: ...
    def stop(self) -> None: ...


class CameraBackend(Protocol):
    @property
    def device_name(self) -> str: ...
    def is_available(self) -> bool: ...
    def start(self) -> None: ...
    def capture(self) -> tuple[bytes, int, int, str]: ...
    def stop(self) -> None: ...


class CameraFrameSource:
    source = LiveVisionSource.CAMERA

    def __init__(self, backend: CameraBackend) -> None:
        self._backend = backend
        self._started = False

    @property
    def label(self) -> str:
        return self._backend.device_name or "Kamera"

    def is_available(self) -> bool:
        return self._backend.is_available()

    def start(self) -> None:
        if self._started:
            return
        if not self.is_available():
            raise LiveVisionError("Kameraya erişilemiyor.")
        try:
            self._backend.start()
        except PermissionError as error:
            raise LiveVisionError("Kamera izni verilmedi.") from error
        except Exception as error:
            raise LiveVisionError("Kameraya erişilemiyor.") from error
        self._started = True

    def capture(self) -> LiveVisionFrame:
        if not self._started:
            raise LiveVisionError("Kamera açık değil.")
        try:
            data, width, height, mime = self._backend.capture()
            return LiveVisionFrame(data, width, height, datetime.now(timezone.utc), self.source, mime, self.label)
        except LiveVisionError:
            raise
        except Exception as error:
            raise LiveVisionError("Kameradan görüntü alınamadı.") from error

    def stop(self) -> None:
        try:
            self._backend.stop()
        finally:
            self._started = False


class _CaptureSource:
    def __init__(self, capture: Callable[[], ScreenContext], source: LiveVisionSource, label: str) -> None:
        self._capture = capture
        self.source = source
        self.label = label
        self._started = False

    def is_available(self) -> bool:
        return True

    def start(self) -> None:
        self._started = True

    def capture(self) -> LiveVisionFrame:
        if not self._started:
            raise LiveVisionError("Canlı takip başlatılmadı.")
        try:
            context = self._capture()
        except ScreenCaptureError as error:
            message = "Seçili bölge artık geçerli değil." if self.source is LiveVisionSource.REGION else "Ekran görüntüsü alınamadı."
            raise LiveVisionError(message) from error
        return LiveVisionFrame(
            context.image_bytes, context.width, context.height, context.captured_at,
            self.source, "image/png", context.display_name,
        )

    def stop(self) -> None:
        self._started = False


class ScreenFrameSource(_CaptureSource):
    def __init__(self, capture_service: object) -> None:
        super().__init__(capture_service.capture, LiveVisionSource.SCREEN, "Ekran")


class RegionFrameSource(_CaptureSource):
    def __init__(self, capture: Callable[[], ScreenContext]) -> None:
        super().__init__(capture, LiveVisionSource.REGION, "Bölge")
