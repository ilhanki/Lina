import pytest

from lina.brain.routing.classifier import DeterministicIntentClassifier
from lina.brain.routing.models import IntentType
from lina.brain.routing.router import IntentRouter


@pytest.mark.parametrize("text,intent", [
    ("Kamerayı aç", IntentType.CAMERA_OPEN),
    ("Kamerayı aç, elimdeki şeye bak", IntentType.CAMERA_ANALYZE),
    ("Kamerayı takip et", IntentType.CAMERA_MONITOR),
    ("Ekranı takip et, hata çıkarsa söyle", IntentType.SCREEN_MONITOR),
    ("Bu bölgeyi izle", IntentType.REGION_MONITOR),
    ("Takibi duraklat", IntentType.LIVE_VISION_PAUSE),
    ("Tekrar devam et", IntentType.LIVE_VISION_RESUME),
    ("Kamerayı kapat", IntentType.LIVE_VISION_STOP),
    ("Şu an neyi izliyorsun?", IntentType.LIVE_VISION_STATUS),
])
def test_live_vision_action_intents(text, intent):
    request = DeterministicIntentClassifier().classify(text)
    assert request.intent is intent
    assert request.requires_confirmation is (intent in {IntentType.CAMERA_OPEN, IntentType.CAMERA_ANALYZE, IntentType.CAMERA_MONITOR, IntentType.SCREEN_MONITOR, IntentType.REGION_MONITOR})


@pytest.mark.parametrize("text", ["Kamera nasıl çalışır?", "Ekran takibi güvenli mi?", "Vision modeli nedir?"])
def test_live_vision_questions_stay_normal_chat(text):
    assert DeterministicIntentClassifier().classify(text).intent is IntentType.CHAT


def test_camera_confirmation_is_privacy_specific():
    request = DeterministicIntentClassifier().classify("Kamerayı takip et")
    message = IntentRouter.confirmation_message(request)
    assert "yerel" in message and "kalıcı olarak saklanmaz" in message
