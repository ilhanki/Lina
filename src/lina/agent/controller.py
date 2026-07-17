"""Single-session Agent Mode lifecycle controller."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from lina.agent.context import AgentContext
from lina.agent.errors import AgentClarificationRequired, AgentErrorCode, AgentPlanError, AgentStateError
from lina.agent.executor import AgentExecutor
from lina.agent.models import (
    AgentEvent, AgentEventSeverity, AgentEventType, AgentPlan, AgentSession,
    AgentSessionStatus, AgentStep, AgentStepStatus, ApprovalDecision, RiskLevel,
    VerificationStatus,
)
from lina.agent.persistence import AgentSessionRepository
from lina.agent.plan_editing import AgentPlanDiff, diff_plans
from lina.agent.planner import AgentPlanner
from lina.agent.policy import AgentPolicy
from lina.agent.reliability import (
    AgentLoopDetector, checkpoint_for_step, idempotency_key,
    normalized_operation_hash, user_error_message,
)
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
        self._loop_detector = AgentLoopDetector()
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
            self._loop_detector.reset()
            self._record_event(AgentEventType.SESSION_CREATED, "Agent görevi oluşturuldu.")
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
            except AgentClarificationRequired as error:
                loop = self._loop_detector.observe_clarification(str(error))
                if loop.detected:
                    session.status = AgentSessionStatus.FAILED
                    session.error_code = AgentErrorCode.LOOP_DETECTED.value
                    session.metrics.loop_detection_count += 1
                    session.last_summary = user_error_message(AgentErrorCode.LOOP_DETECTED)
                    self._record_event(
                        AgentEventType.SESSION_FAILED,
                        session.last_summary,
                        severity=AgentEventSeverity.ERROR,
                        technical_code=session.error_code,
                    )
                else:
                    session.status = AgentSessionStatus.AWAITING_INPUT
                    session.approval_state = ",".join(error.missing_parameters) or "clarification"
                    session.last_summary = str(error)
                session.touch()
                self._persist()
                raise
            except Exception:
                session.status = AgentSessionStatus.FAILED
                session.error_code = AgentErrorCode.INTERNAL_ERROR.value
                session.touch()
                self._record_event(AgentEventType.SESSION_FAILED, "Plan güvenli biçimde hazırlanamadı.", severity=AgentEventSeverity.ERROR, technical_code=session.error_code)
                self._persist()
                raise
            session.metrics.planned_step_count = len(session.plan.steps)
            session.last_summary = "Agent planı hazır."
            self._record_event(AgentEventType.PLAN_CREATED, "Agent planı oluşturuldu.")
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

    def provide_input(
        self,
        session_id: str,
        text: str,
        conversation_id: int | None,
        generation_id: int | None = None,
    ) -> AgentPlan:
        with self._lock:
            session = self._matching(session_id, generation_id)
            if session.status is not AgentSessionStatus.AWAITING_INPUT:
                raise AgentStateError("Agent görevi ek bilgi beklemiyor.")
            if session.conversation_id != conversation_id:
                raise AgentStateError("Agent açıklaması farklı bir sohbetten uygulanamaz.")
            if not text.strip():
                raise AgentStateError("Görevi sürdürmek için gerekli bilgiyi yaz.")
            session.user_request = f"{session.user_request} {text.strip()}"[:2400]
            session.status = AgentSessionStatus.PLANNING
            session.approval_state = None
            session.touch()
            self._persist()
            return self.plan(capabilities=self._capabilities)

    def create_from_template(
        self,
        template_id: str,
        parameters: dict[str, object],
        conversation_id: int | None,
        generation_id: int = 0,
    ) -> AgentSession:
        with self._lock:
            registry = self.planner.template_registry
            if registry is None:
                raise AgentStateError("Hazır Agent görevleri şu anda kullanılamıyor.")
            template = registry.get(template_id)
            if template is None or not template.enabled:
                raise AgentStateError("Seçilen hazır görev kullanılamıyor.")
            capabilities = tuple(self.policy.capability_snapshot(self.executor.registry))
            available = {item.name for item in capabilities if item.available}
            if not template.supports(available):
                raise AgentStateError("Bu görev için gerekli araç şu anda kullanılamıyor.")
            session = self.create_session(f"Template request: {template_id}", conversation_id, generation_id)
            try:
                session.plan = template.create_plan(parameters)
                self.policy.validate_plan(session.plan, available)
            except Exception as error:
                session.status = AgentSessionStatus.FAILED
                session.error_code = AgentErrorCode.INVALID_ARGUMENTS.value
                session.last_summary = user_error_message(session.error_code)
                self._record_event(AgentEventType.SESSION_FAILED, session.last_summary, severity=AgentEventSeverity.ERROR, technical_code=session.error_code)
                session.touch()
                self._persist()
                raise AgentStateError("Hazır görev bilgileri doğrulanamadı.") from error
            self._capabilities = capabilities
            session.metrics.planned_step_count = len(session.plan.steps)
            session.status = AgentSessionStatus.AWAITING_PLAN_APPROVAL
            session.last_summary = "Hazır görev planı oluşturuldu; otomatik olarak başlatılmadı."
            self._record_event(AgentEventType.PLAN_CREATED, "Hazır görev planı oluşturuldu.")
            session.touch()
            self._persist()
            return session

    def apply_edited_plan(
        self,
        session_id: str,
        edited_plan: AgentPlan,
        generation_id: int | None = None,
    ) -> AgentPlanDiff:
        with self._lock:
            session = self._matching(session_id, generation_id)
            if session.plan is None or session.status not in {
                AgentSessionStatus.AWAITING_PLAN_APPROVAL,
                AgentSessionStatus.AWAITING_STEP_APPROVAL,
                AgentSessionStatus.READY,
            }:
                raise AgentStateError("Agent planı bu durumda düzenlenemez.")
            available = {item.name for item in self._capabilities if item.available}
            if not available:
                available = {item.name for item in self.policy.capability_snapshot(self.executor.registry) if item.available}
            self.policy.validate_plan(edited_plan, available)
            difference = diff_plans(session.plan, edited_plan)
            session.plan = edited_plan
            session.current_step_index = next(
                (index for index, step in enumerate(edited_plan.steps) if step.status not in {AgentStepStatus.SUCCEEDED, AgentStepStatus.SKIPPED}),
                len(edited_plan.steps),
            )
            session.status = AgentSessionStatus.AWAITING_PLAN_APPROVAL
            session.approval_state = "plan_modified"
            session.last_summary = "Plan güncellendi; yeniden onay bekliyor."
            self._record_event(AgentEventType.PLAN_MODIFIED, session.last_summary)
            session.touch()
            self._persist()
            return difference

    def regenerate_plan(self, session_id: str, generation_id: int | None = None) -> AgentPlanDiff:
        with self._lock:
            session = self._matching(session_id, generation_id)
            if session.plan is None:
                raise AgentStateError("Yeniden üretilecek Agent planı yok.")
            previous = session.plan
            available = {item.name for item in self._capabilities if item.available}
            if previous.template_id and self.planner.template_registry is not None:
                template = self.planner.template_registry.require(previous.template_id)
                replacement = template.create_plan(_template_parameters(previous))
            else:
                context = AgentContext.bounded(session.user_request, capabilities=self._capabilities)
                replacement = self.planner.plan(context)
            completed = [deepcopy(step) for step in previous.steps if step.status is AgentStepStatus.SUCCEEDED]
            completed_ids = {step.step_id for step in completed}
            replacement.steps = completed + [step for step in replacement.steps if step.step_id not in completed_ids]
            replacement.revision = previous.revision + 1
            self.policy.validate_plan(replacement, available)
            difference = diff_plans(previous, replacement)
            session.plan = replacement
            session.current_step_index = len(completed)
            session.status = AgentSessionStatus.AWAITING_PLAN_APPROVAL
            session.approval_state = "plan_regenerated"
            session.last_summary = "Plan yeniden üretildi; çalıştırılmadan önce onay bekliyor."
            self._record_event(AgentEventType.PLAN_MODIFIED, session.last_summary)
            session.touch()
            self._persist()
            return difference

    def approve_plan(self, session_id: str, generation_id: int | None = None) -> AgentSession:
        with self._lock:
            session = self._matching(session_id, generation_id)
            if session.status is not AgentSessionStatus.AWAITING_PLAN_APPROVAL:
                raise AgentStateError("Plan onay beklemiyor.")
            session.approval_state = "plan_approved"
            session.metrics.approval_count += 1
            session.status = AgentSessionStatus.READY
            session.last_summary = "Plan kullanıcı tarafından onaylandı."
            self._record_event(AgentEventType.PLAN_APPROVED, "Plan kullanıcı tarafından onaylandı.")
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
                    step.error_code = AgentErrorCode.DEPENDENCY_FAILED.value
                    return self._finish_failure()
                if self.policy.requires_step_approval(step):
                    step.status = AgentStepStatus.WAITING_APPROVAL
                    session.status = AgentSessionStatus.AWAITING_STEP_APPROVAL
                    session.approval_state = step.step_id
                    session.last_summary = "Kalıcı adım kullanıcı onayı bekliyor."
                    self._record_event(AgentEventType.APPROVAL_REQUESTED, "Kalıcı adım için onay istendi.", step_id=step.step_id)
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
                self._record_event(AgentEventType.APPROVAL_DENIED, "Kullanıcı onayı reddetti.", step_id=step.step_id)
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
                step.verification_status = None
                session.checkpoints.append(checkpoint_for_step(step))
                self._record_event(AgentEventType.STEP_SKIPPED, "Adım kullanıcı tarafından atlandı.", step_id=step.step_id)
                session.current_step_index += 1
                session.status = AgentSessionStatus.RUNNING
                self._persist()
                return self.run()
            session.metrics.approval_count += 1
            step.approval_required = False
            session.approval_state = f"approved:{step.step_id}"
            session.status = AgentSessionStatus.RUNNING
            self._record_event(AgentEventType.APPROVAL_GRANTED, "Kalıcı adım onaylandı.", step_id=step.step_id)
            if not self._execute_current(step):
                return session
            return self.run()

    def pause(self, session_id: str) -> AgentSession:
        with self._lock:
            session = self._matching(session_id)
            if session.status not in {AgentSessionStatus.RUNNING, AgentSessionStatus.READY, AgentSessionStatus.AWAITING_STEP_APPROVAL}:
                raise AgentStateError("Agent görevi bu durumda duraklatılamaz.")
            session.status = AgentSessionStatus.PAUSED
            session.last_summary = "Agent görevi duraklatıldı."
            self._record_event(AgentEventType.SESSION_PAUSED, session.last_summary)
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
            session.last_summary = "Görev güvenli kullanıcı eylemiyle yeniden başlatıldı."
            self._record_event(AgentEventType.SESSION_RESUMED, session.last_summary)
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
                session = self.active_session
                session.cancellation_token.cancel()
                session.generation_id += 1
                session.status = AgentSessionStatus.INTERRUPTED
                session.error_code = AgentErrorCode.INTERRUPTED.value
                session.last_summary = user_error_message(AgentErrorCode.INTERRUPTED)
                self._record_event(AgentEventType.SESSION_INTERRUPTED, session.last_summary, severity=AgentEventSeverity.WARNING, technical_code=session.error_code)
                session.touch()
                self._persist()
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
        if session.status is AgentSessionStatus.COMPLETED:
            return f"Görev tamamlandı. {completed} adım güvenli biçimde doğrulandı."
        if session.status is AgentSessionStatus.PARTIALLY_COMPLETED:
            return f"Görev kısmen tamamlandı. {completed} adım doğrulandı, {skipped} adım atlandı."
        if session.status is AgentSessionStatus.UNCERTAIN:
            return user_error_message(AgentErrorCode.PERSISTENT_OUTCOME_UNCERTAIN)
        if session.status in {AgentSessionStatus.FAILED, AgentSessionStatus.BLOCKED} and session.error_code:
            return user_error_message(session.error_code)
        if session.status is AgentSessionStatus.AWAITING_INPUT:
            return session.last_summary or "Görevi başlatmak için bazı bilgiler eksik."
        return f"Görev ilerliyor: {completed} tamamlandı, {skipped} atlandı, {failed} başarısız."

    def safe_restart(self, session_id: str, *, user_request: str | None = None) -> AgentSession:
        with self._lock:
            source = self._matching(session_id)
            if source.status not in {
                AgentSessionStatus.FAILED,
                AgentSessionStatus.CANCELLED,
                AgentSessionStatus.INTERRUPTED,
                AgentSessionStatus.BLOCKED,
                AgentSessionStatus.UNCERTAIN,
                AgentSessionStatus.PARTIALLY_COMPLETED,
            }:
                raise AgentStateError("Bu görev güvenli kopya olarak yeniden başlatılamaz.")
            replacement = AgentSession.create(source.conversation_id, user_request or source.user_request)
            replacement.source_session_id = source.session_id
            replacement.generation_id = source.generation_id + 1
            if source.plan is not None:
                id_map = {step.step_id: f"restart-{index}" for index, step in enumerate(source.plan.steps, 1)}
                steps: list[AgentStep] = []
                for original in source.plan.steps:
                    step = deepcopy(original)
                    step.step_id = id_map[original.step_id]
                    step.dependencies = tuple(id_map[item] for item in original.dependencies)
                    step.status = AgentStepStatus.PENDING
                    step.result_summary = None
                    step.error_code = None
                    step.execution_id = None
                    step.verification_status = None
                    step.retry_count = 0
                    step.idempotency_key = None
                    step.approval_required = step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE}
                    steps.append(step)
                replacement.plan = AgentPlan(
                    uuid4().hex,
                    source.plan.summary,
                    steps,
                    template_id=source.plan.template_id,
                    title=source.plan.title,
                    risk_summary=source.plan.risk_summary,
                )
                replacement.metrics.planned_step_count = len(steps)
                replacement.status = AgentSessionStatus.AWAITING_PLAN_APPROVAL
                replacement.duplicate_check_required = any(
                    step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE}
                    and original.status in {AgentStepStatus.RUNNING, AgentStepStatus.VERIFYING, AgentStepStatus.SUCCEEDED, AgentStepStatus.FAILED}
                    for step, original in zip(steps, source.plan.steps)
                )
            self._session = replacement
            self._step_attempts.clear()
            self._loop_detector.reset()
            self._record_event(AgentEventType.SESSION_CREATED, "Görev güvenli bir kopya olarak yeniden hazırlandı.")
            self._persist()
            return replacement

    def _execute_current(self, step: AgentStep) -> bool:
        session = self._require_session()
        if not self.executor.available(step.tool_name):
            step.status = AgentStepStatus.BLOCKED
            step.error_code = AgentErrorCode.TOOL_UNAVAILABLE.value
            step.result_summary = user_error_message(AgentErrorCode.TOOL_UNAVAILABLE)
            session.error_code = step.error_code
            session.metrics.tool_availability_failure_count += 1
            session.checkpoints.append(checkpoint_for_step(step))
            self._record_event(AgentEventType.STEP_FAILED, step.result_summary, step_id=step.step_id, severity=AgentEventSeverity.WARNING, technical_code=step.error_code)
            session.status = AgentSessionStatus.BLOCKED
            session.touch()
            self._persist()
            return False
        step.idempotency_key = step.idempotency_key or idempotency_key(session.session_id, step)
        step.status = AgentStepStatus.RUNNING
        self._record_event(AgentEventType.STEP_STARTED, "Agent adımı başlatıldı.", step_id=step.step_id)
        generation = session.generation_id
        result = self.executor.execute(step, RequestContext(session.conversation_id, generation_id=session.generation_id, confirmed=True), session.cancellation_token)
        if session.generation_id != generation:
            step.status = AgentStepStatus.CANCELLED
            step.error_code = AgentErrorCode.STALE_RESULT.value
            return False
        if session.cancellation_token.cancelled:
            self._finish_cancelled()
            return False
        step.execution_id = result.execution_id
        session.metrics.executed_step_count += 1
        session.metrics.step_duration_ms.append(result.duration_ms)
        step.status = AgentStepStatus.VERIFYING
        verification = self.verifier.verify(step, result)
        step.verification_status = verification.status
        if verification.status is VerificationStatus.VERIFIED:
            step.status = AgentStepStatus.SUCCEEDED
            step.result_summary = verification.summary
            session.metrics.succeeded_count += 1
            session.checkpoints.append(checkpoint_for_step(step))
            self._record_event(AgentEventType.STEP_VERIFIED, "Agent adımı deterministic olarak doğrulandı.", step_id=step.step_id)
            session.current_step_index += 1
            session.touch()
            stored = self._persist()
            if not stored and step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE}:
                step.status = AgentStepStatus.FAILED
                step.verification_status = VerificationStatus.UNCERTAIN
                step.error_code = AgentErrorCode.PERSISTENT_OUTCOME_UNCERTAIN.value
                session.metrics.uncertain_outcome_count += 1
                self._finish_failure(uncertain=True)
                return False
            return True
        step.error_code = result.error_code or (
            AgentErrorCode.VERIFICATION_UNCERTAIN.value
            if verification.status is VerificationStatus.UNCERTAIN
            else AgentErrorCode.VERIFICATION_FAILED.value
        )
        session.error_code = step.error_code
        step.result_summary = verification.summary
        attempts = self._step_attempts.get(step.step_id, 0) + 1
        self._step_attempts[step.step_id] = attempts
        step.retry_count = attempts
        step.status = AgentStepStatus.FAILED
        session.checkpoints.append(checkpoint_for_step(step))
        self._record_event(AgentEventType.STEP_FAILED, "Agent adımı doğrulanamadı.", step_id=step.step_id, severity=AgentEventSeverity.WARNING, technical_code=step.error_code)
        self._persist()
        if (
            verification.status is VerificationStatus.FAILED
            and result.retryable
            and self.policy.can_retry(step, attempts, step.error_code, cancelled=session.cancellation_token.cancelled)
        ):
            session.metrics.retry_count += 1
            return self._execute_current(step)
        session.metrics.failed_count += 1
        if verification.status is VerificationStatus.UNCERTAIN:
            session.metrics.uncertain_outcome_count += 1
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
        self._record_event(AgentEventType.REPLAN_STARTED, "Güvenli yeniden planlama başlatıldı.")
        try:
            replacement = self.planner.replan(context, failed_step, failed_step.error_code or "failed")
        except AgentPlanError:
            return False
        signatures = {normalized_operation_hash(step) for step in session.plan.steps if step.risk_level is RiskLevel.PERSISTENT}
        if any(normalized_operation_hash(step) in signatures for step in replacement.steps if step.risk_level is RiskLevel.PERSISTENT):
            return False
        plan_signature = ":".join(normalized_operation_hash(step) for step in replacement.steps)
        progress_token = ":".join(sorted(step.step_id for step in session.plan.steps if step.status is AgentStepStatus.SUCCEEDED))
        loop = self._loop_detector.observe_replan(plan_signature, progress_token)
        if loop.detected:
            session.metrics.loop_detection_count += 1
            session.error_code = AgentErrorCode.LOOP_DETECTED.value
            return False
        session.metrics.replan_count += 1
        session.plan = AgentPlan(replacement.plan_id, replacement.summary, [step for step in session.plan.steps if step.status is AgentStepStatus.SUCCEEDED] + replacement.steps, revision=session.plan.revision + 1)
        session.current_step_index = sum(step.status is AgentStepStatus.SUCCEEDED for step in session.plan.steps)
        session.status = AgentSessionStatus.AWAITING_PLAN_APPROVAL if any(self.policy.requires_step_approval(step) for step in replacement.steps) else AgentSessionStatus.RUNNING
        self._record_event(AgentEventType.REPLAN_COMPLETED, "Plan güvenli biçimde güncellendi.")
        self._persist()
        return session.status is AgentSessionStatus.RUNNING

    def _finish_success(self) -> AgentSession:
        session = self._require_session()
        skipped = bool(session.plan and any(step.status is AgentStepStatus.SKIPPED for step in session.plan.steps))
        session.status = AgentSessionStatus.PARTIALLY_COMPLETED if skipped else AgentSessionStatus.COMPLETED
        session.current_step_index = len(session.plan.steps) if session.plan else 0
        session.touch()
        session.last_summary = "Görev tamamlandı." if not skipped else "Görev kısmen tamamlandı."
        self._record_event(AgentEventType.SESSION_COMPLETED, session.last_summary)
        self._persist()
        return session

    def _finish_failure(self, uncertain: bool = False) -> AgentSession:
        session = self._require_session()
        completed = bool(session.plan and any(step.status is AgentStepStatus.SUCCEEDED for step in session.plan.steps))
        session.status = AgentSessionStatus.UNCERTAIN if uncertain else (AgentSessionStatus.PARTIALLY_COMPLETED if completed else AgentSessionStatus.FAILED)
        session.error_code = (
            AgentErrorCode.PERSISTENT_OUTCOME_UNCERTAIN.value
            if uncertain
            else session.error_code or AgentErrorCode.INTERNAL_ERROR.value
        )
        session.last_summary = user_error_message(session.error_code)
        session.touch()
        self._record_event(AgentEventType.SESSION_FAILED, session.last_summary, severity=AgentEventSeverity.ERROR, technical_code=session.error_code)
        self._persist()
        return session

    def _finish_cancelled(self) -> AgentSession:
        session = self._require_session()
        if session.plan:
            for step in session.plan.steps[session.current_step_index:]:
                if step.status in {AgentStepStatus.PENDING, AgentStepStatus.WAITING_APPROVAL, AgentStepStatus.RUNNING, AgentStepStatus.VERIFYING}:
                    step.status = AgentStepStatus.CANCELLED
        session.status = AgentSessionStatus.CANCELLED
        session.error_code = AgentErrorCode.USER_CANCELLED.value
        session.metrics.cancellation_count += 1
        session.touch()
        session.last_summary = "Agent görevi iptal edildi."
        self._record_event(AgentEventType.SESSION_CANCELLED, session.last_summary)
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

    def _record_event(
        self,
        event_type: AgentEventType,
        summary: str,
        *,
        step_id: str | None = None,
        severity: AgentEventSeverity = AgentEventSeverity.INFO,
        technical_code: str | None = None,
    ) -> None:
        if self._session is not None:
            self._session.events.append(AgentEvent.create(
                self._session.session_id,
                event_type,
                summary,
                step_id=step_id,
                severity=severity,
                technical_code=technical_code,
            ))

    def _persist(self) -> bool:
        if self.repository is not None and self._session is not None:
            try:
                self.repository.save(self._session)
            except (OSError, ValueError, TypeError):
                return False
        return True


def _template_parameters(plan: AgentPlan) -> dict[str, object]:
    step = next((item for item in plan.steps if item.status is not AgentStepStatus.SUCCEEDED), plan.steps[0])
    values = dict(step.typed_arguments)
    if plan.template_id in {"reminders.summary", "reminders.conflicts"}:
        return {"range": "upcoming"}
    if plan.template_id == "memory.store":
        values.setdefault("category", "conversation_note")
    if plan.template_id == "files.summarize":
        values.setdefault("summary_length", "short")
    return values
