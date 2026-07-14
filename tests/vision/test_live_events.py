from datetime import datetime, timezone
import time

from lina.vision.live.controller import LiveVisionController
from lina.vision.live.models import LiveVisionConfig, LiveVisionFrame, LiveVisionSession, LiveVisionSource, OverlayGeometry


class Source:
    source = LiveVisionSource.SCREEN
    label = "Display"
    def __init__(self): self.stopped = False
    def start(self): pass
    def stop(self): self.stopped = True
    def is_available(self): return True
    def capture(self): return LiveVisionFrame(b"frame", 4, 4, datetime.now(timezone.utc), self.source)


def wait_until(predicate):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if predicate(): return True
        time.sleep(.01)
    return False


def test_controller_emits_preview_change_geometry_state_and_stopped_events():
    controller = LiveVisionController(lambda _frame, _prompt: "ok")
    previews, changes, geometries, states, stopped = [], [], [], [], []
    controller.subscribe_preview_frame(previews.append)
    controller.subscribe_change_regions(changes.append)
    controller.subscribe_overlay_geometry(geometries.append)
    controller.subscribe(states.append)
    controller.subscribe_session_stopped(stopped.append)
    session = LiveVisionSession(LiveVisionSource.SCREEN, config=LiveVisionConfig(capture_interval_seconds=.25, minimum_analysis_interval_seconds=0))
    source = Source()
    controller.start(source, session)
    assert wait_until(lambda: previews and changes)
    assert previews[0].session_id == session.session_id
    geometry = OverlayGeometry(10, 20, 800, 600, "Display")
    assert controller.update_overlay_geometry(geometry)
    assert geometries[-1].geometry == geometry
    assert states[-1].session_id == session.session_id
    controller.stop()
    assert stopped[-1].session_id == session.session_id
    assert source.stopped


def test_overlay_geometry_rejected_without_screen_session():
    controller = LiveVisionController(lambda _frame, _prompt: "ok")
    assert not controller.update_overlay_geometry(OverlayGeometry(0, 0, 10, 10))
