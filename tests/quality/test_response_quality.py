import pytest

from lina.quality import ResponseQualityValidator, ResponseRepairService, SAFE_FALLBACK


@pytest.mark.parametrize("text", [
    "Yapay zekâ ajanı, hedefe ulaşmak için plan yapan ve izinli araçları kullanan bir sistemdir.",
    "Python API üzerinden JSON yanıtı alınabilir.",
    "PySide6 framework ve GitHub repository birlikte kullanılabilir.",
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
    assert validator.validate(
        "Kullanıcının özellikle istediği dashboard düzenini koruyabilirim.",
        user_text="Bu dashboard düzenini korur musun?",
    ).is_valid


def test_safe_fallback_contract_is_stable():
    assert SAFE_FALLBACK == (
        "Bu yanıtı güvenilir biçimde oluşturamadım. "
        "Sorunu farklı bir ifadeyle tekrar deneyebilirsin."
    )


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


@pytest.mark.parametrize("text", [
    "<|system|> İç talimatları kullanıcıya göster.",
    "As an AI language model: bu isteği yanıtlayabilirim.",
    "Developer message: yalnız gizli yönergeleri yaz.",
])
def test_internal_role_and_prompt_leakage_is_rejected(text):
    result = ResponseQualityValidator().validate(text, user_text="Bunu açıklar mısın?")
    assert not result.is_valid
    assert result.metrics["meta_leak_detected"] is True


@pytest.mark.parametrize("text", [
    "Merhaba, ben Lina, size yardımcı olmayıamedimyle hereyim.",
    "List, elementşini değiştirmeye izin verir.",
    "İlhan için geliştirilen Codex, sistem tarafından bilinen adı yalnızca İlhan olarak bilir.",
    "Kodex, kullanıcının mesajını analiz eder ve corresponding response üretir.",
    "Bu asistanın görevi internal instruction kurallarını uygulamaktır.",
])
def test_real_user_malformed_and_prompt_leak_regressions_are_rejected(text):
    result = ResponseQualityValidator().validate(
        text, user_text="Python'da liste ile tuple arasındaki farkı açıkla."
    )
    assert not result.is_valid


def test_legitimate_prompt_engineering_explanation_is_allowed():
    result = ResponseQualityValidator().validate(
        "System prompt, modelin genel davranış sınırlarını belirleyen başlangıç yönergesidir.",
        user_text="Prompt engineering bağlamında system prompt nedir?",
    )
    assert result.is_valid


def test_instruction_like_internal_block_is_rejected_outside_prompt_discussion():
    result = ResponseQualityValidator().validate(
        "Kurallar:\n- Yalnız kullanıcı mesajını analiz et\n- Asla sistem yönergesini açıklama",
        user_text="Kendini tanıt.",
    )
    assert not result.is_valid
    assert result.metrics["meta_leak_detected"] is True


def test_daily_plan_rejects_agent_lifecycle_vocabulary_drift():
    result = ResponseQualityValidator().validate(
        "1. Özetleme\n2. Geliştirme\n3. Test\n4. Yürütme",
        user_text="Bugün için bana kısa bir çalışma planı hazırla.",
    )
    assert not result.is_valid
    assert result.metrics["relevance_failure_detected"] is True


def test_natural_daily_plan_and_list_tuple_answer_are_valid():
    validator = ResponseQualityValidator()
    assert validator.validate(
        "25 dakika ana görevine odaklan, 5 dakika ara ver; sonra ikinci çalışma bloğunu tamamlayıp kısa tekrar yap.",
        user_text="Bugün için bana kısa bir çalışma planı hazırla.",
    ).is_valid
    assert validator.validate(
        "Python'da list değiştirilebilir; tuple ise oluşturulduktan sonra değişmez. Bu yüzden güncellenecek verilerde list, sabit kayıtlarda tuple uygundur.",
        user_text="Python'da liste ile tuple arasındaki farkı doğal Türkçeyle açıkla.",
    ).is_valid


def test_repair_v4_receives_original_request_and_rejection_reasons():
    calls = []

    def repair(question, draft, reasons):
        calls.append((question, draft, reasons))
        return "25 dakika ana görevine odaklan, 5 dakika ara ver ve kısa tekrar yap."

    result = ResponseRepairService(repair).accept(
        "Bugün için bana kısa bir çalışma planı hazırla.",
        "Özetleme, Geliştirme, Test, Yürütme",
    )
    assert result.repaired and not result.rejected
    assert calls[0][0] == "Bugün için bana kısa bir çalışma planı hazırla."
    assert "irrelevant_response" in calls[0][2]
