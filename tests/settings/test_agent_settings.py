import pytest

from lina.settings.models import AgentUserSettings, UserSettings


def test_agent_settings_safe_defaults_and_round_trip():
    settings = UserSettings()
    assert not settings.agent.agent_mode_enabled
    assert settings.agent.max_agent_steps == 8
    assert settings.agent.max_agent_replans == 1
    assert settings.agent.always_confirm_persistent_steps
    assert settings.agent.show_task_template_suggestions
    assert settings.agent.notify_interrupted_tasks_on_startup
    assert settings.agent.agent_history_retention_days == 30
    assert UserSettings.from_dict(settings.to_dict()) == settings


def test_agent_settings_migrate_from_schema_five():
    settings = UserSettings.from_dict({"schema_version": 5, "appearance": {"theme": "light"}})
    assert settings.appearance.theme == "light"
    assert settings.agent == AgentUserSettings()


def test_agent_limits_are_bounded_and_persistent_approval_cannot_be_disabled():
    settings = UserSettings.from_dict({"agent": {"max_agent_steps": 99, "max_agent_replans": 9, "always_confirm_persistent_steps": False}})
    assert settings.agent.max_agent_steps == 8
    assert settings.agent.max_agent_replans == 1
    assert settings.agent.always_confirm_persistent_steps
    with pytest.raises(ValueError):
        UserSettings(agent=AgentUserSettings(always_confirm_persistent_steps=False))


def test_agent_history_retention_and_template_recovery_settings_migrate_safely():
    settings = UserSettings.from_dict({"schema_version": 8, "agent": {
        "show_task_template_suggestions": False,
        "notify_interrupted_tasks_on_startup": False,
        "agent_history_retention_days": 90,
    }})
    assert not settings.agent.show_task_template_suggestions
    assert not settings.agent.notify_interrupted_tasks_on_startup
    assert settings.agent.agent_history_retention_days == 90
    assert UserSettings.from_dict({"agent": {"agent_history_retention_days": 14}}).agent.agent_history_retention_days == 30
    with pytest.raises(ValueError):
        UserSettings(agent=AgentUserSettings(agent_history_retention_days=14))
