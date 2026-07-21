"""Tests for model diagnostics service."""

import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request


from lina.services.model_diagnostics_service import (
    DiagnosticsResult,
    ModelDiagnosticsService,
    ModelStatus,
    format_status_message,
)


class FakeTagsResponse:
    """Fake HTTP response for /api/tags."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "FakeTagsResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class FakeReachableOpener:
    """Fake opener that simulates a reachable Ollama server."""

    def __init__(self, model_names: list[str] | None = None) -> None:
        self.requests: list[Request] = []
        self.timeouts: list[float] = []
        self._model_names = model_names or ["llama3"]

    def __call__(self, request: Request, timeout: float) -> FakeTagsResponse:
        self.requests.append(request)
        self.timeouts.append(timeout)
        return FakeTagsResponse(
            json.dumps(
                {"models": [{"name": model_name} for model_name in self._model_names]}
            ).encode("utf-8")
        )


class FakeUnreachableOpener:
    """Fake opener that simulates an unreachable Ollama server."""

    def __call__(self, request: Request, timeout: float) -> Any:
        raise URLError("connection refused")


class FakeTimeoutOpener:
    """Fake opener that simulates a timeout."""

    def __call__(self, request: Request, timeout: float) -> Any:
        raise TimeoutError("timed out")


# --- ModelDiagnosticsService tests ---


def test_diagnostics_returns_ready_when_ollama_reachable() -> None:
    opener = FakeReachableOpener()
    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="llama3",
        timeout=5.0,
        opener=opener,
    )

    result = service.check_status()

    assert result.status is ModelStatus.READY
    assert result.model_name == "llama3"


def test_diagnostics_returns_unreachable_when_ollama_down() -> None:
    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="llama3",
        timeout=5.0,
        opener=FakeUnreachableOpener(),
    )

    result = service.check_status()

    assert result.status is ModelStatus.OLLAMA_UNREACHABLE
    assert result.model_name == "llama3"


def test_diagnostics_returns_model_not_available_when_model_missing() -> None:
    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="missing-model",
        timeout=5.0,
        opener=FakeReachableOpener(model_names=["llama3"]),
    )

    result = service.check_status()

    assert result.status is ModelStatus.MODEL_NOT_AVAILABLE
    assert result.model_name == "missing-model"


def test_diagnostics_returns_timeout_when_ollama_times_out() -> None:
    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="llama3",
        timeout=5.0,
        opener=FakeTimeoutOpener(),
    )

    result = service.check_status()

    assert result.status is ModelStatus.TIMEOUT
    assert result.model_name == "llama3"


def test_diagnostics_returns_not_configured_when_model_empty() -> None:
    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="",
        timeout=5.0,
        opener=FakeReachableOpener(),
    )

    result = service.check_status()

    assert result.status is ModelStatus.MODEL_NOT_CONFIGURED
    assert result.model_name == ""


def test_diagnostics_returns_not_configured_when_model_whitespace() -> None:
    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="   ",
        timeout=5.0,
        opener=FakeReachableOpener(),
    )

    result = service.check_status()

    assert result.status is ModelStatus.MODEL_NOT_CONFIGURED


def test_diagnostics_configured_model_property() -> None:
    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="llama3.2:3b",
        opener=FakeReachableOpener(),
    )

    assert service.configured_model == "llama3.2:3b"


def test_diagnostics_sends_get_to_api_tags() -> None:
    opener = FakeReachableOpener()
    service = ModelDiagnosticsService(
        base_url="http://localhost:11434/",
        model="llama3",
        timeout=3.0,
        opener=opener,
    )

    service.check_status()

    assert len(opener.requests) == 1
    assert opener.requests[0].full_url == "http://localhost:11434/api/tags"
    assert opener.requests[0].get_method() == "GET"
    assert opener.timeouts == [3.0]


def test_diagnostics_handles_invalid_json_from_ollama() -> None:
    def bad_json_opener(request: Request, timeout: float) -> FakeTagsResponse:
        return FakeTagsResponse(b"not-json")

    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="llama3",
        opener=bad_json_opener,
    )

    result = service.check_status()

    assert result.status is ModelStatus.OLLAMA_UNREACHABLE


def test_diagnostics_handles_non_dict_json_from_ollama() -> None:
    def array_opener(request: Request, timeout: float) -> FakeTagsResponse:
        return FakeTagsResponse(b"[1, 2, 3]")

    service = ModelDiagnosticsService(
        base_url="http://localhost:11434",
        model="llama3",
        opener=array_opener,
    )

    result = service.check_status()

    assert result.status is ModelStatus.OLLAMA_UNREACHABLE


# --- format_status_message tests ---


def test_format_status_message_ready() -> None:
    result = DiagnosticsResult(
        status=ModelStatus.READY,
        model_name="llama3",
        message="Model hazır.",
    )
    assert format_status_message(result) == "Model hazır: llama3"


def test_format_status_message_connecting() -> None:
    result = DiagnosticsResult(
        status=ModelStatus.CONNECTING,
        model_name="llama3",
        message="",
    )
    assert format_status_message(result) == "Modele bağlanılıyor..."


def test_format_status_message_unreachable() -> None:
    result = DiagnosticsResult(
        status=ModelStatus.OLLAMA_UNREACHABLE,
        model_name="llama3",
        message="",
    )
    assert "Ollama'ya ulaşılamıyor" in format_status_message(result)


def test_format_status_message_not_configured() -> None:
    result = DiagnosticsResult(
        status=ModelStatus.MODEL_NOT_CONFIGURED,
        model_name="",
        message="",
    )
    assert "yapılandırılmamış" in format_status_message(result)


def test_format_status_message_model_not_available() -> None:
    result = DiagnosticsResult(
        status=ModelStatus.MODEL_NOT_AVAILABLE,
        model_name="missing-model",
        message="",
    )
    assert "Model yüklü değil: missing-model" == format_status_message(result)


def test_format_status_message_timeout() -> None:
    result = DiagnosticsResult(
        status=ModelStatus.TIMEOUT,
        model_name="llama3",
        message="",
    )
    assert "zaman aşımına uğradı" in format_status_message(result)


# --- ModelStatus enum tests ---


def test_model_status_values() -> None:
    assert ModelStatus.READY.value == "ready"
    assert ModelStatus.CONNECTING.value == "connecting"
    assert ModelStatus.OLLAMA_UNREACHABLE.value == "ollama_unreachable"
    assert ModelStatus.MODEL_NOT_CONFIGURED.value == "model_not_configured"
    assert ModelStatus.MODEL_NOT_AVAILABLE.value == "model_not_available"
    assert ModelStatus.TIMEOUT.value == "timeout"
def test_model_diagnostics_model_can_change() -> None:
    service = ModelDiagnosticsService("http://localhost:11434", "llama3")

    service.set_model("qwen3:4b")

    assert service.configured_model == "qwen3:4b"
