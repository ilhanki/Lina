"""Brain orchestrator for Lina."""

from typing import Sequence

from lina.brain.conversation_context import ConversationContext
from lina.brain.model_provider import ModelMessage, ModelProvider, ModelRequest, ModelResponse
from lina.brain.prompt_builder import ConversationTurn, PromptBuilder
from lina.brain.prompts import DEFAULT_SYSTEM_PROMPT
from lina.vision.models import ImageAttachment


class Brain:
    """Minimal Brain orchestrator."""

    def __init__(
        self,
        model_provider: ModelProvider,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self._model_provider = model_provider
        self._prompt_builder = prompt_builder or PromptBuilder(
            system_prompt=DEFAULT_SYSTEM_PROMPT
        )

    def respond(
        self,
        user_message: str,
        conversation_history: Sequence[ConversationTurn] | None = None,
        project_context: str | None = None,
    ) -> ModelResponse:
        messages = self._prompt_builder.build(
            user_message=user_message,
            history=conversation_history,
            project_context=project_context,
        )
        request = ModelRequest(messages=messages, temperature=0.45, top_p=0.9, repeat_penalty=1.08)
        return self._model_provider.generate(request)

    def respond_with_context(self, context: ConversationContext) -> ModelResponse:
        request = ModelRequest(
            messages=self._prompt_builder.build_from_context(context),
            temperature=0.45, top_p=0.9, repeat_penalty=1.08,
        )
        return self._model_provider.generate(request)

    def respond_with_image(
        self,
        context: ConversationContext,
        attachment: ImageAttachment,
    ) -> ModelResponse:
        """Generate one grounded response from an explicit image attachment."""
        request = ModelRequest(
            messages=self._prompt_builder.build_from_context(context),
            image_attachment=attachment,
        )
        return self._model_provider.generate(request)

    def repair_response(self, user_question: str, draft: str,
                        rejection_reasons: tuple[str, ...] = ()) -> str:
        """Run one low-temperature, non-streaming repair without full history."""
        messages = (
            ModelMessage(
                role="system",
                content=(
                    "Kullanıcının aşağıdaki isteğine doğrudan cevap veren, doğal ve doğru "
                    "Türkçe bir yanıt oluştur. Reddedilen cevaptaki bozuk kelimeleri, yabancı "
                    "dil kırıntılarını, iç sistem açıklamalarını, alakasız görev aşamalarını "
                    "ve tekrarları kullanma. Kullanıcının istemediği yeni bilgi ekleme. "
                    "Python, tuple, list, API, Git, GitHub, PySide6, Codex ve Ollama gibi "
                    "gerekli teknik terimleri doğru biçimde koru."
                ),
            ),
            ModelMessage(
                role="user",
                content=(f"Orijinal kullanıcı isteği:\n{user_question}\n\n"
                         f"Reddedilme nedenleri: {', '.join(rejection_reasons) or 'quality'}\n\n"
                         f"Reddedilen cevap:\n{draft}"),
            ),
        )
        return self._model_provider.generate(ModelRequest(messages=messages, temperature=0.1, top_p=0.8, repeat_penalty=1.05, stream=False)).text
