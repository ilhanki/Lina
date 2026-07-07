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


def test_deterministic_response_service_does_not_handle_chat() -> None:
    service = DeterministicResponseService()

    assert not service.can_handle(Intent(type=IntentType.CHAT))


def test_deterministic_response_service_returns_help_response() -> None:
    service = DeterministicResponseService()

    response = service.handle(Intent(type=IntentType.HELP))

    assert isinstance(response, ModelResponse)
    assert "sohbet edebilir" in response.text
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
    assert "read-only Git" in response.text
    assert "SAFE tool" in response.text
    assert "model bağlantı durumunu teşhis" in response.text
    assert "genel dosya erişimim" in response.text
    assert "shell command execution" in response.text
    assert "Kalıcı memory kullanmıyorum" in response.text
    assert "Git commit, push, reset, checkout veya merge işlemleri yapamam" in response.text
    assert "tehlikeli tool çalıştıramaz" in response.text


def test_deterministic_response_service_returns_current_time() -> None:
    service = DeterministicResponseService(
        clock=lambda: datetime(2026, 7, 7, 15, 42)
    )

    response = service.handle(Intent(type=IntentType.CURRENT_TIME))

    assert response.text == "Şu an saat 15:42."


def test_deterministic_response_service_rejects_unsupported_intent() -> None:
    service = DeterministicResponseService()

    with pytest.raises(ValueError, match="Unsupported deterministic intent"):
        service.handle(Intent(type=IntentType.CHAT))
