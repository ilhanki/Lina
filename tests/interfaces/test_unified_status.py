from lina.interfaces.status import StatusPriority, UnifiedStatusController


def test_unified_status_rejects_stale_callback():
    status = UnifiedStatusController()
    assert status.publish("Düşünüyorum", generation=4)
    assert not status.publish("Hazır", generation=3)
    assert status.current.text == "Düşünüyorum"


def test_unified_status_keeps_secondary_indicators():
    status = UnifiedStatusController()
    status.publish("Agent onay bekliyor", priority=StatusPriority.ATTENTION, secondary=("Mic açık", "Vision açık"))
    assert status.current.secondary == ("Mic açık", "Vision açık")
