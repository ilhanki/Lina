"""Bindings from safe routing tools to existing application services."""

from datetime import datetime, timedelta

from lina.brain.routing.models import IntentType, ToolResult
from lina.brain.routing.registry import SafeToolRegistry, ToolDefinition
from lina.files.models import FileAccessError
from lina.memory.models import MemoryType
from lina.notifications.models import ReminderRecurrence


def build_safe_tool_registry(reminders=None, files=None, memory=None) -> SafeToolRegistry:
    registry = SafeToolRegistry()

    def create_reminder(request, _context):
        args = request.extracted_arguments
        duplicate = next((item for item in reminders.list() if item.status.value == "active" and item.title.casefold() == str(args["title"]).casefold() and item.due_at == args["due_at"] and item.recurrence == args["recurrence"]), None)
        if duplicate is not None:
            return ToolResult(True, "Bu hatırlatıcı zaten mevcut.", duplicate)
        try:
            reminder = reminders.create(args["title"], args["due_at"], args["recurrence"])
        except (RuntimeError, OSError):
            return ToolResult(False, "Hatırlatıcı oluşturulamadı.", error_code="persistence_error")
        return ToolResult(True, f"Tamam, {reminder.due_at.astimezone().strftime('%d.%m.%Y %H:%M')} için hatırlatıcını oluşturdum.", reminder)

    def list_reminders(_request, _context):
        upcoming = [item for item in reminders.list() if item.status.value == "active" and item.due_at > datetime.now(item.due_at.tzinfo)]
        if not upcoming:
            return ToolResult(True, "Yaklaşan hatırlatıcın yok.", ())
        lines = [f"Yaklaşan {len(upcoming)} hatırlatıcın var:"]
        lines.extend(f"- {item.due_at.astimezone().strftime('%d.%m %H:%M')} · {item.title}" for item in upcoming[:10])
        if len(upcoming) > 10:
            lines.append(f"...ve {len(upcoming) - 10} hatırlatıcı daha")
        return ToolResult(True, "\n".join(lines), tuple(upcoming))

    def reminder_summary(request, _context):
        selected = reminders_in_range(str(request.extracted_arguments.get("range", "upcoming")))
        if not selected:
            return ToolResult(True, "Seçilen aralıkta yaklaşan hatırlatıcın yok.", ())
        lines = [f"Seçilen aralıkta {len(selected)} hatırlatıcın var:"]
        lines.extend(f"- {item.due_at.astimezone().strftime('%d.%m %H:%M')} · {item.title}" for item in selected[:10])
        if len(selected) > 10:
            lines.append(f"...ve {len(selected) - 10} hatırlatıcı daha")
        return ToolResult(True, "\n".join(lines), selected)

    def reminder_conflicts(request, _context):
        selected = reminders_in_range(str(request.extracted_arguments.get("range", "upcoming")))
        by_time = {}
        for reminder in selected:
            by_time.setdefault(reminder.due_at, []).append(reminder)
        conflicts = tuple(
            tuple(sorted(group, key=lambda item: (item.title.casefold(), item.id or 0)))
            for _due_at, group in sorted(by_time.items(), key=lambda item: item[0])
            if len(group) > 1
        )
        if not conflicts:
            return ToolResult(True, "Seçilen aralıkta aynı zamana denk gelen hatırlatıcı yok.", ())
        lines = [f"{len(conflicts)} zaman çakışması buldum:"]
        lines.extend(
            f"- {group[0].due_at.astimezone().strftime('%d.%m %H:%M')} · "
            + ", ".join(item.title for item in group)
            for group in conflicts
        )
        return ToolResult(True, "\n".join(lines), conflicts)

    def reminders_in_range(range_name: str):
        now = datetime.now().astimezone()
        active = [
            item for item in reminders.list()
            if item.status.value == "active" and item.due_at > now
        ]
        normalized = range_name.casefold().strip()
        if normalized == "tomorrow":
            tomorrow = (now + timedelta(days=1)).date()
            active = [item for item in active if item.due_at.astimezone().date() == tomorrow]
        elif normalized == "week":
            end = now + timedelta(days=7)
            active = [item for item in active if item.due_at <= end]
        return tuple(sorted(active, key=lambda item: (item.due_at, item.id or 0)))

    def read_file(request, _context):
        try:
            content = files.read_allowed_file(request.extracted_arguments.get("target", ""))
        except FileAccessError:
            return ToolResult(False, "Bu dosyaya erişmeme izin verilmiyor.", error_code="permission_denied")
        suffix = " (önizleme kısaltıldı)" if content.truncated else ""
        return ToolResult(True, f"{content.path} dosyasını okudum{suffix}.\n\n{content.text}", content)

    def store_memory(request, _context):
        content = str(request.extracted_arguments.get("content", "")).strip()
        if not content:
            return ToolResult(False, "Kaydedilecek bilgiyi netleştirir misin?", error_code="validation_error", requires_follow_up=True)
        if memory.is_sensitive_content(content):
            return ToolResult(False, "Bu bilgi hassas göründüğü için hafızaya kaydedemem.", error_code="permission_denied")
        duplicate = next(
            (item for item in memory.list_memories() if " ".join(item.content.casefold().split()) == " ".join(content.casefold().split())),
            None,
        )
        if duplicate is not None:
            return ToolResult(True, "Bu bilgi zaten hafızadaydı; ikinci bir kayıt oluşturmadım.", duplicate)
        created = memory.add_memory(MemoryType.CONVERSATION_NOTE, content)
        return ToolResult(True, "Bunu hafızaya kaydettim." if created else "Bu bilgi zaten hafızadaydı.", created)

    def recall_memory(_request, _context):
        records = memory.list_memories()[:5]
        if not records:
            return ToolResult(True, "Bu konuda hafızamda kayıt bulamadım.", ())
        return ToolResult(True, "Hafızamdaki ilgili kayıtlar:\n" + "\n".join(f"- {item.content}" for item in records), records)

    definitions = (
        ToolDefinition("reminder.create", IntentType.CREATE_REMINDER, "Yerel hatırlatıcı oluştur", {"title": str, "due_at": datetime, "recurrence": (ReminderRecurrence, str)}, True, create_reminder, lambda: reminders is not None, "Hatırlatıcılar şu anda kullanılamıyor."),
        ToolDefinition("reminder.list", IntentType.LIST_REMINDERS, "Yaklaşan hatırlatıcıları listele", {}, False, list_reminders, lambda: reminders is not None, "Hatırlatıcılar şu anda kullanılamıyor."),
        ToolDefinition("reminder.summary", IntentType.SUMMARIZE_REMINDERS, "Seçilen aralıktaki hatırlatıcıları özetle", {"range": str}, False, reminder_summary, lambda: reminders is not None, "Hatırlatıcılar şu anda kullanılamıyor."),
        ToolDefinition("reminder.conflicts", IntentType.CHECK_REMINDER_CONFLICTS, "Aynı zamana denk gelen hatırlatıcıları deterministik olarak bul", {"range": str}, False, reminder_conflicts, lambda: reminders is not None, "Hatırlatıcılar şu anda kullanılamıyor."),
        ToolDefinition("files.read", IntentType.READ_FILE, "Allowlist içindeki dosyayı oku", {"target": str}, False, read_file, lambda: files is not None, "Dosya okuma şu anda kullanılamıyor."),
        ToolDefinition("memory.store", IntentType.MEMORY_STORE, "Açık kullanıcı isteğini hafızaya kaydet", {"content": str}, True, store_memory, lambda: memory is not None, "Memory şu anda kullanılamıyor."),
        ToolDefinition("memory.recall", IntentType.MEMORY_RECALL, "Yerel hafızayı getir", {"query": str}, False, recall_memory, lambda: memory is not None, "Memory şu anda kullanılamıyor."),
    )
    for definition in definitions:
        registry.register(definition)
    for name, intent in (("vision.screen", IntentType.ANALYZE_SCREEN), ("vision.region", IntentType.ANALYZE_REGION), ("vision.image", IntentType.ANALYZE_IMAGE)):
        registry.register(ToolDefinition(name, intent, "Mevcut güvenli vision UI akışı", {}, False, lambda _r, _c: ToolResult(False, "Vision UI etkileşimi gerekiyor.", error_code="ui_required")))
    for intent in (
        IntentType.CAMERA_OPEN, IntentType.CAMERA_ANALYZE, IntentType.CAMERA_MONITOR,
        IntentType.SCREEN_MONITOR, IntentType.REGION_MONITOR, IntentType.LIVE_VISION_PAUSE,
        IntentType.LIVE_VISION_RESUME, IntentType.LIVE_VISION_STOP, IntentType.LIVE_VISION_STATUS,
    ):
        registry.register(ToolDefinition(
            f"live_vision.{intent.value}", intent, "Güvenli live vision UI akışı", {},
            intent in {IntentType.CAMERA_OPEN, IntentType.CAMERA_ANALYZE, IntentType.CAMERA_MONITOR, IntentType.SCREEN_MONITOR, IntentType.REGION_MONITOR},
            lambda _request, _context: ToolResult(False, "Live Vision UI etkileşimi gerekiyor.", error_code="ui_required"),
        ))
    return registry
