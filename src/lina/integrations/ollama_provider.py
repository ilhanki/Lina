"""Ollama model provider implementation."""

import base64
from collections.abc import Callable
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lina.brain.model_provider import (
    ModelProvider,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
)


class OllamaProviderError(ModelProviderError):
    """Raised when the Ollama provider cannot generate a response."""


class OllamaProvider(ModelProvider):
    """Model provider that talks to Ollama's HTTP API."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 30.0,
        max_image_bytes: int = 8_388_608,
        opener: Callable[[Request, float], Any] = urlopen,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._max_image_bytes = max_image_bytes
        self._opener = opener

    def generate(self, request: ModelRequest) -> ModelResponse:
        if not self._model.strip():
            raise OllamaProviderError("Ollama model is not configured")

        messages: list[dict[str, Any]] = [
            {"role": message.role, "content": message.content}
            for message in request.messages
        ]
        if request.image_attachment is not None:
            attachment = request.image_attachment
            if attachment.byte_size > self._max_image_bytes:
                raise OllamaProviderError("Image attachment exceeds configured size limit")
            user_message = next(
                (message for message in reversed(messages) if message["role"] == "user"),
                None,
            )
            if user_message is None:
                raise OllamaProviderError("Image request requires a user message")
            user_message["images"] = [
                base64.b64encode(attachment.data).decode("ascii")
            ]

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }
        if request.image_attachment is not None:
            payload["think"] = False
        response_data = self._post_json("/api/chat", payload)
        response_message = response_data.get("message")
        if not isinstance(response_message, dict):
            raise OllamaProviderError("Ollama response is missing message content")
        response_text = response_message.get("content")

        if not isinstance(response_text, str):
            raise OllamaProviderError("Ollama response is missing text content")
        if not response_text.strip():
            raise OllamaProviderError("Ollama response contains empty text content")

        return ModelResponse(text=response_text.strip())

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        http_request = Request(
            url=f"{self._base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with self._opener(http_request, timeout=self._timeout) as response:
                raw_response = response.read()
        except HTTPError as error:
            raise OllamaProviderError(f"Ollama HTTP error: {error.code}") from error
        except TimeoutError as error:
            raise OllamaProviderError("Ollama request timed out") from error
        except URLError as error:
            raise OllamaProviderError(f"Ollama network error: {error.reason}") from error
        except OSError as error:
            raise OllamaProviderError("Ollama request failed") from error

        try:
            decoded_response = json.loads(raw_response.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OllamaProviderError("Ollama returned invalid JSON") from error

        if not isinstance(decoded_response, dict):
            raise OllamaProviderError("Ollama returned an invalid response shape")

        return decoded_response
