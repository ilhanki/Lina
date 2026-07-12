"""Models for temporary, local-only screen context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class ScreenCaptureError(RuntimeError):
    """Raised when a user-requested screen capture cannot be completed."""


@dataclass(frozen=True, slots=True)
class ScreenContext:
    """An in-memory screenshot attached to the current GUI session."""

    image_bytes: bytes
    width: int
    height: int
    captured_at: datetime
    display_name: str
    estimated_byte_size: int
    source: str = "screen_capture"
