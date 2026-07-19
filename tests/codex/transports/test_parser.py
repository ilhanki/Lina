from lina.codex.models import CodexEventType
from lina.codex.transports.parser import CodexJsonlParser


def test_jsonl_parser_handles_partial_lines_and_final_message() -> None:
    parser = CodexJsonlParser("session")
    assert parser.feed('{"type":"thread.started"') == ()
    events = parser.feed('}\n{"type":"item.completed","item":{"type":"agent_message","text":"Tamamlandı"}}\n')
    assert [event.event_type for event in events] == [
        CodexEventType.SESSION_STARTED, CodexEventType.COMPLETED
    ]
    assert parser.summary == "Tamamlandı"


def test_parser_tolerates_unknown_event_for_forward_compatibility() -> None:
    parser = CodexJsonlParser("session")
    events = parser.feed('{"type":"future.event","message":"ilerliyor"}\n')
    assert events[0].event_type is CodexEventType.ANALYZING


def test_parser_counts_malformed_event_without_exposing_it() -> None:
    parser = CodexJsonlParser("session")
    assert parser.feed("not-json\n") == ()
    assert parser.invalid_lines == 1


def test_parser_maps_runtime_approval_without_auto_approval() -> None:
    parser = CodexJsonlParser("session")
    events = parser.feed('{"type":"command.approval_requested","message":"run tests"}\n')
    assert events[0].event_type is CodexEventType.APPROVAL_REQUESTED
    assert parser.runtime_approval_requested


def test_parser_redacts_secret_like_message() -> None:
    parser = CodexJsonlParser("session")
    event = parser.feed(
        '{"type":"message.completed","text":"api key=sk-secret12345"}\n'
    )[0]
    assert "sk-secret12345" not in event.message


def test_parser_captures_valid_remote_thread_id() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"thread.started","thread_id":"123e4567-e89b-42d3-a456-426614174000"}\n')
    assert parser.remote_session_id == "123e4567-e89b-42d3-a456-426614174000"


def test_parser_rejects_unsafe_remote_thread_id() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"thread.started","thread_id":"bad&id"}\n')
    assert parser.remote_session_id is None
