"""SQLite repository for persistent conversation text and metadata."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from collections.abc import Iterator, Sequence

from lina.conversations.models import (
    CONVERSATION_VIEWS,
    ConversationSearchResult,
    ConversationSession,
    PersistedMessage,
)


class ConversationRepositoryError(RuntimeError):
    """Raised when conversation persistence cannot complete safely."""


class ConversationRepository:
    """Persist conversations using a short-lived SQLite connection per operation."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path.resolve(strict=False)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def init_schema(self) -> None:
        """Create or migrate the conversation schema transactionally."""
        try:
            with self._connection() as connection:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_message_at TEXT
                    )"""
                )
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS conversation_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id INTEGER NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL CHECK (length(trim(content)) > 0),
                        created_at TEXT NOT NULL,
                        sequence_number INTEGER NOT NULL CHECK (sequence_number > 0),
                        message_type TEXT NOT NULL DEFAULT 'text',
                        had_image INTEGER NOT NULL DEFAULT 0 CHECK (had_image IN (0, 1)),
                        image_source TEXT,
                        model_name TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                        UNIQUE (conversation_id, sequence_number),
                        CHECK (image_source IS NULL OR image_source IN ('screen_full', 'screen_region', 'local_image'))
                    )"""
                )
                columns = {
                    str(row[1])
                    for row in connection.execute("PRAGMA table_info(conversations)")
                }
                migrations = {
                    "is_pinned": "ALTER TABLE conversations ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0",
                    "is_archived": "ALTER TABLE conversations ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0",
                    "pinned_at": "ALTER TABLE conversations ADD COLUMN pinned_at TEXT",
                    "archived_at": "ALTER TABLE conversations ADD COLUMN archived_at TEXT",
                }
                for column, statement in migrations.items():
                    if column not in columns:
                        connection.execute(statement)
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversations_activity ON conversations(last_message_at DESC, created_at DESC, id DESC)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversations_visibility ON conversations(is_archived, is_pinned)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON conversation_messages(created_at)"
                )
                connection.execute("PRAGMA user_version = 2")
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to initialize conversation schema") from error

    def create_conversation(
        self,
        title: str = "Yeni Sohbet",
        now: datetime | None = None,
    ) -> ConversationSession:
        timestamp = _ensure_datetime(now)
        normalized_title = _normalize_title(title)
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO conversations (title, created_at, updated_at, last_message_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        normalized_title,
                        _serialize_time(timestamp),
                        _serialize_time(timestamp),
                        _serialize_time(timestamp),
                    ),
                )
                return ConversationSession(
                    id=int(cursor.lastrowid),
                    title=normalized_title,
                    created_at=timestamp,
                    updated_at=timestamp,
                    last_message_at=None,
                )
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to create conversation") from error

    def list_conversations(
        self,
        limit: int = 50,
        view: str = "chats",
    ) -> tuple[ConversationSession, ...]:
        if limit < 1:
            raise ValueError("Conversation limit must be positive")
        if view not in CONVERSATION_VIEWS:
            raise ValueError(f"Unsupported conversation view: {view}")
        visibility = {
            "chats": "is_archived = 0",
            "pinned": "is_archived = 0 AND is_pinned = 1",
            "archive": "is_archived = 1",
        }[view]
        try:
            with self._connection() as connection:
                rows = connection.execute(
                    f"""
                    SELECT id, title, created_at, updated_at, last_message_at,
                           is_pinned, is_archived, pinned_at, archived_at
                    FROM conversations
                    WHERE {visibility}
                    ORDER BY is_pinned DESC,
                             COALESCE(last_message_at, created_at) DESC,
                             created_at DESC, id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return tuple(_row_to_session(row) for row in rows)
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to list conversations") from error

    def get_conversation(self, conversation_id: int) -> ConversationSession | None:
        try:
            with self._connection() as connection:
                row = connection.execute(
                    """SELECT id, title, created_at, updated_at, last_message_at,
                              is_pinned, is_archived, pinned_at, archived_at
                       FROM conversations WHERE id = ?""",
                    (conversation_id,),
                ).fetchone()
            return _row_to_session(row) if row else None
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to load conversation") from error

    def rename_conversation(self, conversation_id: int, title: str, now: datetime | None = None) -> ConversationSession:
        timestamp = _ensure_datetime(now)
        normalized_title = _normalize_title(title)
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                    (normalized_title, _serialize_time(timestamp), conversation_id),
                )
                if cursor.rowcount != 1:
                    raise ConversationRepositoryError("Conversation not found")
            session = self.get_conversation(conversation_id)
            if session is None:
                raise ConversationRepositoryError("Conversation disappeared after rename")
            return session
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to rename conversation") from error

    def delete_conversation(self, conversation_id: int) -> None:
        try:
            with self._connection() as connection:
                connection.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to delete conversation") from error

    def set_pinned(
        self,
        conversation_id: int,
        pinned: bool,
        now: datetime | None = None,
    ) -> ConversationSession:
        """Pin or unpin without changing activity timestamps."""
        timestamp = _serialize_time(_ensure_datetime(now)) if pinned else None
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE conversations SET is_pinned = ?, pinned_at = ? WHERE id = ?",
                    (int(pinned), timestamp, conversation_id),
                )
                if cursor.rowcount != 1:
                    raise ConversationRepositoryError("Conversation not found")
            session = self.get_conversation(conversation_id)
            if session is None:
                raise ConversationRepositoryError("Conversation disappeared after pin update")
            return session
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to update pinned state") from error

    def set_archived(
        self,
        conversation_id: int,
        archived: bool,
        now: datetime | None = None,
    ) -> ConversationSession:
        """Archive or restore without deleting messages or changing activity."""
        timestamp = _serialize_time(_ensure_datetime(now)) if archived else None
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE conversations SET is_archived = ?, archived_at = ? WHERE id = ?",
                    (int(archived), timestamp, conversation_id),
                )
                if cursor.rowcount != 1:
                    raise ConversationRepositoryError("Conversation not found")
            session = self.get_conversation(conversation_id)
            if session is None:
                raise ConversationRepositoryError("Conversation disappeared after archive update")
            return session
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to update archived state") from error

    def search_conversations(
        self,
        query: str,
        view: str = "chats",
        limit: int = 50,
    ) -> tuple[ConversationSearchResult, ...]:
        """Search title and text content with a safe SQLite LIKE fallback."""
        normalized_query = query.strip()
        if len(normalized_query) < 2:
            return ()
        if view not in CONVERSATION_VIEWS:
            raise ValueError(f"Unsupported conversation view: {view}")
        visibility = {
            "chats": "c.is_archived = 0",
            "pinned": "c.is_archived = 0 AND c.is_pinned = 1",
            "archive": "c.is_archived = 1",
        }[view]
        try:
            with self._connection() as connection:
                rows = connection.execute(
                    f"""
                    SELECT c.id, c.title, c.created_at, c.last_message_at,
                           m.id AS message_id, m.role, m.content, m.created_at AS matched_at
                    FROM conversations c
                    LEFT JOIN conversation_messages m ON m.conversation_id = c.id
                    WHERE {visibility}
                    ORDER BY c.is_pinned DESC,
                             COALESCE(c.last_message_at, c.created_at) DESC,
                             c.created_at DESC, c.id DESC, m.sequence_number ASC
                    """,
                ).fetchall()
            results: list[ConversationSearchResult] = []
            seen: set[tuple[int, int | None, str]] = set()
            for row in rows:
                title_match = normalized_query.casefold() in str(row["title"]).casefold()
                message_content = str(row["content"]) if row["content"] else ""
                message_match = normalized_query.casefold() in message_content.casefold()
                if not title_match and not message_match:
                    continue
                match_type = "title" if title_match else "message"
                key = (
                    int(row["id"]),
                    int(row["message_id"]) if row["message_id"] else None,
                    match_type,
                )
                if key in seen:
                    continue
                seen.add(key)
                matched_at = _parse_time(
                    row["matched_at"] or row["last_message_at"] or row["created_at"]
                )
                activity = _parse_time(row["last_message_at"] or row["created_at"])
                snippet_source = str(row["title"]) if title_match else message_content
                results.append(
                    ConversationSearchResult(
                        conversation_id=int(row["id"]),
                        title=str(row["title"]),
                        snippet=_build_snippet(snippet_source, normalized_query),
                        matched_at=matched_at,
                        matched_role=str(row["role"]) if row["role"] else None,
                        match_type=match_type,
                        last_activity_at=activity,
                    )
                )
            return tuple(results[:limit])
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to search conversations") from error

    def clear_messages(self, conversation_id: int, now: datetime | None = None) -> None:
        timestamp = _ensure_datetime(now)
        try:
            with self._connection() as connection:
                connection.execute(
                    "DELETE FROM conversation_messages WHERE conversation_id = ?",
                    (conversation_id,),
                )
                connection.execute(
                    "UPDATE conversations SET title = ?, updated_at = ?, last_message_at = NULL WHERE id = ?",
                    ("Yeni Sohbet", _serialize_time(timestamp), conversation_id),
                )
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to clear conversation") from error

    def add_message(self, message: PersistedMessage) -> PersistedMessage:
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM conversation_messages WHERE conversation_id = ?",
                    (message.conversation_id,),
                )
                sequence = max(message.sequence, int(cursor.fetchone()[0]))
                created_at = _serialize_time(message.created_at)
                inserted = connection.execute(
                    """
                    INSERT INTO conversation_messages
                    (conversation_id, role, content, created_at, sequence_number, message_type, had_image, image_source, model_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message.conversation_id,
                        message.role,
                        message.content.strip(),
                        created_at,
                        sequence,
                        message.message_type,
                        int(message.had_image),
                        message.image_source,
                        message.model_name,
                    ),
                )
                connection.execute(
                    "UPDATE conversations SET updated_at = ?, last_message_at = ? WHERE id = ?",
                    (created_at, created_at, message.conversation_id),
                )
                return PersistedMessage(
                    id=int(inserted.lastrowid),
                    conversation_id=message.conversation_id,
                    role=message.role,
                    content=message.content.strip(),
                    created_at=message.created_at,
                    sequence=sequence,
                    message_type=message.message_type,
                    had_image=message.had_image,
                    image_source=message.image_source,
                    model_name=message.model_name,
                )
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to add conversation message") from error

    def list_messages(self, conversation_id: int, limit: int | None = None) -> tuple[PersistedMessage, ...]:
        if limit is not None and limit < 1:
            raise ValueError("Message limit must be positive")
        try:
            with self._connection() as connection:
                query = """
                    SELECT id, conversation_id, role, content, created_at, sequence_number,
                           message_type, had_image, image_source, model_name
                    FROM conversation_messages
                    WHERE conversation_id = ?
                    ORDER BY sequence_number ASC
                """
                params: Sequence[object] = (conversation_id,)
                if limit is not None:
                    query += " LIMIT ?"
                    params = (conversation_id, limit)
                rows = connection.execute(query, params).fetchall()
            return tuple(_row_to_message(row) for row in rows)
        except sqlite3.Error as error:
            raise ConversationRepositoryError("Unable to list conversation messages") from error

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def _normalize_title(title: str) -> str:
    normalized = " ".join(title.replace("\n", " ").split()).strip()
    if not normalized:
        raise ValueError("Conversation title must not be empty")
    return normalized[:80]


def _ensure_datetime(value: datetime | None) -> datetime:
    timestamp = value or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _serialize_time(value: datetime) -> str:
    return _ensure_datetime(value).isoformat()


def _row_to_session(row: sqlite3.Row) -> ConversationSession:
    return ConversationSession(
        id=int(row["id"]),
        title=str(row["title"]),
        created_at=_parse_time(row["created_at"]),
        updated_at=_parse_time(row["updated_at"]),
        last_message_at=(
            _parse_time(row["last_message_at"])
            if row["last_message_at"]
            else None
        ),
        is_pinned=bool(row["is_pinned"]) if "is_pinned" in row.keys() else False,
        is_archived=bool(row["is_archived"]) if "is_archived" in row.keys() else False,
        pinned_at=(
            _parse_time(row["pinned_at"])
            if "pinned_at" in row.keys() and row["pinned_at"]
            else None
        ),
        archived_at=(
            _parse_time(row["archived_at"])
            if "archived_at" in row.keys() and row["archived_at"]
            else None
        ),
    )


def _row_to_message(row: sqlite3.Row) -> PersistedMessage:
    return PersistedMessage(
        id=int(row["id"]),
        conversation_id=int(row["conversation_id"]),
        role=str(row["role"]),
        content=str(row["content"]),
        created_at=_parse_time(row["created_at"]),
        sequence=int(row["sequence_number"]),
        message_type=str(row["message_type"]),
        had_image=bool(row["had_image"]),
        image_source=str(row["image_source"]) if row["image_source"] else None,
        model_name=str(row["model_name"]) if row["model_name"] else None,
    )


def _parse_time(value: object) -> datetime:
    """Parse stored UTC/legacy timestamps without breaking a whole session."""
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _build_snippet(content: str, query: str, max_length: int = 120) -> str:
    normalized = " ".join(content.split())
    index = normalized.casefold().find(query.casefold())
    if index <= 30:
        return normalized[:max_length]
    start = max(0, index - 30)
    snippet = normalized[start : start + max_length]
    return f"…{snippet}"
