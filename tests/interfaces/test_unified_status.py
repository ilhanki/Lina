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


def test_unified_status_rejects_lower_priority_for_same_generation():
    status = UnifiedStatusController()
    assert status.publish("Güvenlik engeli", priority=StatusPriority.SECURITY, generation=8)
    assert not status.publish("Hazır", priority=StatusPriority.READY, generation=8)
    assert status.current.text == "Güvenlik engeli"


def test_unified_status_allows_newer_generation_to_clear_attention():
    status = UnifiedStatusController()
    status.publish("Onay bekleniyor", priority=StatusPriority.ATTENTION, generation=8)
    assert status.publish("Hazır", priority=StatusPriority.READY, generation=9)
    assert status.current.text == "Hazır"


def test_status_priority_matches_product_activity_order():
    assert StatusPriority.ERROR > StatusPriority.SECURITY
    assert StatusPriority.SECURITY > StatusPriority.ATTENTION
    assert StatusPriority.ATTENTION > StatusPriority.RUNTIME_APPROVAL
    assert StatusPriority.LISTENING > StatusPriority.TRANSCRIBING
    assert StatusPriority.TRANSCRIBING > StatusPriority.SPEAKING
    assert StatusPriority.SPEAKING > StatusPriority.CODEX
    assert StatusPriority.CODEX > StatusPriority.AGENT
    assert StatusPriority.AGENT > StatusPriority.VISION
    assert StatusPriority.VISION > StatusPriority.READY
