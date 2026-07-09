from pathlib import Path

import pytest

from lina.brain.model_provider import ModelResponse
from lina.brain.prompt_builder import ConversationTurn
from lina.memory.repository import MemoryRepository
from lina.memory.service import MemoryService
from lina.services.conversation_service import ConversationService


class FakeBrain:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.histories: list[list[ConversationTurn]] = []
        self.project_contexts: list[str | None] = []
        self.file_contexts: list[str | None] = []
        self.failure_message: str | None = None

    def respond(self, user_message: str) -> ModelResponse:
        self.messages.append(user_message)
        return ModelResponse(text=f"Response: {user_message}")

    def respond_with_context(self, context) -> ModelResponse:
        from lina.brain.model_provider import ModelProviderError

        if self.failure_message is not None:
            raise ModelProviderError(self.failure_message)
        self.messages.append(context.user_message)
        self.histories.append(list(context.conversation_history))
        self.project_contexts.append(context.project_context)
        self.file_contexts.append(context.file_context)
        return ModelResponse(text=f"Response: {context.user_message}")


class FakeIntentAnalyzer:
    def __init__(self, intent_type) -> None:
        self._intent_type = intent_type
        self.messages: list[str] = []

    def analyze(self, message: str):
        from lina.brain.intent import Intent

        self.messages.append(message)
        return Intent(type=self._intent_type)


class SequenceIntentAnalyzer:
    def __init__(self, intent_types) -> None:
        self._intent_types = list(intent_types)

    def analyze(self, message: str):
        from lina.brain.intent import Intent

        return Intent(type=self._intent_types.pop(0))


class FakeDeterministicResponseService:
    def __init__(self, can_handle: bool, handled_intent_types=None) -> None:
        self._can_handle = can_handle
        self._handled_intent_types = handled_intent_types
        self.handled_intents = []

    def can_handle(self, intent) -> bool:
        if self._handled_intent_types is not None:
            return intent.type in self._handled_intent_types
        return self._can_handle

    def handle(self, intent) -> ModelResponse:
        self.handled_intents.append(intent)
        return ModelResponse(text="Deterministic response")


class FakeProjectContextService:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls = 0

    def collect_context(self):
        from lina.services.project_context_service import ProjectContext

        self.calls += 1
        return ProjectContext(text=self.text)


class FakeToolExecutionService:
    def __init__(self, should_fail: bool = False) -> None:
        self.calls: list[str] = []
        self._should_fail = should_fail

    def execute(self, tool_name: str, input_text: str = ""):
        from lina.services.tool_execution_service import ToolExecutionError
        from lina.tools.tool import ToolResult

        self.calls.append(tool_name)
        if self._should_fail:
            raise ToolExecutionError("Tool failed")
        return ToolResult(text="Şu an saat 15:42.")


class FakeMemoryService:
    def __init__(self, is_duplicate: bool = False) -> None:
        self._is_duplicate = is_duplicate
        self.added: list[tuple[object, str, str]] = []
        self.memories = []
        self.forgotten: list[str] = []
        self.clear_count = 0

    def add_memory(self, memory_type, content: str, source: str):
        self.added.append((memory_type, content, source))
        if self._is_duplicate:
            return None
        return FakeMemory(content)

    def is_sensitive_content(self, content: str) -> bool:
        return "şifrem" in content or "api key" in content

    def list_memories(self):
        return tuple(self.memories)

    def forget_memory_by_content(self, content: str) -> int:
        self.forgotten.append(content)
        return 1 if content == "kısa cevapları seviyorum" else 0

    def clear_memories(self) -> int:
        self.clear_count += 1
        return len(self.memories)


class FakeMemory:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeAllowedFile:
    def __init__(self, path: str, exists: bool = True) -> None:
        self.path = path
        self.exists = exists


class FakeFileContent:
    def __init__(self, path: str, text: str, truncated: bool = False) -> None:
        self.path = path
        self.text = text
        self.truncated = truncated


class FakeFileAccessService:
    def __init__(self, should_reject=None) -> None:
        self.should_reject = should_reject
        self.read_requests: list[str] = []
        self.context_requests: list[str] = []

    def list_allowed_files(self):
        return (
            FakeAllowedFile("README.md"),
            FakeAllowedFile("docs/roadmap.md"),
            FakeAllowedFile("missing.md", exists=False),
        )

    def read_allowed_file(self, path_or_alias: str):
        self.read_requests.append(path_or_alias)
        if self.should_reject is not None:
            raise self.should_reject
        return FakeFileContent(path="README.md", text="Readme content")

    def build_file_context(self, path_or_alias: str):
        self.context_requests.append(path_or_alias)
        if self.should_reject is not None:
            raise self.should_reject
        return FakeFileContent(path="docs/roadmap.md", text="Roadmap content")


def test_conversation_service_sends_user_message_to_brain() -> None:
    brain = FakeBrain()
    service = ConversationService(brain=brain)

    service.handle_message("Hello")

    assert brain.messages == ["Hello"]


def test_conversation_service_returns_model_response() -> None:
    service = ConversationService(brain=FakeBrain())

    response = service.handle_message("Hello")

    assert response == ModelResponse(text="Response: Hello")


def test_conversation_service_sends_previous_turns_to_brain() -> None:
    brain = FakeBrain()
    service = ConversationService(brain=brain)

    service.handle_message("Hello")
    service.handle_message("What did I say?")

    assert brain.histories[0] == []
    assert brain.histories[1] == [
        ConversationTurn(user_message="Hello", assistant_response="Response: Hello")
    ]


def test_conversation_service_limits_history() -> None:
    brain = FakeBrain()
    service = ConversationService(brain=brain, history_limit=1)

    service.handle_message("First")
    service.handle_message("Second")
    service.handle_message("Third")

    assert brain.histories[2] == [
        ConversationTurn(user_message="Second", assistant_response="Response: Second")
    ]


def test_conversation_service_routes_deterministic_intent_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    intent_analyzer = FakeIntentAnalyzer(intent_type=IntentType.HELP)
    deterministic_response_service = FakeDeterministicResponseService(can_handle=True)
    service = ConversationService(
        brain=brain,
        intent_analyzer=intent_analyzer,
        deterministic_response_service=deterministic_response_service,
    )

    response = service.handle_message("help")

    assert response == ModelResponse(text="Deterministic response")
    assert brain.messages == []
    assert intent_analyzer.messages == ["help"]
    assert len(deterministic_response_service.handled_intents) == 1


def test_conversation_service_routes_casual_greeting_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.CASUAL_GREETING),
    )

    response = service.handle_message("selam")

    assert response.text == "Selam İlhan! Buradayım, bugün ne yapalım?"
    assert brain.messages == []


def test_conversation_service_routes_computer_control_status_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(
            intent_type=IntentType.COMPUTER_CONTROL_STATUS
        ),
    )

    response = service.handle_message("bilgisayarımı yönetebilir misin")

    assert "bilgisayarını genel olarak yönetemem" in response.text
    assert brain.messages == []


def test_conversation_service_routes_memory_remember_without_calling_brain() -> None:
    from lina.brain.intent import IntentType
    from lina.memory.models import MemoryType

    brain = FakeBrain()
    memory_service = FakeMemoryService()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_REMEMBER),
        memory_service=memory_service,
    )

    response = service.handle_message("bunu hatırla: kısa cevapları seviyorum")

    assert response.text == "Tamam İlhan, bunu hatırlayacağım: kısa cevapları seviyorum."
    assert memory_service.added == [
        (MemoryType.CONVERSATION_NOTE, "kısa cevapları seviyorum", "explicit_user_request")
    ]
    assert brain.messages == []


def test_conversation_service_routes_file_list_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.FILE_LIST_ALLOWED),
        file_access_service=FakeFileAccessService(),
    )

    response = service.handle_message("hangi dosyaları okuyabiliyorsun")

    assert "README.md" in response.text
    assert "docs/roadmap.md" in response.text
    assert "missing.md" not in response.text
    assert brain.messages == []


def test_conversation_service_routes_file_capabilities_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.FILE_CAPABILITIES),
        file_access_service=FakeFileAccessService(),
    )

    response = service.handle_message("bilgisayarımdaki dosyaları okuyabiliyor musun")

    assert "genel dosyaları okuyamıyorum" in response.text
    assert "read-only proje dosyalarını" in response.text
    assert "Dosya yazma" in response.text
    assert brain.messages == []


def test_conversation_service_routes_file_read_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    file_service = FakeFileAccessService()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.FILE_READ),
        file_access_service=file_service,
    )

    response = service.handle_message("README dosyasını oku")

    assert "README.md dosyasının içeriği" in response.text
    assert "Readme content" in response.text
    assert file_service.read_requests == ["readme"]
    assert brain.messages == []


def test_conversation_service_rejects_forbidden_file_without_calling_brain() -> None:
    from lina.brain.intent import IntentType
    from lina.files.models import ForbiddenFilePathError

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.FILE_READ),
        file_access_service=FakeFileAccessService(
            should_reject=ForbiddenFilePathError("forbidden")
        ),
    )

    response = service.handle_message("../README.md dosyasını oku")

    assert "Güvenlik nedeniyle" in response.text
    assert brain.messages == []


def test_conversation_service_rejects_unknown_file_without_calling_brain() -> None:
    from lina.brain.intent import IntentType
    from lina.files.models import UnknownAllowedFileError

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.FILE_READ),
        file_access_service=FakeFileAccessService(
            should_reject=UnknownAllowedFileError("unknown")
        ),
    )

    response = service.handle_message("secret dosyasını oku")

    assert "Bunu okuyamıyorum İlhan" in response.text
    assert brain.messages == []


def test_conversation_service_routes_file_summarize_with_context_to_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    file_service = FakeFileAccessService()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.FILE_SUMMARIZE),
        file_access_service=file_service,
    )

    response = service.handle_message("roadmap dosyasını özetle")

    assert response.text.startswith("Response: docs/roadmap.md dosyasını")
    assert file_service.context_requests == ["roadmap"]
    assert brain.messages == [
        "docs/roadmap.md dosyasını aşağıdaki izinli dosya bağlamına dayanarak Türkçe "
        "ve kısa şekilde özetle. Dosya bağlamı dışında bilgi uydurma. Eğer bağlam "
        "yetersizse bunu açıkça söyle. Selamlama, sohbet sorusu veya meta başlık yazma."
    ]
    assert "Dosya: docs/roadmap.md" in brain.file_contexts[0]
    assert "Roadmap content" in brain.file_contexts[0]


def test_conversation_service_file_summarize_falls_back_when_model_fails() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    brain.failure_message = "Ollama network error"
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.FILE_SUMMARIZE),
        file_access_service=FakeFileAccessService(),
    )

    response = service.handle_message("roadmap dosyasını özetle")

    assert "Dosyayı okuyabildim" in response.text
    assert "Roadmap content" in response.text


def test_conversation_service_file_summarize_does_not_use_unavailable_fallback_for_timeout() -> None:
    from lina.brain.intent import IntentType
    from lina.brain.model_provider import ModelProviderError

    brain = FakeBrain()
    brain.failure_message = "Ollama request timed out"
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.FILE_SUMMARIZE),
        file_access_service=FakeFileAccessService(),
    )

    with pytest.raises(ModelProviderError, match="timed out"):
        service.handle_message("roadmap dosyasını özetle")


def test_conversation_service_file_summarize_keeps_memory_history_context() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=SequenceIntentAnalyzer(
            intent_types=[IntentType.MEMORY_RECALL, IntentType.FILE_SUMMARIZE]
        ),
        memory_service=FakeMemoryService(),
        file_access_service=FakeFileAccessService(),
    )

    service.handle_message("ne hatırlıyorsun")
    service.handle_message("roadmap dosyasını özetle")

    assert brain.histories[0] == []
    assert "Roadmap content" in brain.file_contexts[0]


def test_conversation_service_file_summarize_ignores_previous_casual_history() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=SequenceIntentAnalyzer(
            intent_types=[IntentType.CASUAL_GREETING, IntentType.FILE_SUMMARIZE]
        ),
        file_access_service=FakeFileAccessService(),
    )

    service.handle_message("selam naber")
    response = service.handle_message("roadmap dosyasını özetle")

    assert response.text.startswith("Response: docs/roadmap.md dosyasını")
    assert brain.histories[0] == []
    assert "Dosya: docs/roadmap.md" in brain.file_contexts[0]
    assert "Roadmap content" in brain.file_contexts[0]
    assert "selam naber" not in brain.messages[0].casefold()
    assert "bugün ne yapalım" not in brain.messages[0].casefold()


def test_conversation_service_returns_memory_remember_missing_content() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    memory_service = FakeMemoryService()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_REMEMBER),
        memory_service=memory_service,
    )

    response = service.handle_message("bunu hatırla:")

    assert "Neyi hatırlamamı istediğini" in response.text
    assert memory_service.added == []
    assert brain.messages == []


def test_conversation_service_returns_duplicate_memory_response_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    memory_service = FakeMemoryService(is_duplicate=True)
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_REMEMBER),
        memory_service=memory_service,
    )

    response = service.handle_message("bunu hatırla: kısa cevapları seviyorum")

    assert response.text == "Bunu zaten hatırlıyorum İlhan."
    assert brain.messages == []


def test_conversation_service_rejects_sensitive_memory_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    memory_service = FakeMemoryService()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_REMEMBER),
        memory_service=memory_service,
    )

    response = service.handle_message("bunu hatırla: şifrem 123456")

    assert "Bunu hafızaya kaydetmem doğru olmaz İlhan" in response.text
    assert memory_service.added == []
    assert brain.messages == []


def test_conversation_service_does_not_persist_rejected_sensitive_memory(
    tmp_path: Path,
) -> None:
    from lina.brain.intent import IntentType

    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    memory_service = MemoryService(repository=repository)
    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=SequenceIntentAnalyzer(
            intent_types=[IntentType.MEMORY_REMEMBER, IntentType.MEMORY_LIST]
        ),
        memory_service=memory_service,
    )

    try:
        response = service.handle_message("bunu hatırla: api key abc")
        listed = service.handle_message("hafızanı listele")

        assert "hassas bilgileri saklamamalıyım" in response.text
        assert listed.text == "Şu an hafızamda kayıtlı bir bilgi yok İlhan."
        assert brain.messages == []
    finally:
        memory_service.close()


def test_conversation_service_keeps_single_memory_for_duplicate_remember(
    tmp_path: Path,
) -> None:
    from lina.brain.intent import IntentType

    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    memory_service = MemoryService(repository=repository)
    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=SequenceIntentAnalyzer(
            intent_types=[
                IntentType.MEMORY_REMEMBER,
                IntentType.MEMORY_REMEMBER,
                IntentType.MEMORY_LIST,
            ]
        ),
        memory_service=memory_service,
    )

    try:
        first = service.handle_message("bunu hatırla: kısa cevapları seviyorum")
        second = service.handle_message("bunu hatırla: kısa   cevapları   seviyorum")
        listed = service.handle_message("hafızanı listele")

        assert first.text == "Tamam İlhan, bunu hatırlayacağım: kısa cevapları seviyorum."
        assert second.text == "Bunu zaten hatırlıyorum İlhan."
        assert listed.text == "Şunları hatırlıyorum:\n1. kısa cevapları seviyorum"
        assert brain.messages == []
    finally:
        memory_service.close()


def test_conversation_service_allows_remember_after_forget(tmp_path: Path) -> None:
    from lina.brain.intent import IntentType

    repository = MemoryRepository(tmp_path / "memory.sqlite3")
    memory_service = MemoryService(repository=repository)
    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=SequenceIntentAnalyzer(
            intent_types=[
                IntentType.MEMORY_REMEMBER,
                IntentType.MEMORY_FORGET,
                IntentType.MEMORY_REMEMBER,
                IntentType.MEMORY_LIST,
            ]
        ),
        memory_service=memory_service,
    )

    try:
        service.handle_message("bunu hatırla: kısa cevapları seviyorum")
        service.handle_message("şunu unut: kısa cevapları seviyorum")
        response = service.handle_message("bunu hatırla: kısa cevapları seviyorum")
        listed = service.handle_message("hafızanı listele")

        assert response.text == "Tamam İlhan, bunu hatırlayacağım: kısa cevapları seviyorum."
        assert listed.text == "Şunları hatırlıyorum:\n1. kısa cevapları seviyorum"
        assert brain.messages == []
    finally:
        memory_service.close()


def test_conversation_service_routes_memory_recall_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    memory_service = FakeMemoryService()
    memory_service.memories = [
        FakeMemory("kısa cevapları seviyorum"),
        FakeMemory("Türkçe dokümantasyon istiyorum"),
    ]
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_RECALL),
        memory_service=memory_service,
    )

    response = service.handle_message("ne hatırlıyorsun")

    assert response.text == (
        "Şunları hatırlıyorum:\n"
        "1. kısa cevapları seviyorum\n"
        "2. Türkçe dokümantasyon istiyorum"
    )
    assert brain.messages == []


def test_conversation_service_routes_empty_memory_recall_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_RECALL),
        memory_service=FakeMemoryService(),
    )

    response = service.handle_message("ne hatırlıyorsun")

    assert response.text == "Şu an hafızamda kayıtlı bir bilgi yok İlhan."
    assert brain.messages == []


def test_conversation_service_routes_memory_forget_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    memory_service = FakeMemoryService()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_FORGET),
        memory_service=memory_service,
    )

    response = service.handle_message("şunu unut: kısa cevapları seviyorum")

    assert response.text == "Tamam İlhan, bunu hafızamdan kaldırdım."
    assert memory_service.forgotten == ["kısa cevapları seviyorum"]
    assert brain.messages == []


def test_conversation_service_routes_memory_clear_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    memory_service = FakeMemoryService()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_CLEAR),
        memory_service=memory_service,
    )

    response = service.handle_message("hafızanı sıfırla")

    assert response.text == "Hafızam zaten boş İlhan."
    assert memory_service.clear_count == 0
    assert brain.messages == []


def test_conversation_service_routes_memory_clear_with_records_without_calling_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    memory_service = FakeMemoryService()
    memory_service.memories = [FakeMemory("kısa cevapları seviyorum")]
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.MEMORY_CLEAR),
        memory_service=memory_service,
    )

    response = service.handle_message("hafızanı sıfırla")

    assert response.text == "Hafızamdaki tüm kayıtları temizledim İlhan."
    assert memory_service.clear_count == 1
    assert brain.messages == []


def test_conversation_service_adds_memory_responses_to_history() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=SequenceIntentAnalyzer(
            intent_types=[IntentType.MEMORY_RECALL, IntentType.CHAT]
        ),
        memory_service=FakeMemoryService(),
    )

    service.handle_message("ne hatırlıyorsun")
    service.handle_message("devam")

    assert brain.histories[0] == [
        ConversationTurn(
            user_message="ne hatırlıyorsun",
            assistant_response="Şu an hafızamda kayıtlı bir bilgi yok İlhan.",
        )
    ]


def test_conversation_service_routes_chat_intent_to_brain() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.CHAT),
        deterministic_response_service=FakeDeterministicResponseService(
            can_handle=False
        ),
    )

    response = service.handle_message("Hello")

    assert response == ModelResponse(text="Response: Hello")
    assert brain.messages == ["Hello"]


def test_conversation_service_adds_deterministic_responses_to_history() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=SequenceIntentAnalyzer(
            intent_types=[IntentType.HELP, IntentType.CHAT]
        ),
        deterministic_response_service=FakeDeterministicResponseService(
            can_handle=True,
            handled_intent_types={IntentType.HELP},
        ),
    )

    service.handle_message("help")
    service.handle_message("Continue")

    assert brain.histories[0] == [
        ConversationTurn(
            user_message="help",
            assistant_response="Deterministic response",
        )
    ]


def test_conversation_service_routes_project_intent_with_project_context() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    project_context_service = FakeProjectContextService(text="Sprint 5 completed.")
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.PROJECT_STATUS),
        deterministic_response_service=FakeDeterministicResponseService(
            can_handle=False
        ),
        project_context_service=project_context_service,
    )

    response = service.handle_message("Lina projesinin durumu ne?")

    assert response == ModelResponse(text="Response: Lina projesinin durumu ne?")
    assert brain.messages == ["Lina projesinin durumu ne?"]
    assert len(brain.project_contexts) == 1
    assert "Sprint 5 completed." in brain.project_contexts[0]
    assert "[Kaynak: proje dokümanları]" in brain.project_contexts[0]
    assert project_context_service.calls == 1


def test_conversation_service_project_intent_uses_honest_fallback_without_service() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.PROJECT_SUMMARY),
        deterministic_response_service=FakeDeterministicResponseService(
            can_handle=False
        ),
    )

    service.handle_message("Son sprintlerde ne eklendi?")

    assert brain.project_contexts == ["Proje bağlamı şu anda yapılandırılmamış."]


def test_conversation_service_routes_current_time_to_safe_tool() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    tool_execution_service = FakeToolExecutionService()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.CURRENT_TIME),
        tool_execution_service=tool_execution_service,
    )

    response = service.handle_message("Saat kaç?")

    assert response == ModelResponse(text="Şu an saat 15:42.")
    assert tool_execution_service.calls == ["current_time"]
    assert brain.messages == []


def test_conversation_service_falls_back_when_current_time_tool_fails() -> None:
    from lina.brain.intent import IntentType

    brain = FakeBrain()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.CURRENT_TIME),
        tool_execution_service=FakeToolExecutionService(should_fail=True),
    )

    response = service.handle_message("Saat kaç?")

    assert "Şu an saat" in response.text
    assert brain.messages == []


def test_conversation_service_uses_provided_context_manager() -> None:
    from lina.brain.context_manager import ContextManager
    from lina.brain.intent import IntentType

    class FakeContextManager(ContextManager):
        def build_context(self, user_message, intent, conversation_history):
            from lina.brain.conversation_context import ConversationContext
            
            return ConversationContext(
                user_message=user_message,
                conversation_history=conversation_history,
                project_context="Injected ContextManager output"
            )

    brain = FakeBrain()
    manager = FakeContextManager()
    service = ConversationService(
        brain=brain,
        intent_analyzer=FakeIntentAnalyzer(intent_type=IntentType.PROJECT_STATUS),
        deterministic_response_service=FakeDeterministicResponseService(
            can_handle=False
        ),
        context_manager=manager,
    )

    response = service.handle_message("Lina durumu?")

    assert response == ModelResponse(text="Response: Lina durumu?")
    assert len(brain.project_contexts) == 1
    assert brain.project_contexts[0] == "Injected ContextManager output"
