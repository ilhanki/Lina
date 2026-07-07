from lina.brain.model_provider import ModelResponse
from lina.brain.prompt_builder import ConversationTurn
from lina.services.conversation_service import ConversationService


class FakeBrain:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.histories: list[list[ConversationTurn]] = []
        self.project_contexts: list[str | None] = []

    def respond(self, user_message: str) -> ModelResponse:
        self.messages.append(user_message)
        return ModelResponse(text=f"Response: {user_message}")

    def respond_with_context(self, context) -> ModelResponse:
        self.messages.append(context.user_message)
        self.histories.append(list(context.conversation_history))
        self.project_contexts.append(context.project_context)
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
