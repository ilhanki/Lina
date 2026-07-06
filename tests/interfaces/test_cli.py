from io import StringIO

from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.interfaces.cli import LinaCli


class FakeConversationService:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def handle_message(self, user_message: str) -> ModelResponse:
        self.messages.append(user_message)
        return ModelResponse(text=f"Response: {user_message}")


class FailingConversationService:
    def handle_message(self, user_message: str) -> ModelResponse:
        raise ModelProviderError("Ollama model is not configured")


def test_cli_prints_banner() -> None:
    output_stream = StringIO()
    cli = LinaCli(
        conversation_service=FakeConversationService(),
        input_stream=StringIO("exit\n"),
        output_stream=output_stream,
    )

    cli.run()

    output = output_stream.getvalue()
    assert "Lina v0.1.0" in output
    assert "Merhaba İlhan." in output
    assert "Hazırım." in output


def test_cli_sends_user_messages_to_conversation_service() -> None:
    service = FakeConversationService()
    cli = LinaCli(
        conversation_service=service,
        input_stream=StringIO("Hello\nquit\n"),
        output_stream=StringIO(),
    )

    cli.run()

    assert service.messages == ["Hello"]


def test_cli_prints_conversation_response() -> None:
    output_stream = StringIO()
    cli = LinaCli(
        conversation_service=FakeConversationService(),
        input_stream=StringIO("Hello\nexit\n"),
        output_stream=output_stream,
    )

    cli.run()

    assert "Response: Hello" in output_stream.getvalue()


def test_cli_ignores_empty_messages() -> None:
    service = FakeConversationService()
    cli = LinaCli(
        conversation_service=service,
        input_stream=StringIO("\nexit\n"),
        output_stream=StringIO(),
    )

    cli.run()

    assert service.messages == []


def test_cli_stops_on_quit_commands() -> None:
    service = FakeConversationService()
    cli = LinaCli(
        conversation_service=service,
        input_stream=StringIO("quit\nHello\n"),
        output_stream=StringIO(),
    )

    cli.run()

    assert service.messages == []


def test_cli_prints_model_provider_errors_without_crashing() -> None:
    output_stream = StringIO()
    cli = LinaCli(
        conversation_service=FailingConversationService(),
        input_stream=StringIO("Hello\nquit\n"),
        output_stream=output_stream,
    )

    cli.run()

    assert "Model provider error: Ollama model is not configured" in output_stream.getvalue()
