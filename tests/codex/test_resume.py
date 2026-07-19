from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from lina.codex.models import (
    CodexExecutionMode,
    CodexRemoteSessionReference,
    CodexSession,
    CodexSessionStatus,
    ProjectContext,
)
from lina.codex.repository import CodexHistoryRepository
from lina.codex.resume import assess_resume, valid_cli_session_id, workspace_fingerprint


SESSION_ID = "123e4567-e89b-42d3-a456-426614174000"


def reference(tmp_path: Path, **changes) -> CodexRemoteSessionReference:
    now = datetime.now(timezone.utc)
    values = dict(
        provider="openai-codex-cli", cli_session_id=SESSION_ID,
        local_session_id="local-session", conversation_id=7,
        workspace_fingerprint=workspace_fingerprint(tmp_path),
        workspace_display_name=tmp_path.name, task_summary="Projeyi analiz et",
        mode=CodexExecutionMode.READ_ONLY, created_at=now,
        last_used_at=now, cli_version="0.144.6",
    )
    values.update(changes)
    return CodexRemoteSessionReference(**values)


@pytest.mark.parametrize(
    ("value", "expected"),
    ((SESSION_ID, True), ("safe-session_name.1", True), ("../escape", False),
     ("two words", False), ("x", False), ("name&command", False)),
)
def test_session_id_validation(value: str, expected: bool) -> None:
    assert valid_cli_session_id(value) is expected


def test_resume_is_allowed_only_after_all_checks_and_approval(tmp_path: Path) -> None:
    result = assess_resume(
        reference(tmp_path), tmp_path, cli_version="0.144.6", authenticated=True,
        capability_supported=True, user_approved=True,
    )
    assert result.allowed
    assert not result.reasons


@pytest.mark.parametrize(
    ("changes", "kwargs", "reason"),
    (({}, {"capability_supported": False}, "resume_unsupported"),
     ({"resumable": False}, {}, "session_not_resumable"),
     ({"cli_session_id": "bad/id"}, {}, "invalid_session_id"),
     ({}, {"authenticated": False}, "authentication_required"),
     ({}, {"cli_version": "0.145.0"}, "cli_version_incompatible"),
     ({}, {"user_approved": False}, "user_approval_required")),
)
def test_resume_blocks_each_required_gate(tmp_path: Path, changes: dict,
                                         kwargs: dict, reason: str) -> None:
    values = dict(cli_version="0.144.6", authenticated=True,
                  capability_supported=True, user_approved=True)
    values.update(kwargs)
    result = assess_resume(reference(tmp_path, **changes), tmp_path, **values)
    assert not result.allowed
    assert reason in result.reasons


def test_resume_blocks_changed_workspace(tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    result = assess_resume(
        reference(tmp_path), other, cli_version="0.144.6", authenticated=True,
        capability_supported=True, user_approved=True,
    )
    assert "workspace_mismatch" in result.reasons


def test_resume_blocks_stale_session(tmp_path: Path) -> None:
    old = datetime.now(timezone.utc) - timedelta(days=31)
    result = assess_resume(
        reference(tmp_path, last_used_at=old), tmp_path, cli_version="0.144.6",
        authenticated=True, capability_supported=True, user_approved=True,
    )
    assert "session_stale" in result.reasons


def test_history_persists_only_bounded_resume_metadata(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    session = CodexSession.create(ProjectContext(tmp_path), "Safe summary")
    session.remote_session = reference(tmp_path)
    session.transition(CodexSessionStatus.INTERRUPTED)
    CodexHistoryRepository(path).save(session)
    raw = path.read_text(encoding="utf-8")
    assert SESSION_ID in raw
    assert "raw_stdout" not in raw and "full_prompt" not in raw and "reasoning" not in raw
    loaded = CodexHistoryRepository(path).list()[0]
    assert loaded.resumable
    assert loaded.remote_session_id == SESSION_ID


def test_repository_recovers_orphan_running_records(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    repository = CodexHistoryRepository(path)
    session = CodexSession.create(ProjectContext(tmp_path), "Running task")
    session.transition(CodexSessionStatus.RUNNING)
    repository.save(session)
    recovered = CodexHistoryRepository(path)
    items = recovered.recover_incomplete()
    assert items[0].status is CodexSessionStatus.INTERRUPTED
    assert items[0].exit_category == "orphaned_process"


def test_recovery_items_include_unsurfaced_completed_and_pending_review(tmp_path: Path) -> None:
    repository = CodexHistoryRepository()
    completed = CodexSession.create(ProjectContext(tmp_path), "Completed")
    completed.transition(CodexSessionStatus.COMPLETED)
    repository.save(completed)
    reviewing = CodexSession.create(ProjectContext(tmp_path), "Review")
    reviewing.transition(CodexSessionStatus.COMPLETED)
    reviewing.review_pending = True
    repository.save(reviewing)
    assert {item.task_summary for item in repository.recovery_items()} == {"Completed", "Review"}


def test_mark_surfaced_removes_completed_item_from_recovery(tmp_path: Path) -> None:
    repository = CodexHistoryRepository()
    session = CodexSession.create(ProjectContext(tmp_path), "Completed")
    session.transition(CodexSessionStatus.COMPLETED)
    repository.save(session)
    repository.mark_surfaced(session.session_id)
    assert repository.recovery_items() == ()


def test_history_is_bounded_even_with_unlimited_day_retention(tmp_path: Path) -> None:
    repository = CodexHistoryRepository(max_entries=10)
    for index in range(15):
        session = CodexSession.create(ProjectContext(tmp_path), f"Task {index}")
        session.transition(CodexSessionStatus.COMPLETED)
        repository.save(session)
    repository.cleanup(None)
    assert len(repository.list()) == 10
