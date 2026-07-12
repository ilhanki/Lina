"""Application service for user preference lifecycle."""

from __future__ import annotations

from collections.abc import Callable

from lina.settings.models import UserSettings
from lina.settings.repository import UserSettingsRepository


SettingsListener = Callable[[UserSettings], None]


class UserSettingsService:
    """Keep current user preferences and notify interested application code."""

    def __init__(self, repository: UserSettingsRepository) -> None:
        self._repository = repository
        self._current = repository.load()
        self._listeners: list[SettingsListener] = []

    @property
    def current(self) -> UserSettings:
        return self._current

    def subscribe(self, listener: SettingsListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def update(self, settings: UserSettings, persist: bool = True) -> bool:
        if settings == self._current:
            return False
        if persist:
            self._repository.save(settings)
        self._current = settings
        for listener in tuple(self._listeners):
            listener(settings)
        return True

    def reset(self, persist: bool = True) -> bool:
        return self.update(UserSettings(), persist=persist)
