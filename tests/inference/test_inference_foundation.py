from __future__ import annotations

import pytest

from lina.brain.model_provider import ModelResponse
from lina.inference.models import InferenceMetrics, nanoseconds_to_ms
from lina.inference.service import InferenceDiagnosticsService, ModelLifecycleService


class Provider:
    def __init__(self, model="text"):
        self.calls = []
        self.cancelled = 0
        self.unloaded = 0
        self.last_metrics = InferenceMetrics("ollama", model, 10, 20, generated_tokens=2, tokens_per_second=100)

    def generate(self, request):
        self.calls.append(request)
        return ModelResponse("Hazır.")

    def cancel(self):
        self.cancelled += 1

    def unload(self):
        self.unloaded += 1
        return True


def test_metrics_are_typed_and_privacy_safe():
    metrics = InferenceMetrics("ollama", "model", 12.5, 30.0, prompt_tokens=3)
    assert metrics.provider == "ollama"
    assert not hasattr(metrics, "prompt")
    with pytest.raises(ValueError):
        InferenceMetrics("ollama", "model", None, -1)


def test_nanoseconds_conversion_does_not_guess_missing_values():
    assert nanoseconds_to_ms(2_000_000) == 2.0
    assert nanoseconds_to_ms(None) is None
    assert nanoseconds_to_ms("2") is None


def test_benchmark_uses_fixed_isolated_prompt():
    provider = Provider()
    service = InferenceDiagnosticsService(provider)
    metrics = service.benchmark()
    assert metrics.model == "text"
    request = provider.calls[0]
    assert len(request.messages) == 1
    assert "Hazır" in request.messages[0].content
    assert not hasattr(request, "conversation_id")


def test_benchmark_cancel_reaches_provider():
    provider = Provider()
    service = InferenceDiagnosticsService(provider)
    service.cancel()
    assert provider.cancelled == 1


def test_text_vision_lifecycle_separates_models():
    text = Provider("text")
    vision = Provider("vision")
    lifecycle = ModelLifecycleService(text, vision)
    lifecycle.prepare_text()
    lifecycle.prepare_vision()
    lifecycle.finish_vision()
    assert text.unloaded == 1
    assert vision.unloaded == 2


def test_warmup_is_private_and_shutdown_cleans_both_models():
    text = Provider("text")
    vision = Provider("vision")
    lifecycle = ModelLifecycleService(text, vision)
    metrics = lifecycle.warm_up()
    assert metrics.model == "text"
    assert len(text.calls) == 1
    lifecycle.shutdown()
    assert text.cancelled == 1
    assert vision.cancelled == 1
    assert text.unloaded == 1
    assert vision.unloaded == 2
