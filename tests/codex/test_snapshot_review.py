from dataclasses import replace
from pathlib import Path
import subprocess

import pytest

from lina.codex.changes import (
    CodexChangeSet,
    CodexFileChange,
    CodexReviewDecision,
    CodexReviewSession,
    CodexReviewStatus,
)
from lina.codex.snapshot import (
    CodexGitSnapshot,
    CodexWorkspaceSnapshot,
    build_change_set,
    capture_workspace_snapshot,
    parse_unified_hunks,
    unexpected_git_actions,
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=root, shell=False, check=True,
                            capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip()


def init_git(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Fixture")
    write(root / "app.py", "print('one')\n")
    git(root, "add", "app.py")
    git(root, "commit", "-qm", "initial")


def test_non_git_snapshot_captures_bounded_text_metadata(tmp_path: Path) -> None:
    write(tmp_path / "app.py", "print('ok')\n")
    snapshot = capture_workspace_snapshot(tmp_path)
    assert snapshot.git is None
    assert snapshot.scanned_files == 1
    assert snapshot.files[0].digest
    assert snapshot.files[0].text and snapshot.files[0].text.splitlines() == ["print('ok')"]


def test_snapshot_excludes_dependency_and_cache_directories(tmp_path: Path) -> None:
    write(tmp_path / "node_modules" / "pkg.js", "ignored")
    write(tmp_path / ".venv" / "lib.py", "ignored")
    write(tmp_path / "src" / "app.py", "kept")
    paths = {item.relative_path for item in capture_workspace_snapshot(tmp_path).files}
    assert paths == {"src/app.py"}


def test_snapshot_file_count_is_bounded(tmp_path: Path) -> None:
    for index in range(8):
        write(tmp_path / f"file{index}.txt", str(index))
    snapshot = capture_workspace_snapshot(tmp_path, max_files=3)
    assert snapshot.truncated
    assert snapshot.scanned_files == 3


def test_snapshot_total_bytes_are_bounded(tmp_path: Path) -> None:
    write(tmp_path / "large.txt", "x" * 100)
    snapshot = capture_workspace_snapshot(tmp_path, max_total_bytes=10)
    assert snapshot.truncated
    assert snapshot.scanned_bytes == 0


def test_binary_change_exposes_metadata_not_diff(tmp_path: Path) -> None:
    path = tmp_path / "asset.bin"
    path.write_bytes(b"\x00one")
    before = capture_workspace_snapshot(tmp_path)
    path.write_bytes(b"\x00two")
    change = build_change_set(before, capture_workspace_snapshot(tmp_path)).files[0]
    assert change.binary and not change.diff_available and change.unified_diff == ""


def test_secret_change_is_blocked_without_content(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    write(path, "TOKEN=one")
    before = capture_workspace_snapshot(tmp_path)
    write(path, "TOKEN=changed-longer")
    change_set = build_change_set(before, capture_workspace_snapshot(tmp_path))
    assert change_set.blocked
    assert change_set.files[0].forbidden
    assert not change_set.files[0].diff_available
    assert "changed-longer" not in repr(change_set)


def test_unchanged_secret_is_only_baseline_metadata(tmp_path: Path) -> None:
    write(tmp_path / "auth.json", "private")
    before = capture_workspace_snapshot(tmp_path)
    after = capture_workspace_snapshot(tmp_path)
    assert build_change_set(before, after).files == ()


def test_text_modification_builds_unified_hunk_and_counts(tmp_path: Path) -> None:
    path = tmp_path / "app.py"
    write(path, "one\ntwo\n")
    before = capture_workspace_snapshot(tmp_path)
    write(path, "one\nchanged\nthree\n")
    change = build_change_set(before, capture_workspace_snapshot(tmp_path)).files[0]
    assert change.change_type == "modified"
    assert (change.additions, change.deletions) == (2, 1)
    assert change.hunks and change.diff_available


def test_added_and_deleted_files_are_classified(tmp_path: Path) -> None:
    old = tmp_path / "old.txt"
    write(old, "old\n")
    before = capture_workspace_snapshot(tmp_path)
    old.unlink()
    write(tmp_path / "new.txt", "new\n")
    changes = build_change_set(before, capture_workspace_snapshot(tmp_path)).files
    assert {item.change_type for item in changes} == {"added", "deleted"}


def test_equal_content_move_is_classified_as_rename(tmp_path: Path) -> None:
    old = tmp_path / "old.txt"
    write(old, "same\n")
    before = capture_workspace_snapshot(tmp_path)
    old.rename(tmp_path / "new.txt")
    changes = build_change_set(before, capture_workspace_snapshot(tmp_path)).files
    assert len(changes) == 1 and changes[0].change_type == "renamed"


def test_generated_suffix_is_marked(tmp_path: Path) -> None:
    before = capture_workspace_snapshot(tmp_path)
    write(tmp_path / "bundle.min.js", "minified")
    assert build_change_set(before, capture_workspace_snapshot(tmp_path)).files[0].generated


def test_large_diff_is_truncated(tmp_path: Path) -> None:
    path = tmp_path / "large.txt"
    write(path, "a\n" * 100)
    before = capture_workspace_snapshot(tmp_path)
    write(path, "b\n" * 100)
    change_set = build_change_set(before, capture_workspace_snapshot(tmp_path), max_diff_bytes=80)
    assert change_set.truncated and change_set.files[0].truncated
    assert len(change_set.files[0].unified_diff.encode()) <= 80


def test_unified_parser_supports_multiple_hunks() -> None:
    diff = "@@ -1,1 +1,1 @@ first\n-old\n+new\n@@ -10 +10 @@ second\n-a\n+b\n"
    hunks = parse_unified_hunks(diff)
    assert len(hunks) == 2
    assert (hunks[0].old_start, hunks[1].new_start) == (1, 10)


def test_git_snapshot_captures_head_branch_and_status(tmp_path: Path) -> None:
    init_git(tmp_path)
    snapshot = capture_workspace_snapshot(tmp_path)
    assert snapshot.git and snapshot.git.head == git(tmp_path, "rev-parse", "HEAD")
    assert snapshot.git.branch
    assert "branch.head" in snapshot.git.status_porcelain_v2


def test_git_snapshot_detects_staged_path(tmp_path: Path) -> None:
    init_git(tmp_path)
    write(tmp_path / "app.py", "print('two')\n")
    git(tmp_path, "add", "app.py")
    snapshot = capture_workspace_snapshot(tmp_path)
    assert snapshot.git and snapshot.git.staged_paths == ("app.py",)


@pytest.mark.parametrize(
    ("field", "new_value", "reason"),
    (("head", "new-head", "head_changed"),
     ("branch", "other", "branch_changed"),
     ("tag_fingerprint", "new-tags", "tags_changed"),
     ("remote_fingerprint", "new-remotes", "remotes_changed"),
     ("upstream", "refs/remotes/origin/other", "upstream_changed"),
     ("upstream_head", "remote-new", "remote_head_changed"),
     ("staged_paths", ("app.py",), "staged_state_changed"),
     ("merge_in_progress", True, "merge_started"),
     ("rebase_in_progress", True, "rebase_started")),
)
def test_unexpected_git_actions_are_structured(tmp_path: Path, field: str,
                                               new_value, reason: str) -> None:
    git_state = CodexGitSnapshot(
        head="head", branch="main", tag_fingerprint="tags", remote_fingerprint="remotes",
        upstream="refs/remotes/origin/main", upstream_head="remote-head",
    )
    before = CodexWorkspaceSnapshot(tmp_path, (), git_state, ())
    after = replace(before, git=replace(git_state, **{field: new_value}))
    assert reason in unexpected_git_actions(before, after)


def sample_change_set(tmp_path: Path) -> CodexChangeSet:
    path = tmp_path / "app.py"
    write(path, "one\n")
    before = capture_workspace_snapshot(tmp_path)
    write(path, "two\n")
    return build_change_set(before, capture_workspace_snapshot(tmp_path))


def test_review_accept_is_metadata_only(tmp_path: Path) -> None:
    change_set = sample_change_set(tmp_path)
    content = (tmp_path / "app.py").read_text(encoding="utf-8")
    session = CodexReviewSession(change_set)
    session.decide(CodexReviewDecision("accept", "app.py"))
    assert session.summary().accepted == 1
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == content


def test_review_reject_never_restores_or_deletes_file(tmp_path: Path) -> None:
    change_set = sample_change_set(tmp_path)
    content = (tmp_path / "app.py").read_text(encoding="utf-8")
    session = CodexReviewSession(change_set)
    session.decide(CodexReviewDecision("reject", "app.py", note="Revise safely"))
    assert session.summary().rejected == 1
    assert (tmp_path / "app.py").exists()
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == content


def test_hunk_accept_is_partial_review(tmp_path: Path) -> None:
    session = CodexReviewSession(sample_change_set(tmp_path))
    updated = session.decide(CodexReviewDecision("accept", "app.py", hunk_index=0))
    assert updated.files[0].review_status is CodexReviewStatus.PARTIALLY_ACCEPTED


def test_blocked_file_cannot_be_accepted() -> None:
    blocked = CodexFileChange(
        ".env", "modified", 0, 0, False, False, True, 1, 2, False,
        review_status=CodexReviewStatus.BLOCKED,
    )
    session = CodexReviewSession(CodexChangeSet((blocked,), 0, 0))
    session.decide(CodexReviewDecision("accept", ".env"))
    assert session.summary().blocked == 1


@pytest.mark.parametrize("action", ("inspect", "request_explanation", "send_back"))
def test_review_supports_non_destructive_followup_actions(tmp_path: Path, action: str) -> None:
    session = CodexReviewSession(sample_change_set(tmp_path))
    session.decide(CodexReviewDecision(action, "app.py"))
    assert session.summary().decisions[-1].action == action


def test_review_decision_rejects_unbounded_note() -> None:
    with pytest.raises(ValueError):
        CodexReviewDecision("reject", "app.py", note="x" * 501)
