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


def test_memory_service_does_not_add_duplicate_memory(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        first = service.add_memory(MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum")
        second = service.add_memory(MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum")

        assert first is not None
        assert second is None
        assert [memory.content for memory in service.list_memories()] == [
            "kısa cevapları seviyorum"
        ]
    finally:
        repository.close()


def test_memory_service_treats_case_difference_as_duplicate(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum")
        duplicate = service.add_memory(MemoryType.CONVERSATION_NOTE, "Kısa cevapları seviyorum")

        assert duplicate is None
        assert len(service.list_memories()) == 1
    finally:
        repository.close()


def test_memory_service_treats_whitespace_difference_as_duplicate(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum")
        duplicate = service.add_memory(
            MemoryType.CONVERSATION_NOTE,
            "  kısa   cevapları   seviyorum  ",
        )

        assert duplicate is None
        assert len(service.list_memories()) == 1
    finally:
        repository.close()


def test_memory_service_allows_different_content(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum")
        service.add_memory(MemoryType.CONVERSATION_NOTE, "çok kısa cevapları seviyorum")

        assert [memory.content for memory in service.list_memories()] == [
            "kısa cevapları seviyorum",
            "çok kısa cevapları seviyorum",
        ]
    finally:
        repository.close()


def test_memory_service_allows_same_content_after_forget(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum")
        service.forget_memory_by_content("kısa cevapları seviyorum")

        saved_again = service.add_memory(
            MemoryType.CONVERSATION_NOTE,
            "kısa cevapları seviyorum",
        )

        assert saved_again is not None
        assert [memory.content for memory in service.list_memories()] == [
            "kısa cevapları seviyorum"
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


def test_memory_service_forgets_by_normalized_content(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum")

        count = service.forget_memory_by_content(" Kısa   cevapları   seviyorum ")

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


def test_memory_service_detects_sensitive_content(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)

    try:
        assert service.is_sensitive_content("şifrem 123456")
        assert service.is_sensitive_content("api key abc")
        assert service.is_sensitive_content("kredi kartı 1234")
        assert not service.is_sensitive_content("kısa cevapları seviyorum")
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


def test_memory_service_rejects_blank_and_sensitive_direct_writes(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)
    try:
        import pytest
        with pytest.raises(ValueError, match="must not be empty"):
            service.add_memory(MemoryType.CONVERSATION_NOTE, "   ")
        assert service.add_memory(
            MemoryType.CONVERSATION_NOTE, "private key: very-sensitive"
        ) is None
        assert service.list_memories() == ()
    finally:
        repository.close()


def test_memory_service_can_list_deactivated_records_for_transparency(tmp_path: Path) -> None:
    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    service = MemoryService(repository=repository)
    try:
        service.add_memory(MemoryType.CONVERSATION_NOTE, "Kaldırılacak kayıt")
        service.clear_memories()
        assert service.list_memories() == ()
        all_records = service.list_memories(active_only=False)
        assert len(all_records) == 1
        assert all_records[0].content == "Kaldırılacak kayıt"
        assert all_records[0].is_active is False
    finally:
        repository.close()
