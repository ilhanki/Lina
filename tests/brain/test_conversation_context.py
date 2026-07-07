from lina.brain.conversation_context import ConversationContext
from lina.brain.prompt_builder import ConversationTurn


def test_conversation_context_stores_runtime_context() -> None:
    history = [
        ConversationTurn(user_message="Hello", assistant_response="Hi"),
    ]

    context = ConversationContext(
        user_message="What happened?",
        conversation_history=history,
        project_context="Project context",
        system_notes="Use available context only.",
    )

    assert context.user_message == "What happened?"
    assert context.conversation_history == history
    assert context.project_context == "Project context"
    assert context.system_notes == "Use available context only."
