"""Metadata-only Codex CLI session resume eligibility and identity checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import re

from lina.codex.models import CodexRemoteSessionReference


_SESSION_ID = re.compile(
    r"(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|[A-Za-z0-9][A-Za-z0-9._-]{2,63})\Z"
)


@dataclass(frozen=True, slots=True)
class CodexResumeEligibility:
    allowed: bool
    reasons: tuple[str, ...] = ()

    @property
    def primary_reason(self) -> str | None:
        return self.reasons[0] if self.reasons else None


def valid_cli_session_id(value: str) -> bool:
    return _SESSION_ID.fullmatch(str(value or "")) is not None


def workspace_fingerprint(path: Path) -> str:
    resolved = path.expanduser().resolve()
    normalized = str(resolved).replace("\\", "/").casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def assess_resume(
    reference: CodexRemoteSessionReference,
    workspace: Path,
    *,
    cli_version: str | None,
    authenticated: bool,
    capability_supported: bool,
    user_approved: bool,
    now: datetime | None = None,
    maximum_age_days: int = 30,
) -> CodexResumeEligibility:
    reasons: list[str] = []
    if not capability_supported:
        reasons.append("resume_unsupported")
    if not reference.resumable:
        reasons.append(reference.resume_block_reason or "session_not_resumable")
    if not valid_cli_session_id(reference.cli_session_id):
        reasons.append("invalid_session_id")
    if workspace_fingerprint(workspace) != reference.workspace_fingerprint:
        reasons.append("workspace_mismatch")
    if not authenticated:
        reasons.append("authentication_required")
    if not _compatible_version(reference.cli_version, cli_version):
        reasons.append("cli_version_incompatible")
    current = now or datetime.now(timezone.utc)
    if current - reference.last_used_at > timedelta(days=max(1, maximum_age_days)):
        reasons.append("session_stale")
    if not user_approved:
        reasons.append("user_approval_required")
    return CodexResumeEligibility(not reasons, tuple(dict.fromkeys(reasons)))


def _compatible_version(saved: str, current: str | None) -> bool:
    if not current:
        return False
    try:
        saved_parts = tuple(int(item) for item in saved.split(".")[:2])
        current_parts = tuple(int(item) for item in current.split(".")[:2])
    except ValueError:
        return False
    return len(saved_parts) == 2 and saved_parts == current_parts
