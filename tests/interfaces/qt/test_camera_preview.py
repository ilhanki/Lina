from PySide6.QtGui import QImage

from lina.interfaces.qt.camera_preview import CameraPreviewWindow, _fit_rect, _rendered_region_x
from lina.vision.live.models import CameraConversationState
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


def test_preview_is_mirrored_horizontally(qtbot):
    preview = CameraPreviewWindow("Test Camera", "session")
    qtbot.addWidget(preview)
    image = QImage(2, 1, QImage.Format.Format_RGB32)
    image.setPixel(0, 0, 0xFFFF0000)
    image.setPixel(1, 0, 0xFF0000FF)
    assert preview.set_frame(image, "session")
    assert preview.canvas._image.pixel(0, 0) == image.pixel(1, 0)
    assert preview.canvas._image.pixel(1, 0) == image.pixel(0, 0)


def test_preview_can_disable_mirror_and_boxes_follow_orientation(qtbot):
    preview = CameraPreviewWindow("Test Camera", "session", mirror_enabled=False)
    qtbot.addWidget(preview)
    image = QImage(2, 1, QImage.Format.Format_RGB32)
    image.setPixel(0, 0, 0xFFFF0000)
    image.setPixel(1, 0, 0xFF0000FF)
    preview.set_frame(image, "session")
    assert preview.canvas._image.pixel(0, 0) == image.pixel(0, 0)
    region = ChangeRegion(.1, .2, .3, .4, .8)
    assert _rendered_region_x(region, False) == .1
    assert round(_rendered_region_x(region, True), 3) == .6


def test_camera_conversation_controls_and_visible_states(qtbot):
    preview = CameraPreviewWindow("Test Camera", "session")
    qtbot.addWidget(preview)
    auto, mute = [], []
    preview.automatic_commentary_toggled.connect(auto.append)
    preview.mute_toggled.connect(mute.append)
    preview.auto_commentary_button.setChecked(False)
    preview.mute_button.setChecked(True)
    assert auto == [False] and mute == [True]
    preview.apply_conversation_state(CameraConversationState.LISTENING)
    assert preview.status_label.text() == "Seni dinliyorum"
    preview.apply_conversation_state(CameraConversationState.SPEAKING)
    assert preview.status_label.text() == "Cevap veriyorum"


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
