"""Tests for the Qt screen capture adapter."""

from datetime import datetime

import pytest
from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPixmap

from lina.interfaces.qt.screen_capture import QtScreenCaptureService
from lina.screen.models import SCREEN_CAPTURE_REGION, ScreenCaptureError


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

    def geometry(self) -> QRect:
        return QRect(10, 20, self._pixmap.width(), self._pixmap.height())

    def devicePixelRatio(self) -> float:
        return 1.0


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


def test_capture_screen_uses_explicit_non_primary_monitor(qtbot) -> None:
    pixmap = QPixmap(640, 360)
    pixmap.fill()
    secondary = FakeScreen(pixmap, "Display 2")
    service = QtScreenCaptureService(
        screen_at=lambda _position: None,
        primary_screen=lambda: None,
        cursor_position=lambda: QPoint(),
    )
    context = service.capture_screen(secondary)
    assert context.source_screen_name == "Display 2"
    assert context.width == 640 and context.height == 360
    assert secondary.capture_count == 1


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


def test_capture_region_crops_logical_screen_rectangle(qtbot) -> None:
    pixmap = QPixmap(200, 100)
    pixmap.fill()
    screen = FakeScreen(pixmap, "Display 1")
    service = QtScreenCaptureService(
        screen_at=lambda position: screen,
        primary_screen=lambda: None,
        cursor_position=lambda: QPoint(20, 30),
    )

    context = service.capture_region(QRect(30, 40, 80, 50), screen)

    assert context.source == SCREEN_CAPTURE_REGION
    assert context.display_name == "Seçili Ekran Alanı"
    assert context.source_screen_name == "Display 1"
    assert context.width == 80
    assert context.height == 50
