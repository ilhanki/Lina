from dataclasses import FrozenInstanceError

import pytest

from lina.brain.model_provider import ModelProvider, ModelRequest, ModelResponse


class FakeModelProvider:
    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(text=f"Echo: {request.prompt}")


def test_model_provider_contract_accepts_provider_implementation() -> None:
    provider: ModelProvider = FakeModelProvider()

    response = provider.generate(ModelRequest(prompt="Hello"))

    assert response == ModelResponse(text="Echo: Hello")


def test_model_request_is_immutable() -> None:
    request = ModelRequest(prompt="Hello")

    with pytest.raises(FrozenInstanceError):
        request.prompt = "Other"


def test_model_response_is_immutable() -> None:
    response = ModelResponse(text="Hello")

    with pytest.raises(FrozenInstanceError):
        response.text = "Other"

