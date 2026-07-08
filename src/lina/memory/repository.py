"""SQLite-backed memory repository for Lina."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3
from threading import Lock

from lina.memory.models import MemoryRecord, MemoryType


class MemoryRepository:
    """Persists memory records in a local SQLite database."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._connection = sqlite3.connect(
            self._database_path,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self) -> None:
        """Create the memory table when it does not exist."""
        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    is_active INTEGER NOT NULL
                )
                """
            )
            self._connection.commit()

    def add(self, memory: MemoryRecord) -> MemoryRecord:
        """Persist a memory record and return it with an id."""
        with self._lock:
            cursor = self._connection.execute(
                """
                INSERT INTO memories (type, content, created_at, updated_at, source, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.type.value,
                    memory.content,
                    memory.created_at.isoformat(),
                    memory.updated_at.isoformat(),
                    memory.source,
                    int(memory.is_active),
                ),
            )
            self._connection.commit()
            return MemoryRecord(
                id=int(cursor.lastrowid),
                type=memory.type,
                content=memory.content,
                created_at=memory.created_at,
                updated_at=memory.updated_at,
                source=memory.source,
                is_active=memory.is_active,
            )

    def list_active(self) -> tuple[MemoryRecord, ...]:
        """Return active memory records ordered by creation time."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT id, type, content, created_at, updated_at, source, is_active
                FROM memories
                WHERE is_active = 1
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return tuple(_row_to_memory(row) for row in rows)

    def deactivate_by_content(self, content: str) -> int:
        """Deactivate active memories matching content exactly."""
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self._connection.execute(
                """
                UPDATE memories
                SET is_active = 0, updated_at = ?
                WHERE is_active = 1 AND lower(content) = lower(?)
                """,
                (now, content.strip()),
            )
            self._connection.commit()
            return cursor.rowcount

    def clear(self) -> int:
        """Deactivate all active memory records."""
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self._connection.execute(
                """
                UPDATE memories
                SET is_active = 0, updated_at = ?
                WHERE is_active = 1
                """,
                (now,),
            )
            self._connection.commit()
            return cursor.rowcount

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with self._lock:
            self._connection.close()


def _row_to_memory(row: sqlite3.Row) -> MemoryRecord:
    return MemoryRecord(
        id=int(row["id"]),
        type=MemoryType(row["type"]),
        content=str(row["content"]),
        created_at=datetime.fromisoformat(str(row["created_at"])),
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
        source=str(row["source"]),
        is_active=bool(row["is_active"]),
    )
