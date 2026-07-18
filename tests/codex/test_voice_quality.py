from lina.codex.models import (CodexResult, VerificationOutcome, VerificationReport)
from lina.codex.quality import CodexResponseQuality
from lina.codex.voice import confirmation_prompt, route_codex_voice


def test_voice_routes_explicit_codex_command_to_confirmation():
    intent = route_codex_voice("Lina Codex ile bu projeye bak")
    assert intent.matched and intent.requires_confirmation
    assert "onaylamanı" in confirmation_prompt()


def test_voice_ignores_normal_chat():
    assert not route_codex_voice("Bugün nasılsın?").matched
    assert not route_codex_voice("Codex nedir?").matched


def test_voice_routes_spelling_variant_without_technical_tts_leakage():
    assert route_codex_voice("Lina, kodeksle bu projeyi incele").matched
    prompt = confirmation_prompt()
    assert "system" not in prompt.casefold()
    assert "instruction" not in prompt.casefold()


def test_response_quality_removes_terminal_spam_and_bounds_output():
    report = VerificationReport(VerificationOutcome.SUCCESS, "ok")
    text = CodexResponseQuality().prepare(CodexResult("INFO raw log\nÜç bulgu var."), report)
    assert "INFO" not in text
    assert text.startswith("Analiz tamamlandı.")
    assert "Bulunanlar:" in text
    assert "Herhangi bir dosya değiştirilmedi." in text
    assert "Doğrulama:" in text
