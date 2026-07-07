"""Deterministic responses for simple Lina intents."""

from collections.abc import Callable
from datetime import datetime

from lina.brain.intent import Intent, IntentType
from lina.brain.model_provider import ModelResponse


class DeterministicResponseService:
    """Produces responses for intents that do not require an LLM."""

    def __init__(self, clock: Callable[[], datetime] = datetime.now) -> None:
        self._clock = clock

    def can_handle(self, intent: Intent) -> bool:
        return intent.type in {
            IntentType.HELP,
            IntentType.IDENTITY,
            IntentType.CAPABILITIES,
            IntentType.CURRENT_TIME,
        }

    def handle(self, intent: Intent) -> ModelResponse:
        if intent.type is IntentType.HELP:
            return ModelResponse(
                text=(
                    "Şimdilik benimle sohbet edebilir, 'saat kaç', 'sen kimsin' "
                    "veya 'neler yapabiliyorsun' gibi temel sorular sorabilirsin. "
                    "Çıkmak için exit veya quit yazabilirsin."
                )
            )
        if intent.type is IntentType.IDENTITY:
            return ModelResponse(
                text=(
                    "Ben Lina. İlhan için geliştirilen, yerel çalışması hedeflenen "
                    "modüler bir yapay zekâ masaüstü asistanıyım."
                )
            )
        if intent.type is IntentType.CAPABILITIES:
            return ModelResponse(
                text=(
                    "Şu anda terminal üzerinden sohbet edebiliyorum, Ollama ile yerel "
                    "modele bağlanabiliyorum ve basit komutları anlayabiliyorum. Henüz "
                    "dosyaları, GitHub'ı, kamerayı veya bilgisayarı yönetemiyorum."
                )
            )
        if intent.type is IntentType.CURRENT_TIME:
            return ModelResponse(text=f"Şu an saat {self._clock():%H:%M}.")

        raise ValueError(f"Unsupported deterministic intent: {intent.type.value}")
