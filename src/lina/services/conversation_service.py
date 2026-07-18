"""Conversation service for Lina."""

from dataclasses import replace
from datetime import datetime, timezone

from lina.brain.brain import Brain
from lina.brain.conversation_context import ConversationContext
from lina.brain.context_manager import ContextManager
from lina.brain.intent import Intent, IntentType
from lina.brain.intent_analyzer import IntentAnalyzer
from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.brain.prompt_builder import ConversationTurn
from lina.conversations.service import ConversationHistoryService
from lina.files.file_access_service import FileAccessService
from lina.files.models import (
    FileAccessError,
    ForbiddenFilePathError,
    MissingAllowedFileError,
    UnknownAllowedFileError,
)
from lina.memory.models import MemoryType
from lina.memory.service import MemoryService
from lina.services.deterministic_response_service import DeterministicResponseService
from lina.services.conversation_models import ConversationInput, ConversationResult
from lina.services.model_diagnostics_service import VisionDiagnosticsService, VisionStatus
from lina.services.project_context_service import ProjectContextService
from lina.services.tool_execution_service import ToolExecutionError, ToolExecutionService
from lina.vision.models import VisionRequestError
from lina.vision.live.policy import build_camera_question_prompt
from lina.inference.service import ModelLifecycleService
from lina.quality import ResponseRepairService
from lina.codex.intent import OperationalCodexIntentError, classify_codex_intent


class ConversationService:
    """Coordinates user messages with the Brain."""

    def __init__(
        self,
        brain: Brain,
        intent_analyzer: IntentAnalyzer | None = None,
        deterministic_response_service: DeterministicResponseService | None = None,
        project_context_service: ProjectContextService | None = None,
        context_manager: ContextManager | None = None,
        tool_execution_service: ToolExecutionService | None = None,
        memory_service: MemoryService | None = None,
        file_access_service: FileAccessService | None = None,
        vision_brain: Brain | None = None,
        vision_diagnostics_service: VisionDiagnosticsService | None = None,
        consume_vision_attachment_on_success: bool = True,
        history_limit: int = 6,
        conversation_history_service: ConversationHistoryService | None = None,
        model_lifecycle_service: ModelLifecycleService | None = None,
        response_repair_service: ResponseRepairService | None = None,
    ) -> None:
        self._brain = brain
        self._intent_analyzer = intent_analyzer or IntentAnalyzer()
        self._deterministic_response_service = (
            deterministic_response_service or DeterministicResponseService()
        )
        self._context_manager = context_manager or ContextManager(
            project_context_service=project_context_service,
            history_limit=history_limit,
        )
        self._tool_execution_service = tool_execution_service
        self._memory_service = memory_service
        self._file_access_service = file_access_service
        self._vision_brain = vision_brain
        self._vision_diagnostics_service = vision_diagnostics_service
        self._consume_vision_attachment_on_success = (
            consume_vision_attachment_on_success
        )
        self._history_limit = history_limit
        self._conversation_history_service = conversation_history_service
        self._model_lifecycle_service = model_lifecycle_service
        self._response_repair_service = response_repair_service or ResponseRepairService(
            lambda question, draft, reasons: self._brain.repair_response(question, draft, reasons)
        )
        if conversation_history_service is not None:
            conversation_history_service.start()
            self._history = list(conversation_history_service.model_history())
        else:
            self._history = []

    @property
    def conversation_history_service(self) -> ConversationHistoryService | None:
        """Return the persistence coordinator for the active session."""
        return self._conversation_history_service

    def start_new_session(self) -> None:
        """Start a new isolated session and clear model context."""
        if self._conversation_history_service is not None:
            self._conversation_history_service.new_session()
        self._history.clear()

    def load_session(self, conversation_id: int) -> None:
        """Load one persisted session into the active model context."""
        if self._conversation_history_service is None:
            raise RuntimeError("Conversation persistence is not configured")
        self._conversation_history_service.load_session(conversation_id)
        self._history = list(self._conversation_history_service.model_history())

    def clear_session(self) -> None:
        """Clear active persisted messages and in-memory context."""
        if self._conversation_history_service is not None:
            self._conversation_history_service.clear()
        self._history.clear()

    def handle_message(self, user_message: str) -> ModelResponse:
        """Handle a text-only message through the existing conversation flow."""
        return self.handle_input(ConversationInput(text=user_message)).response

    def handle_input(self, conversation_input: ConversationInput) -> ConversationResult:
        """Handle text with at most one explicit image attachment."""
        user_message = conversation_input.text.strip()
        if not user_message:
            raise ValueError("Conversation input text must not be empty")
        if classify_codex_intent(user_message).operational:
            raise OperationalCodexIntentError("Operational Codex request requires bridge routing.")
        intent = self._intent_analyzer.analyze(user_message)
        attachment_consumed = False
        if self._conversation_history_service is not None:
            self._conversation_history_service.record_user_message(
                user_message,
                had_image=conversation_input.image_attachment is not None,
                image_source=_safe_image_source(conversation_input.image_attachment),
                created_at=conversation_input.created_at,
            )
        if intent.type in {
            IntentType.MEMORY_REMEMBER,
            IntentType.MEMORY_RECALL,
            IntentType.MEMORY_LIST,
            IntentType.MEMORY_FORGET,
            IntentType.MEMORY_CLEAR,
        }:
            response = self._handle_memory_intent(intent.type, user_message)
        elif intent.type in {
            IntentType.FILE_LIST_ALLOWED,
            IntentType.FILE_CAPABILITIES,
            IntentType.FILE_READ,
            IntentType.FILE_SUMMARIZE,
        }:
            response = self._handle_file_intent(intent.type, user_message)
        elif intent.type is IntentType.CURRENT_TIME and self._tool_execution_service:
            try:
                response = ModelResponse(
                    text=self._tool_execution_service.execute("current_time").text
                )
            except ToolExecutionError:
                response = self._deterministic_response_service.handle(intent)
        elif self._deterministic_response_service.can_handle(intent):
            response = self._deterministic_response_service.handle(intent)
        else:
            context = self._context_manager.build_context(
                user_message=user_message,
                intent=intent,
                conversation_history=self._history,
            )
            if conversation_input.image_attachment is None:
                if self._model_lifecycle_service is not None:
                    self._model_lifecycle_service.prepare_text()
                response = self._brain.respond_with_context(context)
            else:
                if self._model_lifecycle_service is not None:
                    self._model_lifecycle_service.prepare_vision()
                self._ensure_vision_ready()
                if self._vision_brain is None:
                    raise VisionRequestError("Vision servisi yapılandırılmamış.")
                try:
                    vision_context = (
                        ConversationContext(build_camera_question_prompt(user_message), ())
                        if conversation_input.image_attachment.source == "live_camera"
                        else context
                    )
                    response = self._vision_brain.respond_with_image(
                        vision_context,
                        conversation_input.image_attachment,
                    )
                    attachment_consumed = self._consume_vision_attachment_on_success
                finally:
                    if self._model_lifecycle_service is not None:
                        self._model_lifecycle_service.finish_vision()

        accepted = self._response_repair_service.accept(user_message, response.text)
        response = ModelResponse(accepted.text)
        assistant_created_at = None
        if not accepted.rejected:
            self._history.append(
                ConversationTurn(
                    user_message=user_message,
                    assistant_response=response.text,
                )
            )
            self._history = self._history[-self._history_limit :]
            assistant_created_at = datetime.now(timezone.utc)
            if self._conversation_history_service is not None:
                self._conversation_history_service.record_assistant_message(
                    response.text,
                    created_at=assistant_created_at,
                )
        return ConversationResult(
            response=response,
            attachment_consumed=attachment_consumed,
            assistant_created_at=assistant_created_at,
            quality_rejected=accepted.rejected,
            response_safe_for_speech=not accepted.rejected,
        )

    def _ensure_vision_ready(self) -> None:
        if self._vision_diagnostics_service is None:
            raise VisionRequestError("Vision diagnostics yapılandırılmamış.")
        result = self._vision_diagnostics_service.check_status()
        if result.status is not VisionStatus.READY:
            if result.status is VisionStatus.VISION_NOT_SUPPORTED:
                raise VisionRequestError(
                    "Seçili model görüntü analizi desteklemiyor. Ayarlardan bir vision modeli seç."
                )
            raise VisionRequestError(result.message)

    def _handle_memory_intent(
        self,
        intent_type: IntentType,
        user_message: str,
    ) -> ModelResponse:
        if self._memory_service is None:
            return ModelResponse(
                text="Hafıza sistemi şu anda yapılandırılmamış."
            )

        if intent_type is IntentType.MEMORY_REMEMBER:
            content = _extract_memory_content(user_message)
            if not content:
                return ModelResponse(
                    text=(
                        "Neyi hatırlamamı istediğini yazman gerekiyor. "
                        "Örnek: bunu hatırla: kısa cevapları seviyorum."
                    )
                )
            if self._memory_service.is_sensitive_content(content):
                return ModelResponse(
                    text=(
                        "Bunu hafızaya kaydetmem doğru olmaz İlhan. Şifre, token, "
                        "kimlik veya ödeme bilgisi gibi hassas bilgileri saklamamalıyım."
                    )
                )
            memory = self._memory_service.add_memory(
                MemoryType.CONVERSATION_NOTE,
                content,
                source="explicit_user_request",
            )
            if memory is None:
                return ModelResponse(text="Bunu zaten hatırlıyorum İlhan.")
            return ModelResponse(text=f"Tamam İlhan, bunu hatırlayacağım: {content}.")

        if intent_type in {IntentType.MEMORY_RECALL, IntentType.MEMORY_LIST}:
            memories = self._memory_service.list_memories()
            if not memories:
                return ModelResponse(text="Şu an hafızamda kayıtlı bir bilgi yok İlhan.")
            lines = ["Şunları hatırlıyorum:"]
            lines.extend(
                f"{index}. {memory.content}"
                for index, memory in enumerate(memories, start=1)
            )
            return ModelResponse(text="\n".join(lines))

        if intent_type is IntentType.MEMORY_FORGET:
            content = _extract_memory_content(user_message)
            if not content:
                return ModelResponse(
                    text=(
                        "Neyi unutmamı istediğini yazman gerekiyor. "
                        "Örnek: şunu unut: kısa cevapları seviyorum."
                    )
                )
            removed_count = self._memory_service.forget_memory_by_content(content)
            if removed_count == 0:
                return ModelResponse(text="Bunu hafızamda bulamadım İlhan.")
            return ModelResponse(text="Tamam İlhan, bunu hafızamdan kaldırdım.")

        if intent_type is IntentType.MEMORY_CLEAR:
            if not self._memory_service.list_memories():
                return ModelResponse(text="Hafızam zaten boş İlhan.")
            self._memory_service.clear_memories()
            return ModelResponse(text="Hafızamdaki tüm kayıtları temizledim İlhan.")

        raise ValueError(f"Unsupported memory intent: {intent_type.value}")

    def _handle_file_intent(
        self,
        intent_type: IntentType,
        user_message: str,
    ) -> ModelResponse:
        if self._file_access_service is None:
            return ModelResponse(
                text="Dosya okuma yeteneği şu anda yapılandırılmamış İlhan."
            )

        if intent_type is IntentType.FILE_LIST_ALLOWED:
            files = [
                file.path
                for file in self._file_access_service.list_allowed_files()
                if file.exists
            ]
            if not files:
                return ModelResponse(
                    text="Şu anda okuyabileceğim mevcut izinli proje dosyası yok İlhan."
                )
            lines = ["Şu an yalnızca şu izinli proje dosyalarını okuyabiliyorum:"]
            lines.extend(f"{index}. {path}" for index, path in enumerate(files, start=1))
            return ModelResponse(text="\n".join(lines))

        if intent_type is IntentType.FILE_CAPABILITIES:
            return ModelResponse(
                text=(
                    "Bilgisayarındaki genel dosyaları okuyamıyorum İlhan. Şu an sadece "
                    "Lina projesinde izinli, read-only proje dosyalarını okuyabilirim. "
                    "Dosya yazma, silme, taşıma veya yeniden adlandırma yetkim yok."
                )
            )

        reference = _extract_file_reference(user_message)
        if not reference:
            return _format_unknown_file_response()

        if intent_type is IntentType.FILE_READ:
            try:
                content = self._file_access_service.read_allowed_file(reference)
            except FileAccessError as error:
                return _format_file_access_error(error)

            return ModelResponse(
                text=_format_file_preview(content.path, content.text, content.truncated)
            )

        if intent_type is IntentType.FILE_SUMMARIZE:
            try:
                content = self._file_access_service.build_file_context(reference)
            except FileAccessError as error:
                return _format_file_access_error(error)

            context = self._context_manager.build_context(
                user_message=_build_file_summary_request(content.path),
                intent=Intent(type=IntentType.CHAT),
                conversation_history=[],
            )
            context = replace(
                context,
                file_context=_format_file_context(
                    content.path,
                    content.text,
                    content.truncated,
                ),
            )
            try:
                return self._brain.respond_with_context(context)
            except ModelProviderError as error:
                if not _is_model_unavailable_error(error):
                    raise
                return ModelResponse(
                    text=(
                        "Dosyayı okuyabildim ama özetlemek için yerel modele bağlı "
                        "değilim. İlk bölümünü gösterebilirim:\n\n"
                        f"{_format_file_preview(content.path, content.text, content.truncated)}"
                    )
                )

        raise ValueError(f"Unsupported file intent: {intent_type.value}")


def _extract_memory_content(message: str) -> str:
    if ":" not in message:
        return ""
    return message.split(":", 1)[1].strip()


def _extract_file_reference(message: str) -> str:
    normalized = message.strip().casefold()
    if _contains_forbidden_file_path(normalized):
        return message.strip()
    known_references = (
        "docs/roadmap.md",
        "docs/development-log.md",
        "docs/architecture.md",
        "docs/vision.md",
        "docs/brain-specification-v1.md",
        "docs/conversation-flow-v1.md",
        "docs/release-notes-v0.3.0-alpha.md",
        "docs/release-notes-v0.3.1-alpha.md",
        "docs/release-notes-v0.4.0-alpha.md",
        "docs/release-notes-v0.4.1-alpha.md",
        "readme",
        "contributing",
        "roadmap",
        "development log",
        "dev log",
        "architecture",
        "vision",
        "brain spec",
        "conversation flow",
        "release notes v0.4.1",
        "v0.4.1 release notes",
        "release notes v0.4.0",
        "v0.4.0 release notes",
        "release notes v0.3.1",
        "v0.3.1 release notes",
        "release notes v0.3.0",
        "v0.3.0 release notes",
    )
    for reference in known_references:
        if reference in normalized:
            return reference
    if ":\\" in message or ":/" in message or ".." in message:
        return message.strip()
    return ""


def _contains_forbidden_file_path(message: str) -> bool:
    normalized = message.strip().replace("\\", "/")
    if not normalized:
        return False
    if normalized.startswith(("/", "~/", "~")):
        return True
    if ":/" in normalized:
        return True
    return ".." in normalized.split("/")


def _format_file_context(path: str, text: str, truncated: bool) -> str:
    suffix = "\n\nNot: Dosya uzun olduğu için yalnızca ilk bölüm kullanıldı." if truncated else ""
    return f"Dosya: {path}\nİçerik:\n{text}{suffix}"


def _build_file_summary_request(path: str) -> str:
    return (
        f"{path} dosyasını aşağıdaki izinli dosya bağlamına dayanarak Türkçe ve kısa "
        "şekilde özetle. Dosya bağlamı dışında bilgi uydurma. Eğer bağlam yetersizse "
        "bunu açıkça söyle. Selamlama, sohbet sorusu veya meta başlık yazma."
    )


def _is_model_unavailable_error(error: ModelProviderError) -> bool:
    error_text = str(error).casefold()
    unavailable_markers = (
        "network error",
        "connection refused",
        "not configured",
        "http error: 404",
        "not found",
    )
    return any(marker in error_text for marker in unavailable_markers)


def _format_file_preview(path: str, text: str, truncated: bool) -> str:
    if truncated:
        return f"{path} dosyası uzun olduğu için ilk bölümü gösteriyorum:\n\n{text}"
    return f"{path} dosyasının içeriği:\n\n{text}"


def _format_unknown_file_response() -> ModelResponse:
    return ModelResponse(
        text=(
            "Bunu okuyamıyorum İlhan. Şu an yalnızca izinli proje dosyalarını "
            "okuyabiliyorum. 'hangi dosyaları okuyabiliyorsun' diyerek listeyi "
            "görebilirsin."
        )
    )


def _format_file_access_error(error: FileAccessError) -> ModelResponse:
    if isinstance(error, ForbiddenFilePathError):
        return ModelResponse(text="Güvenlik nedeniyle bu dosya yolunu okuyamam İlhan.")
    if isinstance(error, UnknownAllowedFileError):
        return _format_unknown_file_response()
    if isinstance(error, MissingAllowedFileError):
        return ModelResponse(text="Bu dosya izinli listede ama şu anda mevcut değil İlhan.")
    return ModelResponse(text="Bu dosyayı güvenli şekilde okuyamadım İlhan.")


def _safe_image_source(attachment: object | None) -> str | None:
    if attachment is None:
        return None
    source = getattr(attachment, "source", None)
    return {
        "screen_capture": "screen_full",
        "screen_capture_full": "screen_full",
        "screen_capture_region": "screen_region",
        "local_file": "local_image",
        "local_image": "local_image",
    }.get(source)
