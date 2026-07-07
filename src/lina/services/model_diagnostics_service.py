"""Model diagnostics service for Lina."""

from dataclasses import dataclass
from enum import Enum
from typing import Any
from collections.abc import Callable
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelStatus(Enum):
    """Possible model connection states."""

    READY = "ready"
    CONNECTING = "connecting"
    OLLAMA_UNREACHABLE = "ollama_unreachable"
    MODEL_NOT_CONFIGURED = "model_not_configured"


@dataclass(frozen=True)
class DiagnosticsResult:
    """Result of a model diagnostics check."""

    status: ModelStatus
    model_name: str
    message: str


def format_status_message(result: DiagnosticsResult) -> str:
    """Return a user-friendly Turkish status message."""
    if result.status is ModelStatus.READY:
        return f"Model hazır: {result.model_name}"
    if result.status is ModelStatus.CONNECTING:
        return "Modele bağlanılıyor..."
    if result.status is ModelStatus.OLLAMA_UNREACHABLE:
        return "Ollama'ya ulaşılamıyor. Ollama çalışıyor mu kontrol edin."
    if result.status is ModelStatus.MODEL_NOT_CONFIGURED:
        return "Model adı yapılandırılmamış."
    return result.message


class ModelDiagnosticsService:
    """Checks Ollama reachability and configured model status."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 5.0,
        opener: Callable[[Request, float], Any] = urlopen,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._opener = opener

    @property
    def configured_model(self) -> str:
        """Return the configured model name."""
        return self._model

    def check_status(self) -> DiagnosticsResult:
        """Check Ollama reachability and return diagnostics result."""
        if not self._model.strip():
            return DiagnosticsResult(
                status=ModelStatus.MODEL_NOT_CONFIGURED,
                model_name="",
                message="Model adı yapılandırılmamış.",
            )

        if not self._is_ollama_reachable():
            return DiagnosticsResult(
                status=ModelStatus.OLLAMA_UNREACHABLE,
                model_name=self._model,
                message="Ollama'ya ulaşılamıyor.",
            )

        return DiagnosticsResult(
            status=ModelStatus.READY,
            model_name=self._model,
            message="Model hazır.",
        )

    def _is_ollama_reachable(self) -> bool:
        """Check if Ollama HTTP API is reachable."""
        request = Request(
            url=f"{self._base_url}/api/tags",
            method="GET",
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                raw = response.read()
                data = json.loads(raw.decode("utf-8"))
                return isinstance(data, dict)
        except (HTTPError, URLError, OSError, json.JSONDecodeError, UnicodeDecodeError):
            return False
