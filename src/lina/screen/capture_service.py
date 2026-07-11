"""Contract for explicit, user-triggered screen capture."""

from __future__ import annotations

from typing import Protocol

from lina.screen.models import ScreenContext


class ScreenCaptureService(Protocol):
    """Capture one screen into temporary in-memory context."""

    def capture(self) -> ScreenContext:
        """Capture the active screen without writing it to disk."""
        ...
