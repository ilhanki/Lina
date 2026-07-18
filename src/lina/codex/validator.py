"""Independent validation of Codex claims and result scope."""

from pathlib import Path

from lina.codex.models import (CodexResult, CodexTask, VerificationOutcome,
                                VerificationReport)
from lina.codex.permissions import WorkspaceAccessError, ensure_within_workspace


class CodexOutputValidator:
    def verify(self, task: CodexTask, result: CodexResult) -> VerificationReport:
        checks: list[str] = []
        if result.stale:
            return VerificationReport(VerificationOutcome.FAILED, "Sonuç güncel değil.", ("stale_result",))
        if not result.summary.strip():
            return VerificationReport(VerificationOutcome.FAILED, "Beklenen sonuç özeti yok.", ("missing_summary",))
        checks.append("summary_present")
        try:
            for changed in result.changed_files:
                ensure_within_workspace(task.workspace, Path(changed))
        except WorkspaceAccessError:
            return VerificationReport(VerificationOutcome.FAILED, "Sonuç çalışma alanı sınırını aşıyor.",
                                      tuple(checks + ["workspace_violation"]))
        checks.append("workspace_contained")
        if task.risk_level.value == "modification" and not result.changed_files:
            return VerificationReport(VerificationOutcome.UNCERTAIN,
                                      "Değişiklik istendi ancak dosya değişikliği kanıtlanamadı.", tuple(checks))
        return VerificationReport(VerificationOutcome.SUCCESS, "Codex sonucu doğrulandı.", tuple(checks))

