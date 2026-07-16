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
