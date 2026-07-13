from __future__ import annotations

import json

from lina.brain.model_provider import ModelMessage, ModelRequest
from lina.integrations.ollama_provider import OllamaProvider
from lina.integrations.ollama_provider import OllamaProviderError
import pytest


class StreamingResponse:
    def __init__(self, lines):
        self.lines = iter(lines)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def readline(self):
        return next(self.lines, b"")

    def close(self):
        return None


def test_streaming_response_collects_text_and_exact_ollama_metrics():
    chunks = [
        {"message": {"content": "Merhaba "}, "done": False},
        {"message": {"content": "dünya"}, "done": True, "prompt_eval_count": 4,
         "eval_count": 2, "eval_duration": 1_000_000_000, "load_duration": 500_000_000},
    ]
    response = StreamingResponse([(json.dumps(item) + "\n").encode() for item in chunks])
    provider = OllamaProvider("http://localhost:11434", "model", opener=lambda *_args, **_kwargs: response, stream=True)
    result = provider.generate(ModelRequest((ModelMessage("user", "test"),)))
    assert result.text == "Merhaba dünya"
    assert provider.last_metrics.prompt_tokens == 4
    assert provider.last_metrics.generated_tokens == 2
    assert provider.last_metrics.tokens_per_second == 2.0
    assert provider.last_metrics.load_ms == 500.0
    assert provider.last_metrics.first_token_ms is not None


def test_missing_ollama_metadata_stays_missing():
    response = StreamingResponse([b'{"message":{"content":"ok"},"done":true}\n'])
    provider = OllamaProvider("http://localhost:11434", "model", opener=lambda *_args, **_kwargs: response, stream=True)
    provider.generate(ModelRequest((ModelMessage("user", "test"),)))
    metrics = provider.last_metrics
    assert metrics.prompt_tokens is None
    assert metrics.generated_tokens is None
    assert metrics.tokens_per_second is None


class TimeoutResponse(StreamingResponse):
    def __init__(self, first_line=None):
        self.first_line = first_line
        self.used = False

    def readline(self):
        if not self.used and self.first_line is not None:
            self.used = True
            return self.first_line
        raise TimeoutError()


def test_first_token_timeout_has_distinct_private_category():
    response = TimeoutResponse()
    provider = OllamaProvider(
        "http://localhost:11434", "model",
        opener=lambda *_args, **_kwargs: response, stream=True,
    )
    with pytest.raises(OllamaProviderError, match="first token"):
        provider.generate(ModelRequest((ModelMessage("user", "test"),)))
    assert provider.last_metrics.error_category == "first_token_timeout"


def test_total_generation_timeout_has_distinct_private_category():
    response = TimeoutResponse(
        '{"message":{"content":"başladı"}}\n'.encode("utf-8")
    )
    provider = OllamaProvider(
        "http://localhost:11434", "model",
        opener=lambda *_args, **_kwargs: response, stream=True,
    )
    with pytest.raises(OllamaProviderError, match="generation timed out"):
        provider.generate(ModelRequest((ModelMessage("user", "test"),)))
    assert provider.last_metrics.error_category == "total_timeout"
