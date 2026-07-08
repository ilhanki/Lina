from datetime import datetime
from pathlib import Path

from lina.memory.models import MemoryRecord, MemoryType
from lina.memory.repository import MemoryRepository


def test_memory_repository_initializes_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.sqlite3"
    repository = MemoryRepository(database_path)

    try:
        assert database_path.exists()
        assert repository.list_active() == ()
    finally:
        repository.close()


def test_memory_repository_adds_and_lists_active_memories(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")

    try:
        saved = repository.add(
            MemoryRecord(
                id=None,
                type=MemoryType.USER_PREFERENCE,
                content="kısa cevapları seviyorum",
                created_at=datetime(2026, 7, 8, 10, 0),
                updated_at=datetime(2026, 7, 8, 10, 0),
                source="explicit_user_request",
            )
        )

        memories = repository.list_active()

        assert saved.id == 1
        assert memories == (saved,)
    finally:
        repository.close()


def test_memory_repository_deactivates_by_content(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")

    try:
        repository.add(_memory("Kısa cevapları seviyorum"))
        repository.add(_memory("Türkçe dokümantasyon istiyorum"))

        count = repository.deactivate_by_content("kısa cevapları seviyorum")

        assert count == 1
        assert [memory.content for memory in repository.list_active()] == [
            "Türkçe dokümantasyon istiyorum"
        ]
    finally:
        repository.close()


def test_memory_repository_clear_deactivates_all_active_memories(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")

    try:
        repository.add(_memory("Birinci kayıt"))
        repository.add(_memory("İkinci kayıt"))

        count = repository.clear()

        assert count == 2
        assert repository.list_active() == ()
    finally:
        repository.close()


def _memory(content: str) -> MemoryRecord:
    now = datetime(2026, 7, 8, 10, 0)
    return MemoryRecord(
        id=None,
        type=MemoryType.CONVERSATION_NOTE,
        content=content,
        created_at=now,
        updated_at=now,
        source="explicit_user_request",
    )
