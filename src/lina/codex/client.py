"""Narrow client contract. The bridge never launches a shell or hidden agent."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from lina.codex.models import CodexEvent, CodexResult, CodexTask, ProjectContext
from lina.codex.transports.diagnostics import CodexCliInfo


class CodexClient(Protocol):
    info: CodexCliInfo

    def execute(self, task: CodexTask, context: ProjectContext,
                on_event: Callable[[CodexEvent], None]) -> CodexResult: ...

    def cancel(self) -> None: ...

    def shutdown(self) -> None: ...


class CodexClientUnavailableError(RuntimeError):
    """Raised when no real transport has been explicitly configured."""


class UnavailableCodexClient:
    def __init__(self, diagnostics: tuple[str, ...] = ("cli_not_found",)) -> None:
        self.info = CodexCliInfo(diagnostics=diagnostics)

    def execute(self, task: CodexTask, context: ProjectContext,
                on_event: Callable[[CodexEvent], None]) -> CodexResult:
        raise CodexClientUnavailableError("Codex istemcisi yapılandırılmadı.")

    def cancel(self) -> None:
        return

    def shutdown(self) -> None:
        return
