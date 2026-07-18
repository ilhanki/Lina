import pytest

from lina.brain.routing.classifier import DeterministicIntentClassifier
from lina.brain.routing.models import IntentType
from lina.codex.intent import CodexIntentKind, classify_codex_intent


@pytest.mark.parametrize("text", [
    "Lina, Codex ile bu projeyi analiz et.",
    "Codex'e bu dosyayı incelet.",
    "Codex'i kullanarak düzelt.",
    "Codex kullan ve riskleri bul.",
    "Codexle bu projeye bak.",
    "Codex'le incele.",
    "kodex ile analiz et",
    "kodeksle geliştir",
    "Codex görevi oluştur",
    "Codex geçmişi",
    "Codex ayarları",
])
def test_operational_codex_variants_are_deterministic(text: str):
    assert classify_codex_intent(text).kind is CodexIntentKind.OPERATIONAL
    assert DeterministicIntentClassifier().classify(text).intent is IntentType.CODEX_OPERATIONAL


@pytest.mark.parametrize("text", [
    "Codex nedir?",
    "Codex nasıl çalışır?",
    "Codex ne işe yarar?",
    "Codex ile ChatGPT arasındaki fark nedir?",
])
def test_informational_codex_questions_remain_chat(text: str):
    assert classify_codex_intent(text).kind is CodexIntentKind.INFORMATIONAL
    assert DeterministicIntentClassifier().classify(text).intent is IntentType.CHAT


def test_unrelated_code_question_is_not_codex_intent():
    assert classify_codex_intent("Python'da tuple nedir?").kind is CodexIntentKind.NONE

