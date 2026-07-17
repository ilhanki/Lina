import pytest

from lina.brain.routing.classifier import DeterministicIntentClassifier
from lina.brain.routing.models import IntentType


@pytest.mark.parametrize(("text", "intent"), [
    ("Agent modunda hatırlatıcılarımı kontrol et", IntentType.AGENT_EXECUTE),
    ("Bunu adım adım yap", IntentType.AGENT_EXECUTE),
    ("Önce plan çıkar", IntentType.AGENT_PLAN),
    ("Görevi duraklat", IntentType.AGENT_PAUSE),
    ("Agent görevine devam et", IntentType.AGENT_RESUME),
    ("Agent görevini iptal et", IntentType.AGENT_CANCEL),
    ("Şu anda hangi adımdasın?", IntentType.AGENT_STATUS),
    ("Agent planını düzenle", IntentType.AGENT_PLAN_EDIT),
    ("Hazır Agent görevlerini göster.", IntentType.AGENT_TEMPLATE_LIST),
    ("Hatırlatıcı şablonunu kullan.", IntentType.AGENT_TEMPLATE_USE),
    ("Agent görev geçmişimi göster.", IntentType.AGENT_TASK_HISTORY),
    ("Yarım kalan görevimi göster.", IntentType.AGENT_TASK_RECOVERY),
    ("Bu görevi güvenli şekilde yeniden başlat.", IntentType.AGENT_TASK_RESTART),
    ("İkinci adımı kaldır.", IntentType.AGENT_STEP_SKIP),
    ("Agent salt okunur adımı tekrar dene.", IntentType.AGENT_RETRY_READ_ONLY),
    ("Belirsiz sonucu kontrol et.", IntentType.AGENT_CHECK_UNCERTAIN_RESULT),
])
def test_explicit_agent_intents(text, intent):
    assert DeterministicIntentClassifier().classify(text).intent is intent


@pytest.mark.parametrize("text", [
    "Yapay zekâ ajanı nedir?", "Agent mode güvenli mi?", "Bir plan nasıl hazırlanır?",
    "Bugün nasılsın?", "Görev şablonu nedir?", "Agent neden hata yapar?", "Retry ne demek?",
])
def test_agent_discussion_and_normal_questions_stay_chat(text):
    assert DeterministicIntentClassifier().classify(text).intent is IntentType.CHAT
