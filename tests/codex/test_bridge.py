from pathlib import Path

import pytest

from lina.codex.bridge import CodexBridge
from lina.codex.client import CodexClientUnavailableError, UnavailableCodexClient
from lina.codex.events import spoken_message, user_message
from lina.codex.models import (CodexEvent, CodexEventType, CodexResult,
                                CodexSessionStatus)
from lina.codex.repository import CodexHistoryRepository
from lina.codex.session import CodexSessionController


class FakeClient:
    def __init__(self, result: CodexResult | None = None, failure: Exception | None = None):
        self.result = result or CodexResult("3 ana iyileştirme bulundu.")
        self.failure = failure
        self.calls = 0

    def execute(self, task, context, on_event):
        self.calls += 1
        if self.failure:
            raise self.failure
        on_event(CodexEvent.create("ignored", CodexEventType.ANALYZING, progress=50))
        return self.result


def prepared_bridge(tmp_path: Path, client=None):
    bridge = CodexBridge(client or FakeClient())
    context = bridge.select_workspace(tmp_path)
    session = bridge.prepare("Bu projeyi analiz et", context)
    return bridge, session


def test_plan_is_shown_before_client_runs(tmp_path: Path):
    client = FakeClient()
    bridge, session = prepared_bridge(tmp_path, client)
    assert bridge.start(session.session_id) is None
    assert session.status is CodexSessionStatus.WAITING_APPROVAL
    assert client.calls == 0


def test_accepted_task_runs_and_is_verified(tmp_path: Path):
    bridge, session = prepared_bridge(tmp_path)
    bridge.start(session.session_id, approved=True)
    assert session.status is CodexSessionStatus.COMPLETED
    assert session.progress == 100


def test_denied_task_is_cancelled(tmp_path: Path):
    bridge, session = prepared_bridge(tmp_path)
    bridge.deny(session.session_id)
    assert session.status is CodexSessionStatus.CANCELLED


def test_client_failure_marks_session_failed(tmp_path: Path):
    bridge, session = prepared_bridge(tmp_path, FakeClient(failure=RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        bridge.start(session.session_id, approved=True)
    assert session.status is CodexSessionStatus.FAILED


def test_uncertain_modification_is_not_reported_completed(tmp_path: Path):
    bridge = CodexBridge(FakeClient(CodexResult("Uyguladım")))
    context = bridge.select_workspace(tmp_path)
    session = bridge.prepare("main.py dosyasını değiştir", context)
    bridge.start(session.session_id, approved=True)
    assert session.status is CodexSessionStatus.FAILED
    assert session.error_code == "verification_uncertain"


def test_unavailable_client_reports_controlled_failure_and_forgets_plan(tmp_path: Path):
    bridge = CodexBridge(UnavailableCodexClient())
    context = bridge.select_workspace(tmp_path)
    session = bridge.prepare("Codex ile bu projeyi analiz et", context)
    with pytest.raises(CodexClientUnavailableError):
        bridge.start(session.session_id, approved=True)
    assert session.status is CodexSessionStatus.FAILED
    assert "henüz yapılandırılmadığı" in session.result_summary
    assert bridge.repository.list() == ()


def test_pause_resume_cancel_lifecycle(tmp_path: Path):
    _, session = prepared_bridge(tmp_path)
    controller = CodexSessionController()
    session.transition(CodexSessionStatus.RUNNING)
    controller.pause(session)
    assert session.status is CodexSessionStatus.PAUSED
    controller.resume(session)
    controller.cancel(session)
    assert session.status is CodexSessionStatus.CANCELLED


def test_event_messages_do_not_expose_raw_payload():
    event = CodexEvent.create("s", CodexEventType.APPROVAL_REQUESTED, "technical spam")
    assert user_message(event) == "Planı başlatmak için onayını bekliyorum."
    assert spoken_message(event) == "Onayını bekliyorum."


def test_history_is_metadata_only(tmp_path: Path):
    path = tmp_path / "history.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repository = CodexHistoryRepository(path)
    real_bridge = CodexBridge(FakeClient(), repository=repository)
    context = real_bridge.select_workspace(workspace)
    real_session = real_bridge.prepare("secret prompt body", context)
    real_bridge.start(real_session.session_id, approved=True)
    payload = path.read_text(encoding="utf-8")
    assert "allowed_files" not in payload and "file_content" not in payload
    assert repository.list()[0].status is CodexSessionStatus.COMPLETED


def test_shutdown_marks_active_session_interrupted(tmp_path: Path):
    bridge = CodexBridge(FakeClient())
    context = bridge.select_workspace(tmp_path)
    session = bridge.prepare("Codex ile projeyi analiz et", context)
    bridge.shutdown()
    assert session.status is CodexSessionStatus.INTERRUPTED
    assert session.error_code == "app_shutdown"
    assert bridge.repository.list()[0].exit_category == "app_shutdown"
