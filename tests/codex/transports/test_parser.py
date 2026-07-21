import json

import pytest

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


def test_parser_accepts_bom_and_crlf() -> None:
    parser = CodexJsonlParser("session")
    events = parser.feed('\ufeff{"type":"turn.started"}\r\n')
    assert events[0].event_type is CodexEventType.ANALYZING
    assert parser.invalid_lines == 0


def test_parser_finishes_partial_final_line() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"item.completed","item":{"type":"agent_message","text":"Bitti"}}')
    assert parser.finish()[0].event_type is CodexEventType.COMPLETED
    assert parser.summary == "Bitti"


def test_parser_ignores_empty_lines() -> None:
    parser = CodexJsonlParser("session")
    assert parser.feed("\n\r\n   \n") == ()
    assert parser.invalid_lines == 0


def test_non_json_warning_is_diagnostic_metadata_only() -> None:
    parser = CodexJsonlParser("session")
    parser.feed("warning: retrying\n")
    assert parser.invalid_lines == 1
    assert "stderr_warnings=1" in parser.diagnostics


def test_usage_event_captures_only_bounded_integer_counts() -> None:
    parser = CodexJsonlParser("session")
    event = parser.feed(
        '{"type":"usage","usage":{"input_tokens":12,"output_tokens":3,"secret":"no"}}\n'
    )[0]
    assert event.event_type is CodexEventType.USAGE
    assert parser.usage == {"input_tokens": 12, "output_tokens": 3}


def test_nested_content_is_flattened_without_raw_payload() -> None:
    parser = CodexJsonlParser("session")
    parser.feed(
        '{"type":"item.completed","item":{"type":"agent_message","content":'
        '[{"text":"Bir"},{"content":{"text":"İki"}}]}}\n'
    )
    assert parser.summary == "Bir\nİki"


def test_parser_preserves_unicode_and_turkish() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"message.completed","text":"İnceleme tamamlandı ✓"}\n')
    assert parser.summary == "İnceleme tamamlandı ✓"


def test_huge_line_is_dropped_and_buffer_released() -> None:
    parser = CodexJsonlParser("session", max_line_characters=1024)
    parser.feed("x" * 2048)
    assert parser.truncated_lines == 1
    assert parser.finish() == ()


def test_missing_final_event_is_explicit_diagnostic() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"turn.started"}\n')
    assert "final_event_missing" in parser.diagnostics


def test_completed_event_satisfies_final_event_diagnostic() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"turn.completed"}\n')
    assert "final_event_missing" not in parser.diagnostics


def test_unknown_future_event_is_counted_without_crashing() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"future.v99","content":{"text":"progress"}}\n')
    assert parser.unknown_events == 1
    assert "unknown_events=1" in parser.diagnostics


def test_stderr_warning_count_does_not_store_content() -> None:
    parser = CodexJsonlParser("session")
    parser.feed_stderr("api key=sk-secret12345")
    assert parser.warning_lines == 1
    assert not hasattr(parser, "stderr")


def test_non_object_json_is_rejected() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('["event"]\n')
    assert parser.invalid_lines == 1


def test_parser_records_dangerous_git_command_as_metadata_signal() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"command.started","item":{"command":"git push origin main"}}\n')
    assert parser.git_action_signals == {"git_push_signal"}
    assert "origin main" not in repr(parser.git_action_signals)


def test_parser_ignores_safe_non_git_command_signal() -> None:
    parser = CodexJsonlParser("session")
    parser.feed('{"type":"command.started","item":{"command":"python -m pytest"}}\n')
    assert parser.git_action_signals == set()


def test_parser_records_successful_test_evidence_without_raw_command() -> None:
    parser = CodexJsonlParser("session")
    parser.feed(
        '{"type":"item.completed","item":{"type":"command_execution",'
        '"command":"python -m pytest tests/private_case.py","exit_code":0}}\n'
    )
    assert parser.tests_passed is True
    assert parser.test_commands == {"pytest"}
    assert "private_case.py" not in repr(parser.test_commands)


def test_parser_records_failed_test_evidence() -> None:
    parser = CodexJsonlParser("session")
    parser.feed(
        '{"type":"item.completed","item":{"type":"command_execution",'
        '"command":"pytest","exit_code":1}}\n'
    )
    assert parser.tests_passed is False


def test_parser_correlates_started_command_with_sparse_completion() -> None:
    parser = CodexJsonlParser("session")
    parser.feed(
        '{"type":"item.started","item":{"id":"cmd-1","type":"command_execution",'
        '"command":"pytest -q","status":"in_progress"}}\n'
        '{"type":"item.completed","item":{"id":"cmd-1","type":"command_execution",'
        '"exit_code":0,"status":"completed"}}\n'
    )
    assert parser.tests_passed is True
    assert parser.test_commands == {"pytest"}


@pytest.mark.parametrize("exit_key", ("exitCode", "return_code", "returnCode"))
def test_parser_accepts_forward_compatible_exit_code_keys(exit_key: str) -> None:
    parser = CodexJsonlParser("session")
    parser.feed(
        '{"type":"item.completed","item":{"id":"cmd-1","type":"command_execution",'
        f'"command":"python -m pytest -q","{exit_key}":0,"status":"completed"}}}}\n'
    )
    assert parser.tests_passed is True


@pytest.mark.parametrize("status", ("failed", "error", "cancelled"))
def test_parser_treats_terminal_failure_without_exit_code_as_failed(status: str) -> None:
    parser = CodexJsonlParser("session")
    parser.feed(
        '{"type":"item.completed","item":{"type":"command_execution",'
        f'"command":"pytest -q","status":"{status}"}}}}\n'
    )
    assert parser.tests_passed is False


@pytest.mark.parametrize(
    "command",
    (
        'powershell.exe -Command "python -m pytest tests -q"',
        'pwsh.exe -Command "C:\\work\\.venv\\Scripts\\python.exe -m pytest -q"',
        "pwsh -Command & 'C:\\Program Files\\Python\\python.exe' -m pytest -q",
        'cmd.exe /c ".venv\\Scripts\\pytest.exe -q"',
        "uv run pytest -q",
        "poetry run pytest -q",
        "py -m pytest -q",
    ),
)
def test_parser_recognizes_wrapped_windows_test_commands(command: str) -> None:
    parser = CodexJsonlParser("session")
    parser.feed(
        '{"type":"item.completed","item":{"type":"command_execution",'
        f'"command":{json.dumps(command)},"exit_code":0,"status":"completed"}}}}\n'
    )
    assert parser.tests_passed is True
    assert parser.test_commands == {"pytest"}
