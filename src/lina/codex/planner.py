"""Deterministic safe task planning before a Codex client is invoked."""

from __future__ import annotations

import re
from pathlib import Path

from lina.codex.models import (CodexRiskLevel, CodexTask, CodexVerificationRule,
                                ExpectedOutput, RequestedAction)


_MODIFICATION_WORDS = re.compile(
    r"\b(değiştir|düzenle|ekle|sil|uygula|optimize et|fix|implement|modify|edit|delete)\b", re.I)
_TEST_EXECUTION_WORDS = re.compile(
    r"\b(?:test|pytest|unittest|doctest)\b.*\b(?:çalıştır|doğrula|run|execute|verify)\b"
    r"|\b(?:çalıştır|doğrula|run|execute|verify)\b.*\b(?:test|pytest|unittest|doctest)\b",
    re.IGNORECASE,
)


class CodexPlanner:
    def plan(self, request: str, workspace: Path) -> CodexTask:
        clean = " ".join(request.split())
        if not clean:
            raise ValueError("Codex görevi için açık bir istek gerekli.")
        modification = bool(_MODIFICATION_WORDS.search(clean))
        risk = CodexRiskLevel.MODIFICATION if modification else CodexRiskLevel.READ_ONLY
        actions = (
            RequestedAction("inspect_structure", purpose="Proje yapısını incele"),
            RequestedAction("detect_technologies", purpose="Kullanılan teknolojileri belirle"),
            RequestedAction("analyze", purpose="Olası hata ve riskleri tespit et"),
            RequestedAction("prepare_summary", purpose="İyileştirme önerilerini hazırla"),
        )
        if modification:
            actions += (RequestedAction("propose_modification", purpose="Dosya bazında değişiklik öner"),)
        rules = [CodexVerificationRule("non_empty_summary"),
                 CodexVerificationRule("workspace_containment")]
        if _TEST_EXECUTION_WORDS.search(clean):
            rules.append(CodexVerificationRule("test_execution_succeeded"))
        return CodexTask.create(
            "Codex ile proje çalışması", clean, clean, workspace, actions,
            risk_level=risk, approval_required=modification,
            expected_output=ExpectedOutput("Lina tarafından özetlenebilir doğrulanmış sonuç"),
            verification_rules=tuple(rules),
        )
