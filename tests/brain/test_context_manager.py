from lina.brain.context_manager import ContextManager
from lina.brain.intent import Intent, IntentType
from lina.brain.prompt_builder import ConversationTurn
from lina.services.project_context_service import ProjectContext


class FakeProjectContextService:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls = 0

    def collect_context(self) -> ProjectContext:
        self.calls += 1
        return ProjectContext(text=self.text)


def test_context_manager_includes_limited_history() -> None:
    history = [
        ConversationTurn(user_message="First", assistant_response="One"),
        ConversationTurn(user_message="Second", assistant_response="Two"),
    ]
    manager = ContextManager(history_limit=1)

    context = manager.build_context(
        user_message="Hello",
        intent=Intent(type=IntentType.CHAT),
        conversation_history=history,
    )

    assert context.conversation_history == (
        ConversationTurn(user_message="Second", assistant_response="Two"),
    )


def test_context_manager_collects_project_context_for_project_intent() -> None:
    project_context_service = FakeProjectContextService(text="Project status")
    manager = ContextManager(project_context_service=project_context_service)

    context = manager.build_context(
        user_message="Project status?",
        intent=Intent(type=IntentType.PROJECT_STATUS),
        conversation_history=[],
    )

    assert context.project_context == "Project status"
    assert project_context_service.calls == 1


def test_context_manager_skips_project_context_for_chat() -> None:
    project_context_service = FakeProjectContextService(text="Project status")
    manager = ContextManager(project_context_service=project_context_service)

    context = manager.build_context(
        user_message="Hello",
        intent=Intent(type=IntentType.CHAT),
        conversation_history=[],
    )

    assert context.project_context is None
    assert project_context_service.calls == 0


def test_context_manager_uses_project_fallback_without_service() -> None:
    manager = ContextManager(project_context_service=None)

    context = manager.build_context(
        user_message="Project status?",
        intent=Intent(type=IntentType.PROJECT_SUMMARY),
        conversation_history=[],
    )

    assert context.project_context == "Proje bağlamı şu anda yapılandırılmamış."
