from __future__ import annotations

import json

from lina.brain.model_provider import ModelMessage, ModelRequest
from lina.integrations.ollama_provider import OllamaProvider


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
