"""Ollama model provider implementation."""

import base64
from collections.abc import Callable
from dataclasses import dataclass
import json
import logging
import re
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lina.brain.model_provider import (
    EmptyModelResponseError,
    ModelProvider,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
)
from lina.inference.models import InferenceMetrics, nanoseconds_to_ms


class OllamaProviderError(ModelProviderError):
    """Raised when the Ollama provider cannot generate a response."""


@dataclass(frozen=True, slots=True)
class OllamaResponseDiagnostics:
    format_type: str
    content_field_found: bool
    content_length: int
    stream_chunk_count: int
    retry_used: bool
    model: str
    request_duration_ms: int
    empty_response_count: int


@dataclass(frozen=True, slots=True)
class NormalizedOllamaResponse:
    text: str
    format_type: str
    content_field_found: bool
    chunk_count: int


_logger = logging.getLogger("lina.ollama")


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
        first_token_timeout: float | None = None,
        total_timeout: float | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._max_image_bytes = max_image_bytes
        self._opener = opener
        self._keep_alive = keep_alive
        self._max_output_tokens = max_output_tokens
        self._stream = stream
        self._first_token_timeout = first_token_timeout or timeout
        self._total_timeout = total_timeout or timeout * 4
        self._last_metrics: InferenceMetrics | None = None
        self._cancelled = threading.Event()
        self._response_lock = threading.Lock()
        self._active_response: Any | None = None
        self._last_response_diagnostics: OllamaResponseDiagnostics | None = None
        self._empty_response_count = 0

    @property
    def last_metrics(self) -> InferenceMetrics | None:
        return self._last_metrics

    @property
    def last_response_diagnostics(self) -> OllamaResponseDiagnostics | None:
        return self._last_response_diagnostics

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
                "temperature": 0.1 if request.temperature is None else request.temperature,
            },
        }
        if request.top_p is not None:
            payload["options"]["top_p"] = request.top_p
        if request.repeat_penalty is not None:
            payload["options"]["repeat_penalty"] = request.repeat_penalty
        if request.stream is not None:
            payload["stream"] = request.stream
        max_output_tokens = request.max_output_tokens or self._max_output_tokens
        if max_output_tokens is not None:
            payload["options"]["num_predict"] = max_output_tokens
        keep_alive = request.keep_alive if request.keep_alive is not None else self._keep_alive
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        if request.image_attachment is not None:
            payload["think"] = False
        try:
            chunks = self._post_stream("/api/chat", payload, started, stream=request.stream)
        except OllamaProviderError as error:
            self._last_metrics = InferenceMetrics(
                provider="ollama", model=model, first_token_ms=None,
                total_ms=(time.perf_counter() - started) * 1000,
                cancelled=self._cancelled.is_set(), error_category=_error_category(error),
            )
            raise
        normalized = normalize_ollama_response(chunks, camera=request.image_attachment is not None)
        retry_used = False
        if not normalized.text:
            self._empty_response_count += 1
            if request.image_attachment is not None and not self._cancelled.is_set():
                retry_used = True
                retry_payload = _empty_vision_retry_payload(payload)
                chunks = self._post_stream("/api/chat", retry_payload, started, stream=False)
                normalized = normalize_ollama_response(chunks, camera=True)
                if not normalized.text:
                    self._empty_response_count += 1

        response_data = chunks[-1]

        first_content = next((chunk for chunk in chunks if _chunk_text(chunk)), None)
        first_token_ms = (
            (float(first_content.get("_received_at", started)) - started) * 1000
            if first_content is not None else None
        )
        self._last_metrics = _build_metrics(
            model, started, first_token_ms, response_data, self._cancelled.is_set()
        )
        self._last_response_diagnostics = OllamaResponseDiagnostics(
            format_type=normalized.format_type,
            content_field_found=normalized.content_field_found,
            content_length=len(normalized.text),
            stream_chunk_count=normalized.chunk_count,
            retry_used=retry_used,
            model=model,
            request_duration_ms=round((time.perf_counter() - started) * 1000),
            empty_response_count=self._empty_response_count,
        )
        _logger.info(
            "ollama_response format_type=%s content_field_found=%s content_length=%d stream_chunk_count=%d retry_used=%s model=%s request_duration_ms=%d empty_response_count=%d",
            self._last_response_diagnostics.format_type,
            self._last_response_diagnostics.content_field_found,
            self._last_response_diagnostics.content_length,
            self._last_response_diagnostics.stream_chunk_count,
            self._last_response_diagnostics.retry_used,
            self._last_response_diagnostics.model,
            self._last_response_diagnostics.request_duration_ms,
            self._last_response_diagnostics.empty_response_count,
        )
        if not normalized.text:
            raise EmptyModelResponseError("Ollama vision response remained empty after retry")
        return ModelResponse(text=normalized.text)

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

    def _post_stream(
        self,
        path: str,
        payload: dict[str, Any],
        started: float,
        stream: bool | None = None,
    ) -> list[dict[str, Any]]:
        stream_enabled = self._stream if stream is None else stream
        payload["stream"] = stream_enabled
        if not stream_enabled:
            response = self._post_json(path, payload)
            if self._cancelled.is_set():
                raise OllamaProviderError("Ollama request cancelled")
            response["_received_at"] = time.perf_counter()
            return [response]
        http_request = self._request(path, payload)
        first_token_received = False
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
                    elapsed = time.perf_counter() - started
                    if elapsed >= self._total_timeout:
                        raise OllamaProviderError("Ollama generation timed out")
                    try:
                        preview = json.loads(line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        preview = None
                    if isinstance(preview, dict) and _chunk_text(preview):
                        first_token_received = True
                    if (
                        not first_token_received
                        and elapsed >= self._first_token_timeout
                    ):
                        raise OllamaProviderError("Ollama first token timed out")
                    if self._cancelled.is_set():
                        raise OllamaProviderError("Ollama request cancelled")
        except Exception as error:
            if isinstance(error, OllamaProviderError):
                raise
            if self._cancelled.is_set():
                raise OllamaProviderError("Ollama request cancelled") from error
            if isinstance(error, TimeoutError):
                message = (
                    "Ollama generation timed out"
                    if first_token_received
                    else "Ollama first token timed out"
                )
                raise OllamaProviderError(message) from error
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
                with self._response_lock:
                    self._active_response = response
                raw_response = response.read()
        except Exception as error:
            if self._cancelled.is_set():
                raise OllamaProviderError("Ollama request cancelled") from error
            self._raise_transport_error(error)
        finally:
            with self._response_lock:
                self._active_response = None

        try:
            decoded_response = json.loads(raw_response.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OllamaProviderError("Ollama returned invalid JSON") from error

        if not isinstance(decoded_response, dict):
            raise OllamaProviderError("Ollama returned an invalid response shape")

        return decoded_response


def _chunk_text(chunk: Any) -> str:
    content, _format_type, _found = _extract_content(chunk)
    return content if isinstance(content, str) else ""


def normalize_ollama_response(chunks: list[Any], *, camera: bool = False) -> NormalizedOllamaResponse:
    parts: list[str] = []
    formats: list[str] = []
    content_found = False
    for chunk in chunks:
        content, format_type, found = _extract_content(chunk)
        content_found = content_found or found
        if found:
            formats.append(format_type)
        if isinstance(content, str) and content:
            current = "".join(parts)
            if content == (parts[-1] if parts else None) or current.endswith(content):
                continue
            if current and content.startswith(current):
                parts[:] = [content]
            else:
                parts.append(content)
    text = _normalize_response_text("".join(parts), camera=camera)
    format_type = formats[0] if formats and len(set(formats)) == 1 else "mixed" if formats else "unknown"
    return NormalizedOllamaResponse(text, format_type, content_found, len(chunks))


def _extract_content(response: Any) -> tuple[Any, str, bool]:
    if isinstance(response, dict):
        message = response.get("message")
        if isinstance(message, dict) and "content" in message:
            return message.get("content"), "message.content", True
        if message is not None and hasattr(message, "content"):
            return getattr(message, "content"), "message.content.attribute", True
        if "response" in response:
            return response.get("response"), "response", True
        return None, "unknown", False
    message = getattr(response, "message", None)
    if message is not None and hasattr(message, "content"):
        return getattr(message, "content"), "message.content.attribute", True
    if hasattr(response, "response"):
        return getattr(response, "response"), "response.attribute", True
    return None, "unknown", False


def _normalize_response_text(value: Any, *, camera: bool) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    fenced = re.fullmatch(r"```(?:\w+)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    text = re.sub(r"^(?:lina|yanıt|cevap)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
    if text.casefold() in {"null", "none", "boş", "bos", "n/a"}:
        return ""
    if not any(character.isalnum() for character in text):
        return ""
    if camera and len(text) > 240:
        first_sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
        text = first_sentence if len(first_sentence) <= 240 else text[:239].rstrip() + "…"
    return text


def _empty_vision_retry_payload(payload: dict[str, Any]) -> dict[str, Any]:
    messages = [dict(message) for message in payload.get("messages", ())]
    user_message = next((message for message in reversed(messages) if message.get("role") == "user"), None)
    if user_message is not None:
        user_message["content"] = "Bu görüntüde ne görüyorsun? Tek kısa Türkçe cümle yaz."
    options = dict(payload.get("options", {}))
    options["temperature"] = 0.0
    return {**payload, "messages": messages, "options": options, "stream": False}


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
    if "first token" in message:
        return "first_token_timeout"
    if "generation timed out" in message:
        return "total_timeout"
    if "timed out" in message:
        return "connection_timeout"
    if "network" in message or "request failed" in message:
        return "connection"
    if "http" in message:
        return "http"
    return "provider"
