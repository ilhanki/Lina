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
            IntentType.CASUAL_GREETING,
            IntentType.COMPUTER_CONTROL_STATUS,
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
                    "Şu anda CLI ve Tkinter GUI üzerinden sohbet edebiliyorum. Ollama "
                    "ile yerel modele bağlanabiliyor, basit intent'leri LLM'e göndermeden "
                    "cevaplayabiliyor, session içi geçici konuşma geçmişi ve runtime "
                    "context kullanabiliyorum. İzinli proje dokümanlarından ve güvenli "
                    "read-only Git bağlamından proje durumunu okuyabiliyorum. SAFE tool "
                    "altyapısıyla saat gibi güvenli araçları çalıştırabiliyor ve "
                    "Ollama/model bağlantı durumunu teşhis edebiliyorum. Henüz bilgisayarı "
                    "genel olarak yönetemem; genel dosya erişimim, kamera, mikrofon, ekran "
                    "görme, shell command execution veya browser automation yeteneğim yok. "
                    "Kalıcı memory kullanmıyorum; Git commit, push, reset, checkout veya "
                    "merge işlemleri yapamam. LLM kendi kendine tehlikeli tool çalıştıramaz."
                )
            )
        if intent.type is IntentType.CURRENT_TIME:
            return ModelResponse(text=f"Şu an saat {self._clock():%H:%M}.")
        if intent.type is IntentType.CASUAL_GREETING:
            return ModelResponse(
                text="Selam İlhan! Buradayım, bugün ne yapalım?"
            )
        if intent.type is IntentType.COMPUTER_CONTROL_STATUS:
            return ModelResponse(
                text=(
                    "Şu anda bilgisayarını genel olarak yönetemem. Henüz ekran görme, "
                    "Windows automation, genel dosya erişimi veya shell command execution "
                    "yeteneğim yok. İleride bu yetenekler güvenli izin akışlarıyla "
                    "eklenebilir, ama bugün bunu yapabildiğimi iddia etmem doğru olmaz."
                )
            )

        raise ValueError(f"Unsupported deterministic intent: {intent.type.value}")
