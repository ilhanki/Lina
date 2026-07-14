from datetime import datetime, timezone
import threading
import time

from lina.vision.live.controller import LiveVisionController
from lina.vision.live.models import LiveVisionConfig, LiveVisionFrame, LiveVisionSession, LiveVisionSource, LiveVisionState


class Source:
    source = LiveVisionSource.SCREEN
    label = "Test Screen"
    def __init__(self): self.value = 0; self.started = 0; self.stopped = 0
    def is_available(self): return True
    def start(self): self.started += 1
    def capture(self):
        self.value += 1
        return LiveVisionFrame(bytes([self.value]), 2, 2, datetime.now(timezone.utc), self.source)
    def stop(self): self.stopped += 1


def session(**kwargs):
    return LiveVisionSession(LiveVisionSource.SCREEN, "hata çıkarsa söyle", LiveVisionConfig(capture_interval_seconds=.25, minimum_analysis_interval_seconds=kwargs.get("minimum", 0)))


def wait_until(predicate, timeout=2):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate(): return True
        time.sleep(.01)
    return False


def test_start_manual_analyze_pause_resume_stop_and_metrics():
    analyzed = []
    controller = LiveVisionController(lambda frame, prompt: analyzed.append((frame.data, prompt)) or "Yeni hata penceresi")
    source = Source(); controller.start(source, session())
    assert controller.snapshot.state is LiveVisionState.MONITORING
    assert controller.pause() and controller.snapshot.state is LiveVisionState.PAUSED
    assert controller.resume()
    assert controller.analyze_now()
    assert wait_until(lambda: bool(analyzed))
    assert "takip hedefi" in analyzed[0][1]
    assert controller.snapshot.metrics.analysis_request_count == 1
    assert controller.stop() and source.stopped >= 1
    assert controller.snapshot.state is LiveVisionState.IDLE


def test_single_frame_analysis_releases_source_and_keeps_result():
    controller = LiveVisionController(lambda _frame, _prompt: "Tek kare sonucu")
    source = Source(); controller.analyze_once(source, session())
    assert wait_until(lambda: controller.snapshot.state is LiveVisionState.IDLE)
    assert controller.snapshot.last_result == "Tek kare sonucu"
    assert source.stopped >= 1


def test_latest_frame_wins_and_pending_queue_is_bounded():
    entered = threading.Event(); release = threading.Event(); seen = []
    def analyze(frame, _prompt):
        seen.append(frame.data); entered.set(); release.wait(2); return "ok"
    controller = LiveVisionController(analyze)
    source = Source(); controller.start(source, session())
    controller.analyze_now(); assert entered.wait(1)
    controller.analyze_now(); controller.analyze_now(); controller.analyze_now()
    release.set()
    assert wait_until(lambda: len(seen) == 2)
    assert seen[-1] == bytes([5])
    assert controller.snapshot.metrics.dropped_frame_count >= 2
    controller.stop()


def test_stale_result_is_ignored_and_cancel_is_called_on_stop():
    entered = threading.Event(); release = threading.Event(); cancelled = []
    def analyze(_frame, _prompt): entered.set(); release.wait(2); return "stale"
    controller = LiveVisionController(analyze, cancel_analysis=lambda: cancelled.append(True))
    source = Source(); controller.start(source, session()); controller.analyze_now(); assert entered.wait(1)
    stopper = threading.Thread(target=controller.stop); stopper.start(); time.sleep(.05); release.set(); stopper.join(2)
    assert cancelled and controller.snapshot.last_result != "stale"


def test_voice_feedback_suppresses_repeated_result():
    spoken = []
    controller = LiveVisionController(lambda _frame, _prompt: "Aynı değişiklik", speaker=lambda text: spoken.append(text) or True)
    source = Source(); controller.start(source, session()); controller.analyze_now()
    assert wait_until(lambda: len(spoken) == 1)
    controller.analyze_now(); time.sleep(.1)
    assert spoken == ["Aynı değişiklik"]
    controller.shutdown()
