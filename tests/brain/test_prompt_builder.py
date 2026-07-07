from lina.brain.prompt_builder import PromptBuilder


def test_prompt_builder_combines_system_prompt_and_user_message() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(user_message="Hello")

    assert prompt == "System:\nYou are Lina.\n\nUser:\nHello"


def test_prompt_builder_strips_outer_whitespace() -> None:
    builder = PromptBuilder(system_prompt="  You are Lina.  ")

    prompt = builder.build(user_message="  Hello  ")

    assert prompt == "System:\nYou are Lina.\n\nUser:\nHello"
