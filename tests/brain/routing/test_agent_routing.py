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
    ("Agent planını düzenle", IntentType.AGENT_MODIFY_PLAN),
])
def test_explicit_agent_intents(text, intent):
    assert DeterministicIntentClassifier().classify(text).intent is intent


@pytest.mark.parametrize("text", [
    "Yapay zekâ ajanı nedir?", "Agent mode güvenli mi?", "Bir plan nasıl hazırlanır?",
    "Bugün nasılsın?",
])
def test_agent_discussion_and_normal_questions_stay_chat(text):
    assert DeterministicIntentClassifier().classify(text).intent is IntentType.CHAT
