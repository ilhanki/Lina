"""Tests for the Qt screen capture adapter."""

from datetime import datetime

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap

from lina.interfaces.qt.screen_capture import QtScreenCaptureService
from lina.screen.models import ScreenCaptureError


class FakeScreen:
    def __init__(self, pixmap: QPixmap, name: str = "Display 1") -> None:
        self._pixmap = pixmap
        self._name = name
        self.capture_count = 0

    def grabWindow(self, window_id: int) -> QPixmap:
        assert window_id == 0
        self.capture_count += 1
        return self._pixmap

    def name(self) -> str:
        return self._name


def test_capture_uses_cursor_screen_and_returns_metadata(qtbot) -> None:
    pixmap = QPixmap(320, 180)
    pixmap.fill()
    screen = FakeScreen(pixmap)
    captured_at = datetime(2026, 7, 11, 21, 30)
    primary_calls = 0

    def primary_screen():
        nonlocal primary_calls
        primary_calls += 1
        return None

    service = QtScreenCaptureService(
        screen_at=lambda position: screen,
        primary_screen=primary_screen,
        cursor_position=lambda: QPoint(10, 20),
        now=lambda: captured_at,
    )

    context = service.capture()

    assert context.width == 320
    assert context.height == 180
    assert context.display_name == "Display 1"
    assert context.captured_at == captured_at
    assert context.image_bytes.startswith(b"\x89PNG")
    assert context.estimated_byte_size == len(context.image_bytes)
    assert screen.capture_count == 1
    assert primary_calls == 0


def test_capture_falls_back_to_primary_screen(qtbot) -> None:
    pixmap = QPixmap(100, 80)
    pixmap.fill()
    primary = FakeScreen(pixmap, "Primary")
    service = QtScreenCaptureService(
        screen_at=lambda position: None,
        primary_screen=lambda: primary,
        cursor_position=lambda: QPoint(),
    )

    context = service.capture()

    assert context.display_name == "Primary"
    assert context.width == 100
    assert context.height == 80


def test_capture_raises_when_no_screen_is_available() -> None:
    service = QtScreenCaptureService(
        screen_at=lambda position: None,
        primary_screen=lambda: None,
        cursor_position=lambda: QPoint(),
    )

    with pytest.raises(ScreenCaptureError, match="No screen"):
        service.capture()


def test_capture_raises_for_null_pixmap(qtbot) -> None:
    screen = FakeScreen(QPixmap(), "Empty")
    service = QtScreenCaptureService(
        screen_at=lambda position: screen,
        primary_screen=lambda: None,
        cursor_position=lambda: QPoint(),
    )

    with pytest.raises(ScreenCaptureError, match="empty image"):
        service.capture()
