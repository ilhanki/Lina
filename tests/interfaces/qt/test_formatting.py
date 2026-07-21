"""Tests for Qt GUI formatting helpers."""

from datetime import datetime

from lina.interfaces.qt.formatting import (
    build_welcome_message,
    derive_session_title,
    format_conversation_datetime,
    format_message_time,
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


def test_conversation_datetime_uses_turkish_relative_labels() -> None:
    local_timezone = datetime.now().astimezone().tzinfo
    now = datetime(2026, 7, 12, 15, 30, tzinfo=local_timezone)

    assert format_conversation_datetime(now, now) == "Bugün · 15:30"
    assert format_conversation_datetime(
        datetime(2026, 7, 11, 22, 30, tzinfo=local_timezone), now
    ) == "Dün · 22:30"
    assert format_conversation_datetime(
        datetime(2026, 7, 1, 18, 45, tzinfo=local_timezone), now
    ) == "1 Tem · 18:45"
    assert format_conversation_datetime(
        datetime(2025, 12, 1, 18, 45, tzinfo=local_timezone), now
    ) == "1 Ara 2025"


def test_welcome_message_is_time_aware_and_deterministic() -> None:
    morning = datetime(2026, 7, 12, 8, tzinfo=datetime.now().astimezone().tzinfo)

    first = build_welcome_message(morning, conversation_id=4)
    second = build_welcome_message(morning, conversation_id=4)

    assert first == second
    assert first[0] == "Günaydın."
    assert format_message_time(morning) == morning.astimezone().strftime("%H:%M")
