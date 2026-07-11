"""Tests for local Ollama vision capability diagnostics."""

import json
from urllib.error import HTTPError, URLError

from lina.services.model_diagnostics_service import (
    VisionDiagnosticsService,
    VisionStatus,
)


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return self._body


def test_vision_diagnostics_returns_ready_for_declared_capability() -> None:
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return FakeResponse({"capabilities": ["completion", "vision"]})

    service = VisionDiagnosticsService(
        base_url="http://localhost:11434/",
        model="qwen3-vl:2b",
        timeout=4.0,
        opener=opener,
    )

    result = service.check_status()

    assert result.status is VisionStatus.READY
    assert result.model_name == "qwen3-vl:2b"
    assert requests[0][0].full_url == "http://localhost:11434/api/show"
    assert requests[0][0].get_method() == "POST"
    assert json.loads(requests[0][0].data) == {"model": "qwen3-vl:2b"}
    assert requests[0][1] == 4.0


def test_vision_diagnostics_rejects_model_without_vision_capability() -> None:
    service = VisionDiagnosticsService(
        base_url="http://localhost:11434",
        model="llama3.2:3b",
        opener=lambda request, timeout: FakeResponse(
            {"capabilities": ["completion", "tools"]}
        ),
    )

    result = service.check_status()

    assert result.status is VisionStatus.VISION_NOT_SUPPORTED
    assert "görüntü desteğine sahip değil" in result.message


def test_vision_diagnostics_reports_missing_model() -> None:
    def opener(request, timeout):
        raise HTTPError(request.full_url, 404, "not found", None, None)

    result = VisionDiagnosticsService(
        "http://localhost:11434", "missing", opener=opener
    ).check_status()

    assert result.status is VisionStatus.MODEL_NOT_AVAILABLE


def test_vision_diagnostics_reports_timeout() -> None:
    def opener(request, timeout):
        raise TimeoutError("timed out")

    result = VisionDiagnosticsService(
        "http://localhost:11434", "vision", opener=opener
    ).check_status()

    assert result.status is VisionStatus.TIMEOUT


def test_vision_diagnostics_reports_unreachable_ollama() -> None:
    def opener(request, timeout):
        raise URLError("connection refused")

    result = VisionDiagnosticsService(
        "http://localhost:11434", "vision", opener=opener
    ).check_status()

    assert result.status is VisionStatus.OLLAMA_UNREACHABLE


def test_vision_diagnostics_reports_malformed_capability_response() -> None:
    result = VisionDiagnosticsService(
        "http://localhost:11434",
        "vision",
        opener=lambda request, timeout: FakeResponse({"capabilities": "vision"}),
    ).check_status()

    assert result.status is VisionStatus.INVALID_RESPONSE


def test_vision_diagnostics_skips_http_when_disabled() -> None:
    calls = []
    service = VisionDiagnosticsService(
        "http://localhost:11434",
        "vision",
        enabled=False,
        opener=lambda request, timeout: calls.append(request),
    )

    result = service.check_status()

    assert result.status is VisionStatus.DISABLED
    assert calls == []
