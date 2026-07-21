"""Tests for conversation history application behavior."""

from datetime import datetime, timezone

import pytest

from lina.conversations.repository import ConversationRepository
from lina.conversations.repository import ConversationRepositoryError
from lina.conversations.service import ConversationHistoryService


def test_service_restores_bounded_history_and_ignores_greeting_title(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository, model_history_messages=1)
    service.start()
    assert service.active_session is None
    service.record_user_message("selam naber")
    service.record_assistant_message("Merhaba İlhan.")
    assert service.active_session is not None
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

    assert service.active_session is not None
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


def test_service_search_pin_archive_and_grouping(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository)
    service.start()
    service.record_user_message("Vision notlarını ara")
    service.record_assistant_message("Vision sonucu")
    assert service.active_session is not None
    first_id = service.active_session.id or 0
    service.new_session()
    service.record_user_message("İkinci sohbet")
    assert service.active_session is not None
    second_id = service.active_session.id or 0

    assert service.search("vision")[0].conversation_id == first_id
    assert service.set_pinned(first_id, True).is_pinned is True
    assert service.list_sessions(view="pinned")[0].id == first_id
    assert service.set_archived(second_id, False) is False
    assert service.group_sessions(
        service.list_sessions(),
        now=datetime.now(timezone.utc),
    )[0][0] == "Bugün"


def test_new_session_and_start_do_not_create_empty_rows(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository)

    service.start()
    service.new_session()
    service.new_session()

    assert service.active_session is None
    assert repository.list_conversations() == ()


def test_first_user_message_materializes_draft_atomically(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository)
    service.start()

    service.record_user_message("Lina projesini planla")

    assert service.active_session is not None
    sessions = repository.list_conversations()
    assert len(sessions) == 1
    assert sessions[0].id == service.active_session.id
    assert len(repository.list_messages(sessions[0].id or 0)) == 1


def test_deleting_last_conversation_returns_to_draft_without_new_row(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository)
    service.start()
    service.record_user_message("Silinecek sohbet")
    conversation_id = service.active_session.id or 0

    assert service.delete(conversation_id) is True
    assert service.active_session is None
    assert repository.list_conversations() == ()


def test_deleting_active_conversation_returns_to_empty_draft(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository)
    service.start()
    service.record_user_message("İlk sohbet")
    first_id = service.active_session.id or 0
    service.new_session()
    service.record_user_message("İkinci sohbet")
    second_id = service.active_session.id or 0

    service.load_session(first_id)
    assert service.delete(first_id) is True

    assert service.active_session is None
    assert repository.get_conversation(second_id) is not None


def test_missing_conversation_does_not_disable_other_persisted_sessions(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    service = ConversationHistoryService(repository)
    service.start()
    service.record_user_message("Korunacak sohbet")
    valid_id = service.active_session.id or 0

    with pytest.raises(ConversationRepositoryError, match="not found"):
        service.load_session(valid_id + 10_000)

    assert service.persistence_available is True
    loaded = service.load_session(valid_id)
    assert loaded.id == valid_id
    assert service.loaded_messages()[0].content == "Korunacak sohbet"
