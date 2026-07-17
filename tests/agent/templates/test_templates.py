from datetime import datetime, timezone

import pytest

from lina.agent import AgentContext, AgentPlanner, AgentPolicy, RiskLevel
from lina.agent.errors import AgentClarificationRequired
from lina.agent.models import CapabilitySnapshot
from lina.agent.templates import (
    TaskTemplate,
    TaskTemplateCategory,
    TaskTemplateMatcher,
    TaskTemplateRegistry,
    build_builtin_template_registry,
)


def _factory(_values):
    from lina.agent import AgentPlan, AgentStep

    return AgentPlan("p", "Özet", [AgentStep("s", "Oku", "Oku", "reminder.list", {})])


def _template(template_id="custom.safe", **overrides):
    values = {
        "template_id": template_id,
        "title": "Güvenli görev",
        "description": "Salt okunur görev.",
        "category": TaskTemplateCategory.CUSTOM,
        "example_phrases": ("Görevi çalıştır.",),
        "required_capabilities": frozenset({"reminder.list"}),
        "optional_capabilities": frozenset(),
        "input_schema": {"query": str},
        "plan_factory": _factory,
    }
    values.update(overrides)
    return TaskTemplate(**values)


def _capability(name, risk=RiskLevel.READ_ONLY, available=True):
    return CapabilitySnapshot(name, "test", (), "ToolResult", risk, risk is RiskLevel.PERSISTENT, available, risk is RiskLevel.READ_ONLY)


def test_template_validates_id_schema_and_serializes_public_metadata():
    template = _template()
    serialized = template.to_dict()
    assert serialized["template_id"] == "custom.safe"
    assert serialized["input_schema"] == {"query": "str"}
    assert "plan_factory" not in serialized
    assert TaskTemplate.from_dict(serialized, _factory).version == 1
    with pytest.raises(ValueError):
        _template("INVALID ID")
    with pytest.raises(TypeError):
        _template(input_schema={"query": "str"})


def test_template_registry_duplicate_filtering_and_deterministic_order():
    registry = TaskTemplateRegistry()
    registry.register(_template("custom.second", title="Z görev"))
    registry.register(_template("custom.first", title="A görev"))
    with pytest.raises(ValueError):
        registry.register(_template("custom.first"))
    assert [item.template_id for item in registry.list()] == ["custom.first", "custom.second"]
    assert registry.list(available_capabilities=set()) == ()
    assert len(registry.list(available_capabilities={"reminder.list"})) == 2


def test_builtin_registry_only_lists_templates_supported_by_real_capabilities():
    registry = build_builtin_template_registry()
    ids = {item.template_id for item in registry.list(available_capabilities={"reminder.summary", "reminder.conflicts"})}
    assert ids == {"reminders.summary", "reminders.conflicts"}
    assert "system.status" not in registry.ids()
    assert "conversation.search" not in registry.ids()


@pytest.mark.parametrize(("text", "template_id"), [
    ("Yarın saat 10'da toplantıyı hatırlat.", "reminders.create"),
    ("Bu haftaki hatırlatıcılarımı özetle.", "reminders.summary"),
    ("Yarınki hatırlatıcılarım çakışıyor mu?", "reminders.conflicts"),
    ("Bundan sonra cevaplarını daha kısa tutmamı hatırla.", "memory.store"),
    ("Benim hakkımda neleri hatırlıyorsun?", "memory.recall"),
    ('"README.md" dosyasını oku ve özetle.', "files.summarize"),
    ("Bu ekran görüntüsünde önemli olan şeyi söyle.", "vision.single_frame"),
])
def test_matcher_recognizes_supported_safe_templates(text, template_id):
    registry = build_builtin_template_registry()
    available = {cap for item in registry.list(enabled_only=False) for cap in item.required_capabilities}
    match = TaskTemplateMatcher(registry).match(text, available_capabilities=available)
    assert match.template_id == template_id
    assert not match.ambiguous


@pytest.mark.parametrize("text", [
    "Hatırlatıcı nedir?",
    "Memory nasıl çalışıyor?",
    "Görev şablonu nedir?",
    "Agent neden hata yapar?",
    "Bugün nasılsın?",
])
def test_matcher_keeps_explanations_and_normal_chat_outside_agent_templates(text):
    registry = build_builtin_template_registry()
    available = {cap for item in registry.list(enabled_only=False) for cap in item.required_capabilities}
    assert TaskTemplateMatcher(registry).match(text, available_capabilities=available).template_id is None


def test_matcher_reports_missing_input_and_respects_agent_mode_and_availability():
    registry = build_builtin_template_registry()
    matcher = TaskTemplateMatcher(registry)
    match = matcher.match("Yarın sporu hatırlat.", available_capabilities={"reminder.create"})
    assert match.template_id == "reminders.create"
    assert match.missing_parameters == ("time",)
    assert matcher.match("Yarın saat 10'da sporu hatırlat.", available_capabilities=set()).reason_code == "no_match"
    assert matcher.match("Yarın saat 10'da sporu hatırlat.", available_capabilities={"reminder.create"}, agent_mode_enabled=False).reason_code == "agent_mode_disabled"


def test_explicit_template_selection_has_priority_and_is_capability_filtered():
    matcher = TaskTemplateMatcher(build_builtin_template_registry())
    selected = matcher.match(
        "Yarın saat 09:00'da koşuyu hatırlat.",
        available_capabilities={"reminder.create"},
        explicit_template_id="reminders.create",
    )
    assert selected.confidence == 1.0
    assert selected.reason_code == "explicit_selection"
    unavailable = matcher.match("x", available_capabilities=set(), explicit_template_id="reminders.create")
    assert unavailable.reason_code == "template_unavailable"


def test_planner_uses_template_factory_and_asks_only_for_missing_time():
    registry = build_builtin_template_registry()
    planner = AgentPlanner(AgentPolicy(), template_registry=registry)
    capabilities = (_capability("reminder.create", RiskLevel.PERSISTENT),)
    context = AgentContext("Yarın saat 10'da sporu hatırlat.", capabilities=capabilities)
    plan = planner.plan(context)
    assert plan.template_id == "reminders.create"
    assert plan.steps[0].tool_name == "reminder.create"
    assert isinstance(plan.steps[0].typed_arguments["due_at"], datetime)
    assert plan.steps[0].approval_required
    with pytest.raises(AgentClarificationRequired, match="Saat kaçta") as error:
        planner.plan(AgentContext("Yarın sporu hatırlat.", capabilities=capabilities))
    assert error.value.missing_parameters == ("time",)


def test_reminder_read_only_templates_use_purpose_built_tools_and_typed_ranges():
    registry = build_builtin_template_registry()
    summary = registry.require("reminders.summary").create_plan({"range": "week"})
    conflicts = registry.require("reminders.conflicts").create_plan({"range": "tomorrow"})
    assert (summary.steps[0].tool_name, summary.steps[0].typed_arguments) == (
        "reminder.summary", {"range": "week"},
    )
    assert (conflicts.steps[0].tool_name, conflicts.steps[0].typed_arguments) == (
        "reminder.conflicts", {"range": "tomorrow"},
    )


def test_reminder_template_rejects_past_time():
    registry = build_builtin_template_registry()
    matcher = TaskTemplateMatcher(registry)
    match = matcher.match("Bugün saat 00:01'de testi hatırlat.", available_capabilities={"reminder.create"})
    assert "future_time" in match.missing_parameters


def test_template_plan_factory_never_executes_a_tool():
    registry = build_builtin_template_registry()
    template = registry.require("memory.store")
    plan = template.create_plan({"content": "Yanıtları kısa tut", "category": "conversation_note"})
    assert plan.steps[0].status.value == "pending"
    assert plan.steps[0].risk_level is RiskLevel.PERSISTENT
