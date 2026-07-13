"""Opt-in wake-word contract; no always-on detector is bundled."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class WakeWordDetector(Protocol):
    def is_available(self) -> bool: ...
    def start(self, callback: Callable[[], None]) -> None: ...
    def stop(self) -> None: ...


class UnavailableWakeWordDetector:
    def is_available(self) -> bool:
        return False

    def start(self, callback: Callable[[], None]) -> None:
        raise RuntimeError("Wake-word detector is unavailable")

    def stop(self) -> None:
        return None
