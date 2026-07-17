"""Privacy-safe Agent session history and recovery metadata persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from threading import RLock

from lina.agent.models import AgentSession, AgentSessionStatus


_INTERRUPTED_ON_LOAD = {
    "running",
    "planning",
    "ready",
    "awaiting_input",
    "awaiting_plan_approval",
    "awaiting_step_approval",
    "replanning",
    "paused",
}
_PRESERVE_DURING_CLEANUP = _INTERRUPTED_ON_LOAD | {"interrupted"}


class AgentSessionRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = RLock()

    def save(self, session: AgentSession) -> None:
        payload = self._safe_metadata(session)
        with self._lock:
            sessions = list(self._read_raw())
            by_id = {str(item.get("session_id")): item for item in sessions if isinstance(item, dict)}
            by_id[session.session_id] = payload
            ordered = sorted(by_id.values(), key=lambda item: str(item.get("updated_at", "")), reverse=True)
            self._write(ordered)

    def load_all(self) -> tuple[dict, ...]:
        safe: list[dict] = []
        with self._lock:
            sessions = self._read_raw()
        for source in sessions:
            if not isinstance(source, dict):
                continue
            item = dict(source)
            if item.get("status") in _INTERRUPTED_ON_LOAD:
                item["status"] = AgentSessionStatus.INTERRUPTED.value
                item["error_code"] = "interrupted"
                item["last_summary"] = "Yarım kalan görev otomatik olarak devam ettirilmedi."
            safe.append(item)
        return tuple(safe)

    def interrupted(self) -> tuple[dict, ...]:
        return tuple(item for item in self.load_all() if item.get("status") == AgentSessionStatus.INTERRUPTED.value)

    def remove(self, session_id: str) -> bool:
        """Remove only Agent metadata; tool-created data is stored elsewhere."""
        with self._lock:
            sessions = list(self._read_raw())
            remaining = [item for item in sessions if item.get("session_id") != session_id]
            if len(remaining) == len(sessions):
                return False
            self._write(remaining)
            return True

    def cleanup(self, retention_days: int | None, *, now: datetime | None = None) -> int:
        if retention_days is None:
            return 0
        if retention_days not in {7, 30, 90}:
            raise ValueError("Desteklenmeyen Agent geçmiş saklama süresi.")
        threshold = (now or datetime.now(timezone.utc)) - timedelta(days=retention_days)
        with self._lock:
            sessions = list(self._read_raw())
            remaining = []
            removed = 0
            for item in sessions:
                status = str(item.get("status", ""))
                updated = _parse_datetime(item.get("updated_at"))
                if status in _PRESERVE_DURING_CLEANUP or updated is None or updated >= threshold:
                    remaining.append(item)
                else:
                    removed += 1
            if removed:
                self._write(remaining)
            return removed

    def _read_raw(self) -> tuple[dict, ...]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return ()
        sessions = raw if isinstance(raw, list) else [raw]
        return tuple(item for item in sessions if isinstance(item, dict))

    def _write(self, sessions: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(sessions, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def _safe_metadata(session: AgentSession) -> dict:
        plan = session.plan
        return {
            "schema_version": 2,
            "session_id": session.session_id,
            "source_session_id": session.source_session_id,
            "conversation_id": session.conversation_id,
            "request_summary": f"Agent request ({len(session.user_request)} characters)",
            "template_id": plan.template_id if plan else None,
            "title": _safe_session_title(plan.template_id if plan else None),
            "status": session.status.value,
            "current_step_index": session.current_step_index,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "generation_id": session.generation_id,
            "error_code": session.error_code,
            "last_summary": _session_summary(session),
            "duplicate_check_required": session.duplicate_check_required,
            "metrics": session.metrics.safe_dict(),
            "plan": None if plan is None else {
                "plan_id": plan.plan_id,
                "summary": f"Agent planı ({len(plan.steps)} adım)",
                "revision": plan.revision,
                "steps": [{
                    "step_id": step.step_id,
                    "title": _safe_step_title(step.tool_name),
                    "tool_name": step.tool_name,
                    "risk_level": step.risk_level.value,
                    "status": step.status.value,
                    "verification_status": step.verification_status.value if step.verification_status else None,
                    "result_summary": _safe_result_summary(step.status.value, step.verification_status.value if step.verification_status else None),
                    "error_code": step.error_code,
                    "retry_count": step.retry_count,
                } for step in plan.steps],
            },
            "checkpoints": [{
                "step_id": item.step_id,
                "status": item.status.value,
                "tool_name": item.tool_name,
                "risk_level": item.risk_level.value,
                "verification_status": item.verification_status.value if item.verification_status else None,
                "short_result_summary": item.short_result_summary[:160],
                "timestamp": item.timestamp.isoformat(),
                "execution_id": item.execution_id,
            } for item in session.checkpoints[-24:]],
            "events": [{
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "step_id": event.step_id,
                "timestamp": event.timestamp.isoformat(),
                "short_summary": _safe_event_summary(event.event_type.value),
                "severity": event.severity.value,
                "user_visible": event.user_visible,
                "technical_code": event.technical_code,
            } for event in session.events[-50:]],
        }


def _session_summary(session: AgentSession) -> str:
    labels = {
        "completed": "Görev tamamlandı.",
        "partially_completed": "Görev kısmen tamamlandı.",
        "failed": "Görev güvenli biçimde tamamlanamadı.",
        "cancelled": "Görev kullanıcı tarafından iptal edildi.",
        "interrupted": "Yarım kalan görev otomatik olarak devam ettirilmedi.",
        "uncertain": "Kalıcı işlemin sonucu belirsiz; otomatik tekrar engellendi.",
    }
    return labels.get(session.status.value, "Agent görevi güncellendi.")


def _safe_step_title(tool_name: str) -> str:
    labels = {
        "reminder.create": "Hatırlatıcı oluşturma adımı",
        "reminder.list": "Hatırlatıcı okuma adımı",
        "memory.store": "Hafıza kaydetme adımı",
        "memory.recall": "Hafıza okuma adımı",
        "files.read": "İzinli dosya okuma adımı",
        "vision.image": "Tek kare analiz adımı",
    }
    return labels.get(tool_name, "Agent araç adımı")


def _safe_session_title(template_id: str | None) -> str:
    labels = {
        "reminders.create": "Hatırlatıcı oluşturma görevi",
        "reminders.summary": "Hatırlatıcı özeti görevi",
        "reminders.conflicts": "Hatırlatıcı çakışma kontrolü",
        "memory.store": "Hafıza kaydetme görevi",
        "memory.recall": "Hafıza kontrolü görevi",
        "files.summarize": "İzinli dosya okuma görevi",
        "vision.single_frame": "Tek kare analiz görevi",
    }
    return labels.get(template_id, "Agent görevi")


def _safe_event_summary(event_type: str) -> str:
    labels = {
        "session_created": "Agent görevi oluşturuldu.",
        "plan_created": "Agent planı oluşturuldu.",
        "plan_modified": "Agent planı güncellendi.",
        "plan_approved": "Agent planı onaylandı.",
        "step_started": "Agent adımı başlatıldı.",
        "approval_requested": "Agent adımı onay bekliyor.",
        "approval_granted": "Agent adımı onaylandı.",
        "approval_denied": "Agent adımı onaylanmadı.",
        "step_verified": "Agent adımı doğrulandı.",
        "step_failed": "Agent adımı tamamlanamadı.",
        "step_skipped": "Agent adımı atlandı.",
        "replan_started": "Yeniden planlama başlatıldı.",
        "replan_completed": "Yeniden planlama tamamlandı.",
        "session_paused": "Agent görevi duraklatıldı.",
        "session_resumed": "Agent görevi yeniden başlatıldı.",
        "session_interrupted": "Agent görevi yarım kaldı.",
        "session_cancelled": "Agent görevi iptal edildi.",
        "session_completed": "Agent görevi tamamlandı.",
        "session_failed": "Agent görevi tamamlanamadı.",
    }
    return labels.get(event_type, "Agent olayı kaydedildi.")


def _safe_result_summary(status: str, verification: str | None) -> str:
    if verification == "verified":
        return "Adım doğrulandı."
    if verification == "uncertain":
        return "Adım sonucu belirsiz."
    return f"Adım durumu: {status}."


def _parse_datetime(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
