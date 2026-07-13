"""Asynchronous-friendly benchmark and model lifecycle coordination."""

from __future__ import annotations

import threading
from typing import Protocol

from lina.brain.model_provider import ModelMessage, ModelRequest
from lina.inference.models import InferenceMetrics


BENCHMARK_PROMPT = "Yalnızca 'Hazır.' yazarak kısa cevap ver."
WARMUP_PROMPT = "Hazır."


class ProfilingProvider(Protocol):
    @property
    def last_metrics(self) -> InferenceMetrics | None: ...
    def generate(self, request: ModelRequest): ...
    def cancel(self) -> None: ...
    def unload(self) -> bool: ...


class InferenceDiagnosticsService:
    def __init__(self, provider: ProfilingProvider) -> None:
        self._provider = provider
        self._cancelled = threading.Event()

    @property
    def last_metrics(self) -> InferenceMetrics | None:
        return self._provider.last_metrics

    def benchmark(self) -> InferenceMetrics:
        self._cancelled.clear()
        self._provider.generate(ModelRequest(messages=(ModelMessage("user", BENCHMARK_PROMPT),)))
        metrics = self._provider.last_metrics
        if metrics is None:
            raise RuntimeError("Performans verisi alınamadı.")
        return metrics

    def cancel(self) -> None:
        self._cancelled.set()
        self._provider.cancel()


class ModelLifecycleService:
    """Avoid intentionally keeping text and vision models resident together."""

    def __init__(self, text_provider: ProfilingProvider, vision_provider: ProfilingProvider) -> None:
        self._text = text_provider
        self._vision = vision_provider
        self._warmup_cancelled = threading.Event()

    def prepare_text(self) -> None:
        self._vision.unload()

    def prepare_vision(self) -> None:
        self._text.unload()

    def finish_vision(self) -> None:
        self._vision.unload()

    def warm_up(self) -> InferenceMetrics | None:
        self._warmup_cancelled.clear()
        self.prepare_text()
        self._text.generate(ModelRequest(messages=(ModelMessage("user", WARMUP_PROMPT),)))
        return None if self._warmup_cancelled.is_set() else self._text.last_metrics

    def cancel_warm_up(self) -> None:
        self._warmup_cancelled.set()
        self._text.cancel()

    def cancel_active(self) -> None:
        self._text.cancel()
        self._vision.cancel()

    def shutdown(self) -> None:
        self.cancel_warm_up()
        self._vision.cancel()
        self._text.unload()
        self._vision.unload()
