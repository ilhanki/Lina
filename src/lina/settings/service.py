"""Application service for user preference lifecycle."""

from __future__ import annotations

from collections.abc import Callable
import logging
import threading

from lina.settings.models import UserSettings
from lina.settings.repository import UserSettingsRepository


SettingsListener = Callable[[UserSettings], None]
_logger = logging.getLogger("lina.settings")


class UserSettingsService:
    """Keep current user preferences and notify interested application code."""

    def __init__(self, repository: UserSettingsRepository) -> None:
        self._repository = repository
        self._current = repository.load()
        self._listeners: list[SettingsListener] = []
        self._lock = threading.RLock()

    @property
    def current(self) -> UserSettings:
        return self._current

    def subscribe(self, listener: SettingsListener) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def unsubscribe(self, listener: SettingsListener) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def update(self, settings: UserSettings, persist: bool = True) -> bool:
        if not isinstance(settings, UserSettings):
            raise TypeError("settings must be a UserSettings value")
        with self._lock:
            if settings == self._current:
                return False
            if persist:
                self._repository.save(settings)
            self._current = settings
            listeners = tuple(self._listeners)
        for listener in listeners:
            try:
                listener(settings)
            except Exception:
                _logger.exception("settings_listener_failed")
        return True

    def reset(self, persist: bool = True) -> bool:
        return self.update(UserSettings(), persist=persist)
