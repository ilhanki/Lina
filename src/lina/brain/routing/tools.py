"""Bindings from safe routing tools to existing application services."""

from datetime import datetime

from lina.brain.routing.models import IntentType, ToolResult
from lina.brain.routing.registry import SafeToolRegistry, ToolDefinition
from lina.files.models import FileAccessError
from lina.memory.models import MemoryType


def build_safe_tool_registry(reminders=None, files=None, memory=None) -> SafeToolRegistry:
    registry = SafeToolRegistry()

    def create_reminder(request, _context):
        args = request.extracted_arguments
        reminder = reminders.create(args["title"], args["due_at"], args["recurrence"])
        return ToolResult(True, f"Tamam, {reminder.due_at.astimezone().strftime('%d.%m.%Y %H:%M')} için hatırlatıcını oluşturdum.", reminder)

    def list_reminders(_request, _context):
        upcoming = [item for item in reminders.list() if item.status.value == "active" and item.due_at > datetime.now(item.due_at.tzinfo)][:10]
        if not upcoming:
            return ToolResult(True, "Yaklaşan hatırlatıcın yok.", ())
        lines = [f"Yaklaşan {len(upcoming)} hatırlatıcın var:"]
        lines.extend(f"- {item.due_at.astimezone().strftime('%d.%m %H:%M')} · {item.title}" for item in upcoming)
        return ToolResult(True, "\n".join(lines), tuple(upcoming))

    def read_file(request, _context):
        try:
            content = files.read_allowed_file(request.extracted_arguments.get("target", ""))
        except FileAccessError:
            return ToolResult(False, "Bu dosyaya erişmeme izin verilmiyor.", error_code="file_rejected")
        suffix = " (önizleme kısaltıldı)" if content.truncated else ""
        return ToolResult(True, f"{content.path} dosyasını okudum{suffix}.\n\n{content.text}", content)

    def store_memory(request, _context):
        content = str(request.extracted_arguments.get("content", "")).strip()
        if not content:
            return ToolResult(False, "Kaydedilecek bilgiyi netleştirir misin?", error_code="empty_memory", requires_follow_up=True)
        if memory.is_sensitive_content(content):
            return ToolResult(False, "Bu bilgi hassas göründüğü için hafızaya kaydedemem.", error_code="sensitive_memory")
        created = memory.add_memory(MemoryType.CONVERSATION_NOTE, content)
        return ToolResult(True, "Bunu hafızaya kaydettim." if created else "Bu bilgi zaten hafızadaydı.", created)

    def recall_memory(_request, _context):
        records = memory.list_memories()[:5]
        if not records:
            return ToolResult(True, "Bu konuda hafızamda kayıt bulamadım.", ())
        return ToolResult(True, "Hafızamdaki ilgili kayıtlar:\n" + "\n".join(f"- {item.content}" for item in records), records)

    definitions = (
        ToolDefinition("reminder.create", IntentType.CREATE_REMINDER, "Yerel hatırlatıcı oluştur", {"title": str, "due_at": datetime}, True, create_reminder, lambda: reminders is not None, "Hatırlatıcılar şu anda kullanılamıyor."),
        ToolDefinition("reminder.list", IntentType.LIST_REMINDERS, "Yaklaşan hatırlatıcıları listele", {}, False, list_reminders, lambda: reminders is not None, "Hatırlatıcılar şu anda kullanılamıyor."),
        ToolDefinition("files.read", IntentType.READ_FILE, "Allowlist içindeki dosyayı oku", {"target": str}, False, read_file, lambda: files is not None, "Dosya okuma şu anda kullanılamıyor."),
        ToolDefinition("memory.store", IntentType.MEMORY_STORE, "Açık kullanıcı isteğini hafızaya kaydet", {"content": str}, True, store_memory, lambda: memory is not None, "Memory şu anda kullanılamıyor."),
        ToolDefinition("memory.recall", IntentType.MEMORY_RECALL, "Yerel hafızayı getir", {"query": str}, False, recall_memory, lambda: memory is not None, "Memory şu anda kullanılamıyor."),
    )
    for definition in definitions:
        registry.register(definition)
    for name, intent in (("vision.screen", IntentType.ANALYZE_SCREEN), ("vision.region", IntentType.ANALYZE_REGION), ("vision.image", IntentType.ANALYZE_IMAGE)):
        registry.register(ToolDefinition(name, intent, "Mevcut güvenli vision UI akışı", {}, False, lambda _r, _c: ToolResult(False, "Vision UI etkileşimi gerekiyor.", error_code="ui_required")))
    return registry
