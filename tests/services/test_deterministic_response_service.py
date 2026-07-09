from datetime import datetime

import pytest

from lina.brain.intent import Intent, IntentType
from lina.brain.model_provider import ModelResponse
from lina.services.deterministic_response_service import DeterministicResponseService


def test_deterministic_response_service_can_handle_supported_intents() -> None:
    service = DeterministicResponseService()

    assert service.can_handle(Intent(type=IntentType.HELP))
    assert service.can_handle(Intent(type=IntentType.IDENTITY))
    assert service.can_handle(Intent(type=IntentType.CAPABILITIES))
    assert service.can_handle(Intent(type=IntentType.CURRENT_TIME))
    assert service.can_handle(Intent(type=IntentType.CASUAL_GREETING))
    assert service.can_handle(Intent(type=IntentType.COMPUTER_CONTROL_STATUS))


def test_deterministic_response_service_does_not_handle_chat() -> None:
    service = DeterministicResponseService()

    assert not service.can_handle(Intent(type=IntentType.CHAT))


def test_deterministic_response_service_returns_help_response() -> None:
    service = DeterministicResponseService()

    response = service.handle(Intent(type=IntentType.HELP))

    assert isinstance(response, ModelResponse)
    assert "sohbet edebilir" in response.text
    assert "bunu hatırla: kısa cevapları seviyorum" in response.text
    assert "ne hatırlıyorsun" in response.text
    assert "hangi dosyaları okuyabiliyorsun" in response.text
    assert "README dosyasını oku" in response.text
    assert "roadmap dosyasını özetle" in response.text
    assert "exit veya quit" in response.text


def test_deterministic_response_service_returns_identity_response() -> None:
    service = DeterministicResponseService()

    response = service.handle(Intent(type=IntentType.IDENTITY))

    assert "Ben Lina" in response.text
    assert "İlhan" in response.text


def test_deterministic_response_service_returns_honest_capabilities_response() -> None:
    service = DeterministicResponseService()

    response = service.handle(Intent(type=IntentType.CAPABILITIES))

    assert "CLI" in response.text
    assert "Tkinter GUI" in response.text
    assert "Ollama" in response.text
    assert "runtime context" in response.text
    assert "yerel ve kalıcı memory" in response.text
    assert "İzinli proje dosyalarını read-only okuyabiliyor" in response.text
    assert "allowlist" in response.text
    assert "rastgele bilgisayar dosyalarına erişemem" in response.text
    assert "dosya yazma, silme veya taşıma yapamam" in response.text
    assert "read-only Git" in response.text
    assert "SAFE tool" in response.text
    assert "model bağlantı durumunu teşhis" in response.text
    assert "genel dosya erişimim" in response.text
    assert "shell command execution" in response.text
    assert "Git commit, push, reset, checkout veya merge işlemleri yapamam" in response.text
    assert "tehlikeli tool çalıştıramaz" in response.text


def test_deterministic_response_service_returns_current_time() -> None:
    service = DeterministicResponseService(
        clock=lambda: datetime(2026, 7, 7, 15, 42)
    )

    response = service.handle(Intent(type=IntentType.CURRENT_TIME))

    assert response.text == "Şu an saat 15:42."


def test_deterministic_response_service_returns_natural_casual_greeting() -> None:
    service = DeterministicResponseService()

    response = service.handle(Intent(type=IntentType.CASUAL_GREETING))

    assert response.text == "Selam İlhan! Buradayım, bugün ne yapalım?"
    assert "Selamlarsın" not in response.text
    assert "about" not in response.text
    assert "progressu" not in response.text
    assert "today'de" not in response.text
    assert len(response.text) < 80


def test_deterministic_response_service_returns_honest_computer_control_status() -> None:
    service = DeterministicResponseService()

    response = service.handle(Intent(type=IntentType.COMPUTER_CONTROL_STATUS))

    assert "Şu anda bilgisayarını genel olarak yönetemem" in response.text
    assert "ekran görme" in response.text
    assert "Windows automation" in response.text
    assert "shell command execution" in response.text
    assert "iddia etmem doğru olmaz" in response.text


def test_deterministic_response_service_rejects_unsupported_intent() -> None:
    service = DeterministicResponseService()

    with pytest.raises(ValueError, match="Unsupported deterministic intent"):
        service.handle(Intent(type=IntentType.CHAT))
