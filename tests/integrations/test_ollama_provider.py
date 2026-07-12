import base64
from datetime import datetime
import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request

import pytest

from lina.brain.model_provider import ModelMessage, ModelRequest, ModelResponse
from lina.integrations.ollama_provider import OllamaProvider, OllamaProviderError
from lina.vision.models import ImageAttachment, PNG_SIGNATURE


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


def test_ollama_provider_generates_chat_response() -> None:
    http_client = FakeOllamaHttpClient(
        b'{"message": {"role": "assistant", "content": "Hello from Ollama"}}'
    )
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        timeout=12.0,
        opener=http_client,
    )

    response = provider.generate(_model_request())

    assert response == ModelResponse(text="Hello from Ollama")


def test_ollama_provider_sends_structured_chat_messages() -> None:
    http_client = FakeOllamaHttpClient(
        b'{"message": {"role": "assistant", "content": "Done"}}'
    )
    provider = OllamaProvider(
        base_url="http://localhost:11434/",
        model="llama3",
        timeout=12.0,
        opener=http_client,
    )

    provider.generate(_model_request())

    request = http_client.requests[0]
    assert request.full_url == "http://localhost:11434/api/chat"
    assert request.get_method() == "POST"
    assert request.headers["Content-type"] == "application/json"
    assert request.data == (
        b'{"model": "llama3", "messages": [{"role": "system", '
        b'"content": "You are Lina."}, {"role": "user", "content": "Hello"}], '
        b'"stream": false, "options": {"temperature": 0.1}}'
    )
    assert http_client.timeouts == [12.0]


def test_ollama_provider_adds_image_only_to_last_user_message() -> None:
    http_client = FakeOllamaHttpClient(
        '{"message": {"role": "assistant", "content": "Görüntü cevabı"}}'.encode(
            "utf-8"
        )
    )
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="qwen3-vl:2b",
        timeout=120.0,
        opener=http_client,
    )
    image = _image_attachment()
    request = ModelRequest(
        messages=(
            ModelMessage(role="system", content="Vision guidance"),
            ModelMessage(role="user", content="Önceki soru"),
            ModelMessage(role="assistant", content="Önceki cevap"),
            ModelMessage(role="user", content="Bu ekranda ne var?"),
        ),
        image_attachment=image,
    )

    provider.generate(request)

    payload = json.loads(http_client.requests[0].data)
    assert payload["model"] == "qwen3-vl:2b"
    assert payload["think"] is False
    assert "images" not in payload["messages"][1]
    encoded = payload["messages"][-1]["images"][0]
    assert encoded == base64.b64encode(image.data).decode("ascii")
    assert "\n" not in encoded
    assert http_client.timeouts == [120.0]


def test_ollama_provider_rejects_oversized_image_before_http() -> None:
    http_client = FakeOllamaHttpClient(
        b'{"message": {"role": "assistant", "content": "unused"}}'
    )
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="qwen3-vl:2b",
        max_image_bytes=8,
        opener=http_client,
    )

    with pytest.raises(OllamaProviderError, match="size limit") as raised:
        provider.generate(
            ModelRequest(
                messages=(ModelMessage(role="user", content="Analyze"),),
                image_attachment=_image_attachment(),
            )
        )

    assert http_client.requests == []
    assert base64.b64encode(_image_attachment().data).decode("ascii") not in str(
        raised.value
    )


def test_ollama_provider_requires_user_message_for_image() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="qwen3-vl:2b",
        opener=FakeOllamaHttpClient(
            b'{"message": {"role": "assistant", "content": "unused"}}'
        ),
    )

    with pytest.raises(OllamaProviderError, match="requires a user message"):
        provider.generate(
            ModelRequest(
                messages=(ModelMessage(role="system", content="Guidance"),),
                image_attachment=_image_attachment(),
            )
        )


def test_ollama_provider_converts_network_errors() -> None:
    def failing_opener(request: Request, timeout: float) -> Any:
        raise URLError("connection refused")

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        opener=failing_opener,
    )

    with pytest.raises(OllamaProviderError, match="Ollama network error"):
        provider.generate(_model_request())


def test_ollama_provider_converts_timeout_errors() -> None:
    def timeout_opener(request: Request, timeout: float) -> Any:
        raise TimeoutError("timed out")

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        opener=timeout_opener,
    )

    with pytest.raises(OllamaProviderError, match="timed out"):
        provider.generate(_model_request())


def test_ollama_provider_rejects_missing_model() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="",
        opener=FakeOllamaHttpClient(
            b'{"message": {"role": "assistant", "content": "Hello"}}'
        ),
    )

    with pytest.raises(OllamaProviderError, match="Ollama model is not configured"):
        provider.generate(_model_request())


def test_ollama_provider_converts_invalid_json() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        opener=FakeOllamaHttpClient(b"not-json"),
    )

    with pytest.raises(OllamaProviderError, match="Ollama returned invalid JSON"):
        provider.generate(_model_request())


def test_ollama_provider_rejects_missing_message_object() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        opener=FakeOllamaHttpClient(b'{"done": true}'),
    )

    with pytest.raises(OllamaProviderError, match="missing message content"):
        provider.generate(_model_request())


def test_ollama_provider_rejects_missing_message_text() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
        opener=FakeOllamaHttpClient(b'{"message": {"role": "assistant"}}'),
    )

    with pytest.raises(OllamaProviderError, match="missing text content"):
        provider.generate(_model_request())


def test_ollama_provider_rejects_empty_message_text() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="qwen3-vl:2b",
        opener=FakeOllamaHttpClient(
            b'{"message": {"role": "assistant", "content": "   "}}'
        ),
    )

    with pytest.raises(OllamaProviderError, match="empty text content"):
        provider.generate(_model_request())


def _model_request() -> ModelRequest:
    return ModelRequest(
        messages=(
            ModelMessage(role="system", content="You are Lina."),
            ModelMessage(role="user", content="Hello"),
        )
    )


def _image_attachment() -> ImageAttachment:
    return ImageAttachment(
        mime_type="image/png",
        data=PNG_SIGNATURE + b"private-image-bytes",
        width=640,
        height=360,
        captured_at=datetime(2026, 7, 11, 23, 45),
        source="screen_capture",
        display_name="Display 1",
    )
def test_ollama_provider_model_can_change_for_future_requests() -> None:
    provider = OllamaProvider("http://localhost:11434", "llama3")

    provider.set_model("qwen3:4b")

    assert provider._model == "qwen3:4b"
