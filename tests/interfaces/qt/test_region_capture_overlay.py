"""Tests for the region capture overlay interaction model."""

from PySide6.QtCore import QPoint, QRect, Qt

from lina.interfaces.qt.region_capture_overlay import MIN_REGION_SIZE, RegionCaptureOverlay


def test_region_overlay_normalizes_reversed_drag_and_emits_selection(qtbot) -> None:
    overlay = RegionCaptureOverlay(QRect(100, 50, 800, 600))
    qtbot.addWidget(overlay)

    with qtbot.waitSignal(overlay.region_selected, timeout=1000) as signal:
        qtbot.mousePress(overlay, Qt.MouseButton.LeftButton, pos=QPoint(700, 500))
        qtbot.mouseMove(overlay, QPoint(100, 100), delay=1)
        qtbot.mouseRelease(overlay, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))

    rectangle = signal.args[0]
    assert rectangle.left() == 101
    assert rectangle.top() == 101
    assert rectangle.width() == 599
    assert rectangle.height() == 399


def test_region_overlay_rejects_small_selection(qtbot) -> None:
    overlay = RegionCaptureOverlay(QRect(0, 0, 800, 600))
    qtbot.addWidget(overlay)
    selected = []
    overlay.region_selected.connect(selected.append)

    qtbot.mousePress(overlay, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
    qtbot.mouseRelease(
        overlay,
        Qt.MouseButton.LeftButton,
        pos=QPoint(MIN_REGION_SIZE - 1, MIN_REGION_SIZE - 1),
    )

    assert selected == []


def test_region_overlay_escape_and_right_click_cancel(qtbot) -> None:
    overlay = RegionCaptureOverlay(QRect(0, 0, 800, 600))
    qtbot.addWidget(overlay)

    with qtbot.waitSignal(overlay.canceled, timeout=1000):
        qtbot.keyClick(overlay, Qt.Key.Key_Escape)

    overlay = RegionCaptureOverlay(QRect(0, 0, 800, 600))
    qtbot.addWidget(overlay)
    with qtbot.waitSignal(overlay.canceled, timeout=1000):
        qtbot.mouseClick(overlay, Qt.MouseButton.RightButton, pos=QPoint(20, 20))


def test_region_overlay_enter_confirms_existing_selection(qtbot) -> None:
    overlay = RegionCaptureOverlay(QRect(0, 0, 800, 600))
    qtbot.addWidget(overlay)
    emitted = []
    overlay.region_selected.connect(emitted.append)
    overlay._selection = QRect(20, 20, 100, 80)

    qtbot.keyClick(overlay, Qt.Key.Key_Return)

    assert emitted == [QRect(20, 20, 100, 80)]
