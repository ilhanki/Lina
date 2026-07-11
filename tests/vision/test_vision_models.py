"""Tests for framework-neutral vision request models."""

from datetime import datetime

import pytest

from lina.vision.models import ImageAttachment, ImageValidationError, PNG_SIGNATURE


def _attachment(**overrides) -> ImageAttachment:
    values = {
        "mime_type": "image/png",
        "data": PNG_SIGNATURE + b"encoded-image",
        "width": 1920,
        "height": 1080,
        "captured_at": datetime(2026, 7, 11, 23, 30),
        "source": "screen_capture",
        "display_name": "Display 1",
    }
    values.update(overrides)
    return ImageAttachment(**values)


def test_image_attachment_keeps_framework_neutral_metadata() -> None:
    attachment = _attachment()

    assert attachment.mime_type == "image/png"
    assert attachment.width == 1920
    assert attachment.height == 1080
    assert attachment.byte_size == len(attachment.data)


@pytest.mark.parametrize(
    ("overrides", "error_message"),
    [
        ({"data": b""}, "must not be empty"),
        ({"data": b"not-png"}, "valid PNG"),
        ({"mime_type": "image/jpeg"}, "image/png"),
        ({"width": 0}, "positive"),
        ({"height": -1}, "positive"),
    ],
)
def test_invalid_image_attachment_is_rejected(overrides, error_message) -> None:
    with pytest.raises(ImageValidationError, match=error_message):
        _attachment(**overrides)
