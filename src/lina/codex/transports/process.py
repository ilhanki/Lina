"""Shell-free Codex subprocess lifecycle with streaming and cancellation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

from lina.codex.transports.diagnostics import contains_sensitive_text, redact
from lina.codex.transports.errors import CodexCancelled, CodexTimeout
from lina.codex.transports.invocation import WindowsCommandInvocation


@dataclass(frozen=True, slots=True)
class ProcessResult:
    args: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    sensitive_output_detected: bool = False


class CodexProcessRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: subprocess.Popen[str] | None = None
        self._cancelled = threading.Event()

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
        launch_args: list[str] | str = (
            invocation.command_line if invocation is not None and invocation.command_line
            else list(command)
        )
        process = subprocess.Popen(
            launch_args, cwd=str(cwd) if cwd else None, shell=False,
            stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", bufsize=1, creationflags=flags,
            env=dict(invocation.environment) if invocation is not None else None,
        )
        with self._lock:
            self._active = process
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        sensitive = threading.Event()

        def read_stream(stream, sink: list[str], callback: Callable[[str], None] | None) -> None:
            for line in iter(stream.readline, ""):
                if contains_sensitive_text(line):
                    sensitive.set()
                sink.append(line)
                if callback is not None:
                    callback(redact(line))
            stream.close()

        out_thread = threading.Thread(target=read_stream, args=(process.stdout, stdout_lines, on_stdout), daemon=True)
        err_thread = threading.Thread(target=read_stream, args=(process.stderr, stderr_lines, on_stderr), daemon=True)
        out_thread.start()
        err_thread.start()
        if process.stdin is not None:
            try:
                process.stdin.write(stdin_text or "")
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                process.stdin.close()
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
            if self._cancelled.is_set():
                raise CodexCancelled()
            safe_args = invocation.display_args if invocation is not None else command
            return ProcessResult(safe_args, int(process.returncode or 0), redact("".join(stdout_lines)),
                                 redact("".join(stderr_lines)), time.monotonic() - start,
                                 sensitive.is_set())
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

    @staticmethod
    def _terminate(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name == "nt":
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                process.terminate()
            process.wait(timeout=1.5)
            return
        except (OSError, subprocess.TimeoutExpired):
            pass
        try:
            process.terminate()
            process.wait(timeout=1.0)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
            try:
                process.wait(timeout=1.0)
            except (OSError, subprocess.TimeoutExpired):
                pass
