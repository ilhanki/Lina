"""User-controlled orchestration facade for the Codex bridge."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from lina.codex.client import CodexClient
from lina.codex.events import user_message
from lina.codex.models import (CodexEvent, CodexEventType, CodexExecutionMode, CodexResult,
                                CodexRiskLevel, CodexSession, CodexSessionStatus, ProjectContext,
                                VerificationOutcome, WorkspacePermissionLevel)
from lina.codex.permissions import WorkspacePermissionStore, ensure_within_workspace, is_secret_path
from lina.codex.planner import CodexPlanner
from lina.codex.repository import CodexHistoryRepository
from lina.codex.validator import CodexOutputValidator


EventListener = Callable[[CodexEvent, str], None]


class CodexBridge:
    def __init__(self, client: CodexClient, *, permissions: WorkspacePermissionStore | None = None,
                 planner: CodexPlanner | None = None, validator: CodexOutputValidator | None = None,
                 repository: CodexHistoryRepository | None = None) -> None:
        self.client = client
        self.permissions = permissions or WorkspacePermissionStore()
        self.planner = planner or CodexPlanner()
        self.validator = validator or CodexOutputValidator()
        self.repository = repository or CodexHistoryRepository()
        self._session: CodexSession | None = None
        self._listeners: list[EventListener] = []

    @property
    def session(self) -> CodexSession | None:
        return self._session

    def subscribe(self, listener: EventListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def select_workspace(self, root: Path, *, level: WorkspacePermissionLevel = WorkspacePermissionLevel.ONE_TIME,
                         session_id: str | None = None) -> ProjectContext:
        grant = self.permissions.grant(root, level, session_id)
        allowed: list[Path] = []
        languages: set[str] = set()
        frameworks: set[str] = set()
        language_by_suffix = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                              ".rs": "Rust", ".go": "Go", ".java": "Java", ".cs": "C#"}
        for path in grant.root.rglob("*"):
            if not path.is_file() or is_secret_path(path) or any(
                    part in {".git", "__pycache__", "node_modules", ".venv"} for part in path.parts):
                continue
            try:
                resolved = ensure_within_workspace(grant.root, path)
            except ValueError:
                continue
            allowed.append(resolved)
            language = language_by_suffix.get(path.suffix.casefold())
            if language:
                languages.add(language)
            if path.name == "pyproject.toml":
                frameworks.add("Python project")
            elif path.name == "package.json":
                frameworks.add("Node.js")
        project_type = "software" if languages else "unknown"
        return ProjectContext(grant.root, tuple(allowed), project_type,
                              tuple(sorted(languages)), tuple(sorted(frameworks)))

    def prepare(self, request: str, context: ProjectContext, *, conversation_id: int | None = None,
                agent_session_id: str | None = None,
                permission_level: WorkspacePermissionLevel = WorkspacePermissionLevel.ONE_TIME) -> CodexSession:
        if not self.permissions.allows(context.root_path):
            raise PermissionError("Codex için önce çalışma klasörü izni gerekli.")
        for path in context.allowed_files:
            ensure_within_workspace(context.root_path, path)
        task = self.planner.plan(request, context.root_path)
        mode = (CodexExecutionMode.CONTROLLED_MODIFICATION
                if task.risk_level is CodexRiskLevel.MODIFICATION else CodexExecutionMode.READ_ONLY)
        session = CodexSession.create(context, task.title, conversation_id, agent_session_id,
                                      permission_level, mode)
        session.task = task
        session.transition(CodexSessionStatus.PLANNING, 10)
        if task.approval_required:
            session.transition(CodexSessionStatus.WAITING_APPROVAL, 20)
            self._emit(CodexEvent.create(session.session_id, CodexEventType.APPROVAL_REQUESTED, progress=20))
        self._session = session
        self.repository.save(session)
        return session

    def start(self, session_id: str, *, approved: bool = False) -> CodexResult | None:
        session = self._matching(session_id)
        task = session.task
        if task is None:
            raise RuntimeError("Codex görevi hazırlanmadı.")
        # Plan approval is explicit for every task; modification tasks also retain
        # their per-action approval requirement in the typed task.
        if not approved:
            session.transition(CodexSessionStatus.WAITING_APPROVAL, 20)
            self.repository.save(session)
            return None
        session.transition(CodexSessionStatus.RUNNING, 30)
        self._emit(CodexEvent.create(session.session_id, CodexEventType.SESSION_STARTED, progress=30))
        try:
            result = self.client.execute(task, session.project_context, self._handle_client_event)
            session.transition(CodexSessionStatus.ANALYZING, 80)
            self._emit(CodexEvent.create(session.session_id, CodexEventType.VERIFICATION_STARTED, progress=85))
            report = self.validator.verify(task, result)
            if report.outcome is VerificationOutcome.FAILED:
                session.result_summary = report.summary
                session.transition(CodexSessionStatus.FAILED, 100)
                self._emit(CodexEvent.create(session.session_id, CodexEventType.FAILED, progress=100))
            else:
                session.result_summary = result.summary[:1000]
                session.transition(CodexSessionStatus.COMPLETED, 100)
                self._emit(CodexEvent.create(session.session_id, CodexEventType.COMPLETED, progress=100))
            return result
        except Exception:
            session.error_code = "client_failure"
            session.result_summary = "Codex istemcisi görevi tamamlayamadı."
            session.transition(CodexSessionStatus.FAILED, 100)
            self._emit(CodexEvent.create(session.session_id, CodexEventType.FAILED, progress=100))
            raise
        finally:
            self.permissions.consume_one_time(session.project_context.root_path)
            self.repository.save(session)

    def deny(self, session_id: str) -> None:
        session = self._matching(session_id)
        session.transition(CodexSessionStatus.CANCELLED)
        self.permissions.consume_one_time(session.project_context.root_path)
        self.repository.save(session)

    def _handle_client_event(self, event: CodexEvent) -> None:
        if self._session is None:
            return
        session = self._session
        if event.progress is not None:
            session.progress = max(session.progress, min(event.progress, 80))
        safe_event = CodexEvent.create(session.session_id, event.event_type, progress=event.progress,
                                       file_name=Path(event.file_name).name if event.file_name else None)
        self._emit(safe_event)

    def _emit(self, event: CodexEvent) -> None:
        message = user_message(event)
        for listener in tuple(self._listeners):
            listener(event, message)

    def _matching(self, session_id: str) -> CodexSession:
        if self._session is None or self._session.session_id != session_id:
            raise ValueError("Codex oturumu bulunamadı.")
        return self._session
