"""Narrow client contract. The bridge never launches a shell or hidden agent."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from lina.codex.models import CodexEvent, CodexResult, CodexTask, ProjectContext


class CodexClient(Protocol):
    def execute(self, task: CodexTask, context: ProjectContext,
                on_event: Callable[[CodexEvent], None]) -> CodexResult: ...


class UnavailableCodexClient:
    def execute(self, task: CodexTask, context: ProjectContext,
                on_event: Callable[[CodexEvent], None]) -> CodexResult:
        raise RuntimeError("Codex istemcisi yapılandırılmadı.")

