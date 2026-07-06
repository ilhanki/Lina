from typing import Any
from urllib.error import URLError
from urllib.request import Request

import pytest

from lina.brain.model_provider import ModelRequest, ModelResponse
from lina.integrations.ollama_provider import OllamaProvider, OllamaProviderError


class FakeHttpResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class FakeOllamaHttpClient:
    def __init__(self, body: bytes) -> None:
        self._body = body
        self.requests: list[Request] = []
        self.timeouts: list[float] = []

    def __call__(self, request: Request, timeout: float) -> FakeHttpResponse:
        self.requests.append(request)
        self.timeouts.append(timeout)
        return FakeHttpResponse(self._body)


def test_ollama_provider_generates_model_response() -> None:
    http_client = FakeOllamaHttpClient(b'{"response": "Hello from Ollama"}')
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        timeout=12.0,
        opener=http_client,
    )

    response = provider.generate(ModelRequest(prompt="Hello"))

    assert response == ModelResponse(text="Hello from Ollama")


def test_ollama_provider_sends_expected_http_request() -> None:
    http_client = FakeOllamaHttpClient(b'{"response": "Done"}')
    provider = OllamaProvider(
        base_url="http://localhost:11434/",
        model="llama3",
        timeout=12.0,
        opener=http_client,
    )

    provider.generate(ModelRequest(prompt="Hello"))

    request = http_client.requests[0]
    assert request.full_url == "http://localhost:11434/api/generate"
    assert request.get_method() == "POST"
    assert request.headers["Content-type"] == "application/json"
    assert request.data == b'{"model": "llama3", "prompt": "Hello", "stream": false}'
    assert http_client.timeouts == [12.0]


def test_ollama_provider_converts_network_errors() -> None:
    def failing_opener(request: Request, timeout: float) -> Any:
        raise URLError("connection refused")

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        opener=failing_opener,
    )

    with pytest.raises(OllamaProviderError, match="Ollama network error"):
        provider.generate(ModelRequest(prompt="Hello"))


def test_ollama_provider_rejects_missing_model() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="",
        opener=FakeOllamaHttpClient(b'{"response": "Hello"}'),
    )

    with pytest.raises(OllamaProviderError, match="Ollama model is not configured"):
        provider.generate(ModelRequest(prompt="Hello"))


def test_ollama_provider_converts_invalid_json() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        opener=FakeOllamaHttpClient(b"not-json"),
    )

    with pytest.raises(OllamaProviderError, match="Ollama returned invalid JSON"):
        provider.generate(ModelRequest(prompt="Hello"))


def test_ollama_provider_rejects_missing_response_text() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        opener=FakeOllamaHttpClient(b'{"done": true}'),
    )

    with pytest.raises(OllamaProviderError, match="missing text content"):
        provider.generate(ModelRequest(prompt="Hello"))
