"""Shell-free Codex subprocess state machine with bounded streaming and tree cleanup."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

from lina.codex.transports.diagnostics import contains_sensitive_text, redact
from lina.codex.transports.errors import CodexCancelled, CodexTimeout
from lina.codex.transports.invocation import WindowsCommandInvocation


class CodexProcessState(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    TERMINATING = "terminating"
    KILLED = "killed"
    EXITED = "exited"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProcessResult:
    args: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    sensitive_output_detected: bool = False
    state: CodexProcessState = CodexProcessState.EXITED
    output_truncated: bool = False


class CodexProcessRunner:
    def __init__(self, *, max_output_bytes: int = 2_000_000,
                 terminate_grace_seconds: float = 1.5) -> None:
        self._lock = threading.Lock()
        self._active: subprocess.Popen[str] | None = None
        self._cancelled = threading.Event()
        self._state = CodexProcessState.CREATED
        self.max_output_bytes = max(16_384, int(max_output_bytes))
        self.terminate_grace_seconds = max(0.05, float(terminate_grace_seconds))

    @property
    def state(self) -> CodexProcessState:
        with self._lock:
            return self._state

    def _set_state(self, state: CodexProcessState) -> None:
        with self._lock:
            self._state = state

    def run(
        self,
        args: Sequence[str | Path] | WindowsCommandInvocation,
        *,
        cwd: Path | None = None,
        stdin_text: str | None = None,
        timeout: float = 120.0,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
    ) -> ProcessResult:
        invocation = args if isinstance(args, WindowsCommandInvocation) else None
        command = (invocation.argv if invocation is not None
                   else tuple(str(item) for item in args))
        if not command:
            raise ValueError("Process command cannot be empty")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        start = time.monotonic()
        self._cancelled.clear()
        self._set_state(CodexProcessState.STARTING)
        launch_args: list[str] | str = (
            invocation.command_line if invocation is not None and invocation.command_line
            else list(command)
        )
        try:
            process = subprocess.Popen(
                launch_args, cwd=str(cwd) if cwd else None, shell=False,
                stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                encoding="utf-8", errors="replace", bufsize=1, creationflags=flags,
                env=dict(invocation.environment) if invocation is not None else None,
            )
        except OSError:
            self._set_state(CodexProcessState.FAILED)
            raise
        with self._lock:
            self._active = process
            self._state = CodexProcessState.RUNNING
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        sensitive = threading.Event()
        truncated = threading.Event()

        def read_stream(stream, sink: list[str], callback: Callable[[str], None] | None) -> None:
            retained = 0
            for line in iter(stream.readline, ""):
                if contains_sensitive_text(line):
                    sensitive.set()
                safe_line = redact(line)
                encoded_size = len(safe_line.encode("utf-8", errors="replace"))
                if retained + encoded_size <= self.max_output_bytes:
                    sink.append(safe_line)
                    retained += encoded_size
                    if callback is not None:
                        callback(safe_line)
                else:
                    truncated.set()
            stream.close()

        out_thread = threading.Thread(
            target=read_stream, args=(process.stdout, stdout_lines, on_stdout),
            name="codex-stdout", daemon=True,
        )
        err_thread = threading.Thread(
            target=read_stream, args=(process.stderr, stderr_lines, on_stderr),
            name="codex-stderr", daemon=True,
        )
        out_thread.start()
        err_thread.start()

        def write_stdin() -> None:
            if process.stdin is None:
                return
            self._set_state(CodexProcessState.WAITING_INPUT)
            try:
                process.stdin.write(stdin_text or "")
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                try:
                    process.stdin.close()
                except OSError:
                    pass
                if process.poll() is None:
                    self._set_state(CodexProcessState.RUNNING)

        input_thread = threading.Thread(target=write_stdin, name="codex-stdin", daemon=True)
        input_thread.start()
        try:
            while process.poll() is None:
                if self._cancelled.is_set():
                    self._terminate(process)
                    raise CodexCancelled()
                if time.monotonic() - start > timeout:
                    self._terminate(process)
                    raise CodexTimeout()
                time.sleep(0.02)
            out_thread.join(timeout=2.0)
            err_thread.join(timeout=2.0)
            input_thread.join(timeout=0.2)
            if self._cancelled.is_set():
                raise CodexCancelled()
            self._set_state(CodexProcessState.EXITED)
            safe_args = invocation.display_args if invocation is not None else command
            return ProcessResult(
                safe_args, int(process.returncode or 0), "".join(stdout_lines),
                "".join(stderr_lines), time.monotonic() - start, sensitive.is_set(),
                CodexProcessState.EXITED, truncated.is_set(),
            )
        except (CodexCancelled, CodexTimeout):
            raise
        except Exception:
            self._set_state(CodexProcessState.FAILED)
            raise
        finally:
            with self._lock:
                if self._active is process:
                    self._active = None

    def cancel(self) -> None:
        self._cancelled.set()
        with self._lock:
            process = self._active
        if process is not None and process.poll() is None:
            self._terminate(process)

    def shutdown(self) -> None:
        self.cancel()

    def _terminate(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        self._set_state(CodexProcessState.TERMINATING)
        try:
            if os.name == "nt":
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                process.terminate()
            process.wait(timeout=self.terminate_grace_seconds)
            self._set_state(CodexProcessState.KILLED)
            return
        except (OSError, subprocess.TimeoutExpired):
            pass
        if os.name == "nt":
            try:
                subprocess.run(
                    ("taskkill", "/PID", str(process.pid), "/T", "/F"), shell=False,
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=5, check=False,
                )
            except (OSError, subprocess.SubprocessError):
                pass
        try:
            process.kill()
            process.wait(timeout=1.0)
        except (OSError, subprocess.TimeoutExpired):
            pass
        self._set_state(CodexProcessState.KILLED)
