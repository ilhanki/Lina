"""Ephemeral workspace snapshots used to verify real CLI effects."""

from __future__ import annotations

import hashlib
from pathlib import Path

from lina.codex.models import CodexExecutionEvidence, ProjectContext
from lina.codex.permissions import ensure_within_workspace, is_secret_path


def capture_workspace(context: ProjectContext) -> tuple[tuple[str, str], ...]:
    fingerprints: list[tuple[str, str]] = []
    try:
        candidates = tuple(context.root_path.rglob("*"))
    except OSError:
        candidates = context.allowed_files
    for raw_path in candidates:
        if any(part.casefold() in {".git", "__pycache__", "node_modules", ".venv"}
               for part in raw_path.parts):
            continue
        try:
            path = ensure_within_workspace(context.root_path, raw_path)
        except (OSError, ValueError):
            continue
        if not path.is_file() or is_secret_path(path):
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            relative = path.relative_to(context.root_path).as_posix()
        except OSError:
            continue
        fingerprints.append((relative, digest))
    return tuple(sorted(fingerprints))


def build_evidence(before: tuple[tuple[str, str], ...],
                   after: tuple[tuple[str, str], ...], exit_code: int,
                   *, sensitive_output_detected: bool = False) -> CodexExecutionEvidence:
    return CodexExecutionEvidence(exit_code=exit_code, before_fingerprints=before,
                                  after_fingerprints=after,
                                  sensitive_output_detected=sensitive_output_detected)


def changed_paths(evidence: CodexExecutionEvidence, root: Path) -> tuple[str, ...]:
    before = dict(evidence.before_fingerprints)
    after = dict(evidence.after_fingerprints)
    names = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    return tuple(str(ensure_within_workspace(root, root / name)) for name in names)
