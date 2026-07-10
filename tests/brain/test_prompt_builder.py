from lina.brain.conversation_context import ConversationContext
from lina.brain.model_provider import ModelMessage
from lina.brain.prompt_builder import ConversationTurn, PromptBuilder


def test_prompt_builder_creates_system_and_user_messages() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(user_message="Hello")

    assert messages[0].role == "system"
    assert "You are Lina." in messages[0].content
    assert "Yalnız son user mesajına" in messages[0].content
    assert messages[-1] == ModelMessage(role="user", content="Hello")


def test_prompt_builder_strips_outer_whitespace() -> None:
    builder = PromptBuilder(system_prompt="  You are Lina.  ")

    messages = builder.build(user_message="  Hello  ")

    assert messages[0].content.startswith("You are Lina.")
    assert messages[-1].content == "Hello"


def test_prompt_builder_preserves_structured_history_roles() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(
        user_message="What is my name?",
        history=[
            ConversationTurn(
                user_message="My name is Ilhan.",
                assistant_response="Nice to meet you.",
            ),
        ],
    )

    assert messages == (
        messages[0],
        ModelMessage(role="user", content="My name is Ilhan."),
        ModelMessage(role="assistant", content="Nice to meet you."),
        ModelMessage(role="user", content="What is my name?"),
    )


def test_prompt_builder_does_not_promote_malformed_text_to_a_name() -> None:
    builder = PromptBuilder(system_prompt="User identity is İlhan.")

    messages = builder.build(
        user_message="bir proje fikri düşünüyorum",
        history=[
            ConversationTurn(
                user_message="Marrabalina Nesussan",
                assistant_response="Seni anlayamadım İlhan.",
            )
        ],
    )

    assert messages[1] == ModelMessage(role="user", content="Marrabalina Nesussan")
    assert messages[-1] == ModelMessage(
        role="user",
        content="bir proje fikri düşünüyorum",
    )
    assert "Kullanıcı mesajından isim türetme" in messages[0].content


def test_prompt_builder_truncates_long_history_fields() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")
    long_user_message = "u" * 1300
    long_assistant_response = "a" * 1300

    messages = builder.build(
        user_message="Continue",
        history=[
            ConversationTurn(
                user_message=long_user_message,
                assistant_response=long_assistant_response,
            ),
        ],
    )

    assert long_user_message not in messages[1].content
    assert long_assistant_response not in messages[2].content
    assert "[geçmiş mesaj kısaltıldı]" in messages[1].content
    assert "[geçmiş mesaj kısaltıldı]" in messages[2].content
    assert messages[-1].content == "Continue"


def test_prompt_builder_includes_project_context_in_system_message() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(
        user_message="What happened in the project?",
        project_context="Sprint 5 completed.",
    )

    assert "Project context:" in messages[0].content
    assert "Sprint 5 completed." in messages[0].content
    assert messages[-1].content == "What happened in the project?"


def test_prompt_builder_includes_memory_context_in_system_message() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(
        user_message="How should you answer?",
        memory_context="Hatırlanan bilgiler:\n- kısa cevapları seviyorum",
    )

    assert "Memory context:" in messages[0].content
    assert "yalnızca yardımcı bağlam olarak kullan" in messages[0].content
    assert "- kısa cevapları seviyorum" in messages[0].content


def test_prompt_builder_skips_empty_memory_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(user_message="Hello", memory_context=" ")

    assert "Memory context:" not in messages[0].content


def test_prompt_builder_includes_project_and_memory_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(
        user_message="What happened?",
        project_context="Project context",
        memory_context="Memory context",
    )

    assert "Memory context:" in messages[0].content
    assert "Project context:" in messages[0].content


def test_file_context_uses_system_and_current_user_only() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(
        user_message="Summarize this file.",
        history=[ConversationTurn(user_message="Hello", assistant_response="Hi")],
        file_context="File: README.md\nContent:\nLina docs",
    )

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "File context:" in messages[0].content
    assert "izinli dosya bağlamını birincil kaynak olarak kullan" in messages[0].content
    assert "Lina docs" in messages[0].content
    assert messages[1] == ModelMessage(role="user", content="Summarize this file.")


def test_prompt_builder_skips_empty_file_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(user_message="Hello", file_context=" ")

    assert messages[-1] == ModelMessage(role="user", content="Hello")


def test_file_context_keeps_memory_and_project_as_system_context() -> None:
    builder = PromptBuilder(system_prompt="You are Lina.")

    messages = builder.build(
        user_message="What should I know?",
        project_context="Project context",
        memory_context="Memory context",
        file_context="File context",
    )

    assert "Memory context:" in messages[0].content
    assert "Project context:" in messages[0].content
    assert "File context:" in messages[0].content


def test_prompt_builder_builds_messages_from_conversation_context() -> None:
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

    messages = builder.build_from_context(context)

    assert len(messages) == 2
    assert "Project context" in messages[0].content
    assert "Memory context" in messages[0].content
    assert "File context" in messages[0].content
    assert messages[-1] == ModelMessage(role="user", content="What happened?")
