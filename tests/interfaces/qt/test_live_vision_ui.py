from datetime import datetime, timezone

from lina.brain.model_provider import ModelResponse
from lina.interfaces.qt.main_window import LinaMainWindow
from lina.vision.live.models import LiveVisionMetrics, LiveVisionSnapshot, LiveVisionSource, LiveVisionState


class Conversation:
    def handle_message(self, _message): return ModelResponse("ok")


class Controller:
    def __init__(self):
        self.snapshot = LiveVisionSnapshot(LiveVisionState.IDLE)
        self.listener = None; self.analyze_count = 0; self.pause_count = 0; self.stop_count = 0; self.shutdown_count = 0
    def subscribe(self, listener): self.listener = listener
    def analyze_now(self): self.analyze_count += 1; return True
    def pause(self): self.pause_count += 1; return True
    def resume(self): return True
    def stop(self): self.stop_count += 1; return True
    def shutdown(self): self.shutdown_count += 1


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


def test_close_shuts_live_vision_down(qtbot):
    controller = Controller()
    window = LinaMainWindow(Conversation(), live_vision_controller=controller, thread_pool=ImmediatePool())
    qtbot.addWidget(window)
    window.show(); qtbot.wait(10)
    window.close()
    assert controller.shutdown_count == 1
