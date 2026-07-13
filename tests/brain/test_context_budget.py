from lina.brain.context_manager import trim_conversation_history
from lina.brain.prompt_builder import ConversationTurn


def turn(index: int, size: int = 20):
    return ConversationTurn(f"user-{index}-" + "u" * size, f"assistant-{index}-" + "a" * size)


def test_context_budget_preserves_newest_complete_pairs():
    history = [turn(1), turn(2), turn(3)]
    trimmed = trim_conversation_history(history, max_turns=3, character_budget=100)
    assert trimmed[-1].user_message.startswith("user-3")
    assert all(item.user_message and item.assistant_response for item in trimmed)
    assert history == [turn(1), turn(2), turn(3)]


def test_context_excludes_base64_images_and_internal_metadata():
    history = [ConversationTurn("data:image/png;base64," + "A" * 300, "<tool_debug>secret</tool_debug>Yanıt")]
    trimmed = trim_conversation_history(history, 5, 1000)
    assert "A" * 100 not in trimmed[0].user_message
    assert "secret" not in trimmed[0].assistant_response
    assert "Yanıt" in trimmed[0].assistant_response


def test_oversized_newest_pair_is_bounded_not_dropped():
    trimmed = trim_conversation_history([turn(1, 1000)], 2, 200)
    assert len(trimmed) == 1
    assert len(trimmed[0].user_message) <= 100
    assert len(trimmed[0].assistant_response) <= 100
