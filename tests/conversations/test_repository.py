"""Tests for the isolated conversation SQLite repository."""

from datetime import datetime, timezone
import sqlite3

import pytest

from lina.conversations.models import PersistedMessage
from lina.conversations.repository import ConversationRepository


def test_repository_creates_idempotent_schema_and_enables_foreign_keys(tmp_path) -> None:
    path = tmp_path / "conversations.sqlite3"
    repository = ConversationRepository(path)
    repository.init_schema()

    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(conversation_messages)")
        }
        assert "conversations" in tables
        assert "conversation_messages" in tables
        assert "image_bytes" not in columns
        assert "base64" not in columns
        assert "file_path" not in columns
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 0

    with repository._connection() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_repository_supports_session_crud_and_cascade_delete(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    session = repository.create_conversation(now=now)
    message = repository.add_message(
        PersistedMessage(
            id=None,
            conversation_id=session.id or 0,
            role="user",
            content="Merhaba",
            created_at=now,
            sequence=1,
        )
    )

    assert message.id is not None
    assert repository.list_conversations()[0].last_message_at == now
    renamed = repository.rename_conversation(session.id or 0, "İlk Sohbet", now=now)
    assert renamed.title == "İlk Sohbet"
    assert len(repository.list_messages(session.id or 0)) == 1

    repository.delete_conversation(session.id or 0)

    assert repository.get_conversation(session.id or 0) is None
    assert repository.list_messages(session.id or 0) == ()


def test_repository_orders_sessions_by_recent_activity(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    first = repository.create_conversation(
        now=datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    second = repository.create_conversation(
        title="İkinci sohbet",
        now=datetime(2026, 1, 2, tzinfo=timezone.utc)
    )
    repository.add_message(
        PersistedMessage(
            id=None,
            conversation_id=first.id or 0,
            role="user",
            content="Son aktivite",
            created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
            sequence=1,
        )
    )

    assert [session.id for session in repository.list_conversations()] == [
        first.id,
        second.id,
    ]


def test_repository_handles_legacy_naive_and_malformed_timestamps(tmp_path) -> None:
    path = tmp_path / "conversations.sqlite3"
    repository = ConversationRepository(path)
    session = repository.create_conversation()
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE conversations SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-01-01T12:00:00", "not-a-timestamp", session.id),
        )

    loaded = repository.get_conversation(session.id or 0)

    assert loaded is not None
    assert loaded.created_at.tzinfo is not None
    assert loaded.updated_at.tzinfo is not None


def test_repository_hides_legacy_empty_default_conversations(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    session = repository.create_conversation()

    assert repository.list_conversations() == ()
    assert repository.search_conversations("Yeni") == ()
    assert repository.get_conversation(session.id or 0) is not None


def test_repository_migrates_existing_schema_without_losing_data(tmp_path) -> None:
    path = tmp_path / "conversations.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_message_at TEXT
            );
            CREATE TABLE conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                message_type TEXT NOT NULL DEFAULT 'text',
                had_image INTEGER NOT NULL DEFAULT 0,
                image_source TEXT,
                model_name TEXT
            );
            INSERT INTO conversations (title, created_at, updated_at)
            VALUES ('Eski Sohbet', '2026-01-01T12:00:00+00:00', '2026-01-01T12:00:00+00:00');
            INSERT INTO conversation_messages
            (conversation_id, role, content, created_at, sequence_number)
            VALUES (1, 'user', 'Korunacak mesaj', '2026-01-01T12:01:00+00:00', 1);
            """
        )

    repository = ConversationRepository(path)

    session = repository.get_conversation(1)
    messages = repository.list_messages(1)
    assert session is not None
    assert session.is_pinned is False
    assert session.is_archived is False
    assert messages[0].content == "Korunacak mesaj"
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2


def test_repository_searches_title_and_message_with_safe_like_queries(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    title_session = repository.create_conversation("Türkçe Vision Notları")
    message_session = repository.create_conversation("Başka Sohbet")
    for session, content in (
        (title_session, "Görsel modeli hazır."),
        (message_session, "Ekran görüntüsünü incelemeliyiz."),
    ):
        repository.add_message(
            PersistedMessage(
                id=None,
                conversation_id=session.id or 0,
                role="user",
                content=content,
                created_at=datetime.now(timezone.utc),
                sequence=1,
            )
        )

    title_results = repository.search_conversations("vision")
    message_results = repository.search_conversations("GÖRÜNTÜ")
    wildcard_results = repository.search_conversations("%_")

    assert title_results[0].conversation_id == title_session.id
    assert title_results[0].match_type == "title"
    assert message_results[0].conversation_id == message_session.id
    assert wildcard_results == ()


def test_repository_pin_archive_filters_preserve_activity_timestamp(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    session = repository.create_conversation(
        now=datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    before = repository.get_conversation(session.id or 0)

    pinned = repository.set_pinned(session.id or 0, True)
    archived = repository.set_archived(session.id or 0, True)

    assert pinned.is_pinned is True
    assert archived.is_archived is True
    assert archived.last_message_at == before.last_message_at
    assert repository.list_conversations(view="chats") == ()
    assert repository.list_conversations(view="pinned") == ()
    assert repository.list_conversations(view="archive")[0].id == session.id


def test_repository_validates_message_metadata_and_rejects_empty_content(tmp_path) -> None:
    repository = ConversationRepository(tmp_path / "conversations.sqlite3")
    session = repository.create_conversation()

    with pytest.raises(ValueError):
        repository.add_message(
            PersistedMessage(
                id=None,
                conversation_id=session.id or 0,
                role="assistant",
                content=" ",
                created_at=datetime.now(timezone.utc),
                sequence=1,
            )
        )

    with pytest.raises(ValueError):
        PersistedMessage(
            id=None,
            conversation_id=session.id or 0,
            role="user",
            content="Görsel",
            created_at=datetime.now(timezone.utc),
            sequence=1,
            image_source="C:/secret/image.png",
            had_image=True,
        )


def test_repository_persists_safe_visual_metadata_only(tmp_path) -> None:
    path = tmp_path / "conversations.sqlite3"
    repository = ConversationRepository(path)
    session = repository.create_conversation()
    repository.add_message(
        PersistedMessage(
            id=None,
            conversation_id=session.id or 0,
            role="user",
            content="Bu görseli açıkla",
            created_at=datetime.now(timezone.utc),
            sequence=1,
            had_image=True,
            image_source="screen_region",
        )
    )

    with sqlite3.connect(path) as connection:
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'conversation_messages'"
        ).fetchone()[0]
        assert "BLOB" not in sql.upper()
        assert "BASE64" not in sql.upper()
        assert "PATH" not in sql.upper()
        row = connection.execute(
            "SELECT had_image, image_source FROM conversation_messages"
        ).fetchone()
        assert row == (1, "screen_region")
