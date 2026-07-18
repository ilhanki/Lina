"""Deterministic safe task planning before a Codex client is invoked."""

from __future__ import annotations

import re
from pathlib import Path

from lina.codex.models import (CodexRiskLevel, CodexTask, CodexVerificationRule,
                                ExpectedOutput, RequestedAction)


_MODIFICATION_WORDS = re.compile(
    r"\b(değiştir|düzenle|ekle|sil|uygula|optimize et|fix|implement|modify|edit|delete)\b", re.I)


class CodexPlanner:
    def plan(self, request: str, workspace: Path) -> CodexTask:
        clean = " ".join(request.split())
        if not clean:
            raise ValueError("Codex görevi için açık bir istek gerekli.")
        modification = bool(_MODIFICATION_WORDS.search(clean))
        risk = CodexRiskLevel.MODIFICATION if modification else CodexRiskLevel.ANALYSIS
        actions = (
            RequestedAction("inspect_structure", purpose="Proje yapısını ve ana teknolojileri belirle"),
            RequestedAction("analyze", purpose="Riskleri ve iyileştirme alanlarını bul"),
            RequestedAction("prepare_summary", purpose="Kanıta dayalı kısa sonuç hazırla"),
        )
        if modification:
            actions += (RequestedAction("propose_modification", purpose="Dosya bazında değişiklik öner"),)
        return CodexTask.create(
            "Codex ile proje çalışması", clean, clean, workspace, actions,
            risk_level=risk, approval_required=modification,
            expected_output=ExpectedOutput("Lina tarafından özetlenebilir doğrulanmış sonuç"),
            verification_rules=(CodexVerificationRule("non_empty_summary"),
                                CodexVerificationRule("workspace_containment")),
        )

