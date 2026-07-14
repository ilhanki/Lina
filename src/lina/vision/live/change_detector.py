"""Deterministic, dependency-free image change detection."""

from __future__ import annotations

from io import BytesIO
from typing import Callable

from lina.vision.live.models import ChangeRegion, ChangeSensitivity, LiveVisionFrame


_THRESHOLDS = {ChangeSensitivity.LOW: 0.22, ChangeSensitivity.MEDIUM: 0.12, ChangeSensitivity.HIGH: 0.055}
_BLOCK_THRESHOLDS = {ChangeSensitivity.LOW: 56, ChangeSensitivity.MEDIUM: 32, ChangeSensitivity.HIGH: 14}


class FrameChangeDetector:
    """Compare small luminance signatures; never retains encoded image bytes."""

    def __init__(self, sensitivity: ChangeSensitivity = ChangeSensitivity.MEDIUM, signature_size: int = 16, signature_builder: Callable[[LiveVisionFrame, int], tuple[int, ...]] | None = None) -> None:
        if signature_size < 2:
            raise ValueError("Signature size must be at least 2")
        self.sensitivity = sensitivity
        self.signature_size = signature_size
        self._signature_builder = signature_builder or _qt_luminance_signature
        self._baseline: tuple[int, ...] | None = None
        self.last_difference = 0.0
        self.last_regions: tuple[ChangeRegion, ...] = ()

    def reset(self) -> None:
        self._baseline = None
        self.last_difference = 0.0
        self.last_regions = ()

    def observe(self, frame: LiveVisionFrame, *, update_on_change: bool = True) -> bool:
        signature = self._signature_builder(frame, self.signature_size)
        if not signature:
            self.last_regions = ()
            return False
        if self._baseline is None or len(self._baseline) != len(signature):
            self._baseline = signature
            self.last_regions = ()
            return False
        self.last_difference = sum(abs(a - b) for a, b in zip(self._baseline, signature)) / (255 * len(signature))
        self.last_regions = _change_regions(
            self._baseline,
            signature,
            self.signature_size,
            _BLOCK_THRESHOLDS[self.sensitivity],
        )
        changed = self.last_difference >= _THRESHOLDS[self.sensitivity] or bool(self.last_regions)
        if changed and update_on_change:
            self._baseline = signature
        return changed

    def accept_baseline(self, frame: LiveVisionFrame) -> None:
        signature = self._signature_builder(frame, self.signature_size)
        if signature:
            self._baseline = signature


def _qt_luminance_signature(frame: LiveVisionFrame, size: int) -> tuple[int, ...]:
    """Decode in memory with Qt, downscale and return luminance only."""
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QImage
        image = QImage.fromData(frame.data)
        if image.isNull():
            return ()
        image = image.scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation).convertToFormat(QImage.Format.Format_RGB32)
        return tuple((299 * image.pixelColor(x, y).red() + 587 * image.pixelColor(x, y).green() + 114 * image.pixelColor(x, y).blue()) // 1000 for y in range(size) for x in range(size))
    except Exception:
        return _byte_signature(frame.data, size * size)


def _byte_signature(data: bytes, count: int) -> tuple[int, ...]:
    if not data:
        return ()
    step = max(1, len(data) // count)
    values = tuple(data[index] for index in range(0, len(data), step))
    return values[:count]


def _change_regions(
    previous: tuple[int, ...],
    current: tuple[int, ...],
    size: int,
    threshold: int,
    *,
    minimum_blocks: int = 2,
    maximum_regions: int = 5,
) -> tuple[ChangeRegion, ...]:
    """Merge adjacent changed grid cells into normalized motion/change boxes."""
    changed = {
        (index % size, index // size)
        for index, (before, after) in enumerate(zip(previous, current))
        if abs(before - after) >= threshold
    }
    components: list[tuple[int, int, int, int, int, float]] = []
    while changed:
        seed = changed.pop()
        stack = [seed]
        cells = [seed]
        while stack:
            x, y = stack.pop()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in changed:
                    changed.remove(neighbor)
                    stack.append(neighbor)
                    cells.append(neighbor)
        if len(cells) < minimum_blocks:
            continue
        xs = [cell[0] for cell in cells]
        ys = [cell[1] for cell in cells]
        mean_delta = sum(abs(previous[y * size + x] - current[y * size + x]) for x, y in cells) / (255 * len(cells))
        components.append((min(xs), min(ys), max(xs), max(ys), len(cells), mean_delta))
    components.sort(key=lambda item: (item[4], item[5]), reverse=True)
    return tuple(
        ChangeRegion(
            left / size,
            top / size,
            (right - left + 1) / size,
            (bottom - top + 1) / size,
            min(1.0, score),
        )
        for left, top, right, bottom, _count, score in components[:maximum_regions]
    )
