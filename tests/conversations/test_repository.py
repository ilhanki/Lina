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
