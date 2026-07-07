from lina.brain.prompt_builder import ConversationTurn, PromptBuilder


def test_prompt_builder_combines_system_prompt_and_user_message() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(user_message="Hello")

    assert prompt == "System:\nYou are Lina.\n\nUser:\nHello"


def test_prompt_builder_strips_outer_whitespace() -> None:
    builder = PromptBuilder(system_prompt="  You are Lina.  ")

    prompt = builder.build(user_message="  Hello  ")

    assert prompt == "System:\nYou are Lina.\n\nUser:\nHello"


def test_prompt_builder_includes_conversation_history() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(
        user_message="What is my name?",
        history=[
            ConversationTurn(user_message="My name is Ilhan.", assistant_response="Nice to meet you."),
        ],
    )

    assert prompt == (
        "System:\nYou are Lina.\n\n"
        "Conversation history:\n"
        "User: My name is Ilhan.\n"
        "Assistant: Nice to meet you.\n\n"
        "User:\nWhat is my name?"
    )
