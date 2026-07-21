"""Memory service for Lina."""

from collections.abc import Callable
from datetime import datetime

from lina.memory.models import MemoryRecord, MemoryType
from lina.memory.repository import MemoryRepository


class MemoryService:
    """Coordinates memory operations for application services."""

    def __init__(
        self,
        repository: MemoryRepository,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def add_memory(
        self,
        memory_type: MemoryType,
        content: str,
        source: str = "explicit_user_request",
    ) -> MemoryRecord | None:
        """Add a memory record."""
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("Memory content must not be empty")
        if self.is_sensitive_content(normalized_content):
            return None
        if self._has_active_memory(normalized_content):
            return None

        now = self._clock()
        return self._repository.add(
            MemoryRecord(
                id=None,
                type=memory_type,
                content=normalized_content,
                created_at=now,
                updated_at=now,
                source=source,
            )
        )

    def _has_active_memory(self, content: str) -> bool:
        normalized_content = _normalize_memory_content(content)
        return any(
            _normalize_memory_content(memory.content) == normalized_content
            for memory in self.list_memories(active_only=True)
        )

    def is_sensitive_content(self, content: str) -> bool:
        """Return whether content looks too sensitive to store."""
        normalized_content = _normalize_memory_content(content)
        sensitive_keywords = (
            "şifrem",
            "parolam",
            "password",
            "token",
            "api key",
            "kredi kartı",
            "kart numarası",
            "tc kimlik",
            "tckn",
            "kimlik numaram",
            "adresim",
            "secret",
            "access key",
            "private key",
            "cvv",
            "iban",
        )
        return any(keyword in normalized_content for keyword in sensitive_keywords)

    def list_memories(self, active_only: bool = True) -> tuple[MemoryRecord, ...]:
        """List memories."""
        if active_only:
            return self._repository.list_active()
        return self._repository.list_all()

    def forget_memory_by_content(self, content: str) -> int:
        """Forget active memories matching content."""
        normalized_content = _normalize_memory_content(content)
        removed_count = 0
        for memory in self.list_memories(active_only=True):
            if _normalize_memory_content(memory.content) == normalized_content:
                removed_count += self._repository.deactivate_by_content(memory.content)
        return removed_count

    def clear_memories(self) -> int:
        """Forget all active memories."""
        return self._repository.clear()

    def build_memory_context(
        self,
        max_items: int,
        max_characters: int,
    ) -> str | None:
        """Build a short memory context for prompts."""
        memories = self.list_memories(active_only=True)[:max_items]
        if not memories:
            return None

        lines = ["Hatırlanan kullanıcı bilgileri:"]
        for memory in memories:
            candidate = f"- {memory.content}"
            next_text = "\n".join([*lines, candidate])
            if len(next_text) > max_characters:
                break
            lines.append(candidate)

        if len(lines) == 1:
            return None

        return "\n".join(lines)

    def close(self) -> None:
        """Close the underlying repository."""
        self._repository.close()


def _normalize_memory_content(content: str) -> str:
    return " ".join(content.strip().casefold().split())
