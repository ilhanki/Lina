"""Local input-device discovery and safe default fallback."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import sounddevice


_logger = logging.getLogger("lina.voice")


@dataclass(frozen=True, slots=True)
class AudioInputDevice:
    id: int
    name: str
    channels: int
    is_default: bool = False


class AudioInputDeviceService:
    def __init__(self, backend: Any = sounddevice) -> None:
        self._backend = backend

    def list_devices(self) -> tuple[AudioInputDevice, ...]:
        try:
            raw_devices = self._backend.query_devices()
            default_id = self._default_device_id()
        except Exception:
            return ()
        devices = []
        for index, raw in enumerate(raw_devices):
            channels = int(raw.get("max_input_channels", 0))
            if channels <= 0:
                continue
            devices.append(
                AudioInputDevice(
                    id=index,
                    name=str(raw.get("name", f"Input {index}")),
                    channels=channels,
                    is_default=index == default_id,
                )
            )
        return tuple(devices)

    def resolve(self, selected_id: int | None) -> int | None:
        devices = self.list_devices()
        if selected_id is not None and any(device.id == selected_id for device in devices):
            return selected_id
        if selected_id is not None:
            _logger.warning("audio_input_fallback reason=selected_device_unavailable")
        default = next((device for device in devices if device.is_default), None)
        return default.id if default is not None else (devices[0].id if devices else None)

    def is_available(self, selected_id: int | None = None) -> bool:
        return self.resolve(selected_id) is not None

    def test_device(self, selected_id: int | None = None) -> bool:
        device_id = self.resolve(selected_id)
        if device_id is None:
            return False
        try:
            details = self._backend.query_devices(device_id)
        except Exception:
            return False
        return int(details.get("max_input_channels", 0)) > 0

    def _default_device_id(self) -> int | None:
        default = getattr(self._backend, "default", None)
        value = getattr(default, "device", None)
        if isinstance(value, (tuple, list)) and value:
            return int(value[0]) if int(value[0]) >= 0 else None
        if isinstance(value, int):
            return value if value >= 0 else None
        try:
            device = self._backend.query_devices(kind="input")
        except Exception:
            return None
        all_devices = self._backend.query_devices()
        for index, candidate in enumerate(all_devices):
            if candidate.get("name") == device.get("name"):
                return index
        return None
