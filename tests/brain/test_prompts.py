from lina.brain.prompts import DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_identifies_lina() -> None:
    assert "Lina" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_identifies_user() -> None:
    assert "İlhan" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_requires_turkish_answers() -> None:
    assert "Türkçe" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prevents_language_mixing() -> None:
    assert "cümlenin tamamı doğal Türkçe olmalı" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prevents_broken_mixed_words() -> None:
    assert "kelime kırpıntısı kullanma" in DEFAULT_SYSTEM_PROMPT
    assert "about" in DEFAULT_SYSTEM_PROMPT
    assert "progressu" in DEFAULT_SYSTEM_PROMPT
    assert "starting pointina" in DEFAULT_SYSTEM_PROMPT
    assert "tentang" in DEFAULT_SYSTEM_PROMPT
    assert "today'de" in DEFAULT_SYSTEM_PROMPT
    assert "algunos" in DEFAULT_SYSTEM_PROMPT
    assert "melez ifadeler üretme" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_allows_technical_terms() -> None:
    assert "Commit, branch, repository, provider, prompt, CLI, GUI ve tool" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prefers_honest_uncertainty() -> None:
    assert "bunu kesin bilmiyorum" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_avoids_claiming_missing_capabilities() -> None:
    assert "sahip olmadığın yetenekleri varmış gibi gösterme" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prevents_project_history_hallucination() -> None:
    assert "proje geçmişi" in DEFAULT_SYSTEM_PROMPT
    assert "hallucination yapma" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_respects_project_context() -> None:
    assert "Project context" in DEFAULT_SYSTEM_PROMPT
    assert "Kaynak: git" in DEFAULT_SYSTEM_PROMPT
    assert "projeyle ilgili soruları doğrudan oradaki bilgilere dayanarak yanıtla" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_handles_missing_info_honestly() -> None:
    assert "erişimin yoksa bunu dürüstçe belirt" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prevents_exaggerated_promises() -> None:
    assert "Abartılı vaat verme" in DEFAULT_SYSTEM_PROMPT
