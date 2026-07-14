from PySide6.QtGui import QImage

from lina.interfaces.qt.camera_preview import CameraPreviewWindow, _fit_rect
from lina.vision.live.models import ChangeRegion, LiveVisionState


def test_preview_receives_frame_and_rejects_stale_session(qtbot):
    preview = CameraPreviewWindow("Test Camera", "current")
    qtbot.addWidget(preview)
    image = QImage(640, 360, QImage.Format.Format_RGB32)
    image.fill(0x336699)
    assert not preview.set_frame(image, "stale")
    assert preview.canvas._image.isNull()
    assert preview.set_frame(image, "current")
    assert not preview.canvas._image.isNull()


def test_preview_boxes_status_controls_hide_and_show(qtbot):
    preview = CameraPreviewWindow("Test Camera", "session")
    qtbot.addWidget(preview)
    preview.show(); qtbot.wait(10)
    region = ChangeRegion(.1, .2, .3, .4, .8)
    assert preview.set_change_regions((region,), "session")
    assert preview.canvas.regions == (region,)
    preview.apply_state(LiveVisionState.PAUSED)
    assert preview.pause_button.text() == "Devam Et"
    assert "Duraklatıldı" in preview.status_label.text()
    preview.hide_button.click()
    assert not preview.isVisible()
    preview.show()
    assert preview.isVisible()
    preview._expire_regions(preview._region_generation)
    assert preview.canvas.regions == ()


def test_preview_control_signals_and_permanent_cleanup(qtbot):
    preview = CameraPreviewWindow("Test Camera", "session")
    qtbot.addWidget(preview)
    calls = []
    preview.analyze_requested.connect(lambda: calls.append("analyze"))
    preview.pause_requested.connect(lambda: calls.append("pause"))
    preview.stop_requested.connect(lambda: calls.append("stop"))
    preview.analyze_button.click(); preview.pause_button.click(); preview.stop_button.click()
    assert calls == ["analyze", "pause", "stop"]
    preview.close_permanently()
    assert preview.canvas._image.isNull()


def test_fit_rect_preserves_aspect_ratio():
    rectangle = _fit_rect(400, 400, 640, 360)
    assert round(rectangle.width()) == 400
    assert round(rectangle.height()) == 225
