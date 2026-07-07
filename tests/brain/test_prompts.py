from lina.brain.prompts import DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_identifies_lina() -> None:
    assert "Lina" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_identifies_user() -> None:
    assert "İlhan" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_requires_turkish_answers() -> None:
    assert "Türkçe" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_avoids_claiming_missing_capabilities() -> None:
    assert "sahip olmadığın yetenekleri varmış gibi gösterme" in DEFAULT_SYSTEM_PROMPT
