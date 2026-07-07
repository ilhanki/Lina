from lina.brain.context_manager import ContextManager
from lina.brain.intent import Intent, IntentType
from lina.brain.prompt_builder import ConversationTurn
from lina.services.project_context_service import ProjectContext
from lina.services.git_context_service import GitContext


class FakeProjectContextService:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls = 0

    def collect_context(self) -> ProjectContext:
        self.calls += 1
        return ProjectContext(text=self.text)


class FakeGitContextService:
    def __init__(self, context: GitContext) -> None:
        self._context = context
        self.calls = 0

    def collect_context(self) -> GitContext:
        self.calls += 1
        return self._context


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

    assert "[Kaynak: proje dokümanları]" in context.project_context
    assert "Project status" in context.project_context
    assert project_context_service.calls == 1


def test_context_manager_collects_git_context_for_project_intent() -> None:
    git_context = GitContext(
        current_branch="main",
        recent_commits="abc1234 test",
        working_tree_status="",
        available=True,
    )
    git_service = FakeGitContextService(git_context)
    manager = ContextManager(git_context_service=git_service)

    context = manager.build_context(
        user_message="Git status?",
        intent=Intent(type=IntentType.PROJECT_STATUS),
        conversation_history=[],
    )

    assert "[Kaynak: git]" in context.project_context
    assert "Branch: main" in context.project_context
    assert git_service.calls == 1


def test_context_manager_combines_project_and_git_context() -> None:
    project_service = FakeProjectContextService(text="Project docs")
    git_context = GitContext(
        current_branch="main",
        recent_commits="abc1234 test",
        working_tree_status="",
        available=True,
    )
    git_service = FakeGitContextService(git_context)
    
    manager = ContextManager(
        project_context_service=project_service,
        git_context_service=git_service,
    )

    context = manager.build_context(
        user_message="Status?",
        intent=Intent(type=IntentType.PROJECT_STATUS),
        conversation_history=[],
    )

    assert "[Kaynak: proje dokümanları]" in context.project_context
    assert "Project docs" in context.project_context
    assert "[Kaynak: git]" in context.project_context
    assert "Branch: main" in context.project_context


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
    manager = ContextManager(project_context_service=None, git_context_service=None)

    context = manager.build_context(
        user_message="Project status?",
        intent=Intent(type=IntentType.PROJECT_SUMMARY),
        conversation_history=[],
    )

    assert context.project_context == "Proje bağlamı şu anda yapılandırılmamış."


def test_context_manager_uses_fallback_when_services_have_no_content() -> None:
    project_service = FakeProjectContextService(text="")
    git_context = GitContext(
        current_branch="",
        recent_commits="",
        working_tree_status="",
        available=False,
    )
    git_service = FakeGitContextService(git_context)
    
    manager = ContextManager(
        project_context_service=project_service,
        git_context_service=git_service,
    )

    context = manager.build_context(
        user_message="Status?",
        intent=Intent(type=IntentType.PROJECT_STATUS),
        conversation_history=[],
    )

    assert context.project_context == "Proje bağlamı şu anda yapılandırılmamış."
