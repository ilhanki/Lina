"""Single-session Agent Mode lifecycle controller."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from lina.agent.context import AgentContext
from lina.agent.errors import AgentPlanError, AgentStateError
from lina.agent.executor import AgentExecutor
from lina.agent.models import (
    AgentPlan, AgentSession, AgentSessionStatus, AgentStep, AgentStepStatus,
    ApprovalDecision, VerificationStatus,
)
from lina.agent.persistence import AgentSessionRepository
from lina.agent.planner import AgentPlanner
from lina.agent.policy import AgentPolicy
from lina.agent.verifier import AgentVerifier
from lina.brain.routing.models import RequestContext


@dataclass(frozen=True, slots=True)
class AgentProgress:
    session_id: str
    status: AgentSessionStatus
    current: int
    total: int
    summary: str


class AgentController:
    """Coordinates plans without hidden background continuation."""

    def __init__(
        self,
        planner: AgentPlanner,
        executor: AgentExecutor,
        verifier: AgentVerifier,
        policy: AgentPolicy,
        repository: AgentSessionRepository | None = None,
        *,
        auto_start_read_only_plans: bool = False,
        always_show_plan: bool = True,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.policy = policy
        self.repository = repository
        self.auto_start_read_only_plans = auto_start_read_only_plans
        self.always_show_plan = always_show_plan
        self._session: AgentSession | None = None
        self._capabilities = ()
        self._step_attempts: dict[str, int] = {}
        self._lock = RLock()

    @property
    def active_session(self) -> AgentSession | None:
        return self._session if self._session is not None and not self._session.terminal else None

    @property
    def session(self) -> AgentSession | None:
        return self._session

    def create_session(self, user_request: str, conversation_id: int | None, generation_id: int = 0) -> AgentSession:
        with self._lock:
            if self.active_session is not None:
                raise AgentStateError("Aynı anda yalnızca bir Agent görevi çalışabilir.")
            if not user_request.strip():
                raise AgentStateError("Agent görevi için açık bir istek gerekli.")
            session = AgentSession.create(conversation_id, user_request)
            session.generation_id = generation_id
            self._session = session
            self._step_attempts.clear()
            self._persist()
            return session

    def plan(self, capabilities=None, recent_messages=(), relevant_memories=()) -> AgentPlan:
        with self._lock:
            session = self._require_session()
            if session.status not in {AgentSessionStatus.IDLE, AgentSessionStatus.PLANNING}:
                raise AgentStateError("Agent görevi bu durumda planlanamaz.")
            session.status = AgentSessionStatus.PLANNING
            self._capabilities = tuple(capabilities or self.policy.capability_snapshot(self.executor.registry))
            self._persist()
            context = AgentContext.bounded(session.user_request, recent_messages, relevant_memories, self._capabilities)
            try:
                session.plan = self.planner.plan(context)
            except Exception:
                session.status = AgentSessionStatus.FAILED
                session.touch()
                self._persist()
                raise
            session.metrics.planned_step_count = len(session.plan.steps)
            auto = (
                self.auto_start_read_only_plans and not self.always_show_plan
                and len(session.plan.steps) == 1
                and not self.policy.requires_step_approval(session.plan.steps[0])
            )
            session.status = AgentSessionStatus.READY if auto else AgentSessionStatus.AWAITING_PLAN_APPROVAL
            session.touch()
            self._persist()
            if auto:
                self.run()
            return session.plan

    def approve_plan(self, session_id: str, generation_id: int | None = None) -> AgentSession:
        with self._lock:
            session = self._matching(session_id, generation_id)
            if session.status is not AgentSessionStatus.AWAITING_PLAN_APPROVAL:
                raise AgentStateError("Plan onay beklemiyor.")
            session.approval_state = "plan_approved"
            session.metrics.approval_count += 1
            session.status = AgentSessionStatus.READY
            session.touch()
            self._persist()
            return session

    def run(self, conversation_id: int | None = None) -> AgentSession:
        with self._lock:
            session = self._require_session()
            if conversation_id is not None and session.conversation_id != conversation_id:
                raise AgentStateError("Agent sonucu farklı bir sohbete uygulanamaz.")
            if session.status not in {AgentSessionStatus.READY, AgentSessionStatus.RUNNING}:
                raise AgentStateError("Agent görevi çalışmaya hazır değil.")
            session.status = AgentSessionStatus.RUNNING
            while session.plan and session.current_step_index < len(session.plan.steps):
                if session.cancellation_token.cancelled:
                    return self._finish_cancelled()
                step = session.plan.steps[session.current_step_index]
                if step.status in {AgentStepStatus.SUCCEEDED, AgentStepStatus.SKIPPED}:
                    session.current_step_index += 1
                    continue
                if any(self._step_by_id(dep).status is not AgentStepStatus.SUCCEEDED for dep in step.dependencies):
                    step.status = AgentStepStatus.BLOCKED
                    step.error_code = "dependency_failed"
                    return self._finish_failure()
                if self.policy.requires_step_approval(step):
                    step.status = AgentStepStatus.WAITING_APPROVAL
                    session.status = AgentSessionStatus.AWAITING_STEP_APPROVAL
                    session.approval_state = step.step_id
                    session.touch()
                    self._persist()
                    return session
                if not self._execute_current(step):
                    return session
            return self._finish_success()

    def approve_step(self, session_id: str, decision: ApprovalDecision, generation_id: int | None = None) -> AgentSession:
        with self._lock:
            session = self._matching(session_id, generation_id)
            if session.status is not AgentSessionStatus.AWAITING_STEP_APPROVAL or session.plan is None:
                raise AgentStateError("Agent adımı onay beklemiyor.")
            step = session.plan.steps[session.current_step_index]
            if decision is ApprovalDecision.AMBIGUOUS:
                return session
            if decision is ApprovalDecision.CANCEL:
                return self.cancel(session_id)
            if decision is ApprovalDecision.MODIFY:
                session.status = AgentSessionStatus.AWAITING_PLAN_APPROVAL
                session.approval_state = "modify_requested"
                self._persist()
                return session
            if decision is ApprovalDecision.SKIP:
                step.status = AgentStepStatus.SKIPPED
                step.result_summary = "Kullanıcı tarafından atlandı."
                session.metrics.skipped_count += 1
                session.current_step_index += 1
                session.status = AgentSessionStatus.RUNNING
                self._persist()
                return self.run()
            session.metrics.approval_count += 1
            step.approval_required = False
            session.approval_state = f"approved:{step.step_id}"
            session.status = AgentSessionStatus.RUNNING
            if not self._execute_current(step):
                return session
            return self.run()

    def pause(self, session_id: str) -> AgentSession:
        with self._lock:
            session = self._matching(session_id)
            if session.status not in {AgentSessionStatus.RUNNING, AgentSessionStatus.READY, AgentSessionStatus.AWAITING_STEP_APPROVAL}:
                raise AgentStateError("Agent görevi bu durumda duraklatılamaz.")
            session.status = AgentSessionStatus.PAUSED
            session.touch()
            self._persist()
            return session

    def resume(self, session_id: str) -> AgentSession:
        with self._lock:
            session = self._matching(session_id)
            if session.status is not AgentSessionStatus.PAUSED:
                raise AgentStateError("Agent görevi duraklatılmış değil.")
            if session.plan and session.current_step_index < len(session.plan.steps) and session.plan.steps[session.current_step_index].status is AgentStepStatus.WAITING_APPROVAL:
                session.status = AgentSessionStatus.AWAITING_STEP_APPROVAL
                self._persist()
                return session
            session.status = AgentSessionStatus.READY
            self._persist()
            return self.run()

    def cancel(self, session_id: str) -> AgentSession:
        with self._lock:
            session = self._matching(session_id)
            session.cancellation_token.cancel()
            session.generation_id += 1
            return self._finish_cancelled()

    def shutdown(self) -> None:
        with self._lock:
            if self.active_session is not None:
                self.cancel(self.active_session.session_id)
            self.executor.shutdown()

    def status(self) -> AgentProgress | None:
        session = self._session
        if session is None:
            return None
        total = len(session.plan.steps) if session.plan else 0
        return AgentProgress(session.session_id, session.status, min(session.current_step_index + (0 if session.terminal else 1), total), total, self.result_summary())

    def result_summary(self) -> str:
        session = self._session
        if session is None:
            return "Aktif Agent görevi yok."
        if session.plan is None:
            return "Agent planı henüz hazırlanmadı."
        completed = sum(step.status is AgentStepStatus.SUCCEEDED for step in session.plan.steps)
        skipped = sum(step.status is AgentStepStatus.SKIPPED for step in session.plan.steps)
        failed = sum(step.status in {AgentStepStatus.FAILED, AgentStepStatus.BLOCKED} for step in session.plan.steps)
        return f"Tamamlanan: {completed}; atlanan: {skipped}; başarısız: {failed}."

    def _execute_current(self, step: AgentStep) -> bool:
        session = self._require_session()
        step.status = AgentStepStatus.RUNNING
        result = self.executor.execute(step, RequestContext(session.conversation_id, generation_id=session.generation_id, confirmed=True), session.cancellation_token)
        if session.cancellation_token.cancelled:
            self._finish_cancelled()
            return False
        step.execution_id = result.execution_id
        session.metrics.executed_step_count += 1
        session.metrics.step_duration_ms.append(result.duration_ms)
        step.status = AgentStepStatus.VERIFYING
        verification = self.verifier.verify(step, result)
        if verification.status is VerificationStatus.VERIFIED:
            step.status = AgentStepStatus.SUCCEEDED
            step.result_summary = verification.summary
            session.metrics.succeeded_count += 1
            session.current_step_index += 1
            session.touch()
            self._persist()
            return True
        step.error_code = result.error_code or verification.status.value
        step.result_summary = verification.summary
        attempts = self._step_attempts.get(step.step_id, 0) + 1
        self._step_attempts[step.step_id] = attempts
        if verification.status is VerificationStatus.FAILED and self.policy.can_retry(step, attempts):
            return self._execute_current(step)
        step.status = AgentStepStatus.FAILED
        session.metrics.failed_count += 1
        if self._try_replan(step):
            return True
        self._finish_failure(uncertain=verification.status is VerificationStatus.UNCERTAIN)
        return False

    def _try_replan(self, failed_step: AgentStep) -> bool:
        session = self._require_session()
        if session.metrics.replan_count >= self.policy.max_replans or session.plan is None:
            return False
        completed = tuple(step.result_summary or step.title for step in session.plan.steps if step.status is AgentStepStatus.SUCCEEDED)
        context = AgentContext.bounded(session.user_request, capabilities=self._capabilities, completed=completed)
        session.status = AgentSessionStatus.REPLANNING
        try:
            replacement = self.planner.replan(context, failed_step, failed_step.error_code or "failed")
        except AgentPlanError:
            return False
        signatures = {(step.tool_name, repr(sorted(step.typed_arguments.items()))) for step in session.plan.steps if step.risk_level.value == "persistent"}
        if any((step.tool_name, repr(sorted(step.typed_arguments.items()))) in signatures for step in replacement.steps if step.risk_level.value == "persistent"):
            return False
        session.metrics.replan_count += 1
        session.plan = AgentPlan(replacement.plan_id, replacement.summary, [step for step in session.plan.steps if step.status is AgentStepStatus.SUCCEEDED] + replacement.steps, revision=session.plan.revision + 1)
        session.current_step_index = sum(step.status is AgentStepStatus.SUCCEEDED for step in session.plan.steps)
        session.status = AgentSessionStatus.AWAITING_PLAN_APPROVAL if any(self.policy.requires_step_approval(step) for step in replacement.steps) else AgentSessionStatus.RUNNING
        self._persist()
        return session.status is AgentSessionStatus.RUNNING

    def _finish_success(self) -> AgentSession:
        session = self._require_session()
        skipped = bool(session.plan and any(step.status is AgentStepStatus.SKIPPED for step in session.plan.steps))
        session.status = AgentSessionStatus.PARTIALLY_COMPLETED if skipped else AgentSessionStatus.COMPLETED
        session.current_step_index = len(session.plan.steps) if session.plan else 0
        session.touch()
        self._persist()
        return session

    def _finish_failure(self, uncertain: bool = False) -> AgentSession:
        session = self._require_session()
        completed = bool(session.plan and any(step.status is AgentStepStatus.SUCCEEDED for step in session.plan.steps))
        session.status = AgentSessionStatus.PARTIALLY_COMPLETED if completed or uncertain else AgentSessionStatus.FAILED
        session.touch()
        self._persist()
        return session

    def _finish_cancelled(self) -> AgentSession:
        session = self._require_session()
        if session.plan:
            for step in session.plan.steps[session.current_step_index:]:
                if step.status in {AgentStepStatus.PENDING, AgentStepStatus.WAITING_APPROVAL, AgentStepStatus.RUNNING, AgentStepStatus.VERIFYING}:
                    step.status = AgentStepStatus.CANCELLED
        session.status = AgentSessionStatus.CANCELLED
        session.metrics.cancellation_count += 1
        session.touch()
        self._persist()
        return session

    def _matching(self, session_id: str, generation_id: int | None = None) -> AgentSession:
        session = self._require_session()
        if session.session_id != session_id or (generation_id is not None and session.generation_id != generation_id):
            raise AgentStateError("Eski veya farklı Agent oturumu yanıtı yok sayıldı.")
        return session

    def _require_session(self) -> AgentSession:
        if self._session is None:
            raise AgentStateError("Aktif Agent görevi yok.")
        return self._session

    def _step_by_id(self, step_id: str) -> AgentStep:
        session = self._require_session()
        return next(step for step in session.plan.steps if step.step_id == step_id)  # type: ignore[union-attr]

    def _persist(self) -> None:
        if self.repository is not None and self._session is not None:
            self.repository.save(self._session)
