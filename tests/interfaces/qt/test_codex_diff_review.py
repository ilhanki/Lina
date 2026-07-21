from PySide6.QtCore import Qt

from lina.codex.changes import CodexChangeSet, CodexFileChange, CodexReviewStatus
from lina.interfaces.qt.codex_diff_review import CodexDiffReviewDialog


def file_change(**changes) -> CodexFileChange:
    values = dict(
        relative_path="src/app.py", change_type="modified", additions=2, deletions=1,
        binary=False, generated=False, forbidden=False, size_before=10, size_after=14,
        diff_available=True, unified_diff="--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1,2 @@\n-old\n+new\n+line\n",
    )
    values.update(changes)
    return CodexFileChange(**values)


def test_diff_dialog_renders_summary_and_file_list(qtbot) -> None:
    dialog = CodexDiffReviewDialog(CodexChangeSet((file_change(),), 2, 1), task_title="Fix")
    qtbot.addWidget(dialog)
    assert "1 dosya" in dialog.summary_label.text()
    assert dialog.file_list.count() == 1
    assert "src/app.py" in dialog.file_list.item(0).text()
    assert "+new" in dialog.diff_view.toPlainText()
    assert dialog.search.placeholderText() == "Değişikliklerde ara"
    assert "Çalışma alanı" in dialog.summary_label.text()


def test_binary_change_shows_metadata_only(qtbot) -> None:
    change = file_change(relative_path="asset.bin", binary=True, diff_available=False,
                         unified_diff="", size_before=12, size_after=20)
    dialog = CodexDiffReviewDialog(CodexChangeSet((change,), 0, 0))
    qtbot.addWidget(dialog)
    assert "Binary dosya" in dialog.diff_view.toPlainText()
    assert "12 bayt" in dialog.diff_view.toPlainText()


def test_forbidden_change_hides_diff_and_disables_decisions(qtbot) -> None:
    change = file_change(relative_path=".env", forbidden=True, diff_available=False,
                         unified_diff="SECRET=never", review_status=CodexReviewStatus.BLOCKED)
    dialog = CodexDiffReviewDialog(CodexChangeSet((change,), 0, 0))
    qtbot.addWidget(dialog)
    assert "Hassas dosya" in dialog.diff_view.toPlainText()
    assert "SECRET=never" not in dialog.diff_view.toPlainText()
    assert not dialog.accept_file_button.isEnabled()
    assert not dialog.reject_file_button.isEnabled()


def test_truncated_diff_is_labeled(qtbot) -> None:
    dialog = CodexDiffReviewDialog(CodexChangeSet((file_change(truncated=True),), 2, 1,
                                                  truncated=True))
    qtbot.addWidget(dialog)
    assert "kısaltıldı" in dialog.diff_view.toPlainText()


def test_accept_and_reject_emit_typed_decisions(qtbot) -> None:
    dialog = CodexDiffReviewDialog(CodexChangeSet((file_change(),), 2, 1))
    qtbot.addWidget(dialog)
    decisions = []
    dialog.decision_requested.connect(decisions.append)
    qtbot.mouseClick(dialog.accept_file_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(dialog.reject_file_button, Qt.MouseButton.LeftButton)
    assert [item.action for item in decisions] == ["accept", "reject"]
    assert all(item.relative_path == "src/app.py" for item in decisions)


def test_accept_all_skips_forbidden_files(qtbot) -> None:
    blocked = file_change(relative_path=".env", forbidden=True,
                          review_status=CodexReviewStatus.BLOCKED)
    dialog = CodexDiffReviewDialog(CodexChangeSet((file_change(), blocked), 2, 1))
    qtbot.addWidget(dialog)
    decisions = []
    dialog.decision_requested.connect(decisions.append)
    qtbot.mouseClick(dialog.accept_all_button, Qt.MouseButton.LeftButton)
    assert [item.relative_path for item in decisions] == ["src/app.py"]


def test_wrap_toggle_changes_diff_view_mode(qtbot) -> None:
    dialog = CodexDiffReviewDialog(CodexChangeSet((file_change(),), 2, 1))
    qtbot.addWidget(dialog)
    dialog.wrap_toggle.setChecked(True)
    assert dialog.diff_view.lineWrapMode().name == "WidgetWidth"


def test_dialog_switches_to_vertical_splitter_when_narrow(qtbot) -> None:
    dialog = CodexDiffReviewDialog(CodexChangeSet((file_change(),), 2, 1))
    qtbot.addWidget(dialog)
    dialog.resize(700, 600)
    dialog.show()
    qtbot.wait(20)
    assert dialog.splitter.orientation() is Qt.Orientation.Vertical
    dialog.resize(1000, 600)
    qtbot.wait(20)
    assert dialog.splitter.orientation() is Qt.Orientation.Horizontal


def test_empty_change_set_explains_zero_diff(qtbot) -> None:
    dialog = CodexDiffReviewDialog(CodexChangeSet((), 0, 0))
    qtbot.addWidget(dialog)
    assert "Herhangi bir dosya değiştirilmedi" in dialog.diff_view.toPlainText()
