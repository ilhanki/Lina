"""Short Turkish rendering helpers for template preflight."""

from lina.agent.models import AgentPlan, RiskLevel
from lina.agent.templates.models import TaskTemplate, TaskTemplateMatch, TaskTemplatePreflight


_PARAMETER_LABELS = {
    "title": "başlık",
    "date": "tarih",
    "time": "saat",
    "due_at": "tarih ve saat",
    "content": "kaydedilecek bilgi",
    "target": "dosya",
}


def build_preflight(template: TaskTemplate, match: TaskTemplateMatch, plan: AgentPlan | None = None) -> TaskTemplatePreflight:
    return TaskTemplatePreflight(
        template.template_id,
        template.title,
        plan.summary if plan is not None else template.description,
        tuple(_PARAMETER_LABELS.get(name, name) for name in match.missing_parameters),
        bool(plan and any(step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE} for step in plan.steps)) or "Kalıcı" in template.risk_summary,
        len(plan.steps) if plan is not None else 0,
        template.risk_summary,
    )


def render_preflight(preflight: TaskTemplatePreflight) -> str:
    persistent = "Var; çalıştırmadan önce ayrı onay istenecek." if preflight.has_persistent_action else "Yok."
    missing = ", ".join(preflight.required_information) if preflight.required_information else "Eksik bilgi yok."
    return (
        f"{preflight.title} görevi hazır.\n"
        f"Plan: {preflight.plan_summary}\n"
        f"Gerekli bilgiler: {missing}\n"
        f"Kalıcı işlem: {persistent}\n"
        f"Adım sayısı: {preflight.estimated_step_count}"
    )
