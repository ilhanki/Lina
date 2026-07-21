from pathlib import Path
from datetime import datetime, timezone

from lina.codex.changes import CodexChangeSet, CodexFileChange
from lina.codex.models import (CodexHistoryEntry, CodexSession, CodexSessionStatus,
                                ProjectContext)
from lina.codex.transports.diagnostics import CodexCliInfo
from lina.interfaces.qt.codex_panel import CodexInspector


def test_panel_shows_cli_missing(qtbot) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    panel.render(None, info=CodexCliInfo())
    assert "Codex komut aracı · Bulunamadı" in panel.cli_status_label.text()
    assert not panel.login_button.isVisible()


def test_panel_shows_login_required_and_supported_device_auth(qtbot, tmp_path: Path) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    panel.render(None, info=CodexCliInfo(
        tmp_path / "codex.exe", "1.2.3", True, False, supports_exec=True,
        supports_json=True, supports_device_auth=True,
    ))
    panel.show()
    assert "Oturum gerekli" in panel.cli_status_label.text()
    assert panel.login_button.isVisible()
    assert panel.device_login_button.isVisible()


def test_panel_shows_ready_and_general_auth_method_only(qtbot, tmp_path: Path) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    panel.render(None, info=CodexCliInfo(
        tmp_path / "codex.exe", "1.2.3", True, True, "ChatGPT",
        supports_exec=True, supports_json=True,
    ))
    panel.show()
    assert "Hazır" in panel.cli_status_label.text()
    assert "ChatGPT" in panel.auth_status_label.text()
    assert panel.logout_button.isVisible()


def test_panel_hides_raw_candidate_source_and_kind(qtbot, tmp_path: Path) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    panel.render(None, info=CodexCliInfo(
        tmp_path / "codex.cmd", "0.144.6", True, False,
        selected_candidate_source="path:codex.cmd", executable_kind="cmd_wrapper",
    ))
    assert "codex.cmd" in panel.candidate_label.text()
    assert "Komut dosyası" in panel.candidate_label.text()
    assert "cmd_wrapper" not in panel.candidate_label.text()
    assert "path:codex.cmd" not in panel.candidate_label.text()


def test_panel_shows_review_pending_summary(qtbot, tmp_path: Path) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    session = CodexSession.create(ProjectContext(tmp_path), "Change task")
    session.transition(CodexSessionStatus.COMPLETED)
    session.review_pending = True
    change = CodexFileChange("app.py", "modified", 2, 1, False, False, False, 1, 2, True)
    panel.render(session, change_set=CodexChangeSet((change,), 2, 1))
    panel.show()
    assert panel.review_card.isVisible()
    assert "1 dosyada" in panel.review_summary_label.text()
    assert "İnceleme bekliyor" in panel.review_summary_label.text()


def test_panel_shows_recovery_actions_without_auto_resume(qtbot) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    entry = CodexHistoryEntry(
        "session", "Interrupted", datetime.now(timezone.utc),
        CodexSessionStatus.INTERRUPTED, "", resumable=True,
        workspace_display_name="Lina",
    )
    panel.render(None, recovery=(entry,))
    panel.show()
    assert panel.recovery_card.isVisible()
    assert not panel.recovery_resume_button.isEnabled()
    assert "tamamlanmadan" in panel.recovery_label.text()
