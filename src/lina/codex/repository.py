"""Metadata-only Codex history storage; prompts and file contents are never retained."""

from __future__ import annotations

import json
import hashlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lina.codex.models import (CodexHistoryEntry, CodexSession, CodexSessionStatus)


class CodexHistoryRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._entries: list[CodexHistoryEntry] = []
        if path is not None and path.exists():
            self._load()

    def save(self, session: CodexSession) -> CodexHistoryEntry:
        workspace_hash = hashlib.sha256(
            str(session.project_context.root_path).casefold().encode("utf-8")
        ).hexdigest()[:16]
        entry = CodexHistoryEntry(session.session_id, session.task_summary[:160], session.created_at,
                                  session.status, session.result_summary[:500], workspace_hash,
                                  session.execution_mode.value,
                                  session.task.risk_level.value if session.task else "unknown",
                                  session.approval_decision, session.cli_version,
                                  session.verification_outcome, session.duration_seconds,
                                  session.exit_category, session.updated_at,
                                  session.project_context.root_path.name[:120], session.last_event,
                                  session.last_activity_at, session.process_termination_status,
                                  session.changed_file_count, session.additions, session.deletions,
                                  bool(session.remote_session and session.remote_session.resumable),
                                  session.review_pending,
                                  session.error_code or "none", session.result_surfaced,
                                  session.remote_session.cli_session_id if session.remote_session else None)
        self._entries = [item for item in self._entries if item.session_id != entry.session_id]
        self._entries.append(entry)
        self._flush()
        return entry

    def list(self) -> tuple[CodexHistoryEntry, ...]:
        return tuple(sorted(self._entries, key=lambda item: item.created_at, reverse=True))

    def delete(self, session_id: str) -> None:
        self._entries = [item for item in self._entries if item.session_id != session_id]
        self._flush()

    def mark_surfaced(self, session_id: str) -> None:
        self._entries = [
            replace(item, result_surfaced=True) if item.session_id == session_id else item
            for item in self._entries
        ]
        self._flush()

    def recover_incomplete(self) -> tuple[CodexHistoryEntry, ...]:
        live_states = {
            CodexSessionStatus.ANALYZING, CodexSessionStatus.PLANNING,
            CodexSessionStatus.WAITING_APPROVAL, CodexSessionStatus.RUNNING,
            CodexSessionStatus.VERIFYING, CodexSessionStatus.PAUSED,
        }
        recovered: list[CodexHistoryEntry] = []
        updated: list[CodexHistoryEntry] = []
        for item in self._entries:
            if item.status in live_states:
                item = replace(
                    item, status=CodexSessionStatus.INTERRUPTED,
                    exit_category="orphaned_process", failure_category="interrupted",
                    process_termination_status="process_not_alive", last_event="interrupted",
                )
                recovered.append(item)
            updated.append(item)
        self._entries = updated
        if recovered:
            self._flush()
        return tuple(recovered)

    def recovery_items(self) -> tuple[CodexHistoryEntry, ...]:
        return tuple(item for item in self.list() if (
            item.status is CodexSessionStatus.INTERRUPTED
            or (item.status is CodexSessionStatus.COMPLETED and not item.result_surfaced)
            or item.review_pending
        ))

    def cleanup(self, retention_days: int | None) -> None:
        if retention_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
            self._entries = [item for item in self._entries if item.created_at >= cutoff]
            self._flush()

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self._entries = [CodexHistoryEntry(
                str(item["session_id"]), str(item["task_summary"]),
                datetime.fromisoformat(item["created_at"]), CodexSessionStatus(item["status"]),
                str(item.get("result_summary", "")),
                str(item.get("workspace_hash", "")), str(item.get("operation_type", "unknown")),
                str(item.get("risk", "unknown")), str(item.get("approval_decision", "unknown")),
                str(item["cli_version"]) if item.get("cli_version") else None,
                str(item.get("verification", "unverified")),
                float(item.get("duration_seconds", 0.0)), str(item.get("exit_category", "unknown")),
                datetime.fromisoformat(item["updated_at"]) if item.get("updated_at") else None,
                str(item.get("workspace_display_name", ""))[:120],
                str(item.get("last_event", "unknown")),
                datetime.fromisoformat(item["last_activity_at"]) if item.get("last_activity_at") else None,
                str(item.get("process_termination_status", "unknown")),
                int(item.get("changed_file_count", 0)), int(item.get("additions", 0)),
                int(item.get("deletions", 0)), bool(item.get("resumable", False)),
                bool(item.get("review_pending", False)),
                str(item.get("failure_category", "none")),
                bool(item.get("result_surfaced", False)),
                str(item["remote_session_id"]) if item.get("remote_session_id") else None,
            ) for item in payload if isinstance(item, dict)]
        except (OSError, ValueError, TypeError, KeyError):
            self._entries = []

    def _flush(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [{"session_id": item.session_id, "task_summary": item.task_summary,
                    "created_at": item.created_at.isoformat(), "status": item.status.value,
                    "result_summary": item.result_summary, "workspace_hash": item.workspace_hash,
                    "operation_type": item.operation_type, "risk": item.risk,
                    "approval_decision": item.approval_decision, "cli_version": item.cli_version,
                    "verification": item.verification, "duration_seconds": item.duration_seconds,
                    "exit_category": item.exit_category,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                    "workspace_display_name": item.workspace_display_name,
                    "last_event": item.last_event,
                    "last_activity_at": item.last_activity_at.isoformat() if item.last_activity_at else None,
                    "process_termination_status": item.process_termination_status,
                    "changed_file_count": item.changed_file_count,
                    "additions": item.additions, "deletions": item.deletions,
                    "resumable": item.resumable, "review_pending": item.review_pending,
                    "failure_category": item.failure_category,
                    "result_surfaced": item.result_surfaced,
                    "remote_session_id": item.remote_session_id} for item in self._entries]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
