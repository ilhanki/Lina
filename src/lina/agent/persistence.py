"""Minimal privacy-safe session metadata persistence."""

from __future__ import annotations

import json
from pathlib import Path

from lina.agent.models import AgentSession, AgentSessionStatus, safe_value


class AgentSessionRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, session: AgentSession) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._safe_metadata(session)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def load_all(self) -> tuple[dict, ...]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return ()
        sessions = raw if isinstance(raw, list) else [raw]
        safe = []
        for item in sessions:
            if not isinstance(item, dict):
                continue
            if item.get("status") in {"running", "planning", "ready", "awaiting_plan_approval", "awaiting_step_approval", "replanning"}:
                item["status"] = AgentSessionStatus.INTERRUPTED.value
            safe.append(item)
        return tuple(safe)

    @staticmethod
    def _safe_metadata(session: AgentSession) -> dict:
        plan = session.plan
        return {
            "schema_version": 1,
            "session_id": session.session_id,
            "conversation_id": session.conversation_id,
            "request_summary": session.user_request[:160],
            "status": session.status.value,
            "current_step_index": session.current_step_index,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "generation_id": session.generation_id,
            "metrics": session.metrics.safe_dict(),
            "plan": None if plan is None else {
                "plan_id": plan.plan_id, "summary": plan.summary[:240], "revision": plan.revision,
                "steps": [{
                    "step_id": step.step_id, "title": step.title[:160], "tool_name": step.tool_name,
                    "risk_level": step.risk_level.value, "status": step.status.value,
                    "result_summary": (step.result_summary or "")[:240], "error_code": step.error_code,
                } for step in plan.steps],
            },
        }
