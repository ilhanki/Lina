"""Intent routing, pending clarification and confirmation enforcement."""

from datetime import datetime, timedelta, timezone
import logging
from time import monotonic

from lina.brain.routing.classifier import DeterministicIntentClassifier
from lina.brain.routing.models import IntentRequest, IntentType, PendingIntent, RequestContext, ToolResult
from lina.brain.routing.registry import SafeToolRegistry


class IntentRouter:
    def __init__(self, registry: SafeToolRegistry, classifier=None, clock=None, enabled_provider=None) -> None:
        self.registry = registry
        self.classifier = classifier or DeterministicIntentClassifier()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._enabled_provider = enabled_provider or (lambda: True)
        self._pending: dict[int | None, PendingIntent] = {}
        self._executed_intents: set[str] = set()
        self._logger = logging.getLogger("lina.intent_routing")

    def route(self, text: str, conversation_id: int | None = None, generation_id: int = 0) -> IntentRequest:
        if not self._enabled_provider():
            return IntentRequest(IntentType.CHAT, 1.0, text, source="disabled")
        pending = self.pending_for(conversation_id)
        if pending and pending.request.intent is IntentType.CREATE_REMINDER:
            combined = f"{pending.request.original_text} {text}"
            request = self.classifier.classify(combined)
        else:
            request = self.classifier.classify(text)
        self._logger.info(
            "intent_routed type=%s source=%s confidence=%s",
            request.intent.value,
            request.source,
            _confidence_bucket(request.confidence),
        )
        missing = tuple(request.extracted_arguments.get("missing_fields", ()))
        if missing:
            self._pending[conversation_id] = PendingIntent(request, conversation_id, missing, self._clock(), generation_id)
        else:
            self._pending.pop(conversation_id, None)
        return request

    def execute(self, request: IntentRequest, context: RequestContext) -> ToolResult:
        if request.intent_id in self._executed_intents:
            return ToolResult(False, "Bu işlem zaten işlendi.", error_code="duplicate")
        definition = self.registry.get(request.intent)
        if definition is None:
            return ToolResult(False, "Bu işlem Lina’nın mevcut yetkileri dışında.", error_code="unsupported")
        if not definition.available():
            return ToolResult(False, definition.unavailable_message, error_code="unavailable")
        if not _arguments_match(definition.input_schema, request.extracted_arguments):
            return ToolResult(False, "İşlem bilgileri doğrulanamadı.", error_code="invalid_arguments")
        if definition.requires_confirmation and not context.confirmed:
            return ToolResult(False, self.confirmation_message(request), error_code="confirmation_required", requires_follow_up=True)
        self._executed_intents.add(request.intent_id)
        started = monotonic()
        try:
            result = definition.execute(request, context)
        except Exception:
            result = ToolResult(False, "İşlem tamamlanamadı.", error_code="execution_failed")
        self._logger.info(
            "tool_executed name=%s success=%s duration_ms=%d",
            definition.name,
            result.success,
            int((monotonic() - started) * 1000),
        )
        return result

    def pending_for(self, conversation_id: int | None) -> PendingIntent | None:
        pending = self._pending.get(conversation_id)
        if pending and self._clock() - pending.created_at > timedelta(minutes=10):
            self._pending.pop(conversation_id, None)
            return None
        return pending

    def cancel_pending(self, conversation_id: int | None = None) -> None:
        if conversation_id in self._pending:
            self._pending.pop(conversation_id, None)
        elif conversation_id is None:
            self._pending.clear()

    @staticmethod
    def clarification_message(request: IntentRequest) -> str | None:
        missing = request.extracted_arguments.get("missing_fields", ())
        if "future_time" in missing:
            return "Geçmiş bir saat seçemeyiz. Hangi gelecek tarih ve saati kullanayım?"
        if "date" in missing and "time" in missing:
            return "Hangi gün ve saat için hatırlatayım?"
        if "date" in missing:
            return "Hangi gün hatırlatayım?"
        if "time" in missing:
            return "Saat kaçta hatırlatayım?"
        if "title" in missing:
            return "Neyi hatırlatmamı istersin?"
        return None

    @staticmethod
    def confirmation_message(request: IntentRequest) -> str:
        if request.intent is IntentType.CREATE_REMINDER:
            due = request.extracted_arguments.get("due_at")
            title = request.extracted_arguments.get("title", "")
            formatted = due.astimezone().strftime("%d.%m.%Y %H:%M") if due else "belirtilen zaman"
            return f"{formatted} için “{title}” hatırlatıcısı oluşturulsun mu?"
        if request.intent is IntentType.MEMORY_STORE:
            return "Bu bilgi hafızaya kaydedilsin mi?"
        return "Bu işlem onaylansın mı?"


def _arguments_match(schema: dict[str, type], arguments: dict[str, object]) -> bool:
    return all(key in arguments and isinstance(arguments[key], expected) for key, expected in schema.items())


def _confidence_bucket(value: float) -> str:
    if value >= 0.9:
        return "high"
    if value >= 0.6:
        return "medium"
    return "low"
