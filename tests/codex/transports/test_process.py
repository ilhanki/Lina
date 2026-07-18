import sys
import threading
import time

import pytest

from lina.codex.transports.errors import CodexCancelled, CodexTimeout
from lina.codex.transports.process import CodexProcessRunner


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

