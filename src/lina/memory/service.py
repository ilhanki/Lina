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
    ) -> MemoryRecord:
        """Add a memory record."""
        normalized_content = content.strip()
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

    def list_memories(self, active_only: bool = True) -> tuple[MemoryRecord, ...]:
        """List memories."""
        if active_only:
            return self._repository.list_active()
        return self._repository.list_active()

    def forget_memory_by_content(self, content: str) -> int:
        """Forget active memories matching content."""
        return self._repository.deactivate_by_content(content)

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
