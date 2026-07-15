from datetime import datetime
import json
import threading
from types import SimpleNamespace
from urllib.request import Request

import pytest

from lina.brain.model_provider import EmptyModelResponseError, ModelMessage, ModelRequest
from lina.integrations.ollama_provider import OllamaProvider, normalize_ollama_response
from lina.vision.models import ImageAttachment, PNG_SIGNATURE


class Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self): return self
    def __exit__(self, *_args): return None
    def read(self): return self.body
    def close(self): return None


class SequenceClient:
    def __init__(self, *bodies: bytes) -> None:
        self.bodies = list(bodies)
        self.requests: list[Request] = []

    def __call__(self, request: Request, timeout: float):
        self.requests.append(request)
        return Response(self.bodies.pop(0))


class BlockingResponse(Response):
    def __init__(self) -> None:
        super().__init__(b"")
        self.started = threading.Event()
        self.closed = threading.Event()

    def read(self):
        self.started.set()
        self.closed.wait(2)
        raise OSError("private closed response")

    def close(self):
        self.closed.set()


@pytest.mark.parametrize(("response", "expected"), [
    ({"message": {"content": " Elinde bir şişe var. "}}, "Elinde bir şişe var."),
    (SimpleNamespace(message=SimpleNamespace(content="Elini kaldırıyorsun.")), "Elini kaldırıyorsun."),
    ({"response": "Görüntüde bir fare var."}, "Görüntüde bir fare var."),
    (SimpleNamespace(response="Bir bardak görünüyor."), "Bir bardak görünüyor."),
    ({"message": {"content": "```text\nElinde bir şişe var.\n```"}}, "Elinde bir şişe var."),
    ({"message": {"content": "Lina: Elini kaldırıyorsun."}}, "Elini kaldırıyorsun."),
])
def test_typed_response_formats_are_normalized(response, expected):
    assert normalize_ollama_response([response], camera=True).text == expected


@pytest.mark.parametrize("response", [
    {"message": {"content": None}},
    {"message": {"content": "   "}},
    {"message": {"content": "...!?"}},
    {"message": {"content": "null"}},
    {"message": {"content": "", "thinking": "private reasoning"}},
    {"done": True, "metadata": {"tokens": 2}},
    object(),
])
def test_empty_and_malformed_responses_normalize_to_empty(response):
    assert normalize_ollama_response([response], camera=True).text == ""


def test_stream_chunks_join_and_empty_first_chunk_is_not_failure():
    normalized = normalize_ollama_response([
        {"message": {"content": ""}, "done": False},
        {"message": {"content": "Elinde "}, "done": False},
        {"message": {"content": "bir fare var."}, "done": True},
    ], camera=True)
    assert normalized.text == "Elinde bir fare var."
    assert normalized.chunk_count == 3


def test_empty_vision_response_retries_once_with_short_non_stream_prompt():
    client = SequenceClient(
        b'{"message":{"content":"   "},"done":true}',
        ' {"message":{"content":"Elinde bir su şişesi var."},"done":true} '.encode("utf-8"),
    )
    provider = OllamaProvider("http://localhost:11434", "qwen3-vl:2b", opener=client, stream=False)
    result = provider.generate(_vision_request("PRIVATE USER QUESTION"))
    assert result.text == "Elinde bir su şişesi var."
    assert len(client.requests) == 2
    retry = json.loads(client.requests[1].data)
    assert retry["stream"] is False
    assert retry["options"]["temperature"] == 0.0
    assert retry["messages"][-1]["content"] == "Bu görüntüde ne görüyorsun? Tek kısa Türkçe cümle yaz."
    assert retry["messages"][-1]["images"]
    assert provider.last_response_diagnostics.retry_used


def test_two_empty_vision_responses_stop_after_one_retry():
    client = SequenceClient(
        b'{"message":{"content":null}}',
        b'{"message":{"content":"..."}}',
    )
    provider = OllamaProvider("http://localhost:11434", "qwen3-vl:2b", opener=client)
    with pytest.raises(EmptyModelResponseError):
        provider.generate(_vision_request())
    assert len(client.requests) == 2
    assert provider.last_response_diagnostics.empty_response_count == 2


def test_response_diagnostics_and_logs_do_not_expose_prompt_image_or_raw_response(caplog):
    secret = "PRIVATE QUESTION MUST NOT BE LOGGED"
    raw = "PRIVATE RAW RESPONSE MUST NOT BE LOGGED"
    client = SequenceClient(json.dumps({"message": {"content": raw}}).encode())
    provider = OllamaProvider("http://localhost:11434", "qwen3-vl:2b", opener=client)
    with caplog.at_level("INFO", logger="lina.ollama"):
        provider.generate(_vision_request(secret))
    diagnostics = provider.last_response_diagnostics
    assert diagnostics.content_field_found and diagnostics.content_length == len(raw)
    assert diagnostics.format_type == "message.content"
    assert secret not in caplog.text and raw not in caplog.text
    assert "private-image-bytes" not in caplog.text and "iVBOR" not in caplog.text


def test_camera_stop_cancels_empty_response_retry_without_stale_result():
    blocking = BlockingResponse()
    requests = []

    def opener(request, timeout):
        requests.append(request)
        return Response(b'{"message":{"content":""}}') if len(requests) == 1 else blocking

    provider = OllamaProvider("http://localhost:11434", "qwen3-vl:2b", opener=opener)
    errors = []
    worker = threading.Thread(
        target=lambda: _capture_error(errors, lambda: provider.generate(_vision_request())),
        daemon=True,
    )
    worker.start()
    assert blocking.started.wait(1)
    provider.cancel()
    worker.join(2)
    assert not worker.is_alive()
    assert len(requests) == 2
    assert errors and "cancelled" in str(errors[0]).casefold()
    assert blocking.closed.is_set()


def _capture_error(errors, callback):
    try:
        callback()
    except Exception as error:
        errors.append(error)


def _vision_request(question: str = "Ne görüyorsun?") -> ModelRequest:
    attachment = ImageAttachment(
        mime_type="image/png", data=PNG_SIGNATURE + b"private-image-bytes",
        width=640, height=360, captured_at=datetime(2026, 7, 15),
        source="live_camera", display_name="Camera",
    )
    return ModelRequest(
        messages=(ModelMessage("system", "safe vision"), ModelMessage("user", question)),
        image_attachment=attachment,
    )
