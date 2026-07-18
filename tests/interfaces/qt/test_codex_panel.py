from pathlib import Path

from lina.codex.models import (CodexSession, CodexSessionStatus, ProjectContext)
from lina.interfaces.qt.codex_panel import CodexInspector


def test_codex_inspector_shows_active_task_workspace_and_progress(qtbot, tmp_path: Path):
    panel = CodexInspector()
    qtbot.addWidget(panel)
    session = CodexSession.create(ProjectContext(tmp_path), "Projeyi analiz et")
    session.transition(CodexSessionStatus.RUNNING, 55)
    panel.render(session)
    assert "Projeyi analiz et" in panel.task_label.text()
    assert tmp_path.name in panel.workspace_label.text()
    assert panel.progress.value() == 55
    assert not panel.approval_card.isVisible()


def test_codex_approval_card_has_approve_deny_and_edit(qtbot, tmp_path: Path):
    panel = CodexInspector()
    qtbot.addWidget(panel)
    session = CodexSession.create(ProjectContext(tmp_path), "Dosyayı düzenle")
    session.transition(CodexSessionStatus.WAITING_APPROVAL, 20)
    panel.render(session)
    panel.show()
    assert panel.approval_card.isVisible()
    assert panel.approve_button.text() == "Onayla"
    assert panel.deny_button.text() == "Reddet"
    assert panel.edit_button.text() == "Düzenle"


def test_codex_workspace_card_has_select_and_cancel(qtbot):
    panel = CodexInspector()
    qtbot.addWidget(panel)
    panel.render_workspace_required("Codex ile bu projeyi analiz et")
    panel.show()
    assert panel.workspace_card.isVisible()
    assert panel.workspace_select_button.text() == "Klasör Seç"
    assert panel.workspace_cancel_button.text() == "İptal"
