"""Forward-compatible, bounded incremental parser for Codex CLI JSONL events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lina.codex.models import CodexEvent, CodexEventType
from lina.codex.resume import valid_cli_session_id
from lina.codex.transports.diagnostics import redact


class CodexJsonlParser:
    def __init__(self, session_id: str, *, max_line_characters: int = 262_144,
                 max_events: int = 10_000, max_messages: int = 500) -> None:
        self.session_id = session_id
        self.max_line_characters = max(1024, int(max_line_characters))
        self.max_events = max(100, int(max_events))
        self.max_messages = max(10, int(max_messages))
        self._buffer = ""
        self._first_line = True
        self.events: list[CodexEvent] = []
        self.messages: list[str] = []
        self.changed_files: set[str] = set()
        self.invalid_lines = 0
        self.warning_lines = 0
        self.unknown_events = 0
        self.truncated_lines = 0
        self.runtime_approval_requested = False
        self.remote_session_id: str | None = None
        self.final_event_seen = False
        self.usage: dict[str, int] = {}

    def feed(self, chunk: str) -> tuple[CodexEvent, ...]:
        self._buffer += str(chunk or "")
        emitted: list[CodexEvent] = []
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            event = self._parse_line(line.rstrip("\r"))
            if event is not None and len(self.events) < self.max_events:
                self.events.append(event)
                emitted.append(event)
        if len(self._buffer) > self.max_line_characters:
            self._buffer = ""
            self.truncated_lines += 1
            self.invalid_lines += 1
        return tuple(emitted)

    def finish(self) -> tuple[CodexEvent, ...]:
        if not self._buffer.strip():
            self._buffer = ""
            return ()
        event = self._parse_line(self._buffer.rstrip("\r"))
        self._buffer = ""
        if event is None or len(self.events) >= self.max_events:
            return ()
        self.events.append(event)
        return (event,)

    def feed_stderr(self, line: str) -> None:
        if str(line or "").strip():
            self.warning_lines += 1

    @property
    def summary(self) -> str:
        return "\n".join(item for item in self.messages if item).strip()

    @property
    def diagnostics(self) -> tuple[str, ...]:
        values: list[str] = []
        if self.invalid_lines:
            values.append(f"invalid_lines={self.invalid_lines}")
        if self.unknown_events:
            values.append(f"unknown_events={self.unknown_events}")
        if self.warning_lines:
            values.append(f"stderr_warnings={self.warning_lines}")
        if self.truncated_lines:
            values.append(f"truncated_lines={self.truncated_lines}")
        if not self.final_event_seen:
            values.append("final_event_missing")
        return tuple(values)

    def _parse_line(self, line: str) -> CodexEvent | None:
        if self._first_line:
            line = line.lstrip("\ufeff")
            self._first_line = False
        if not line.strip():
            return None
        if len(line) > self.max_line_characters:
            self.truncated_lines += 1
            self.invalid_lines += 1
            return None
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            self.invalid_lines += 1
            self.warning_lines += 1
            return None
        if not isinstance(payload, dict):
            self.invalid_lines += 1
            return None
        raw_type = str(payload.get("type") or payload.get("event") or "unknown").casefold()
        item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
        for key in ("thread_id", "session_id", "conversation_id"):
            candidate_id = payload.get(key)
            if isinstance(candidate_id, str) and valid_cli_session_id(candidate_id):
                self.remote_session_id = candidate_id
                break
        text = self._extract_text(item)
        path = self._extract_path(item)
        if path:
            self.changed_files.add(path)
        if text and any(token in raw_type for token in ("message", "completed", "response", "agent")):
            if len(self.messages) < self.max_messages:
                self.messages.append(text)
        if "usage" in raw_type:
            self._capture_usage(payload)
            event_type = CodexEventType.USAGE
        elif "approval" in raw_type or "approval" in str(item.get("type", "")).casefold():
            self.runtime_approval_requested = True
            event_type = CodexEventType.APPROVAL_REQUESTED
        elif "error" in raw_type or "failed" in raw_type:
            event_type = CodexEventType.FAILED
            self.final_event_seen = True
        elif "file" in raw_type or path:
            event_type = CodexEventType.MODIFICATION_COMPLETED
        elif "turn.started" in raw_type or "item.started" in raw_type:
            event_type = CodexEventType.ANALYZING
        elif "thread.started" in raw_type or "session" in raw_type:
            event_type = CodexEventType.SESSION_STARTED
        elif "completed" in raw_type or "turn.completed" in raw_type:
            event_type = CodexEventType.COMPLETED
            self.final_event_seen = True
        else:
            event_type = CodexEventType.ANALYZING
            self.unknown_events += 1
        return CodexEvent.create(
            self.session_id, event_type, redact(text),
            file_name=Path(path).name if path else None,
        )

    def _capture_usage(self, payload: dict[str, Any]) -> None:
        source = payload.get("usage") if isinstance(payload.get("usage"), dict) else payload
        for key in ("input_tokens", "output_tokens", "cached_input_tokens", "total_tokens"):
            value = source.get(key)
            if isinstance(value, int) and 0 <= value <= 10**12:
                self.usage[key] = value

    @classmethod
    def _extract_text(cls, payload: dict[str, Any]) -> str:
        for key in ("text", "message", "content", "summary", "output_text"):
            value = payload.get(key)
            if isinstance(value, str):
                return redact(value).strip()
            if isinstance(value, list):
                parts: list[str] = []
                for item in value[:100]:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict):
                        nested = cls._extract_text(item)
                        if nested:
                            parts.append(nested)
                if parts:
                    return redact("\n".join(parts)).strip()
            if isinstance(value, dict):
                nested = cls._extract_text(value)
                if nested:
                    return nested
        return ""

    @staticmethod
    def _extract_path(payload: dict[str, Any]) -> str | None:
        for key in ("path", "file", "file_path"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:1000]
        return None
