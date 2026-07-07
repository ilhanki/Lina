from lina.brain.prompts import DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_identifies_lina() -> None:
    assert "Lina" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_identifies_user() -> None:
    assert "İlhan" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_requires_turkish_answers() -> None:
    assert "Türkçe" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prevents_language_mixing() -> None:
    assert "gereksiz şekilde başka dillerle karıştırma" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prevents_broken_mixed_words() -> None:
    assert "kırpılmış yabancı kelimeler kullanma" in DEFAULT_SYSTEM_PROMPT
    assert "progressu" in DEFAULT_SYSTEM_PROMPT
    assert "starting pointina" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_allows_technical_terms() -> None:
    assert "Commit, branch, repository, provider, prompt, CLI" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prefers_honest_uncertainty() -> None:
    assert "bunu kesin bilmiyorum" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_avoids_claiming_missing_capabilities() -> None:
    assert "sahip olmadığın yetenekleri varmış gibi gösterme" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prevents_project_history_hallucination() -> None:
    assert "Proje geçmişi" in DEFAULT_SYSTEM_PROMPT
    assert "uydurma" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_prevents_claiming_external_access() -> None:
    assert "GitHub'ı" in DEFAULT_SYSTEM_PROMPT
    assert "gördüğünü söyleme" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_handles_today_project_questions_honestly() -> None:
    assert "bugün projede ne yapıldığını" in DEFAULT_SYSTEM_PROMPT
    assert "yalnızca mevcut konuşmaya göre" in DEFAULT_SYSTEM_PROMPT
