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
    MODEL_NOT_AVAILABLE = "model_not_available"
    TIMEOUT = "timeout"


class VisionStatus(Enum):
    """Possible local vision capability states."""

    READY = "ready"
    DISABLED = "disabled"
    OLLAMA_UNREACHABLE = "ollama_unreachable"
    MODEL_NOT_AVAILABLE = "model_not_available"
    VISION_NOT_SUPPORTED = "vision_not_supported"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True)
class DiagnosticsResult:
    """Result of a model diagnostics check."""

    status: ModelStatus
    model_name: str
    message: str


@dataclass(frozen=True)
class VisionDiagnosticsResult:
    """Result of a configured local vision capability check."""

    status: VisionStatus
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
    if result.status is ModelStatus.MODEL_NOT_AVAILABLE:
        return f"Model yüklü değil: {result.model_name}"
    if result.status is ModelStatus.TIMEOUT:
        return "Ollama yanıt vermedi. Bağlantı zaman aşımına uğradı."
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

        available_models = self._get_available_models()
        if available_models is ModelStatus.TIMEOUT:
            return DiagnosticsResult(
                status=ModelStatus.TIMEOUT,
                model_name=self._model,
                message="Ollama yanıt vermedi.",
            )
        if available_models is ModelStatus.OLLAMA_UNREACHABLE:
            return DiagnosticsResult(
                status=ModelStatus.OLLAMA_UNREACHABLE,
                model_name=self._model,
                message="Ollama'ya ulaşılamıyor.",
            )
        if available_models == ():
            return DiagnosticsResult(
                status=ModelStatus.MODEL_NOT_AVAILABLE,
                model_name=self._model,
                message="Yapılandırılmış model Ollama içinde bulunamadı.",
            )
        if self._model not in available_models:
            return DiagnosticsResult(
                status=ModelStatus.MODEL_NOT_AVAILABLE,
                model_name=self._model,
                message="Yapılandırılmış model Ollama içinde bulunamadı.",
            )

        return DiagnosticsResult(
            status=ModelStatus.READY,
            model_name=self._model,
            message="Model hazır.",
        )

    def _get_available_models(self) -> tuple[str, ...] | ModelStatus:
        """Return available Ollama model names, or an error status."""
        request = Request(
            url=f"{self._base_url}/api/tags",
            method="GET",
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                raw = response.read()
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, dict):
                    return ModelStatus.OLLAMA_UNREACHABLE
                models = data.get("models")
                if not isinstance(models, list):
                    return ()
                names: list[str] = []
                for model in models:
                    if isinstance(model, dict) and isinstance(model.get("name"), str):
                        names.append(model["name"])
                return tuple(names)
        except TimeoutError:
            return ModelStatus.TIMEOUT
        except (HTTPError, URLError, OSError, json.JSONDecodeError, UnicodeDecodeError):
            return ModelStatus.OLLAMA_UNREACHABLE


class VisionDiagnosticsService:
    """Validate a configured Ollama model through its declared capabilities."""

    def __init__(
        self,
        base_url: str,
        model: str,
        enabled: bool = True,
        timeout: float = 5.0,
        opener: Callable[[Request, float], Any] = urlopen,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model.strip()
        self._enabled = enabled
        self._timeout = timeout
        self._opener = opener

    @property
    def configured_model(self) -> str:
        """Return the configured vision model name."""
        return self._model

    def check_status(self) -> VisionDiagnosticsResult:
        """Check model presence and the explicit Ollama vision capability."""
        if not self._enabled:
            return self._result(VisionStatus.DISABLED, "Vision devre dışı.")
        if not self._model:
            return self._result(
                VisionStatus.MODEL_NOT_AVAILABLE,
                "Vision modeli yapılandırılmamış.",
            )

        request = Request(
            url=f"{self._base_url}/api/show",
            data=json.dumps({"model": self._model}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                raw = response.read()
        except HTTPError as error:
            if error.code == 404:
                return self._result(
                    VisionStatus.MODEL_NOT_AVAILABLE,
                    "Görüntü analizi için vision modeli kurulu değil.",
                )
            return self._result(
                VisionStatus.OLLAMA_UNREACHABLE,
                "Ollama vision modelini doğrulayamadı.",
            )
        except TimeoutError:
            return self._result(VisionStatus.TIMEOUT, "Vision kontrolü zaman aşımına uğradı.")
        except (URLError, OSError):
            return self._result(
                VisionStatus.OLLAMA_UNREACHABLE,
                "Lina yerel modele ulaşamadı.",
            )

        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._result(
                VisionStatus.INVALID_RESPONSE,
                "Vision capability cevabı okunamadı.",
            )
        if not isinstance(data, dict) or not isinstance(data.get("capabilities"), list):
            return self._result(
                VisionStatus.INVALID_RESPONSE,
                "Vision capability cevabı geçersiz.",
            )
        capabilities = data["capabilities"]
        if "vision" not in capabilities:
            return self._result(
                VisionStatus.VISION_NOT_SUPPORTED,
                "Seçili Ollama modeli görüntü desteğine sahip değil.",
            )
        return self._result(VisionStatus.READY, "Vision hazır.")

    def _result(self, status: VisionStatus, message: str) -> VisionDiagnosticsResult:
        return VisionDiagnosticsResult(
            status=status,
            model_name=self._model,
            message=message,
        )
