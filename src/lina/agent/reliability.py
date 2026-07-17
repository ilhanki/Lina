"""Idempotency, loop detection and user-safe recovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from lina.agent.errors import AgentErrorCode
from lina.agent.models import AgentCheckpoint, AgentStep, AgentStepStatus, VerificationStatus, utc_now


_ERROR_MESSAGES = {
    AgentErrorCode.TOOL_UNAVAILABLE: "Bu adım için gerekli araç şu anda kullanılamıyor.",
    AgentErrorCode.INVALID_ARGUMENTS: "Görev adımının bilgileri doğrulanamadı.",
    AgentErrorCode.PERMISSION_DENIED: "Bu adım için gerekli izin yok.",
    AgentErrorCode.APPROVAL_REQUIRED: "Bu adım için açık onay gerekiyor.",
    AgentErrorCode.USER_CANCELLED: "Agent görevi iptal edildi.",
    AgentErrorCode.TIMEOUT: "Araç zamanında yanıt vermedi.",
    AgentErrorCode.TRANSIENT_FAILURE: "Geçici bir sorun oluştu.",
    AgentErrorCode.PERSISTENT_OUTCOME_UNCERTAIN: "İşlemin tamamlanıp tamamlanmadığını doğrulayamadım. Aynı işlemi otomatik olarak tekrarlamayacağım.",
    AgentErrorCode.VERIFICATION_FAILED: "Adım sonucu beklenen değerlerle eşleşmedi.",
    AgentErrorCode.VERIFICATION_UNCERTAIN: "Adımın sonucunu kesin olarak doğrulayamadım.",
    AgentErrorCode.DEPENDENCY_FAILED: "Gerekli önceki adım tamamlanmadığı için görev durdu.",
    AgentErrorCode.LOOP_DETECTED: "Plan aynı adımları tekrar etmeye başladı ve güvenlik için durduruldu.",
    AgentErrorCode.STEP_LIMIT_REACHED: "Plan güvenli adım sınırına ulaştı.",
    AgentErrorCode.REPLAN_LIMIT_REACHED: "Güvenli yeniden planlama sınırına ulaşıldı.",
    AgentErrorCode.STALE_RESULT: "Eski bir Agent sonucu yok sayıldı.",
    AgentErrorCode.INTERRUPTED: "Yarım kalan görev otomatik olarak devam ettirilmedi.",
    AgentErrorCode.PROHIBITED: "Bu işlem Agent yetkilerinin dışında.",
    AgentErrorCode.UNSUPPORTED_REQUEST: "Bu görev için desteklenen güvenli bir araç yok.",
    AgentErrorCode.STORAGE_FAILURE: "Görev geçmişi kaydedilemedi; normal sohbeti kullanmaya devam edebilirsin.",
    AgentErrorCode.INTERNAL_ERROR: "Agent görevi güvenli biçimde tamamlanamadı.",
}


_RECOVERY_ACTIONS = {
    AgentErrorCode.TOOL_UNAVAILABLE: ("Tekrar Kontrol Et", "Görevi Bitir"),
    AgentErrorCode.INVALID_ARGUMENTS: ("Bilgiyi Tamamla", "İptal"),
    AgentErrorCode.TIMEOUT: ("Tekrar Dene", "Atla", "İptal"),
    AgentErrorCode.TRANSIENT_FAILURE: ("Tekrar Dene", "Atla", "İptal"),
    AgentErrorCode.PERSISTENT_OUTCOME_UNCERTAIN: ("Mevcut Kaydı Kontrol Et", "Yeniden Oluşturma", "İptal"),
    AgentErrorCode.VERIFICATION_UNCERTAIN: ("Sonucu Kontrol Et", "Görevi Bitir"),
    AgentErrorCode.PROHIBITED: (),
}


def user_error_message(code: str | AgentErrorCode) -> str:
    try:
        resolved = AgentErrorCode(code)
    except ValueError:
        resolved = AgentErrorCode.INTERNAL_ERROR
    return _ERROR_MESSAGES[resolved]


def recovery_actions(code: str | AgentErrorCode) -> tuple[str, ...]:
    try:
        resolved = AgentErrorCode(code)
    except ValueError:
        resolved = AgentErrorCode.INTERNAL_ERROR
    return _RECOVERY_ACTIONS.get(resolved, ("Görevi Bitir",))


def normalized_operation_hash(step: AgentStep) -> str:
    payload = {"tool": step.tool_name, "arguments": _normalize(step.typed_arguments)}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


def idempotency_key(session_id: str, step: AgentStep) -> str:
    value = f"{session_id}:{step.step_id}:{normalized_operation_hash(step)}".encode("utf-8")
    return sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class AgentLoopResult:
    detected: bool
    reason: str | None = None
    repeated_signature: str | None = None
    attempt_count: int = 0


class AgentLoopDetector:
    def __init__(self, repeat_limit: int = 2) -> None:
        self.repeat_limit = max(2, repeat_limit)
        self._counts: dict[str, int] = {}
        self._clarifications: dict[str, int] = {}
        self._last_progress_token: str | None = None
        self._no_progress_replans = 0

    def observe_step(self, step: AgentStep) -> AgentLoopResult:
        signature = normalized_operation_hash(step)
        count = self._counts.get(signature, 0) + 1
        self._counts[signature] = count
        return AgentLoopResult(count >= self.repeat_limit, "repeated_tool_arguments" if count >= self.repeat_limit else None, signature, count)

    def observe_clarification(self, text: str) -> AgentLoopResult:
        signature = sha256(" ".join(text.casefold().split()).encode("utf-8")).hexdigest()
        count = self._clarifications.get(signature, 0) + 1
        self._clarifications[signature] = count
        return AgentLoopResult(count >= self.repeat_limit, "repeated_clarification" if count >= self.repeat_limit else None, signature, count)

    def observe_replan(self, plan_signature: str, progress_token: str) -> AgentLoopResult:
        if self._last_progress_token == progress_token:
            self._no_progress_replans += 1
        else:
            self._no_progress_replans = 0
            self._last_progress_token = progress_token
        signature_count = self._counts.get(plan_signature, 0) + 1
        self._counts[plan_signature] = signature_count
        detected = signature_count >= self.repeat_limit or self._no_progress_replans >= self.repeat_limit
        return AgentLoopResult(detected, "replan_without_progress" if detected else None, plan_signature, max(signature_count, self._no_progress_replans))

    def reset(self) -> None:
        self._counts.clear()
        self._clarifications.clear()
        self._last_progress_token = None
        self._no_progress_replans = 0


def checkpoint_for_step(step: AgentStep) -> AgentCheckpoint:
    verification = step.verification_status
    summary = _checkpoint_summary(step, verification)
    return AgentCheckpoint(
        step.step_id,
        step.status,
        step.tool_name,
        step.risk_level,
        verification,
        summary,
        utc_now(),
        step.execution_id,
    )


def _checkpoint_summary(step: AgentStep, verification: VerificationStatus | None) -> str:
    if step.status is AgentStepStatus.SUCCEEDED:
        return "Adım deterministic olarak doğrulandı."
    if verification is VerificationStatus.UNCERTAIN:
        return "Adım sonucu belirsiz; otomatik tekrar engellendi."
    if step.status is AgentStepStatus.SKIPPED:
        return "Adım kullanıcı tarafından atlandı."
    return "Adım güvenli biçimde tamamlanamadı."


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_normalize(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "value"):
        return _normalize(value.value)
    return f"<{type(value).__name__}>"
