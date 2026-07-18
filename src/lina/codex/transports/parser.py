"""Forward-compatible incremental parser for Codex CLI JSONL events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lina.codex.models import CodexEvent, CodexEventType
from lina.codex.transports.diagnostics import redact


class CodexJsonlParser:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._buffer = ""
        self.events: list[CodexEvent] = []
        self.messages: list[str] = []
        self.changed_files: set[str] = set()
        self.invalid_lines = 0
        self.runtime_approval_requested = False

    def feed(self, chunk: str) -> tuple[CodexEvent, ...]:
        self._buffer += chunk
        emitted: list[CodexEvent] = []
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            event = self._parse_line(line)
            if event is not None:
                self.events.append(event)
                emitted.append(event)
        return tuple(emitted)

    def finish(self) -> tuple[CodexEvent, ...]:
        if not self._buffer.strip():
            self._buffer = ""
            return ()
        event = self._parse_line(self._buffer)
        self._buffer = ""
        if event is None:
            return ()
        self.events.append(event)
        return (event,)

    @property
    def summary(self) -> str:
        return "\n".join(item for item in self.messages if item).strip()

    def _parse_line(self, line: str) -> CodexEvent | None:
        if not line.strip():
            return None
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            self.invalid_lines += 1
            return None
        if not isinstance(payload, dict):
            self.invalid_lines += 1
            return None
        raw_type = str(payload.get("type") or payload.get("event") or "unknown").casefold()
        item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
        text = self._extract_text(item)
        path = self._extract_path(item)
        if path:
            self.changed_files.add(path)
        if text and any(token in raw_type for token in ("message", "completed", "response", "agent")):
            self.messages.append(text)
        if "approval" in raw_type or "approval" in str(item.get("type", "")).casefold():
            self.runtime_approval_requested = True
            event_type = CodexEventType.APPROVAL_REQUESTED
        elif "error" in raw_type or "failed" in raw_type:
            event_type = CodexEventType.FAILED
        elif "file" in raw_type or path:
            event_type = CodexEventType.MODIFICATION_COMPLETED
        elif "turn.started" in raw_type or "item.started" in raw_type:
            event_type = CodexEventType.ANALYZING
        elif "thread.started" in raw_type or "session" in raw_type:
            event_type = CodexEventType.SESSION_STARTED
        elif "completed" in raw_type or "turn.completed" in raw_type:
            event_type = CodexEventType.COMPLETED
        else:
            event_type = CodexEventType.ANALYZING
        return CodexEvent.create(self.session_id, event_type, redact(text),
                                 file_name=Path(path).name if path else None)

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        for key in ("text", "message", "content", "summary"):
            value = payload.get(key)
            if isinstance(value, str):
                return redact(value).strip()
        return ""

    @staticmethod
    def _extract_path(payload: dict[str, Any]) -> str | None:
        for key in ("path", "file", "file_path"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

