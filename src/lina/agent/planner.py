"""Typed planning with one repair attempt and deterministic fallback."""

from __future__ import annotations

import json
from typing import Callable
from uuid import uuid4

from lina.agent.context import AgentContext
from lina.agent.errors import AgentClarificationRequired, AgentPlanError, AgentPolicyError
from lina.agent.models import AgentPlan, AgentStep, RiskLevel, VerificationRule
from lina.agent.policy import AgentPolicy
from lina.brain.routing.validation import parse_reminder_arguments


class AgentPlanner:
    def __init__(
        self,
        policy: AgentPolicy,
        generator: Callable[[AgentContext, str | None], object] | None = None,
        template_registry: object | None = None,
    ) -> None:
        self.policy = policy
        self.generator = generator
        self.template_registry = template_registry

    def plan(self, context: AgentContext) -> AgentPlan:
        available = {item.name for item in context.capabilities if item.available}
        template_plan = self._template_plan(context, available)
        if template_plan is not None:
            plan = template_plan
        elif self.generator is None:
            plan = self._deterministic_plan(context, available)
        else:
            plan = self._generate_with_repair(context)
        self.policy.validate_plan(plan, available)
        return plan

    def match_template(self, context: AgentContext):
        if self.template_registry is None:
            return None
        from lina.agent.templates.matcher import TaskTemplateMatcher

        available = {item.name for item in context.capabilities if item.available}
        return TaskTemplateMatcher(self.template_registry).match(
            context.user_request,
            available_capabilities=available,
            agent_mode_enabled=True,
        )

    def _template_plan(self, context: AgentContext, available: set[str]) -> AgentPlan | None:
        match = self.match_template(context)
        if match is None or match.template_id is None:
            if match is not None and match.ambiguous:
                raise AgentClarificationRequired(
                    "Bunu hatırlatıcı olarak mı oluşturayım, yoksa yalnızca plan mı hazırlayayım?"
                )
            return None
        if match.missing_parameters:
            raise AgentClarificationRequired(
                _clarification_for(match.missing_parameters), match.missing_parameters
            )
        template = self.template_registry.require(match.template_id)
        from lina.agent.templates.validators import validate_parameters

        parameters = dict(match.extracted_parameters)
        validate_parameters(dict(template.input_schema), parameters)
        return template.create_plan(parameters)

    def replan(self, context: AgentContext, failed_step: AgentStep, error_code: str) -> AgentPlan:
        if self.generator is None:
            raise AgentPlanError("Bu görev için güvenli bir yeniden plan oluşturamadım.")
        raw = self.generator(context, f"failed_step={failed_step.step_id}; error_code={error_code[:64]}")
        plan = self._parse(raw)
        self.policy.validate_plan(plan, {item.name for item in context.capabilities if item.available})
        return plan

    def _generate_with_repair(self, context: AgentContext) -> AgentPlan:
        raw = self.generator(context, None)
        try:
            return self._parse(raw)
        except (AgentPlanError, ValueError, TypeError):
            repaired = self.generator(context, "Önceki çıktı şemaya uymadı; yalnızca geçerli typed plan döndür.")
            try:
                return self._parse(repaired)
            except (AgentPlanError, ValueError, TypeError) as error:
                raise AgentPlanError("Bu görev için güvenli bir plan oluşturamadım.") from error

    def _deterministic_plan(self, context: AgentContext, available: set[str]) -> AgentPlan:
        text = context.user_request.casefold()
        prohibited = ("shell", "powershell", "cmd", "dosya sil", "tarayıcı", "browser", "e-posta gönder", "fare", "klavye")
        if any(term in text for term in prohibited):
            raise AgentPolicyError("Bu işlem Agent Mode yetkilerinin dışında.")
        candidates: list[tuple[str, str, dict]] = []
        if "hatırlat" in text or "hatirlat" in text:
            if any(term in text for term in ("liste", "göster", "kontrol")):
                candidates.append(("Hatırlatıcıları listele", "reminder.list", {}))
            else:
                arguments, missing = parse_reminder_arguments(context.user_request)
                if missing:
                    raise AgentPlanError("Hatırlatıcı ayrıntıları net olmadığı için güvenli plan oluşturamadım.")
                candidates.append(("Hatırlatıcı oluştur", "reminder.create", arguments))
        elif "hafıza" in text or "hafiza" in text or "hatırlıyor" in text:
            candidates.append(("Hafızada ara", "memory.recall", {"query": context.user_request[:240]}))
        elif "dosya" in text and "oku" in text:
            raise AgentPlanError("Okunacak izinli dosya açıkça belirtilmeli.")
        else:
            raise AgentPlanError("Bu görev için güvenli bir plan oluşturamadım.")
        steps = []
        for index, (title, tool, arguments) in enumerate(candidates, 1):
            if tool not in available:
                raise AgentPlanError("Gerekli araç şu anda kullanılamıyor.")
            risk = self.policy.risk_for(tool)
            steps.append(AgentStep(f"step-{index}", title, title, tool, arguments, risk, risk is RiskLevel.PERSISTENT))
        return AgentPlan(uuid4().hex, "İsteği güvenli ve doğrulanabilir adımlarla tamamla.", steps)

    @staticmethod
    def _parse(raw: object) -> AgentPlan:
        if isinstance(raw, AgentPlan):
            return raw
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError as error:
                raise AgentPlanError("Planner çıktısı geçerli JSON değil.") from error
        if not isinstance(raw, dict) or not isinstance(raw.get("steps"), list):
            raise AgentPlanError("Planner çıktısı geçerli plan şemasında değil.")
        steps = []
        for item in raw["steps"]:
            if not isinstance(item, dict):
                raise AgentPlanError("Planner adımı geçersiz.")
            steps.append(AgentStep(
                step_id=str(item.get("step_id", "")), title=str(item.get("title", "")),
                description=str(item.get("description", item.get("title", ""))),
                tool_name=str(item.get("tool_name", "")), typed_arguments=item.get("typed_arguments", {}),
                risk_level=RiskLevel(item.get("risk_level", "read_only")),
                approval_required=bool(item.get("approval_required", False)),
                dependencies=tuple(item.get("dependencies", ())),
                verification_rule=VerificationRule.from_value(item.get("verification_rule", "typed_success")),
            ))
        return AgentPlan(
            str(raw.get("plan_id") or uuid4().hex), str(raw.get("summary", "")).strip(), steps,
            raw.get("estimated_step_count"), bool(raw.get("requires_approval", True)),
            revision=int(raw.get("revision", 1)),
            template_id=str(raw["template_id"]) if raw.get("template_id") else None,
            title=str(raw["title"]) if raw.get("title") else None,
            risk_summary=str(raw.get("risk_summary", "")),
        )


def _clarification_for(missing: tuple[str, ...]) -> str:
    missing_set = set(missing)
    if "future_time" in missing_set:
        return "Geçmiş bir saat seçemeyiz. Hangi gelecek tarih ve saati kullanayım?"
    if missing_set == {"time"}:
        return "Saat kaçta hatırlatayım?"
    if missing_set == {"date"}:
        return "Hangi gün hatırlatayım?"
    if missing_set == {"title"}:
        return "Neyi hatırlatmamı istersin?"
    if missing_set == {"content"}:
        return "Hangi bilgiyi hafızaya kaydetmemi istersin?"
    if missing_set == {"target"}:
        return "Hangi izinli dosyayı okumamı istersin?"
    return "Görevi başlatmak için bazı bilgiler eksik."
