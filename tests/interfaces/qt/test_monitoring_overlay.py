from PySide6.QtCore import QRect, Qt

from lina.interfaces.qt.monitoring_overlay import MonitoringBorderOverlay


def test_overlay_is_click_through_tool_without_focus(qtbot):
    overlay = MonitoringBorderOverlay(lambda: QRect(10, 20, 800, 600), "Lina ekranı izliyor")
    qtbot.addWidget(overlay)
    assert overlay.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    assert overlay.windowFlags() & Qt.WindowType.Tool
    assert overlay.windowFlags() & Qt.WindowType.WindowTransparentForInput
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    assert overlay.focusPolicy() is Qt.FocusPolicy.NoFocus


def test_overlay_geometry_pause_resume_and_close(qtbot):
    geometry = {"value": QRect(0, 0, 640, 480)}
    overlay = MonitoringBorderOverlay(lambda: geometry["value"], "Lina bu bölgeyi izliyor")
    qtbot.addWidget(overlay)
    overlay.start(); qtbot.wait(10)
    assert overlay.geometry() == QRect(0, 0, 640, 480)
    overlay.set_paused(True)
    assert overlay.paused and overlay.windowOpacity() < 1
    overlay.set_paused(False)
    assert not overlay.paused and overlay.windowOpacity() == 1
    geometry["value"] = QRect(100, 200, 320, 240)
    overlay.refresh_geometry()
    assert overlay.geometry() == geometry["value"]
    overlay.close_permanently()
    assert not overlay.isVisible()


def test_unexpected_overlay_close_is_observable(qtbot):
    overlay = MonitoringBorderOverlay(lambda: QRect(0, 0, 100, 100), "Lina ekranı izliyor")
    qtbot.addWidget(overlay)
    closed = []
    overlay.closed_unexpectedly.connect(lambda: closed.append(True))
    overlay.show(); overlay.close()
    assert closed == [True]
