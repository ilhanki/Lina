"""Explicit Codex session state transitions with pause/cancel controls."""

from lina.codex.models import CodexSession, CodexSessionStatus


class CodexSessionController:
    def pause(self, session: CodexSession) -> None:
        if session.status is not CodexSessionStatus.RUNNING:
            raise ValueError("Yalnız çalışan Codex görevi duraklatılabilir.")
        session.transition(CodexSessionStatus.PAUSED)

    def resume(self, session: CodexSession) -> None:
        if session.status is not CodexSessionStatus.PAUSED:
            raise ValueError("Codex görevi duraklatılmış değil.")
        session.transition(CodexSessionStatus.RUNNING)

    def cancel(self, session: CodexSession) -> None:
        if session.terminal:
            return
        session.transition(CodexSessionStatus.CANCELLED)

    def interrupt(self, session: CodexSession) -> None:
        if not session.terminal:
            session.transition(CodexSessionStatus.INTERRUPTED)

