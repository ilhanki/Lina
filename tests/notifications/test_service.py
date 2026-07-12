from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from lina.notifications.models import ReminderRecurrence, ReminderStatus
from lina.notifications.repository import NotificationRepository
from lina.notifications.service import NotificationService


def test_service_create_edit_complete_delete_and_snooze(tmp_path) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "n.sqlite3"))
    due = datetime.now(timezone.utc) + timedelta(days=2)
    reminder = service.create("Toplantı", due, ReminderRecurrence.DAILY)
    edited = service.update(replace(reminder, title="Güncellendi"))
    assert edited.title == "Güncellendi"
    assert service.snooze(edited, timedelta(minutes=10)).due_at == due + timedelta(minutes=10)
    assert service.snooze(edited, timedelta(hours=1)).due_at == due + timedelta(hours=1)
    assert service.snooze_tomorrow(edited).due_at == due + timedelta(days=1)
    assert service.complete(edited).status is ReminderStatus.COMPLETED
    assert service.delete(edited).status is ReminderStatus.DELETED


def test_service_rejects_past_and_naive_dates(tmp_path) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "n.sqlite3"))
    with pytest.raises(ValueError, match="gelecekte"):
        service.create("Geçmiş", datetime.now(timezone.utc) - timedelta(seconds=1))
    with pytest.raises(ValueError, match="timezone-aware"):
        service.create("Naive", datetime.now())


def test_service_normalizes_repository_failure() -> None:
    class Broken:
        def create(self, _reminder): raise OSError("disk")
    with pytest.raises(RuntimeError, match="kaydedilemedi"):
        NotificationService(Broken()).create("Test", datetime.now(timezone.utc) + timedelta(days=1))
