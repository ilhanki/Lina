import pytest

from lina.quality import ResponseQualityValidator, ResponseRepairService, SAFE_FALLBACK


@pytest.mark.parametrize("text", [
    "Yapay zekâ ajanı, hedefe ulaşmak için plan yapan ve izinli araçları kullanan bir sistemdir.",
    "Python API üzerinden JSON yanıtı alınabilir.",
])
def test_valid_turkish_and_allowed_technical_terms(text):
    assert ResponseQualityValidator().validate(text, user_text="Bu nedir?").is_valid


@pytest.mark.parametrize("text", [
    "Sen nasılsın, ben Sen Lina'sın. Yapay zeka images thingsi yapan sistemdir.",
    "Aynı cümle burada. Aynı cümle burada. Aynı cümle burada.",
    "Assistant: kullanıcı: Ben Sen Lina'sın.",
    "...!!!",
    "",
    "Sen nasılsın, ben Sen Lina'sın. Yapay zekâ agent hakkında trí tuệ nhân tạo ve thingsi söyler. Aynı fikir. Aynı fikir.",
    "Bu responseu düzenleyip fileı chatte kullanabilirsin.",
])
def test_obvious_corruption_is_rejected(text):
    assert not ResponseQualityValidator().validate(text, user_text="Yapay zekâ ajanı nedir?").is_valid


def test_repair_runs_once_and_accepts_only_final_text():
    calls = []
    service = ResponseRepairService(lambda question, draft: calls.append((question, draft)) or "Bu, doğal ve düzgün bir Türkçe cevaptır.")
    result = service.accept("Bu nedir?", "thingsi imagesi")
    assert result.repaired and not result.rejected
    assert result.text == "Bu, doğal ve düzgün bir Türkçe cevaptır."
    assert len(calls) == 1


def test_failed_repair_uses_safe_fallback_without_loop():
    calls = []
    service = ResponseRepairService(lambda _question, _draft: calls.append(True) or "!!!")
    result = service.accept("Bu nedir?", "thingsi imagesi")
    assert result.text == SAFE_FALLBACK
    assert result.rejected
    assert calls == [True]
    assert service.repair_count == 1
    assert service.rejection_count == 1


def test_foreign_phrase_and_suffix_leakage_are_privacy_safe_metrics():
    result = ResponseQualityValidator().validate(
        "Yapay zekâ için trí tuệ nhân tạo açıklaması ve responseu burada.",
        user_text="Yapay zekâ ajanı nedir?",
    )
    assert not result.is_valid
    assert result.metrics["foreign_phrase_detected"] is True
    assert all("trí" not in str(value) for value in result.metrics.values())


@pytest.mark.parametrize("text", [
    "Merhaba! Nasıl yardımcı olabilirim? Yapay zekâ ajanı plan hazırlayan bir sistemdir.",
    "Bu açıklama user için some things anlatıyor.",
    "Yapay zekâ ajanı plan yapar và izinli araçları kullanır.",
    "Memoryyi toolu kullanarak contexti günceller.",
])
def test_generic_boilerplate_and_orphan_foreign_words_are_rejected(text):
    result = ResponseQualityValidator().validate(text, user_text="Yapay zekâ ajanı nedir?")
    assert not result.is_valid
    assert result.rejection_reason in {
        "language_mixing", "foreign_word_leak", "generic_boilerplate", "malformed"
    }


def test_casual_turkish_and_explicit_english_remain_valid():
    validator = ResponseQualityValidator()
    assert validator.validate("İyiyim, teşekkür ederim.", user_text="Nasılsın Lina?").is_valid
    assert validator.validate(
        "This response explains what the system does.",
        user_text="What does this system do?",
        expected_language="unknown",
    ).is_valid


def test_cancelled_or_stale_repair_is_never_presented():
    states = iter((True, False))
    service = ResponseRepairService(lambda _question, _draft: "Düzgün ve doğal Türkçe cevap.")
    result = service.accept(
        "Bu nedir?",
        "thingsi imagesi",
        request_is_current=lambda: next(states),
    )
    assert result.stale and result.cancelled
    assert result.text == ""
