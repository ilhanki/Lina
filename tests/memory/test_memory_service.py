from datetime import datetime
from pathlib import Path

from lina.memory.models import MemoryType
from lina.memory.repository import MemoryRepository
from lina.memory.service import MemoryService


def test_memory_service_adds_memory(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(
        repository=repository,
        clock=lambda: datetime(2026, 7, 8, 11, 0),
    )

    try:
        memory = service.add_memory(
            MemoryType.USER_PREFERENCE,
            " kısa cevapları seviyorum ",
        )

        assert memory.content == "kısa cevapları seviyorum"
        assert memory.type is MemoryType.USER_PREFERENCE
        assert memory.source == "explicit_user_request"
        assert memory.created_at == datetime(2026, 7, 8, 11, 0)
    finally:
        repository.close()


def test_memory_service_lists_memories(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "Birinci kayıt")
        service.add_memory(MemoryType.PROJECT_DECISION, "İkinci kayıt")

        memories = service.list_memories()

        assert [memory.content for memory in memories] == [
            "Birinci kayıt",
            "İkinci kayıt",
        ]
    finally:
        repository.close()


def test_memory_service_forgets_by_content(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum")

        count = service.forget_memory_by_content("kısa cevapları seviyorum")

        assert count == 1
        assert service.list_memories() == ()
    finally:
        repository.close()


def test_memory_service_clears_memories(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "Birinci kayıt")
        service.add_memory(MemoryType.CONVERSATION_NOTE, "İkinci kayıt")

        count = service.clear_memories()

        assert count == 2
        assert service.list_memories() == ()
    finally:
        repository.close()


def test_memory_service_builds_limited_memory_context(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.USER_PREFERENCE, "kısa cevapları seviyorum")
        service.add_memory(MemoryType.PROJECT_DECISION, "Türkçe dokümantasyon tercih ediliyor")
        service.add_memory(MemoryType.CONVERSATION_NOTE, "Üçüncü kayıt")

        context = service.build_memory_context(max_items=2, max_characters=120)

        assert context == (
            "Hatırlanan kullanıcı bilgileri:\n"
            "- kısa cevapları seviyorum\n"
            "- Türkçe dokümantasyon tercih ediliyor"
        )
    finally:
        repository.close()


def test_memory_service_returns_no_context_when_empty(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        assert service.build_memory_context(max_items=8, max_characters=1200) is None
    finally:
        repository.close()
