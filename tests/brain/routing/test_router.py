from datetime import datetime, timedelta, timezone

from lina.brain.routing.models import IntentRequest, IntentType, RequestContext, ToolResult
from lina.brain.routing.registry import SafeToolRegistry, ToolDefinition
from lina.brain.routing.router import IntentRouter


def _registry(calls):
    registry = SafeToolRegistry()
    registry.register(ToolDefinition("reminder.create", IntentType.CREATE_REMINDER, "Create", {"title": str}, True, lambda request, context: calls.append(request.intent_id) or ToolResult(True, "Oluşturuldu.")))
    return registry


def test_router_requires_confirmation_and_prevents_duplicate_execution() -> None:
    calls = []
    router = IntentRouter(_registry(calls))
    request = IntentRequest(IntentType.CREATE_REMINDER, 1, "test", {"title": "Test"}, True)
    assert router.execute(request, RequestContext(1)).error_code == "confirmation_required"
    assert router.execute(request, RequestContext(1, confirmed=True)).success
    assert router.execute(request, RequestContext(1, confirmed=True)).error_code == "duplicate"
    assert len(calls) == 1


def test_pending_intent_is_conversation_isolated_completed_and_expires() -> None:
    now = datetime(2026, 7, 12, 10, tzinfo=timezone.utc)
    router = IntentRouter(SafeToolRegistry(), clock=lambda: now)
    first = router.route("Yarın spor yapmayı hatırlat", conversation_id=1)
    assert router.clarification_message(first) == "Saat kaçta hatırlatayım?"
    assert router.pending_for(2) is None
    second = router.route("18:00", conversation_id=1)
    assert second.intent is IntentType.CREATE_REMINDER
    assert second.extracted_arguments["missing_fields"] == ()
    router.route("Yarın kitap okumayı hatırlat", conversation_id=3)
    router._clock = lambda: now + timedelta(minutes=11)
    assert router.pending_for(3) is None


def test_routing_disabled_and_unavailable_tool_fallback() -> None:
    disabled = IntentRouter(SafeToolRegistry(), enabled_provider=lambda: False)
    assert disabled.route("Hatırlatıcılarımı göster").intent is IntentType.CHAT
    registry = SafeToolRegistry()
    registry.register(ToolDefinition("memory.recall", IntentType.MEMORY_RECALL, "Recall", {}, False, lambda r, c: ToolResult(True, "ok"), available=lambda: False, unavailable_message="Memory kullanılamıyor."))
    result = IntentRouter(registry).execute(IntentRequest(IntentType.MEMORY_RECALL, 1, "hatırla"), RequestContext(None))
    assert result.error_code == "unavailable"
    assert result.user_message == "Memory kullanılamıyor."
