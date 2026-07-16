"""Allowlisted, schema-validated Agent tool execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime
from threading import Lock
from time import monotonic
from uuid import uuid4

from lina.agent.models import AgentStep, CancellationToken, ExecutionResult
from lina.brain.routing.models import IntentRequest, RequestContext


class AgentExecutor:
    def __init__(self, registry: object, timeout_seconds: float = 30.0) -> None:
        self.registry = registry
        self.timeout_seconds = max(0.1, timeout_seconds)
        self._active: set[str] = set()
        self._lock = Lock()
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="lina-agent")

    def execute(self, step: AgentStep, context: RequestContext, cancellation: CancellationToken) -> ExecutionResult:
        execution_id = uuid4().hex
        if cancellation.cancelled:
            return ExecutionResult(False, "Agent görevi iptal edildi.", error_code="cancelled", execution_id=execution_id)
        with self._lock:
            if step.step_id in self._active:
                return ExecutionResult(False, "Bu adım zaten çalışıyor.", error_code="duplicate_execution", execution_id=execution_id)
            self._active.add(step.step_id)
        started = monotonic()
        try:
            definition = getattr(self.registry, "get_by_name", lambda _name: None)(step.tool_name)
            if definition is None or not definition.available():
                return self._result(False, "Gerekli araç şu anda kullanılamıyor.", "unavailable", execution_id, started)
            error = self._validate_arguments(step.typed_arguments, definition.input_schema)
            if error:
                return self._result(False, error, "validation_error", execution_id, started)
            request = IntentRequest(definition.intent, 1.0, "Agent Mode step", dict(step.typed_arguments), definition.requires_confirmation, "agent", execution_id)
            future = self._pool.submit(definition.execute, request, context)
            try:
                raw = future.result(timeout=self.timeout_seconds)
            except TimeoutError:
                future.cancel()
                return self._result(False, "Araç zaman aşımına uğradı.", "timeout", execution_id, started, True)
            except Exception:
                return self._result(False, "Araç adımı güvenli biçimde tamamlanamadı.", "execution_error", execution_id, started)
            if cancellation.cancelled:
                return self._result(False, "Agent görevi iptal edildi.", "cancelled", execution_id, started)
            return ExecutionResult(bool(raw.success), str(raw.user_message)[:500], raw.data, raw.error_code, execution_id, round((monotonic() - started) * 1000), bool(raw.retryable))
        finally:
            with self._lock:
                self._active.discard(step.step_id)

    @staticmethod
    def _validate_arguments(arguments: dict, schema: dict[str, type]) -> str | None:
        unknown = set(arguments) - set(schema)
        if unknown:
            return "Araç adımı izin verilmeyen argüman içeriyor."
        for name, kind in schema.items():
            if name not in arguments:
                return f"Araç adımı gerekli '{name}' argümanını içermiyor."
            if kind is datetime and isinstance(arguments[name], str):
                try:
                    arguments[name] = datetime.fromisoformat(arguments[name])
                except ValueError:
                    return f"'{name}' argümanı geçersiz."
            if not isinstance(arguments[name], kind):
                return f"'{name}' argümanı beklenen türde değil."
        return None

    @staticmethod
    def _result(success, summary, code, execution_id, started, retryable=False):
        return ExecutionResult(success, summary, error_code=code, execution_id=execution_id, duration_ms=round((monotonic() - started) * 1000), retryable=retryable)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
