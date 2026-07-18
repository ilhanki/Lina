from pathlib import Path

import pytest

from lina.codex.models import (CodexExecutionMode, CodexEvent, CodexEventType,
                                CodexRiskLevel, CodexSession, CodexSessionStatus,
                                CodexTask, ProjectContext, RequestedAction,
                                WorkspacePermissionLevel)


def test_session_defaults_and_transitions(tmp_path: Path):
    session = CodexSession.create(ProjectContext(tmp_path), "Analiz")
    assert session.status is CodexSessionStatus.CREATED
    assert session.permission_level is WorkspacePermissionLevel.ONE_TIME
    assert session.execution_mode is CodexExecutionMode.READ_ONLY
    session.transition(CodexSessionStatus.RUNNING, 150)
    assert (session.status, session.progress) == (CodexSessionStatus.RUNNING, 100)


def test_modification_task_always_requires_approval(tmp_path: Path):
    task = CodexTask.create("Başlık", "Açıklama", "Amaç", tmp_path,
                            (RequestedAction("edit"),),
                            risk_level=CodexRiskLevel.MODIFICATION,
                            approval_required=False)
    assert task.approval_required is True


def test_invalid_task_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        CodexTask.create("", "", "", tmp_path, ())


def test_event_is_typed_and_bounded():
    event = CodexEvent.create("s", CodexEventType.ANALYZING, "x" * 300)
    assert event.event_type is CodexEventType.ANALYZING
    assert len(event.message) == 240

