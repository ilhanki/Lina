from datetime import datetime, timedelta, timezone

from lina.brain.routing.classifier import DeterministicIntentClassifier
from lina.brain.routing.models import IntentRequest, IntentType, RequestContext
from lina.brain.routing.router import IntentRouter
from lina.brain.routing.tools import build_safe_tool_registry
from lina.files.file_access_service import FileAccessService
from lina.memory.repository import MemoryRepository
from lina.memory.service import MemoryService
from lina.notifications.repository import NotificationRepository
from lina.notifications.service import NotificationService


def _services(tmp_path):
    (tmp_path / "README.md").write_text("Güvenli içerik", encoding="utf-8")
    reminders = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    files = FileAccessService(tmp_path, allowed_paths=("README.md",), aliases={"readme": "README.md"})
    memory = MemoryService(MemoryRepository(tmp_path / "memory.sqlite3"))
    return reminders, files, memory


def test_registry_contains_only_supported_safe_tools(tmp_path) -> None:
    registry = build_safe_tool_registry(*_services(tmp_path))
    assert registry.names() == (
        "files.read", "memory.recall", "memory.store", "reminder.create", "reminder.list",
        "vision.image", "vision.region", "vision.screen",
    )
    assert not any(term in " ".join(registry.names()) for term in ("shell", "write", "delete", "network"))
    assert registry.availability_reason(IntentType.READ_FILE) is None
    assert build_safe_tool_registry().availability_reason(IntentType.READ_FILE) == "Dosya okuma şu anda kullanılamıyor."


def test_reminder_create_confirmation_cancel_duplicate_and_list(tmp_path) -> None:
    reminders, files, memory = _services(tmp_path)
    router = IntentRouter(build_safe_tool_registry(reminders, files, memory))
    request = IntentRequest(IntentType.CREATE_REMINDER, 1, "", {"title": "Ara", "due_at": datetime.now(timezone.utc) + timedelta(hours=2), "recurrence": "none"}, True)
    assert router.execute(request, RequestContext(1)).error_code == "confirmation_required"
    assert reminders.list() == ()
    assert router.execute(request, RequestContext(1, confirmed=True)).success
    assert len(reminders.list()) == 1
    assert router.execute(request, RequestContext(1, confirmed=True)).error_code == "duplicate"
    listed = router.execute(IntentRequest(IntentType.LIST_REMINDERS, 1, ""), RequestContext(1))
    assert "Yaklaşan 1" in listed.user_message


def test_file_allowlist_and_traversal_do_not_leak_content(tmp_path) -> None:
    reminders, files, memory = _services(tmp_path)
    router = IntentRouter(build_safe_tool_registry(reminders, files, memory))
    allowed = router.execute(DeterministicIntentClassifier().classify("README dosyasını oku"), RequestContext(None))
    rejected = router.execute(DeterministicIntentClassifier().classify("../README.md dosyasını oku"), RequestContext(None))
    assert allowed.success and "Güvenli içerik" in allowed.user_message
    assert not rejected.success and rejected.error_code == "permission_denied"
    assert "Güvenli içerik" not in rejected.user_message
    assert ".." not in rejected.user_message
    absolute = router.execute(DeterministicIntentClassifier().classify("C:/secret.txt dosyasını oku"), RequestContext(None))
    assert absolute.error_code == "permission_denied"
    assert "secret" not in absolute.user_message


def test_memory_store_requires_confirmation_rejects_sensitive_and_recalls(tmp_path) -> None:
    reminders, files, memory = _services(tmp_path)
    router = IntentRouter(build_safe_tool_registry(reminders, files, memory))
    store = DeterministicIntentClassifier().classify("Şunu hatırla: Koyu temayı seviyorum")
    assert router.execute(store, RequestContext(1)).error_code == "confirmation_required"
    assert router.execute(store, RequestContext(1, confirmed=True)).success
    recalled = router.execute(DeterministicIntentClassifier().classify("Geçen söylediğim şeyi bul"), RequestContext(1))
    assert "Koyu temayı seviyorum" in recalled.user_message
    sensitive = DeterministicIntentClassifier().classify("Şunu hatırla: şifrem 1234")
    assert router.execute(sensitive, RequestContext(1, confirmed=True)).error_code == "permission_denied"


def test_unavailable_services_return_safe_message() -> None:
    router = IntentRouter(build_safe_tool_registry())
    result = router.execute(IntentRequest(IntentType.READ_FILE, 1, "", {"target": "README.md"}), RequestContext(None))
    assert result.error_code == "unavailable"


def test_reminder_list_is_capped_and_duplicate_create_is_safe(tmp_path) -> None:
    reminders, files, memory = _services(tmp_path)
    router = IntentRouter(build_safe_tool_registry(reminders, files, memory))
    for index in range(12):
        reminders.create(f"R{index}", datetime.now(timezone.utc) + timedelta(days=index + 1))
    listed = router.execute(IntentRequest(IntentType.LIST_REMINDERS, 1, ""), RequestContext(None))
    assert listed.user_message.count("\n-") == 10
    assert "...ve 2 hatırlatıcı daha" in listed.user_message
    due = datetime.now(timezone.utc) + timedelta(hours=3)
    first = IntentRequest(IntentType.CREATE_REMINDER, 1, "", {"title": "Aynı", "due_at": due, "recurrence": "none"}, True)
    second = IntentRequest(IntentType.CREATE_REMINDER, 1, "", {"title": "Aynı", "due_at": due, "recurrence": "none"}, True)
    assert router.execute(first, RequestContext(None, confirmed=True)).success
    assert "zaten mevcut" in router.execute(second, RequestContext(None, confirmed=True)).user_message
    assert len([item for item in reminders.list() if item.title == "Aynı"]) == 1
