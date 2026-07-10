from dataclasses import FrozenInstanceError

import pytest

from lina.brain.model_provider import (
    ModelProvider,
    ModelProviderError,
    ModelMessage,
    ModelRequest,
    ModelResponse,
)


class FakeModelProvider:
    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(text=f"Echo: {request.messages[-1].content}")


def test_model_provider_contract_accepts_provider_implementation() -> None:
    provider: ModelProvider = FakeModelProvider()

    response = provider.generate(
        ModelRequest(messages=(ModelMessage(role="user", content="Hello"),))
    )

    assert response == ModelResponse(text="Echo: Hello")


def test_model_request_is_immutable() -> None:
    request = ModelRequest(
        messages=(ModelMessage(role="user", content="Hello"),)
    )

    with pytest.raises(FrozenInstanceError):
        request.messages = ()


def test_model_message_is_immutable() -> None:
    message = ModelMessage(role="user", content="Hello")

    with pytest.raises(FrozenInstanceError):
        message.content = "Other"


def test_model_response_is_immutable() -> None:
    response = ModelResponse(text="Hello")

    with pytest.raises(FrozenInstanceError):
        response.text = "Other"


def test_model_provider_error_keeps_message() -> None:
    error = ModelProviderError("Provider failed")

    assert str(error) == "Provider failed"
