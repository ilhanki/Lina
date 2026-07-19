import sys
import threading
import time

import pytest

from lina.codex.transports.errors import CodexCancelled, CodexTimeout
from lina.codex.transports.process import CodexProcessRunner, CodexProcessState


def test_process_streams_stdout_and_uses_stdin() -> None:
    runner = CodexProcessRunner()
    lines: list[str] = []
    result = runner.run(
        (sys.executable, "-c", "import sys; print(sys.stdin.read())"),
        stdin_text="güvenli prompt", on_stdout=lines.append, timeout=5,
    )
    assert result.exit_code == 0
    assert "güvenli prompt" in result.stdout
    assert lines


def test_process_timeout_terminates_child() -> None:
    runner = CodexProcessRunner()
    with pytest.raises(CodexTimeout):
        runner.run((sys.executable, "-c", "import time; time.sleep(5)"), timeout=0.05)


def test_process_cancellation_terminates_child() -> None:
    runner = CodexProcessRunner()
    errors: list[Exception] = []

    def execute() -> None:
        try:
            runner.run((sys.executable, "-c", "import time; time.sleep(5)"), timeout=10)
        except Exception as error:
            errors.append(error)

    thread = threading.Thread(target=execute)
    thread.start()
    time.sleep(0.1)
    runner.cancel()
    thread.join(timeout=3)
    assert not thread.is_alive()
    assert errors and isinstance(errors[0], CodexCancelled)


def test_process_detects_and_redacts_sensitive_output() -> None:
    runner = CodexProcessRunner()
    result = runner.run((sys.executable, "-c", "print('api key=sk-secret12345')"), timeout=5)
    assert result.sensitive_output_detected
    assert "sk-secret12345" not in result.stdout


def test_process_state_machine_exits_cleanly() -> None:
    runner = CodexProcessRunner()
    result = runner.run((sys.executable, "-c", "print('ok')"), timeout=5)
    assert result.state is CodexProcessState.EXITED
    assert runner.state is CodexProcessState.EXITED


def test_process_bounds_stdout_while_draining_child() -> None:
    runner = CodexProcessRunner(max_output_bytes=16_384)
    result = runner.run((sys.executable, "-c", "print('x' * 30000)"), timeout=5)
    assert result.output_truncated
    assert len(result.stdout.encode()) <= 16_384


def test_process_bounds_stderr_flood() -> None:
    runner = CodexProcessRunner(max_output_bytes=16_384)
    result = runner.run(
        (sys.executable, "-c", "import sys; sys.stderr.write('x' * 30000)"), timeout=5
    )
    assert result.output_truncated
    assert len(result.stderr.encode()) <= 16_384


def test_process_reports_failed_state_when_launch_fails(tmp_path) -> None:
    runner = CodexProcessRunner()
    with pytest.raises(OSError):
        runner.run((tmp_path / "missing-executable.exe",), timeout=1)
    assert runner.state is CodexProcessState.FAILED


def test_timeout_ends_in_killed_state() -> None:
    runner = CodexProcessRunner(terminate_grace_seconds=0.05)
    with pytest.raises(CodexTimeout):
        runner.run((sys.executable, "-c", "import time; time.sleep(5)"), timeout=0.05)
    assert runner.state is CodexProcessState.KILLED


def test_cancel_ends_in_killed_state() -> None:
    runner = CodexProcessRunner(terminate_grace_seconds=0.05)
    errors = []

    def execute() -> None:
        try:
            runner.run((sys.executable, "-c", "import time; time.sleep(5)"), timeout=10)
        except Exception as error:
            errors.append(error)

    thread = threading.Thread(target=execute)
    thread.start()
    time.sleep(0.1)
    runner.cancel()
    thread.join(timeout=3)
    assert errors and isinstance(errors[0], CodexCancelled)
    assert runner.state is CodexProcessState.KILLED
