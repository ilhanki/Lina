"""Tests for conversation history application behavior."""

from datetime import datetime, timezone

from lina.conversations.repository import ConversationRepository
from lina.conversations.service import ConversationHistoryService


def test_service_restores_bounded_history_and_ignores_greeting_title(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository, model_history_messages=1)
    service.start()
    service.record_user_message("selam naber")
    service.record_assistant_message("Merhaba İlhan.")
    assert service.active_session.title == "Yeni Sohbet"
    service.record_user_message("Lina projesi için bir plan yap")
    service.record_assistant_message("Elbette.")

    restored = ConversationHistoryService(repository, model_history_messages=1)
    restored.load_session(service.active_session.id or 0)

    assert restored.active_session.title == "Lina projesi için bir plan yap"
    assert restored.model_history()[0].user_message == "Lina projesi için bir plan yap"


def test_service_keeps_vision_as_metadata_without_raw_image(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository)
    service.start()
    service.record_user_message(
        "Bu görseli açıkla", had_image=True, image_source="local_image"
    )
    service.record_assistant_message("Görselde bir pencere var.")

    messages = repository.list_messages(service.active_session.id or 0)

    assert messages[0].had_image is True
    assert messages[0].image_source == "local_image"
    assert all(not hasattr(message, "image_bytes") for message in messages)


def test_disabled_service_falls_back_to_in_memory_session(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "unused.sqlite3")
    service = ConversationHistoryService(repository, enabled=False)
    service.start()
    service.record_user_message("Sadece bu oturum")
    service.record_assistant_message("Tamam.")

    assert service.persistence_available is False
    assert len(service.model_history()) == 1
    assert repository.list_conversations() == ()
