from lina.codex.models import (CodexResult, VerificationOutcome, VerificationReport)
from lina.codex.quality import CodexResponseQuality
from lina.codex.voice import (CodexControlAction, confirmation_prompt,
                              route_codex_control, route_codex_voice)


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


def test_voice_routes_codex_status_control() -> None:
    assert route_codex_control("Codex görev durumu nedir?").action is CodexControlAction.STATUS


def test_voice_routes_codex_stop_control() -> None:
    assert route_codex_control("Codex görevini durdur").action is CodexControlAction.STOP


def test_voice_routes_codex_resume_control() -> None:
    assert route_codex_control("Codex görevine devam et").action is CodexControlAction.RESUME


def test_voice_routes_codex_change_review_control() -> None:
    assert route_codex_control("Codex değişiklikleri göster").action is CodexControlAction.SHOW_CHANGES


def test_voice_control_does_not_capture_normal_chat() -> None:
    assert not route_codex_control("Bugün ne yapıyorsun?").matched
