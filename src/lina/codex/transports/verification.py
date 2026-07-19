"""Bounded workspace evidence and Verification V2 helpers."""

from __future__ import annotations

from pathlib import Path

from lina.codex.models import CodexExecutionEvidence, ProjectContext
from lina.codex.permissions import ensure_within_workspace
from lina.codex.snapshot import (CodexWorkspaceSnapshot, build_change_set,
                                 capture_workspace_snapshot)


def capture_workspace(context: ProjectContext) -> CodexWorkspaceSnapshot:
    return capture_workspace_snapshot(context.root_path)


def build_evidence(
    before: CodexWorkspaceSnapshot,
    after: CodexWorkspaceSnapshot,
    exit_code: int,
    *,
    sensitive_output_detected: bool = False,
) -> CodexExecutionEvidence:
    change_set = build_change_set(before, after)
    reasons = list(change_set.integrity_reasons)
    if before.truncated or after.truncated:
        reasons.append("snapshot_truncated")
    if change_set.blocked:
        reasons.append("forbidden_path_changed")
    return CodexExecutionEvidence(
        exit_code=exit_code, before_fingerprints=before.fingerprint_pairs,
        after_fingerprints=after.fingerprint_pairs,
        sensitive_output_detected=sensitive_output_detected,
        integrity_reasons=tuple(dict.fromkeys(reasons)),
    )


def changed_paths(evidence: CodexExecutionEvidence, root: Path) -> tuple[str, ...]:
    before = dict(evidence.before_fingerprints)
    after = dict(evidence.after_fingerprints)
    names = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    return tuple(str(ensure_within_workspace(root, root / name)) for name in names)
