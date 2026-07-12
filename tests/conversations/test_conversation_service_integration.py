"""Integration tests for ConversationService persistence boundaries."""

from datetime import datetime, timezone

from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.conversations.repository import ConversationRepository
from lina.conversations.service import ConversationHistoryService
from lina.services.conversation_models import ConversationInput
from lina.services.conversation_service import ConversationService
from lina.vision.models import ImageAttachment, PNG_SIGNATURE


class FakeBrain:
    def __init__(self, failure: bool = False) -> None:
        self.failure = failure
        self.histories = []

    def respond_with_context(self, context):
        self.histories.append(tuple(context.conversation_history))
        if self.failure:
            raise ModelProviderError("network error")
        return ModelResponse(text=f"Yanıt: {context.user_message}")

    def respond_with_image(self, context, attachment):
        return ModelResponse(text="Görsel yanıtı")


class ReadyVision:
    def check_status(self):
        from lina.services.model_diagnostics_service import (
            VisionDiagnosticsResult,
            VisionStatus,
        )

        return VisionDiagnosticsResult(VisionStatus.READY, "vision", "Hazır")


def _service(tmp_path, brain=None):
    brain = brain or FakeBrain()
    history = ConversationHistoryService(
        ConversationRepository(tmp_path / "conversations.sqlite3")
    )
    service = ConversationService(
        brain=brain,
        vision_brain=brain,
        conversation_history_service=history,
        vision_diagnostics_service=ReadyVision(),
    )
    return service, history


def test_conversation_service_persists_text_and_restores_session_context(tmp_path) -> None:
    service, history = _service(tmp_path)
    service.handle_message("Bir proje fikrim var")
    conversation_id = history.active_session.id or 0

    messages = history._repository.list_messages(conversation_id)  # type: ignore[union-attr]

    assert [(message.role, message.content) for message in messages] == [
        ("user", "Bir proje fikrim var"),
        ("assistant", "Yanıt: Bir proje fikrim var"),
    ]


def test_model_failure_keeps_user_message_without_empty_assistant(tmp_path) -> None:
    service, history = _service(tmp_path, FakeBrain(failure=True))

    try:
        service.handle_message("Model hata verecek")
    except ModelProviderError:
        pass

    messages = history._repository.list_messages(history.active_session.id or 0)  # type: ignore[union-attr]
    assert [message.role for message in messages] == ["user"]


def test_new_session_does_not_leak_previous_history(tmp_path) -> None:
    brain = FakeBrain()
    service, history = _service(tmp_path, brain)
    service.handle_message("İlk oturum")
    service.start_new_session()
    service.handle_message("İkinci oturum")

    assert brain.histories[-1] == ()


def test_vision_user_message_persists_metadata_without_attachment_bytes(tmp_path) -> None:
    service, history = _service(tmp_path)
    service.handle_input(
        ConversationInput(
            text="Bu görseli açıkla",
            image_attachment=ImageAttachment(
                mime_type="image/png",
                data=PNG_SIGNATURE + b"temporary",
                width=10,
                height=10,
                captured_at=datetime.now(timezone.utc),
                source="screen_capture_region",
                display_name="ignored.png",
            ),
        )
    )

    message = history._repository.list_messages(history.active_session.id or 0)[0]  # type: ignore[union-attr]
    assert message.had_image is True
    assert message.image_source == "screen_region"
    assert not hasattr(message, "data")
