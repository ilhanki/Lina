"""Turn verified Codex output into concise, user-facing Lina language."""

import re

from lina.codex.models import CodexResult, VerificationReport


class CodexResponseQuality:
    def prepare(self, result: CodexResult, report: VerificationReport) -> str:
        text = re.sub(r"(?m)^\s*(?:\$|>|DEBUG|INFO|TRACE).*$", "", result.summary)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if len(text) > 1600:
            text = text[:1597].rstrip() + "…"
        prefix = ("Analiz tamamlandı." if report.outcome.value == "success"
                  else "Sonuç kesin olarak doğrulanamadı.")
        return f"{prefix}\n\n{text}" if text else prefix

