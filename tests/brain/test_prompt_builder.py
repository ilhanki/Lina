from lina.brain.conversation_context import ConversationContext
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
            ConversationTurn(
                user_message="My name is Ilhan.",
                assistant_response="Nice to meet you.",
            ),
        ],
    )

    assert prompt == (
        "System:\nYou are Lina.\n\n"
        "Conversation history:\n"
        "User: My name is Ilhan.\n"
        "Assistant: Nice to meet you.\n\n"
        "User:\nWhat is my name?"
    )


def test_prompt_builder_includes_project_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(
        user_message="What happened in the project?",
        project_context="Sprint 5 completed.",
    )

    assert "Project context:" in prompt
    assert "Aşağıdaki proje bağlamına dayan" in prompt
    assert "Sprint 5 completed." in prompt
    assert "User:\nWhat happened in the project?" in prompt


def test_prompt_builder_includes_memory_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(
        user_message="How should you answer?",
        memory_context="Hatırlanan kullanıcı bilgileri:\n- kısa cevapları seviyorum",
    )

    assert "Memory context:" in prompt
    assert "yalnızca yardımcı bağlam olarak kullan" in prompt
    assert "- kısa cevapları seviyorum" in prompt


def test_prompt_builder_skips_empty_memory_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(user_message="Hello", memory_context=" ")

    assert "Memory context:" not in prompt


def test_prompt_builder_includes_project_and_memory_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(
        user_message="What happened?",
        project_context="Project context",
        memory_context="Memory context",
    )

    assert "Memory context:" in prompt
    assert "Project context:" in prompt


def test_prompt_builder_includes_file_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(
        user_message="Summarize this file.",
        file_context="File: README.md\nContent:\nLina docs",
    )

    assert "File context:" in prompt
    assert "izinli dosya bağlamını birincil kaynak olarak kullan" in prompt
    assert "önceki sohbet mesajlarına göre değil, dosya içeriğine göre cevap ver" in prompt
    assert "selamlama, sohbet sorusu veya meta başlık yazma" in prompt
    assert "File: README.md" in prompt
    assert "Lina docs" in prompt


def test_prompt_builder_skips_empty_file_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(user_message="Hello", file_context=" ")

    assert "File context:" not in prompt


def test_prompt_builder_includes_memory_project_and_file_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    prompt = builder.build(
        user_message="What should I know?",
        project_context="Project context",
        memory_context="Memory context",
        file_context="File context",
    )

    assert "Memory context:" in prompt
    assert "Project context:" in prompt
    assert "File context:" in prompt


def test_prompt_builder_builds_from_conversation_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")
    context = ConversationContext(
        user_message="What happened?",
        conversation_history=[
            ConversationTurn(user_message="Hello", assistant_response="Hi"),
        ],
        project_context="Project context",
        memory_context="Memory context",
        file_context="File context",
    )

    prompt = builder.build_from_context(context)

    assert "Project context" in prompt
    assert "Memory context" in prompt
    assert "File context" in prompt
    assert "Conversation history:" not in prompt
    assert "User:\nWhat happened?" in prompt
