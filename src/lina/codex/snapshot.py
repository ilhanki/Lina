"""Bounded Git and non-Git snapshots plus safe ephemeral diff generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import difflib
import hashlib
import os
from pathlib import Path
import re
import subprocess

from lina.codex.changes import (CodexChangeSet, CodexDiffHunk, CodexFileChange,
                                CodexReviewStatus)
from lina.codex.permissions import is_secret_path


EXCLUDED_DIRECTORIES = frozenset({
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "build", "dist",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache", "cache",
})
GENERATED_SUFFIXES = frozenset({".min.js", ".min.css", ".map", ".lock"})


@dataclass(frozen=True, slots=True)
class CodexFileFingerprint:
    relative_path: str
    size: int
    mtime_ns: int
    digest: str | None
    mode: int = 0
    binary: bool = False
    forbidden: bool = False
    text: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class CodexGitSnapshot:
    head: str | None = None
    branch: str | None = None
    status_porcelain_v2: str = ""
    tag_fingerprint: str = ""
    remote_fingerprint: str = ""
    upstream: str | None = None
    upstream_head: str | None = None
    staged_paths: tuple[str, ...] = ()
    merge_in_progress: bool = False
    rebase_in_progress: bool = False


@dataclass(frozen=True, slots=True)
class CodexWorkspaceSnapshot:
    root: Path
    files: tuple[CodexFileFingerprint, ...]
    git: CodexGitSnapshot | None
    forbidden_paths: tuple[str, ...]
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    truncated: bool = False
    scanned_files: int = 0
    scanned_bytes: int = 0

    @property
    def fingerprint_pairs(self) -> tuple[tuple[str, str], ...]:
        return tuple((item.relative_path, item.digest or f"meta:{item.size}:{item.mtime_ns}")
                     for item in self.files if not item.forbidden)


def capture_workspace_snapshot(
    root: Path,
    *,
    max_files: int = 5000,
    max_total_bytes: int = 50 * 1024 * 1024,
    max_hash_bytes: int = 5 * 1024 * 1024,
    max_diff_file_bytes: int = 512 * 1024,
) -> CodexWorkspaceSnapshot:
    resolved = root.expanduser().resolve()
    fingerprints: list[CodexFileFingerprint] = []
    forbidden: list[str] = []
    scanned_bytes = 0
    truncated = False
    for path in _bounded_files(resolved):
        if len(fingerprints) + len(forbidden) >= max_files:
            truncated = True
            break
        try:
            relative = path.relative_to(resolved).as_posix()
            stat = path.stat()
        except (OSError, ValueError):
            continue
        if is_secret_path(path):
            forbidden.append(relative)
            fingerprints.append(CodexFileFingerprint(
                relative, stat.st_size, stat.st_mtime_ns, None, stat.st_mode, forbidden=True
            ))
            continue
        if path.is_symlink():
            fingerprints.append(CodexFileFingerprint(
                relative, stat.st_size, stat.st_mtime_ns, None, stat.st_mode, forbidden=True
            ))
            forbidden.append(relative)
            continue
        if scanned_bytes + stat.st_size > max_total_bytes:
            truncated = True
            continue
        scanned_bytes += stat.st_size
        digest: str | None = None
        binary = False
        text: str | None = None
        try:
            with path.open("rb") as handle:
                data = handle.read(min(max_hash_bytes, stat.st_size + 1))
            binary = b"\x00" in data[:8192]
            if stat.st_size <= max_hash_bytes:
                digest = hashlib.sha256(data).hexdigest()
            if not binary and stat.st_size <= max_diff_file_bytes:
                text = data.decode("utf-8", errors="replace")
        except OSError:
            pass
        fingerprints.append(CodexFileFingerprint(
            relative, stat.st_size, stat.st_mtime_ns, digest, stat.st_mode, binary, False, text
        ))
    git = _capture_git(resolved)
    return CodexWorkspaceSnapshot(
        resolved, tuple(sorted(fingerprints, key=lambda item: item.relative_path)), git,
        tuple(sorted(forbidden)), truncated=truncated,
        scanned_files=len(fingerprints) + len(forbidden), scanned_bytes=scanned_bytes,
    )


def build_change_set(
    before: CodexWorkspaceSnapshot,
    after: CodexWorkspaceSnapshot,
    *,
    max_diff_bytes: int = 1_000_000,
) -> CodexChangeSet:
    before_files = {item.relative_path: item for item in before.files}
    after_files = {item.relative_path: item for item in after.files}
    forbidden = set(before.forbidden_paths) | set(after.forbidden_paths)
    deleted = {name: item for name, item in before_files.items() if name not in after_files}
    added = {name: item for name, item in after_files.items() if name not in before_files}
    rename_from: dict[str, str] = {}
    used_deleted: set[str] = set()
    for new_name, new_item in added.items():
        if not new_item.digest:
            continue
        match = next((old_name for old_name, old_item in deleted.items()
                      if old_name not in used_deleted and old_item.digest == new_item.digest), None)
        if match:
            rename_from[new_name] = match
            used_deleted.add(match)
    names = sorted((before_files.keys() | after_files.keys() | forbidden) - used_deleted)
    changes: list[CodexFileChange] = []
    total_diff_bytes = 0
    for name in names:
        renamed_from = rename_from.get(name)
        old = before_files.get(renamed_from or name)
        new = after_files.get(name)
        if old and new and old.digest == new.digest and old.size == new.size and (
            not (old.forbidden or new.forbidden) or old.mtime_ns == new.mtime_ns
        ) and old.mode == new.mode and renamed_from is None:
            continue
        if name in forbidden:
            changes.append(CodexFileChange(
                name, "renamed" if renamed_from else _change_type(old, new), 0, 0,
                bool((old and old.binary) or (new and new.binary)), False, True,
                old.size if old else 0, new.size if new else 0, False,
                verification_status="blocked_secret_path",
                review_status=CodexReviewStatus.BLOCKED,
            ))
            continue
        binary = bool((old and old.binary) or (new and new.binary))
        available = not binary and (old is None or old.text is not None) and (new is None or new.text is not None)
        diff = ""
        hunks: tuple[CodexDiffHunk, ...] = ()
        additions = deletions = 0
        was_truncated = False
        if available:
            diff = "".join(difflib.unified_diff(
                (old.text or "").splitlines(keepends=True) if old else [],
                (new.text or "").splitlines(keepends=True) if new else [],
                fromfile=f"a/{name}", tofile=f"b/{name}", lineterm="\n",
            ))
            encoded = diff.encode("utf-8", errors="replace")
            remaining = max(0, max_diff_bytes - total_diff_bytes)
            if len(encoded) > remaining:
                diff = encoded[:remaining].decode("utf-8", errors="ignore")
                was_truncated = True
            total_diff_bytes += min(len(encoded), remaining)
            additions, deletions = _line_counts(diff)
            hunks = parse_unified_hunks(diff, truncated=was_truncated)
        changes.append(CodexFileChange(
            name, ("renamed" if renamed_from else _change_type(old, new)), additions, deletions, binary,
            _is_generated(name), False, old.size if old else 0, new.size if new else 0,
            bool(diff), verification_status="captured", hunks=hunks,
            unified_diff=diff, truncated=was_truncated,
        ))
    integrity = unexpected_git_actions(before, after)
    return CodexChangeSet(
        tuple(changes), sum(item.additions for item in changes),
        sum(item.deletions for item in changes),
        truncated=before.truncated or after.truncated or any(item.truncated for item in changes),
        integrity_reasons=integrity,
    )


def parse_unified_hunks(diff: str, *, truncated: bool = False) -> tuple[CodexDiffHunk, ...]:
    header_re = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
    hunks: list[CodexDiffHunk] = []
    current: tuple[int, int, int, int, str] | None = None
    lines: list[str] = []
    for line in diff.splitlines():
        match = header_re.match(line)
        if match:
            if current:
                hunks.append(CodexDiffHunk(*current[:4], current[4], tuple(lines), False))
            current = (
                int(match.group(1)), int(match.group(2) or 1),
                int(match.group(3)), int(match.group(4) or 1), match.group(5).strip(),
            )
            lines = []
        elif current and not line.startswith(("---", "+++")):
            lines.append(line)
    if current:
        hunks.append(CodexDiffHunk(*current[:4], current[4], tuple(lines), truncated))
    return tuple(hunks)


def unexpected_git_actions(before: CodexWorkspaceSnapshot,
                           after: CodexWorkspaceSnapshot) -> tuple[str, ...]:
    first, second = before.git, after.git
    if first is None or second is None:
        return () if first is second else ("git_repository_state_changed",)
    reasons: list[str] = []
    for field_name, reason in (
        ("head", "head_changed"), ("branch", "branch_changed"),
        ("tag_fingerprint", "tags_changed"), ("remote_fingerprint", "remotes_changed"),
        ("upstream", "upstream_changed"), ("upstream_head", "remote_head_changed"),
    ):
        if getattr(first, field_name) != getattr(second, field_name):
            reasons.append(reason)
    if first.staged_paths != second.staged_paths:
        reasons.append("staged_state_changed")
    if not first.merge_in_progress and second.merge_in_progress:
        reasons.append("merge_started")
    if not first.rebase_in_progress and second.rebase_in_progress:
        reasons.append("rebase_started")
    return tuple(reasons)


def _bounded_files(root: Path):
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = tuple(os.scandir(directory))
        except OSError:
            continue
        for entry in entries:
            path = Path(entry.path)
            if entry.is_dir(follow_symlinks=False):
                if entry.name.casefold() not in EXCLUDED_DIRECTORIES:
                    pending.append(path)
            elif entry.is_file(follow_symlinks=False) or entry.is_symlink():
                yield path


def _capture_git(root: Path) -> CodexGitSnapshot | None:
    if _git(root, "rev-parse", "--is-inside-work-tree")[0] != 0:
        return None
    _, head = _git(root, "rev-parse", "HEAD")
    _, branch = _git(root, "branch", "--show-current")
    _, status = _git(root, "status", "--porcelain=v2", "--branch")
    _, tags = _git(root, "for-each-ref", "--format=%(refname:short):%(objectname)", "refs/tags")
    _, remote_names = _git(root, "remote")
    remote_material: list[str] = []
    for name in remote_names.splitlines()[:50]:
        code, url = _git(root, "config", "--get", f"remote.{name}.url")
        if code == 0:
            remote_material.append(f"{name}:{hashlib.sha256(url.encode()).hexdigest()}")
    upstream_code, upstream = _git(root, "rev-parse", "--symbolic-full-name", "@{u}")
    upstream_head_code, upstream_head = _git(root, "rev-parse", "@{u}")
    staged = tuple(sorted(_staged_paths(status)))
    git_dir_code, git_dir = _git(root, "rev-parse", "--git-dir")
    git_path = (root / git_dir.strip()).resolve() if git_dir_code == 0 else root / ".git"
    return CodexGitSnapshot(
        head.strip() or None, branch.strip() or None, status[:1_000_000],
        hashlib.sha256(tags.encode()).hexdigest(),
        hashlib.sha256("\n".join(remote_material).encode()).hexdigest(),
        upstream.strip() if upstream_code == 0 else None,
        upstream_head.strip() if upstream_head_code == 0 else None,
        staged, (git_path / "MERGE_HEAD").exists(),
        (git_path / "rebase-merge").exists() or (git_path / "rebase-apply").exists(),
    )


def _git(root: Path, *arguments: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ("git", *arguments), cwd=root, shell=False, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return result.returncode, result.stdout[:1_000_000]


def _staged_paths(status: str) -> set[str]:
    paths: set[str] = set()
    for line in status.splitlines():
        parts = line.split()
        if line.startswith(("1 ", "2 ")) and len(parts) >= 9 and parts[1][0] != ".":
            paths.add(parts[-1])
    return paths


def _change_type(old: CodexFileFingerprint | None, new: CodexFileFingerprint | None) -> str:
    if old is None:
        return "added"
    if new is None:
        return "deleted"
    if old.digest == new.digest and old.mode != new.mode:
        return "mode_changed"
    return "modified"


def _line_counts(diff: str) -> tuple[int, int]:
    additions = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    return additions, deletions


def _is_generated(name: str) -> bool:
    folded = name.casefold()
    return any(folded.endswith(suffix) for suffix in GENERATED_SUFFIXES)
