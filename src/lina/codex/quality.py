"""Turn verified Codex output into concise, user-facing Lina language."""

from pathlib import Path
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
        changed = tuple(dict.fromkeys(Path(item).name for item in result.changed_files))
        change_summary = (
            f"Değişen dosyalar ({len(changed)}): {', '.join(changed[:12])}"
            if changed else "Herhangi bir dosya değiştirilmedi."
        )
        evidence = result.evidence
        if evidence is None or evidence.tests_passed is None:
            tests = "Test sonucu: CLI tarafından doğrulanabilir test kanıtı sunulmadı."
        else:
            tests = "Test sonucu: Başarılı." if evidence.tests_passed else "Test sonucu: Başarısız."
        verification = f"Doğrulama: {report.summary}"
        findings = f"Bulunanlar:\n{text}" if text else "Bulunanlar: Ayrıntılı bulgu sunulmadı."
        return "\n\n".join((prefix, findings, change_summary, tests, verification))
