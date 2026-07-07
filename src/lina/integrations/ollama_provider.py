"""Ollama model provider implementation."""

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
        opener: Callable[[Request, float], Any] = urlopen,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._opener = opener

    def generate(self, request: ModelRequest) -> ModelResponse:
        if not self._model.strip():
            raise OllamaProviderError("Ollama model is not configured")

        payload = {
            "model": self._model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }
        response_data = self._post_json("/api/generate", payload)
        response_text = response_data.get("response")

        if not isinstance(response_text, str):
            raise OllamaProviderError("Ollama response is missing text content")

        return ModelResponse(text=response_text)

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
