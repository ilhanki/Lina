"""Threaded reminder scheduler with injectable clock and presenter."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Event, Lock, Thread
from typing import Protocol

from lina.notifications.models import NotificationEvent, Reminder, ReminderStatus
from lina.notifications.repository import NotificationRepository
from lina.notifications.service import next_occurrence


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FakeClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value

    def advance(self, **kwargs: int) -> None:
        from datetime import timedelta
        self.value += timedelta(**kwargs)


class NotificationScheduler:
    def __init__(self, repository: NotificationRepository, presenter, clock: Clock | None = None, interval_seconds: float = 30.0, settings_provider=None) -> None:
        self._repository = repository
        self._presenter = presenter
        self._clock = clock or SystemClock()
        self._interval = interval_seconds
        self._stop = Event()
        self._lock = Lock()
        self._thread: Thread | None = None
        self._notified: set[int] = set()
        self._settings_provider = settings_provider

    def check_once(self) -> tuple[Reminder, ...]:
        return self._process_due(missed=False)

    def process_missed(self) -> tuple[Reminder, ...]:
        return self._process_due(missed=True)

    def _process_due(self, missed: bool) -> tuple[Reminder, ...]:
        if self._stop.is_set():
            return ()
        settings = self._settings_provider() if self._settings_provider else None
        if settings is not None and not settings.reminders_enabled:
            return ()
        now = self._clock.now()
        try:
            due = tuple(item for item in self._repository.list() if item.status is ReminderStatus.ACTIVE and item.due_at <= now)
        except Exception:
            return ()
        fired: list[Reminder] = []
        events: list[tuple[Reminder, NotificationEvent]] = []
        for reminder in due:
            try:
                event = self._repository.create_event(reminder, reminder.due_at)
            except Exception:
                continue
            if event is None:
                continue
            fired.append(reminder)
            events.append((reminder, event))
        allow_desktop = settings is None or settings.desktop_notifications_enabled
        allow_missed = not missed or settings is None or settings.show_missed_reminders
        collapsed = missed and len(events) >= 4
        if collapsed and allow_desktop and allow_missed:
            summary = NotificationEvent(None, 0, f"{len(events)} kaçırılmış hatırlatıcın var", now)
            try:
                self._presenter(summary)
            except Exception:
                pass
        for reminder, event in events:
            status = "suppressed"
            try:
                if allow_desktop and allow_missed and not collapsed:
                    status = self._presenter(event)
            except Exception:
                status = "failed"
            try:
                self._repository.update_delivery_status(event.id or 0, status)
            except Exception:
                pass
            next_due = next_occurrence(reminder)
            if next_due is None:
                try: self._repository.update(replace(reminder, last_notified_at=now))
                except Exception: pass
            else:
                while next_due <= now:
                    next_due += timedelta(days=1 if reminder.recurrence.value == "daily" else 7)
                try: self._repository.update(replace(reminder, due_at=next_due, last_notified_at=now))
                except Exception: pass
        return tuple(fired)

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = Thread(target=self._run, name="lina-notification-scheduler", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        self._thread = None

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            self.check_once()
