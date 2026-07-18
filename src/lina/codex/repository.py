"""Metadata-only Codex history storage; prompts and file contents are never retained."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lina.codex.models import CodexHistoryEntry, CodexSession, CodexSessionStatus


class CodexHistoryRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._entries: list[CodexHistoryEntry] = []
        if path is not None and path.exists():
            self._load()

    def save(self, session: CodexSession) -> CodexHistoryEntry:
        entry = CodexHistoryEntry(session.session_id, session.task_summary[:160], session.created_at,
                                  session.status, session.result_summary[:500])
        self._entries = [item for item in self._entries if item.session_id != entry.session_id]
        self._entries.append(entry)
        self._flush()
        return entry

    def list(self) -> tuple[CodexHistoryEntry, ...]:
        return tuple(sorted(self._entries, key=lambda item: item.created_at, reverse=True))

    def delete(self, session_id: str) -> None:
        self._entries = [item for item in self._entries if item.session_id != session_id]
        self._flush()

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
            ) for item in payload if isinstance(item, dict)]
        except (OSError, ValueError, TypeError, KeyError):
            self._entries = []

    def _flush(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [{"session_id": item.session_id, "task_summary": item.task_summary,
                    "created_at": item.created_at.isoformat(), "status": item.status.value,
                    "result_summary": item.result_summary} for item in self._entries]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
