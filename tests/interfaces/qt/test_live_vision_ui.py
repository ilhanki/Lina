from datetime import datetime, timezone

from PySide6.QtCore import QRect
from PySide6.QtGui import QImage

from lina.brain.model_provider import ModelResponse
from lina.brain.routing.models import IntentRequest, IntentType
import lina.interfaces.qt.main_window as main_window_module
from lina.interfaces.qt.main_window import LinaMainWindow
from lina.interfaces.qt.monitoring_overlay import MonitoringBorderOverlay
from lina.vision.live.models import LiveVisionFrame, LiveVisionMetrics, LiveVisionSnapshot, LiveVisionSource, LiveVisionState


class Conversation:
    def handle_message(self, _message): return ModelResponse("ok")


class Controller:
    def __init__(self):
        self.snapshot = LiveVisionSnapshot(LiveVisionState.IDLE)
        self.listener = None; self.analyze_count = 0; self.pause_count = 0; self.stop_count = 0; self.shutdown_count = 0; self.start_count = 0
    def subscribe(self, listener): self.listener = listener
    def subscribe_preview_frame(self, listener): self.preview_listener = listener
    def subscribe_change_regions(self, listener): self.change_listener = listener
    def subscribe_session_stopped(self, listener): self.stopped_listener = listener
    def start(self, source, session, **kwargs):
        self.start_count += 1
        self.start_kwargs = kwargs
        source.start()
        self.source = source
        self.snapshot = LiveVisionSnapshot(LiveVisionState.MONITORING, session.source, source.label, session.session_id)
        return session.session_id
    def update_overlay_geometry(self, geometry): self.overlay_geometry = geometry; return True
    def analyze_now(self): self.analyze_count += 1; return True
    def pause(self): self.pause_count += 1; return True
    def resume(self): return True
    def stop(self): self.stop_count += 1; return True
    def shutdown(self): self.shutdown_count += 1


class CameraBackend:
    device_name = "Test Camera"
    def __init__(self, _device=None): self.preview = None; self.error = None; self.started = False
    def is_available(self): return True
    def start(self): self.started = True
    def stop(self): self.started = False
    def capture(self): return b"png", 10, 10, "image/png"
    def subscribe_preview(self, listener): self.preview = listener
    def subscribe_error(self, listener): self.error = listener
    def clear_listeners(self): self.preview = None; self.error = None


class Screen:
    def __init__(self, geometry=QRect(100, 200, 800, 600), name="Display 2"):
        self._geometry = geometry; self._name = name
    def geometry(self): return QRect(self._geometry)
    def name(self): return self._name


class ScreenCapture:
    def capture(self): return None
    def capture_screen(self, screen): return None
    def capture_region(self, rectangle, screen): return None


class ImmediatePool:
    def start(self, worker): worker.run()


def test_live_vision_panel_shows_privacy_state_result_and_controls(qtbot):
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    window.show(); qtbot.wait(10)
    snapshot = LiveVisionSnapshot(
        LiveVisionState.MONITORING, LiveVisionSource.CAMERA, "Integrated Camera", "session",
        datetime.now(timezone.utc), "Elindeki nesne bir adaptöre benziyor.", metrics=LiveVisionMetrics(source=LiveVisionSource.CAMERA),
    )
    controller.snapshot = snapshot
    window._apply_live_vision_snapshot(snapshot)
    assert "Kamera" in window._live_indicator.text()
    assert "Takip ediliyor" in window._live_indicator.text()
    assert "adaptöre" in window._live_result.text()
    assert window._live_analyze.isEnabled() and window._live_stop.isEnabled()
    window._live_analyze.click()
    assert controller.analyze_count == 1


def test_live_vision_pause_and_unavailable_states_are_textual(qtbot):
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    window.show(); qtbot.wait(10)
    paused = LiveVisionSnapshot(LiveVisionState.PAUSED, LiveVisionSource.SCREEN, "Display")
    controller.snapshot = paused
    window._apply_live_vision_snapshot(paused)
    assert "Duraklatıldı" in window._live_indicator.text()
    assert window._live_pause.text() == "Devam Et"
    window._apply_live_vision_snapshot(LiveVisionSnapshot(LiveVisionState.UNAVAILABLE, user_message="Kameraya erişilemiyor."))
    assert "Kameraya erişilemiyor" in window._live_result.text()
    assert not window._live_stop.isEnabled()


def test_camera_question_without_active_camera_gets_clear_answer(qtbot):
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    window._composer.input.setPlainText("Ne görüyorsun?")
    window.send_message()
    assert window._last_response_text == "Kamera şu anda açık değil."


def test_close_shuts_live_vision_down(qtbot):
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    window.show(); qtbot.wait(10)
    window.close()
    assert controller.shutdown_count == 1


def test_camera_session_opens_one_preview_and_hidden_preview_keeps_indicator(qtbot, monkeypatch):
    monkeypatch.setattr(main_window_module, "QtCameraBackend", CameraBackend)
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    result = window._execute_live_intent(IntentRequest(IntentType.CAMERA_MONITOR, 1, "Kamerayı izle"))
    assert result.success
    assert window._camera_preview is not None and window._camera_preview.isVisible()
    first = window._camera_preview
    window._show_camera_preview("Test Camera", window._live_session_id)
    assert window._camera_preview is not first
    snapshot = LiveVisionSnapshot(LiveVisionState.MONITORING, LiveVisionSource.CAMERA, "Test Camera", window._live_session_id)
    window._apply_live_vision_snapshot(snapshot)
    window._camera_preview.hide_preview()
    assert "Kamera" in window._live_indicator.text()
    assert window._live_show_preview.isEnabled()


def test_camera_open_immediately_analyzes_and_current_frame_becomes_question_context(qtbot, monkeypatch):
    monkeypatch.setattr(main_window_module, "QtCameraBackend", CameraBackend)

    class QuestionController(Controller):
        def capture_current_frame(self, _question=""):
            return LiveVisionFrame(
                b"ephemeral-png", 10, 10, datetime.now(timezone.utc),
                LiveVisionSource.CAMERA, source_label="Test Camera",
            )

    controller = QuestionController()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    result = window._execute_live_intent(IntentRequest(IntentType.CAMERA_OPEN, 1, "Kamerayı aç"))
    assert result.success
    assert controller.start_kwargs["analyze_immediately"] is True
    context = window._capture_live_camera_context()
    assert context is not None
    assert context.source == main_window_module.LIVE_CAMERA_CONTEXT
    assert context.display_name == "Test Camera"


def test_stale_camera_image_is_ignored_and_current_image_is_rendered(qtbot):
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    window._live_session_id = "current"
    window._show_camera_preview("Test Camera", "current")
    image = QImage(20, 20, QImage.Format.Format_RGB32)
    window._apply_camera_image(image, "stale")
    assert window._camera_preview.canvas._image.isNull()
    window._apply_camera_image(image, "current")
    assert not window._camera_preview.canvas._image.isNull()


def test_idle_state_closes_preview_and_mandatory_overlay(qtbot):
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    window._live_session_id = "session"
    window._show_camera_preview("Test Camera", "session")
    overlay = MonitoringBorderOverlay(lambda: QRect(0, 0, 100, 100), "Lina ekranı izliyor")
    window._monitoring_overlay = overlay
    overlay.show()
    window._apply_live_vision_snapshot(LiveVisionSnapshot(LiveVisionState.IDLE))
    assert window._camera_preview is None
    assert window._monitoring_overlay is None
    assert not overlay.isVisible()


def test_full_screen_and_region_overlays_follow_geometry_and_pause(qtbot):
    controller = Controller()
    screen = Screen()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, screen_capture_service=ScreenCapture(), thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    window._start_screen_monitor(screen, "")
    assert window._monitoring_overlay.geometry() == screen.geometry()
    assert controller.overlay_geometry.width == 800
    screen._geometry = QRect(300, 400, 1024, 768)
    window._monitoring_overlay.refresh_geometry()
    assert window._monitoring_overlay.geometry() == screen.geometry()
    window._apply_live_vision_snapshot(LiveVisionSnapshot(LiveVisionState.PAUSED, LiveVisionSource.SCREEN, "Display 2", window._live_session_id))
    assert window._monitoring_overlay.paused
    window._start_region_monitor(screen, QRect(20, 30, 200, 100), "")
    assert window._monitoring_overlay.geometry() == QRect(320, 430, 200, 100)


def test_monitoring_does_not_start_when_privacy_border_cannot_show(qtbot, monkeypatch):
    class InvisibleOverlay(MonitoringBorderOverlay):
        def show(self): pass

    monkeypatch.setattr(main_window_module, "MonitoringBorderOverlay", InvisibleOverlay)
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, screen_capture_service=ScreenCapture(), thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    try:
        window._start_screen_monitor(Screen(), "")
    except Exception as error:
        assert "çerçevesi" in str(error)
    else:
        raise AssertionError("Monitoring started without its mandatory privacy border")
    assert controller.start_count == 0
