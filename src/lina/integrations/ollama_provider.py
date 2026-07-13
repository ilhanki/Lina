"""Ollama model provider implementation."""

import base64
from collections.abc import Callable
import json
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lina.brain.model_provider import (
    ModelProvider,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
)
from lina.inference.models import InferenceMetrics, nanoseconds_to_ms


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
        keep_alive: str | int | None = None,
        max_output_tokens: int | None = None,
        stream: bool = False,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._max_image_bytes = max_image_bytes
        self._opener = opener
        self._keep_alive = keep_alive
        self._max_output_tokens = max_output_tokens
        self._stream = stream
        self._last_metrics: InferenceMetrics | None = None
        self._cancelled = threading.Event()
        self._response_lock = threading.Lock()
        self._active_response: Any | None = None

    @property
    def last_metrics(self) -> InferenceMetrics | None:
        return self._last_metrics

    def generate(self, request: ModelRequest) -> ModelResponse:
        self._cancelled.clear()
        started = time.perf_counter()
        model = self._model
        if not model.strip():
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
            "model": model,
            "messages": messages,
            "stream": self._stream,
            "options": {
                "temperature": 0.1,
            },
        }
        max_output_tokens = request.max_output_tokens or self._max_output_tokens
        if max_output_tokens is not None:
            payload["options"]["num_predict"] = max_output_tokens
        keep_alive = request.keep_alive if request.keep_alive is not None else self._keep_alive
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        if request.image_attachment is not None:
            payload["think"] = False
        try:
            chunks = self._post_stream("/api/chat", payload)
        except OllamaProviderError as error:
            self._last_metrics = InferenceMetrics(
                provider="ollama", model=model, first_token_ms=None,
                total_ms=(time.perf_counter() - started) * 1000,
                cancelled=self._cancelled.is_set(), error_category=_error_category(error),
            )
            raise
        response_data = chunks[-1]
        response_text = "".join(_chunk_text(chunk) for chunk in chunks).strip()
        response_message = response_data.get("message")
        if not response_text and not isinstance(response_message, dict):
            raise OllamaProviderError("Ollama response is missing message content")
        if not response_text and isinstance(response_message, dict):
            response_text = response_message.get("content")
        if not isinstance(response_text, str):
            raise OllamaProviderError("Ollama response is missing text content")
        if not response_text.strip():
            raise OllamaProviderError("Ollama response contains empty text content")

        first_content = next((chunk for chunk in chunks if _chunk_text(chunk)), None)
        first_token_ms = (
            (float(first_content.get("_received_at", started)) - started) * 1000
            if first_content is not None else None
        )
        self._last_metrics = _build_metrics(
            model, started, first_token_ms, response_data, self._cancelled.is_set()
        )
        return ModelResponse(text=response_text.strip())

    def set_model(self, model: str) -> None:
        """Use a different locally configured model for future requests."""
        normalized = model.strip()
        if not normalized:
            raise ValueError("Ollama model must not be empty")
        if any(character in normalized for character in "\r\n\x00"):
            raise ValueError("Ollama model contains control characters")
        self._model = normalized

    def configure(self, keep_alive: str | int | None, max_output_tokens: int) -> None:
        if max_output_tokens < 32 or max_output_tokens > 8192:
            raise ValueError("Maximum output tokens must be between 32 and 8192")
        self._keep_alive = keep_alive
        self._max_output_tokens = max_output_tokens

    def cancel(self) -> None:
        self._cancelled.set()
        with self._response_lock:
            response = self._active_response
        if response is not None:
            try:
                response.close()
            except Exception:
                pass

    def unload(self) -> bool:
        try:
            self._post_json(
                "/api/generate",
                {"model": self._model, "keep_alive": 0, "stream": False},
            )
        except OllamaProviderError:
            return False
        return True

    def _post_stream(self, path: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if not self._stream:
            response = self._post_json(path, payload)
            response["_received_at"] = time.perf_counter()
            return [response]
        http_request = self._request(path, payload)
        try:
            with self._opener(http_request, timeout=self._timeout) as response:
                with self._response_lock:
                    self._active_response = response
                raw_lines: list[tuple[bytes, float]] = []
                while True:
                    line = response.readline()
                    if not line:
                        break
                    raw_lines.append((line, time.perf_counter()))
                    if self._cancelled.is_set():
                        raise OllamaProviderError("Ollama request cancelled")
        except Exception as error:
            if isinstance(error, OllamaProviderError):
                raise
            if self._cancelled.is_set():
                raise OllamaProviderError("Ollama request cancelled") from error
            self._raise_transport_error(error)
        finally:
            with self._response_lock:
                self._active_response = None
        chunks: list[dict[str, Any]] = []
        for raw_line, received_at in raw_lines:
            if self._cancelled.is_set():
                raise OllamaProviderError("Ollama request cancelled")
            try:
                line = raw_line.decode("utf-8")
            except UnicodeDecodeError as error:
                raise OllamaProviderError("Ollama returned invalid JSON") from error
            if not line.strip():
                continue
            try:
                decoded = json.loads(line)
            except json.JSONDecodeError as error:
                raise OllamaProviderError("Ollama returned invalid JSON") from error
            if not isinstance(decoded, dict):
                raise OllamaProviderError("Ollama returned an invalid response shape")
            decoded["_received_at"] = received_at
            chunks.append(decoded)
        if not chunks:
            raise OllamaProviderError("Ollama returned invalid JSON")
        return chunks

    def _request(self, path: str, payload: dict[str, Any]) -> Request:
        return Request(
            url=f"{self._base_url}{path}", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )

    def _raise_transport_error(self, error: Exception) -> None:
        if isinstance(error, HTTPError):
            raise OllamaProviderError(f"Ollama HTTP error: {error.code}") from error
        if isinstance(error, TimeoutError):
            raise OllamaProviderError("Ollama request timed out") from error
        if isinstance(error, URLError):
            raise OllamaProviderError(f"Ollama network error: {error.reason}") from error
        if isinstance(error, OSError):
            raise OllamaProviderError("Ollama request failed") from error
        raise error

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        http_request = self._request(path, payload)

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


def _chunk_text(chunk: dict[str, Any]) -> str:
    message = chunk.get("message")
    return str(message.get("content", "")) if isinstance(message, dict) else ""


def _build_metrics(model: str, started: float, first_token_ms: float | None, metadata: dict[str, Any], cancelled: bool) -> InferenceMetrics:
    generated = metadata.get("eval_count") if isinstance(metadata.get("eval_count"), int) else None
    generation_ms = nanoseconds_to_ms(metadata.get("eval_duration"))
    rate = generated / (generation_ms / 1000) if generated is not None and generation_ms else None
    return InferenceMetrics(
        provider="ollama", model=model, first_token_ms=first_token_ms,
        total_ms=(time.perf_counter() - started) * 1000,
        prompt_tokens=metadata.get("prompt_eval_count") if isinstance(metadata.get("prompt_eval_count"), int) else None,
        generated_tokens=generated, tokens_per_second=rate,
        load_ms=nanoseconds_to_ms(metadata.get("load_duration")),
        prompt_evaluation_ms=nanoseconds_to_ms(metadata.get("prompt_eval_duration")),
        generation_ms=generation_ms, cancelled=cancelled,
        error_category="cancelled" if cancelled else None,
    )


def _error_category(error: Exception) -> str:
    message = str(error).casefold()
    if "cancel" in message:
        return "cancelled"
    if "timed out" in message:
        return "timeout"
    if "network" in message or "request failed" in message:
        return "connection"
    if "http" in message:
        return "http"
    return "provider"
