"""Framework-neutral models for local vision requests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class ImageValidationError(ValueError):
    """Raised when an image attachment is unsafe or malformed."""


@dataclass(frozen=True, slots=True)
class ImageAttachment:
    """One in-memory PNG attachment for a single conversation request."""

    mime_type: str
    data: bytes
    width: int
    height: int
    captured_at: datetime
    source: str
    display_name: str

    def __post_init__(self) -> None:
        if self.mime_type != "image/png":
            raise ImageValidationError("Image attachment must use image/png")
        if not self.data:
            raise ImageValidationError("Image attachment data must not be empty")
        if not self.data.startswith(PNG_SIGNATURE):
            raise ImageValidationError("Image attachment must contain valid PNG data")
        if self.width <= 0 or self.height <= 0:
            raise ImageValidationError("Image dimensions must be positive")

    @property
    def byte_size(self) -> int:
        """Return the in-memory encoded image size."""
        return len(self.data)
