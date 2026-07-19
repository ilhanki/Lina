"""Typed, ephemeral Codex change review models and non-destructive decisions."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum


class CodexReviewStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIALLY_ACCEPTED = "partially_accepted"
    INFORMATIONAL = "informational"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class CodexDiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header: str
    lines: tuple[str, ...]
    truncated: bool = False


@dataclass(frozen=True, slots=True)
class CodexFileChange:
    relative_path: str
    change_type: str
    additions: int
    deletions: int
    binary: bool
    generated: bool
    forbidden: bool
    size_before: int
    size_after: int
    diff_available: bool
    verification_status: str = "unverified"
    review_status: CodexReviewStatus = CodexReviewStatus.PENDING
    hunks: tuple[CodexDiffHunk, ...] = ()
    unified_diff: str = field(default="", repr=False)
    truncated: bool = False


@dataclass(frozen=True, slots=True)
class CodexChangeSet:
    files: tuple[CodexFileChange, ...]
    additions: int
    deletions: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    truncated: bool = False
    integrity_reasons: tuple[str, ...] = ()

    @property
    def changed_file_count(self) -> int:
        return len(self.files)

    @property
    def blocked(self) -> bool:
        return bool(self.integrity_reasons or any(item.forbidden for item in self.files))


@dataclass(frozen=True, slots=True)
class CodexReviewDecision:
    action: str
    relative_path: str | None = None
    hunk_index: int | None = None
    note: str = ""
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.action not in {"accept", "reject", "inspect", "request_explanation", "send_back"}:
            raise ValueError("Unsupported Codex review decision")
        if len(self.note) > 500:
            raise ValueError("Review note exceeds safe metadata bounds")


@dataclass(frozen=True, slots=True)
class CodexReviewSummary:
    accepted: int
    rejected: int
    pending: int
    blocked: int
    decisions: tuple[CodexReviewDecision, ...] = ()

    @property
    def complete(self) -> bool:
        return self.pending == 0 and self.blocked == 0

    @property
    def approved_for_continue(self) -> bool:
        return self.complete and self.rejected == 0


class CodexReviewSession:
    """In-memory review state. Decisions never mutate workspace files."""

    def __init__(self, change_set: CodexChangeSet) -> None:
        self.change_set = change_set
        self._decisions: list[CodexReviewDecision] = []

    def decide(self, decision: CodexReviewDecision) -> CodexChangeSet:
        self._decisions.append(decision)
        files: list[CodexFileChange] = []
        for item in self.change_set.files:
            if decision.relative_path is not None and item.relative_path != decision.relative_path:
                files.append(item)
                continue
            status = item.review_status
            if item.forbidden:
                status = CodexReviewStatus.BLOCKED
            elif decision.action == "accept" and decision.hunk_index is not None:
                status = CodexReviewStatus.PARTIALLY_ACCEPTED
            elif decision.action == "accept":
                status = CodexReviewStatus.ACCEPTED
            elif decision.action == "reject":
                status = CodexReviewStatus.REJECTED
            elif decision.action == "inspect":
                status = CodexReviewStatus.INFORMATIONAL
            files.append(replace(item, review_status=status))
        self.change_set = replace(self.change_set, files=tuple(files))
        return self.change_set

    def summary(self) -> CodexReviewSummary:
        statuses = [item.review_status for item in self.change_set.files]
        return CodexReviewSummary(
            accepted=statuses.count(CodexReviewStatus.ACCEPTED),
            rejected=statuses.count(CodexReviewStatus.REJECTED),
            pending=statuses.count(CodexReviewStatus.PENDING),
            blocked=statuses.count(CodexReviewStatus.BLOCKED),
            decisions=tuple(self._decisions),
        )
