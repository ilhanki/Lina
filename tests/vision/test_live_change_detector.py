from datetime import datetime, timezone

import pytest

from lina.vision.live.change_detector import FrameChangeDetector
from lina.vision.live.models import ChangeSensitivity, LiveVisionFrame, LiveVisionSource


def frame(value: int = 0) -> LiveVisionFrame:
    return LiveVisionFrame(bytes([value + 1]), 2, 2, datetime.now(timezone.utc), LiveVisionSource.SCREEN)


def signature_builder(item, size):
    return (item.data[0] - 1,) * (size * size)


@pytest.mark.parametrize("sensitivity,delta,expected", [
    (ChangeSensitivity.LOW, 40, False),
    (ChangeSensitivity.MEDIUM, 40, True),
    (ChangeSensitivity.HIGH, 20, True),
])
def test_sensitivity_presets(sensitivity, delta, expected):
    detector = FrameChangeDetector(sensitivity, signature_builder=signature_builder)
    assert detector.observe(frame(0)) is False
    assert detector.observe(frame(delta)) is expected


def test_identical_and_small_noise_are_ignored():
    detector = FrameChangeDetector(signature_builder=signature_builder)
    assert not detector.observe(frame(30))
    assert not detector.observe(frame(30))
    assert not detector.observe(frame(35))


def test_meaningful_change_updates_baseline_deterministically():
    detector = FrameChangeDetector(signature_builder=signature_builder)
    detector.observe(frame(0))
    assert detector.observe(frame(100))
    assert not detector.observe(frame(100))
    detector.reset()
    assert not detector.observe(frame(100))


def test_empty_signature_is_safe():
    detector = FrameChangeDetector(signature_builder=lambda _frame, _size: ())
    assert detector.observe(frame()) is False


def test_invalid_signature_size_is_rejected():
    with pytest.raises(ValueError):
        FrameChangeDetector(signature_size=1)
