"""Tests for Qt GUI formatting helpers."""

from lina.interfaces.qt.formatting import (
    derive_session_title,
    normalize_assistant_text,
)


def test_normalize_assistant_text_removes_repeated_lina_prefixes() -> None:
    assert normalize_assistant_text("Lina:Lina: Merhaba") == "Merhaba"
    assert normalize_assistant_text("Lina: Lina: Cevap") == "Cevap"


def test_session_title_skips_simple_greetings() -> None:
    assert derive_session_title("selam naber") == "Yeni Sohbet"


def test_session_title_uses_first_meaningful_message() -> None:
    assert derive_session_title("roadmap dosyasını özetle") == "roadmap dosyasını özetle"
    assert derive_session_title("x" * 80).endswith("...")
