from pathlib import Path

from lina.codex.models import (CodexExecutionEvidence, CodexResult, CodexRiskLevel,
                                VerificationOutcome)
from lina.codex.planner import CodexPlanner
from lina.codex.validator import CodexOutputValidator


def test_analysis_plan_is_non_modifying(tmp_path: Path):
    task = CodexPlanner().plan("Bu projeyi analiz et", tmp_path)
    assert task.risk_level is CodexRiskLevel.READ_ONLY
    assert task.approval_required is False


def test_modification_plan_requires_approval(tmp_path: Path):
    task = CodexPlanner().plan("main.py dosyasını değiştir", tmp_path)
    assert task.risk_level is CodexRiskLevel.MODIFICATION
    assert task.approval_required is True


def test_verification_success(tmp_path: Path):
    task = CodexPlanner().plan("analiz et", tmp_path)
    report = CodexOutputValidator().verify(task, CodexResult("Üç bulgu var."))
    assert report.outcome is VerificationOutcome.SUCCESS


def test_verification_rejects_stale_result(tmp_path: Path):
    task = CodexPlanner().plan("analiz et", tmp_path)
    report = CodexOutputValidator().verify(task, CodexResult("Eski", stale=True))
    assert report.outcome is VerificationOutcome.FAILED


def test_modification_without_changed_file_is_uncertain(tmp_path: Path):
    task = CodexPlanner().plan("dosyayı değiştir", tmp_path)
    report = CodexOutputValidator().verify(task, CodexResult("Tamamlandı"))
    assert report.outcome is VerificationOutcome.UNCERTAIN


def test_changed_file_outside_workspace_fails(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    task = CodexPlanner().plan("dosyayı değiştir", root)
    report = CodexOutputValidator().verify(
        task, CodexResult("Tamamlandı", changed_files=(str(tmp_path / "other.py"),)))
    assert report.outcome is VerificationOutcome.FAILED


def test_requested_test_requires_successful_execution_evidence(tmp_path: Path) -> None:
    task = CodexPlanner().plan("Yalnız test komutunu çalıştır ve sonucu doğrula", tmp_path)
    missing = CodexOutputValidator().verify(
        task, CodexResult("Testler geçti", evidence=CodexExecutionEvidence(exit_code=0))
    )
    assert missing.outcome is VerificationOutcome.FAILED
    assert "test_execution_evidence_missing" in missing.checks
    assert "Oturum durumunu yenileyip" in missing.summary
    verified = CodexOutputValidator().verify(
        task, CodexResult("Testler geçti", evidence=CodexExecutionEvidence(
            exit_code=0, tests_passed=True, test_commands=("pytest",),
        ))
    )
    assert verified.outcome is VerificationOutcome.SUCCESS
