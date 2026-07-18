"""Translate typed bridge events into concise Lina-facing messages."""

from lina.codex.models import CodexEvent, CodexEventType


_MESSAGES = {
    CodexEventType.SESSION_STARTED: "Codex görevi başlatıldı.",
    CodexEventType.ANALYZING: "Projeyi inceliyorum.",
    CodexEventType.PLANNING: "Güvenli çalışma planını hazırlıyorum.",
    CodexEventType.FILE_SCANNED: "Dosya analizi tamamlandı.",
    CodexEventType.SUGGESTION_READY: "Öneriler hazır.",
    CodexEventType.APPROVAL_REQUESTED: "Değişiklik için onayını bekliyorum.",
    CodexEventType.MODIFICATION_STARTED: "Onaylanan değişiklik uygulanıyor.",
    CodexEventType.MODIFICATION_COMPLETED: "Onaylanan değişiklik tamamlandı.",
    CodexEventType.VERIFICATION_STARTED: "Sonucu doğruluyorum.",
    CodexEventType.COMPLETED: "Codex görevi tamamlandı.",
    CodexEventType.FAILED: "Codex görevi güvenli biçimde tamamlanamadı.",
}


def user_message(event: CodexEvent) -> str:
    return _MESSAGES[event.event_type]


def spoken_message(event: CodexEvent) -> str:
    if event.event_type is CodexEventType.APPROVAL_REQUESTED:
        return "Onayını bekliyorum."
    if event.event_type is CodexEventType.COMPLETED:
        return "Analiz tamamlandı."
    if event.event_type is CodexEventType.SESSION_STARTED:
        return "Codex görevini hazırladım."
    return user_message(event)

