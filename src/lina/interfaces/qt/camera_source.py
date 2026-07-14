"""Qt Multimedia camera backend with ephemeral in-memory frames."""

from __future__ import annotations

import threading
import time

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QMetaObject, QThread, Qt
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices, QVideoSink

from lina.vision.live.models import LiveVisionError


class QtCameraBackend:
    """Expose the latest QVideoFrame without recording or persistent storage."""

    def __init__(self, device_id: str | None = None, frame_timeout: float = 3.0) -> None:
        self._requested_device_id = device_id
        self._frame_timeout = frame_timeout
        self._camera: QCamera | None = None
        self._session: QMediaCaptureSession | None = None
        self._sink: QVideoSink | None = None
        self._image = None
        self._condition = threading.Condition()
        self._device = self._select_device()

    @property
    def device_name(self) -> str:
        return self._device.description() if self._device is not None else "Kamera"

    def is_available(self) -> bool:
        return self._device is not None

    def start(self) -> None:
        if self._camera is not None:
            return
        self._device = self._select_device()
        if self._device is None:
            raise LiveVisionError("Kameraya erişilemiyor.")
        self._sink = QVideoSink()
        self._sink.videoFrameChanged.connect(self._receive_frame)
        self._session = QMediaCaptureSession()
        self._camera = QCamera(self._device)
        self._session.setCamera(self._camera)
        self._session.setVideoSink(self._sink)
        self._camera.start()

    def capture(self) -> tuple[bytes, int, int, str]:
        deadline = time.monotonic() + self._frame_timeout
        with self._condition:
            while self._image is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise LiveVisionError("Kameradan görüntü alınamadı.")
                self._condition.wait(remaining)
            image = self._image.copy()
        data = QByteArray()
        buffer = QBuffer(data)
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            raise LiveVisionError("Kameradan görüntü alınamadı.")
        try:
            if not image.save(buffer, "PNG"):
                raise LiveVisionError("Kameradan görüntü alınamadı.")
        finally:
            buffer.close()
        return bytes(data), image.width(), image.height(), "image/png"

    def stop(self) -> None:
        camera, sink = self._camera, self._sink
        self._camera = None
        self._session = None
        self._sink = None
        if camera is not None:
            if camera.thread() is QThread.currentThread():
                camera.stop()
            else:
                QMetaObject.invokeMethod(camera, "stop", Qt.ConnectionType.BlockingQueuedConnection)
        if sink is not None:
            try:
                sink.videoFrameChanged.disconnect(self._receive_frame)
            except RuntimeError:
                pass
        with self._condition:
            self._image = None
            self._condition.notify_all()

    def _receive_frame(self, frame) -> None:
        if not frame.isValid():
            return
        image = frame.toImage()
        if image.isNull():
            return
        with self._condition:
            self._image = image.copy()
            self._condition.notify_all()

    def _select_device(self):
        devices = QMediaDevices.videoInputs()
        if not devices:
            return None
        if self._requested_device_id:
            requested = self._requested_device_id.encode("utf-8")
            for device in devices:
                if bytes(device.id()) == requested:
                    return device
        default = QMediaDevices.defaultVideoInput()
        return default if not default.isNull() else devices[0]


def camera_devices() -> tuple[tuple[str, str], ...]:
    return tuple((bytes(device.id()).decode("utf-8", errors="replace"), device.description()) for device in QMediaDevices.videoInputs())
