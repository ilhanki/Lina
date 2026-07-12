"""Application service for persistent conversation history."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from lina.brain.prompt_builder import ConversationTurn
from lina.conversations.models import ConversationSearchResult, ConversationSession, PersistedMessage
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

    def start(self) -> ConversationSession | None:
        """Open the newest session or keep an ephemeral draft session."""
        if self._enabled and self._persistence_available:
            try:
                sessions = self._repository.list_conversations()  # type: ignore[union-attr]
                if sessions:
                    return self.load_session(sessions[0].id or 0)
            except ConversationRepositoryError:
                self._persistence_available = False
        return self.new_session()

    def new_session(self) -> None:
        """Start an isolated draft without writing an empty database row."""
        self._memory_messages.clear()
        self._active_session = None

    def list_sessions(
        self,
        limit: int = 50,
        view: str = "chats",
    ) -> tuple[ConversationSession, ...]:
        if not self._enabled or not self._persistence_available:
            return ()
        try:
            return self._repository.list_conversations(limit, view=view)  # type: ignore[union-attr]
        except ConversationRepositoryError:
            self._persistence_available = False
            return ()

    def search(
        self,
        query: str,
        view: str = "chats",
        limit: int = 50,
    ) -> tuple[ConversationSearchResult, ...]:
        """Search only persisted title and message text."""
        if not self._enabled or not self._persistence_available:
            return ()
        try:
            return self._repository.search_conversations(  # type: ignore[union-attr]
                query, view=view, limit=limit
            )
        except ConversationRepositoryError:
            self._persistence_available = False
            return ()

    def set_pinned(self, conversation_id: int, pinned: bool) -> ConversationSession | None:
        """Update pin state without changing activity ordering."""
        if not self._enabled or not self._persistence_available:
            return None
        try:
            return self._repository.set_pinned(  # type: ignore[union-attr]
                conversation_id, pinned, now=self._clock()
            )
        except ConversationRepositoryError:
            self._persistence_available = False
            return None

    def set_archived(self, conversation_id: int, archived: bool) -> bool:
        """Archive/restore a session and safely leave an archived active session."""
        if not self._enabled or not self._persistence_available:
            return False
        try:
            self._repository.set_archived(  # type: ignore[union-attr]
                conversation_id, archived, now=self._clock()
            )
        except ConversationRepositoryError:
            self._persistence_available = False
            return False
        was_active = bool(
            archived
            and self._active_session is not None
            and self._active_session.id == conversation_id
        )
        if was_active:
            self._activate_latest_or_draft()
        return was_active

    @staticmethod
    def group_sessions(
        sessions: tuple[ConversationSession, ...],
        now: datetime | None = None,
    ) -> tuple[tuple[str, tuple[ConversationSession, ...]], ...]:
        """Group sessions by local calendar activity without empty groups."""
        current = (now or datetime.now(timezone.utc)).astimezone()
        buckets: dict[str, list[ConversationSession]] = {}
        for session in sessions:
            activity = (session.last_message_at or session.created_at).astimezone()
            age = (current.date() - activity.date()).days
            if age == 0:
                label = "Bugün"
            elif age == 1:
                label = "Dün"
            elif age < 7:
                label = "Son 7 Gün"
            elif age < 30:
                label = "Son 30 Gün"
            else:
                label = "Daha Eski"
            buckets.setdefault(label, []).append(session)
        order = ("Bugün", "Dün", "Son 7 Gün", "Son 30 Gün", "Daha Eski")
        return tuple(
            (label, tuple(buckets[label]))
            for label in order
            if label in buckets
        )

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
        if self._active_session is None and self._enabled and self._persistence_available:
            self._materialize_first_message(
                content=content,
                had_image=had_image,
                image_source=image_source,
                created_at=created_at,
            )
            return
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
            raise ConversationRepositoryError("No active persisted conversation")
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

    def _materialize_first_message(
        self,
        content: str,
        had_image: bool,
        image_source: str | None,
        created_at: datetime | None,
    ) -> None:
        message = PersistedMessage(
            id=None,
            conversation_id=0,
            role="user",
            content=content,
            created_at=created_at or self._clock(),
            sequence=1,
            had_image=had_image,
            image_source=image_source,
        )
        session, persisted = self._repository.create_conversation_with_first_message(  # type: ignore[union-attr]
            title=_derive_title(content),
            message=message,
        )
        self._active_session = session
        self._memory_messages = [persisted]

    def _activate_latest_or_draft(self) -> None:
        sessions = self.list_sessions(view="chats")
        if sessions:
            self.load_session(sessions[0].id or 0)
        else:
            self.new_session()

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
            now = created_at or self._clock()
            message = PersistedMessage(
                id=None,
                conversation_id=0,
                role=role,
                content=content,
                created_at=now,
                sequence=len(self._memory_messages) + 1,
                had_image=had_image,
                image_source=image_source,
                model_name=model_name,
            )
            self._memory_messages.append(message)
            return
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
