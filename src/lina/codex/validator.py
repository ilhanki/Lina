"""Independent validation of Codex claims and result scope."""

from pathlib import Path

from lina.codex.models import (CodexResult, CodexTask, VerificationOutcome,
                                VerificationReport)
from lina.codex.permissions import WorkspaceAccessError, ensure_within_workspace, is_secret_path


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
        if any(is_secret_path(Path(changed)) for changed in result.changed_files):
            return VerificationReport(VerificationOutcome.FAILED, "Hassas dosya değişikliği engellendi.",
                                      tuple(checks + ["forbidden_file"]))
        evidence = result.evidence
        if evidence is not None:
            if evidence.integrity_reasons:
                return VerificationReport(
                    VerificationOutcome.FAILED,
                    "Codex görevi çalışma alanı veya Git bütünlüğünü koruyamadı.",
                    tuple(checks + list(evidence.integrity_reasons)),
                )
            if evidence.sensitive_output_detected:
                return VerificationReport(VerificationOutcome.FAILED,
                                          "Codex çıktısında hassas veri olasılığı algılandı ve içerik maskelendi.",
                                          tuple(checks + ["sensitive_output_detected"]))
            if evidence.exit_code != 0:
                return VerificationReport(VerificationOutcome.FAILED, "Codex işlemi başarılı çıkış vermedi.",
                                          tuple(checks + ["exit_code_failed"]))
            checks.append("exit_code_zero")
            changed_by_snapshot = evidence.before_fingerprints != evidence.after_fingerprints
            if task.risk_level.value != "modification" and changed_by_snapshot:
                return VerificationReport(VerificationOutcome.FAILED,
                                          "Salt-okunur görev çalışma alanını değiştirdi.",
                                          tuple(checks + ["read_only_changed"]))
            checks.append("workspace_snapshot_checked")
        if task.risk_level.value == "modification" and not result.changed_files:
            return VerificationReport(VerificationOutcome.UNCERTAIN,
                                      "Değişiklik istendi ancak dosya değişikliği kanıtlanamadı.", tuple(checks))
        return VerificationReport(VerificationOutcome.SUCCESS, "Codex sonucu doğrulandı.", tuple(checks))
