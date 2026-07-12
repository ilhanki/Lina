"""Application service for persistent conversation history."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from lina.brain.prompt_builder import ConversationTurn
from lina.conversations.models import ConversationSession, PersistedMessage
from lina.conversations.repository import ConversationRepository, ConversationRepositoryError


class ConversationHistoryService:
    """Coordinate session state without exposing repository details to the GUI."""

    def __init__(
        self,
        repository: ConversationRepository | None,
        enabled: bool = True,
        max_loaded_messages: int = 500,
        model_history_messages: int = 30,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if max_loaded_messages < 1 or model_history_messages < 1:
            raise ValueError("Conversation history limits must be positive")
        self._repository = repository
        self._enabled = enabled and repository is not None
        self._max_loaded_messages = max_loaded_messages
        self._model_history_messages = model_history_messages
        self._clock = clock
        self._active_session: ConversationSession | None = None
        self._memory_messages: list[PersistedMessage] = []
        self._persistence_available = self._enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def persistence_available(self) -> bool:
        return self._persistence_available

    @property
    def active_session(self) -> ConversationSession | None:
        return self._active_session

    def start(self) -> ConversationSession:
        """Open the newest session or create the first local session."""
        if self._enabled and self._persistence_available:
            try:
                sessions = self._repository.list_conversations()  # type: ignore[union-attr]
                if sessions:
                    return self.load_session(sessions[0].id or 0)
            except ConversationRepositoryError:
                self._persistence_available = False
        return self.new_session()

    def new_session(self) -> ConversationSession:
        """Create an isolated session and make it active."""
        self._memory_messages.clear()
        if self._enabled and self._persistence_available:
            try:
                self._active_session = self._repository.create_conversation(  # type: ignore[union-attr]
                    now=self._clock()
                )
                return self._active_session
            except ConversationRepositoryError:
                self._persistence_available = False
        now = self._clock()
        self._active_session = ConversationSession(None, "Yeni Sohbet", now, now, None)
        return self._active_session

    def list_sessions(self, limit: int = 50) -> tuple[ConversationSession, ...]:
        if not self._enabled or not self._persistence_available:
            return (self._active_session,) if self._active_session else ()
        try:
            return self._repository.list_conversations(limit)  # type: ignore[union-attr]
        except ConversationRepositoryError:
            self._persistence_available = False
            return ()

    def load_session(self, conversation_id: int) -> ConversationSession:
        if not self._enabled or not self._persistence_available:
            raise ConversationRepositoryError("Conversation persistence is unavailable")
        try:
            session = self._repository.get_conversation(conversation_id)  # type: ignore[union-attr]
            if session is None:
                raise ConversationRepositoryError("Conversation not found")
            self._active_session = session
            self._memory_messages = list(
                self._repository.list_messages(  # type: ignore[union-attr]
                    conversation_id, limit=self._max_loaded_messages
                )
            )
            return session
        except ConversationRepositoryError:
            self._persistence_available = False
            raise

    def model_history(self) -> tuple[ConversationTurn, ...]:
        """Return only bounded text exchanges for Brain context."""
        turns: list[ConversationTurn] = []
        pending_user: str | None = None
        for message in self._memory_messages:
            if message.role == "user":
                pending_user = message.content
            elif message.role == "assistant" and pending_user is not None:
                turns.append(ConversationTurn(pending_user, message.content))
                pending_user = None
        return tuple(turns[-self._model_history_messages :])

    def loaded_messages(self) -> tuple[PersistedMessage, ...]:
        """Return the bounded messages loaded for the active session."""
        return tuple(self._memory_messages)

    def record_user_message(
        self,
        content: str,
        had_image: bool = False,
        image_source: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self._record_message(
            role="user",
            content=content,
            had_image=had_image,
            image_source=image_source,
            created_at=created_at,
        )
        self._maybe_update_title(content)

    def record_assistant_message(
        self,
        content: str,
        model_name: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        if not content.strip():
            return
        self._record_message(
            role="assistant",
            content=content,
            model_name=model_name,
            created_at=created_at,
        )

    def rename(self, title: str) -> ConversationSession:
        if self._active_session is None:
            self.new_session()
        if self._enabled and self._persistence_available and self._active_session.id is not None:
            try:
                self._active_session = self._repository.rename_conversation(  # type: ignore[union-attr]
                    self._active_session.id, title, now=self._clock()
                )
                return self._active_session
            except ConversationRepositoryError:
                self._persistence_available = False
        normalized = _normalize_title(title)
        session = self._active_session
        self._active_session = ConversationSession(
            session.id, normalized, session.created_at, self._clock(), session.last_message_at
        )
        return self._active_session

    def rename_session(self, conversation_id: int, title: str) -> ConversationSession:
        """Rename an active or inactive persisted session through one API."""
        if self._active_session is not None and self._active_session.id == conversation_id:
            return self.rename(title)
        if not self._enabled or not self._persistence_available:
            raise ConversationRepositoryError("Conversation persistence is unavailable")
        try:
            return self._repository.rename_conversation(  # type: ignore[union-attr]
                conversation_id, title, now=self._clock()
            )
        except ConversationRepositoryError:
            self._persistence_available = False
            raise

    def clear(self) -> None:
        self._memory_messages.clear()
        if self._active_session is None:
            self.new_session()
            return
        if self._enabled and self._persistence_available and self._active_session.id is not None:
            try:
                self._repository.clear_messages(self._active_session.id, now=self._clock())  # type: ignore[union-attr]
            except ConversationRepositoryError:
                self._persistence_available = False
        self._active_session = ConversationSession(
            self._active_session.id,
            "Yeni Sohbet",
            self._active_session.created_at,
            self._clock(),
            None,
        )

    def delete(self, conversation_id: int) -> bool:
        was_active = bool(self._active_session and self._active_session.id == conversation_id)
        if self._enabled and self._persistence_available:
            try:
                self._repository.delete_conversation(conversation_id)  # type: ignore[union-attr]
            except ConversationRepositoryError:
                self._persistence_available = False
                return False
        if was_active:
            self.new_session()
        return was_active

    def _record_message(
        self,
        role: str,
        content: str,
        had_image: bool = False,
        image_source: str | None = None,
        model_name: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        if self._active_session is None:
            self.new_session()
        session_id = self._active_session.id or 0
        message = PersistedMessage(
            id=None,
            conversation_id=session_id,
            role=role,
            content=content,
            created_at=created_at or self._clock(),
            sequence=len(self._memory_messages) + 1,
            had_image=had_image,
            image_source=image_source,
            model_name=model_name,
        )
        self._memory_messages.append(message)
        self._memory_messages = self._memory_messages[-self._max_loaded_messages :]
        session = self._active_session
        self._active_session = ConversationSession(
            session.id,
            session.title,
            session.created_at,
            message.created_at,
            message.created_at,
        )
        if self._enabled and self._persistence_available and self._active_session.id is not None:
            try:
                persisted = self._repository.add_message(message)  # type: ignore[union-attr]
                self._memory_messages[-1] = persisted
            except ConversationRepositoryError:
                self._persistence_available = False

    def _maybe_update_title(self, content: str) -> None:
        if self._active_session is None or self._active_session.title != "Yeni Sohbet":
            return
        title = _derive_title(content)
        if title != "Yeni Sohbet":
            self.rename(title)


def _normalize_title(title: str) -> str:
    normalized = " ".join(title.replace("\n", " ").split()).strip()
    if not normalized:
        raise ValueError("Conversation title must not be empty")
    return normalized[:80]


def _derive_title(message: str) -> str:
    normalized = _normalize_title(message)
    if normalized.casefold() in {"selam", "merhaba", "naber", "nasılsın", "selam naber"}:
        return "Yeni Sohbet"
    return normalized[:44].rstrip() + ("..." if len(normalized) > 44 else "")
