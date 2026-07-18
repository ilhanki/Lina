from pathlib import Path

from lina.codex.models import (
    CodexExecutionEvidence,
    CodexResult,
    CodexRiskLevel,
    CodexTask,
    RequestedAction,
    VerificationOutcome,
)
from lina.codex.validator import CodexOutputValidator


def make_task(tmp_path: Path, risk: CodexRiskLevel) -> CodexTask:
    return CodexTask.create("Görev", "Açıklama", "Amaç", tmp_path,
                            (RequestedAction("inspect"),), risk_level=risk)


def test_read_only_unchanged_is_verified(tmp_path: Path) -> None:
    fingerprints = (("app.py", "one"),)
    result = CodexResult("Tamam", evidence=CodexExecutionEvidence(
        exit_code=0, before_fingerprints=fingerprints, after_fingerprints=fingerprints
    ))
    assert CodexOutputValidator().verify(make_task(tmp_path, CodexRiskLevel.READ_ONLY), result).outcome \
        is VerificationOutcome.SUCCESS


def test_read_only_changed_fails_verification(tmp_path: Path) -> None:
    result = CodexResult("Tamam", changed_files=(str(tmp_path / "app.py"),),
                         evidence=CodexExecutionEvidence(
                             exit_code=0, before_fingerprints=(("app.py", "one"),),
                             after_fingerprints=(("app.py", "two"),)))
    report = CodexOutputValidator().verify(make_task(tmp_path, CodexRiskLevel.READ_ONLY), result)
    assert report.outcome is VerificationOutcome.FAILED
    assert "read_only_changed" in report.checks


def test_modification_with_diff_is_verified(tmp_path: Path) -> None:
    changed = str(tmp_path / "app.py")
    result = CodexResult("Tamam", changed_files=(changed,), evidence=CodexExecutionEvidence(
        exit_code=0, before_fingerprints=(("app.py", "one"),),
        after_fingerprints=(("app.py", "two"),)))
    assert CodexOutputValidator().verify(make_task(tmp_path, CodexRiskLevel.MODIFICATION), result).outcome \
        is VerificationOutcome.SUCCESS


def test_sensitive_output_fails_without_repeating_secret(tmp_path: Path) -> None:
    result = CodexResult("[REDACTED]", evidence=CodexExecutionEvidence(
        exit_code=0, sensitive_output_detected=True
    ))
    report = CodexOutputValidator().verify(make_task(tmp_path, CodexRiskLevel.READ_ONLY), result)
    assert report.outcome is VerificationOutcome.FAILED
    assert "sensitive_output_detected" in report.checks

