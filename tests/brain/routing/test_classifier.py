from datetime import datetime, timezone

from lina.brain.routing.classifier import DeterministicIntentClassifier
from lina.brain.routing.models import IntentType
from lina.brain.routing.validation import parse_reminder_arguments
from lina.notifications.models import ReminderRecurrence


def test_classifier_routes_supported_intents_and_chat() -> None:
    classifier = DeterministicIntentClassifier()
    cases = {
        "Merhaba, nasılsın?": IntentType.CHAT,
        "Yarın saat 9'da beni ara diye hatırlat": IntentType.CREATE_REMINDER,
        "Hatırlatıcılarımı göster": IntentType.LIST_REMINDERS,
        "Ekranı analiz et": IntentType.ANALYZE_SCREEN,
        "Ekranda bölge seçip incele": IntentType.ANALYZE_REGION,
        "Şu görseli incele": IntentType.ANALYZE_IMAGE,
        "README dosyasını oku": IntentType.READ_FILE,
        "Şunu hatırla: Koyu temayı seviyorum": IntentType.MEMORY_STORE,
        "Geçen söylediğim şeyi bul": IntentType.MEMORY_RECALL,
        "E-posta gönder": IntentType.UNSUPPORTED,
        "PowerShell komutu çalıştır": IntentType.UNSAFE,
        "Hatırlatıcılar sence faydalı mı?": IntentType.CHAT,
    }
    for text, intent in cases.items():
        assert classifier.classify(text).intent is intent


def test_classifier_handles_turkish_casing_and_punctuation() -> None:
    request = DeterministicIntentClassifier().classify("HATIRLATICILARIMI GÖSTER!!!")
    assert request.intent is IntentType.LIST_REMINDERS


def test_reminder_parser_dates_times_recurrence_and_missing_fields() -> None:
    now = datetime(2026, 7, 12, 10, tzinfo=timezone.utc)
    daily, missing = parse_reminder_arguments("Yarın saat 9'da ilaç almayı hatırlat her gün", now)
    weekly, _ = parse_reminder_arguments("Yarın 20:30 toplantıyı hatırlat her hafta", now)
    incomplete, incomplete_missing = parse_reminder_arguments("Yarın spor yapmayı hatırlat", now)
    past, past_missing = parse_reminder_arguments("Bugün saat 8 kahvaltıyı hatırlat", now)
    assert missing == ()
    assert daily["due_at"].astimezone().date().isoformat() == "2026-07-13"
    assert daily["due_at"].astimezone().hour == 9
    assert daily["recurrence"] is ReminderRecurrence.DAILY
    assert weekly["recurrence"] is ReminderRecurrence.WEEKLY
    assert "time" in incomplete_missing and incomplete["due_at"] is None
    assert "future_time" in past_missing


def test_reminder_title_and_trailing_memory_content_are_clean() -> None:
    reminder = DeterministicIntentClassifier().classify("Yarın saat 9'da beni ara diye hatırlat")
    memory = DeterministicIntentClassifier().classify("Koyu temayı tercih ettiğimi unutma")
    assert reminder.extracted_arguments["title"] == "Ara"
    assert memory.extracted_arguments["content"] == "Koyu temayı tercih ettiğimi"
