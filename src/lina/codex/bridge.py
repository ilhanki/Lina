"""User-controlled orchestration facade for the Codex bridge."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import time

from lina.codex.client import CodexClient, CodexClientUnavailableError
from lina.codex.events import user_message
from lina.codex.models import (CodexEvent, CodexEventType, CodexExecutionMode, CodexResult,
                                CodexRiskLevel, CodexSession, CodexSessionStatus, ProjectContext,
                                VerificationOutcome, WorkspacePermissionLevel)
from lina.codex.permissions import (WorkspacePermissionStore, ensure_within_workspace,
                                    is_secret_path, validate_codex_request_scope)
from lina.codex.planner import CodexPlanner
from lina.codex.quality import CodexResponseQuality
from lina.codex.repository import CodexHistoryRepository
from lina.codex.validator import CodexOutputValidator
from lina.codex.transports.errors import CodexTransportError
from lina.agent.models import ApprovalDecision
from lina.codex.changes import (CodexChangeSet, CodexReviewDecision,
                                CodexReviewSession, CodexReviewSummary)


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
        self.response_quality = CodexResponseQuality()
        self._session: CodexSession | None = None
        self._listeners: list[EventListener] = []
        self._reviews: dict[str, CodexReviewSession] = {}

    @property
    def session(self) -> CodexSession | None:
        return self._session

    @property
    def client_info(self):
        return getattr(self.client, "info", None)

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
        for index, path in enumerate(grant.root.rglob("*")):
            if index >= 5000:
                break
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
        validate_codex_request_scope(request)
        if not self.permissions.allows(context.root_path):
            raise PermissionError("Codex için önce çalışma klasörü izni gerekli.")
        if self._session is not None and not self._session.terminal:
            previous = self._session
            previous.transition(CodexSessionStatus.CANCELLED)
            self.permissions.consume_one_time(previous.project_context.root_path)
            self.repository.delete(previous.session_id)
        for path in context.allowed_files:
            ensure_within_workspace(context.root_path, path)
        task = self.planner.plan(request, context.root_path)
        mode = (CodexExecutionMode.CONTROLLED_MODIFICATION
                if task.risk_level is CodexRiskLevel.MODIFICATION else CodexExecutionMode.READ_ONLY)
        session = CodexSession.create(context, task.title, conversation_id, agent_session_id,
                                      permission_level, mode)
        session.task = task
        info = self.client_info
        session.cli_version = info.version if info is not None else None
        session.transition(CodexSessionStatus.PLANNING, 10)
        session.transition(CodexSessionStatus.WAITING_APPROVAL, 20)
        self._emit(CodexEvent.create(
            session.session_id, CodexEventType.APPROVAL_REQUESTED, progress=20
        ))
        self._session = session
        self.repository.save(session)
        return session

    def start(self, session_id: str, *, approved: bool = False,
              resume_reference=None) -> CodexResult | None:
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
        session.approval_decision = "approved"
        session.transition(CodexSessionStatus.RUNNING, 30)
        started = time.monotonic()
        self._emit(CodexEvent.create(session.session_id, CodexEventType.SESSION_STARTED, progress=30))
        retain_history = True
        try:
            if resume_reference is not None:
                if not hasattr(self.client, "resume"):
                    raise CodexClientUnavailableError("Codex resume kullanılamıyor.")
                result = self.client.resume(
                    task, session.project_context, resume_reference,
                    self._handle_client_event, approved=approved,
                )
            else:
                result = self.client.execute(task, session.project_context, self._handle_client_event)
            session.remote_session = result.remote_session
            session.changed_file_count = len(result.changed_files)
            if isinstance(result.change_set, CodexChangeSet):
                session.additions = result.change_set.additions
                session.deletions = result.change_set.deletions
                if result.change_set.files:
                    self._reviews[session.session_id] = CodexReviewSession(result.change_set)
            session.transition(CodexSessionStatus.VERIFYING, 80)
            self._emit(CodexEvent.create(session.session_id, CodexEventType.VERIFICATION_STARTED, progress=85))
            report = self.validator.verify(task, result)
            session.verification_outcome = report.outcome.value
            if report.outcome is not VerificationOutcome.SUCCESS:
                session.error_code = f"verification_{report.outcome.value}"
                session.result_summary = report.summary
                session.transition(CodexSessionStatus.FAILED, 100)
                session.exit_category = "verification_failed"
                self._emit(CodexEvent.create(session.session_id, CodexEventType.FAILED, progress=100))
            else:
                session.result_summary = self.response_quality.prepare(result, report)
                session.review_pending = bool(
                    task.risk_level is CodexRiskLevel.MODIFICATION and result.changed_files
                )
                session.transition(CodexSessionStatus.COMPLETED, 100)
                session.exit_category = "success"
                self._emit(CodexEvent.create(session.session_id, CodexEventType.COMPLETED, progress=100))
            return result
        except CodexClientUnavailableError:
            retain_history = False
            session.error_code = "client_unavailable"
            session.result_summary = (
                "Codex bağlantısı henüz yapılandırılmadığı için görev başlatılamadı. "
                "Çalışma alanı ve plan kaydedilmedi."
            )
            session.transition(CodexSessionStatus.FAILED, 100)
            session.exit_category = "client_unavailable"
            self._emit(CodexEvent.create(session.session_id, CodexEventType.FAILED, progress=100))
            self.repository.delete(session.session_id)
            raise
        except CodexTransportError as error:
            session.error_code = error.code
            session.result_summary = error.user_message
            status = (
                CodexSessionStatus.CANCELLED if error.code == "cancelled"
                else CodexSessionStatus.PAUSED if error.code == "runtime_approval_required"
                else CodexSessionStatus.FAILED
            )
            session.transition(status, 100)
            session.exit_category = error.code
            event_type = (CodexEventType.APPROVAL_REQUESTED
                          if status is CodexSessionStatus.PAUSED else CodexEventType.FAILED)
            self._emit(CodexEvent.create(session.session_id, event_type, progress=100))
            raise
        except Exception:
            session.error_code = "client_failure"
            session.result_summary = "Codex istemcisi görevi tamamlayamadı."
            session.transition(CodexSessionStatus.FAILED, 100)
            session.exit_category = "client_failure"
            self._emit(CodexEvent.create(session.session_id, CodexEventType.FAILED, progress=100))
            raise
        finally:
            session.duration_seconds = max(0.0, time.monotonic() - started)
            if session.status is not CodexSessionStatus.PAUSED:
                self.permissions.consume_one_time(session.project_context.root_path)
            if retain_history:
                self.repository.save(session)

    def cancel(self) -> None:
        if hasattr(self.client, "cancel"):
            self.client.cancel()
        if self._session is not None and not self._session.terminal:
            self._session.transition(CodexSessionStatus.CANCELLED, 100)
            self._session.error_code = "cancelled"
            self._session.result_summary = "Codex görevi iptal edildi."
            self.repository.save(self._session)

    def refresh_client_info(self):
        if hasattr(self.client, "refresh"):
            return self.client.refresh()
        return self.client_info

    def launch_login(self, *, device_auth: bool = False) -> None:
        if not hasattr(self.client, "launch_login"):
            raise CodexClientUnavailableError("Codex CLI bulunamadı.")
        self.client.launch_login(device_auth=device_auth)

    def logout(self, *, confirmed: bool = False):
        if not hasattr(self.client, "logout"):
            raise CodexClientUnavailableError("Codex CLI bulunamadı.")
        return self.client.logout(confirmed=confirmed)

    def diagnostics_report(self) -> str:
        if not hasattr(self.client, "diagnostics_report"):
            return "Codex CLI diagnostics kullanılamıyor."
        return self.client.diagnostics_report()

    def mark_result_surfaced(self, session_id: str) -> None:
        session = self._matching(session_id)
        session.result_surfaced = True
        self.repository.save(session)
        self.repository.mark_surfaced(session_id)

    def review_summary(self, session_id: str) -> CodexReviewSummary | None:
        self._matching(session_id)
        review = self._reviews.get(session_id)
        return review.summary() if review is not None else None

    def review_change_set(self, session_id: str) -> CodexChangeSet | None:
        self._matching(session_id)
        review = self._reviews.get(session_id)
        return review.change_set if review is not None else None

    def decide_review(self, session_id: str,
                      decision: CodexReviewDecision) -> CodexReviewSummary:
        session = self._matching(session_id)
        review = self._reviews.get(session_id)
        if review is None:
            raise ValueError("İncelenecek Codex değişikliği yok.")
        review.decide(decision)
        summary = review.summary()
        session.review_pending = not summary.approved_for_continue
        self.repository.save(session)
        return summary

    def complete_review(self, session_id: str) -> None:
        session = self._matching(session_id)
        summary = self.review_summary(session_id)
        if summary is None or not summary.approved_for_continue:
            raise PermissionError("Codex değişiklikleri onaylanmadan devam edilemez.")
        session.review_pending = False
        self.repository.save(session)

    def shutdown(self) -> None:
        if hasattr(self.client, "shutdown"):
            self.client.shutdown()
        if self._session is not None and not self._session.terminal:
            self._session.process_termination_status = "shutdown_requested"
            self._session.transition(CodexSessionStatus.INTERRUPTED, 100)
            self._session.error_code = "app_shutdown"
            self._session.result_summary = "Codex görevi uygulama kapanırken kesintiye uğradı."
            self._session.exit_category = "app_shutdown"
            self.repository.save(self._session)

    def deny(self, session_id: str) -> None:
        session = self._matching(session_id)
        session.approval_decision = "denied"
        session.exit_category = "user_denied"
        session.transition(CodexSessionStatus.CANCELLED)
        self.permissions.consume_one_time(session.project_context.root_path)
        self.repository.save(session)

    def decide(self, session_id: str, decision: ApprovalDecision) -> CodexResult | None:
        """Reuse Agent Mode's unambiguous approval decisions."""
        decision = ApprovalDecision(decision)
        if decision is ApprovalDecision.APPROVE:
            return self.start(session_id, approved=True)
        if decision in {ApprovalDecision.SKIP, ApprovalDecision.CANCEL}:
            self.deny(session_id)
            return None
        if decision is ApprovalDecision.MODIFY:
            self._matching(session_id).transition(CodexSessionStatus.WAITING_APPROVAL, 20)
            return None
        raise ValueError("Codex onayı açık değil; onayla, reddet veya düzenle.")

    def _handle_client_event(self, event: CodexEvent) -> None:
        if self._session is None:
            return
        session = self._session
        session.last_event = event.event_type.value
        session.last_activity_at = event.occurred_at
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
