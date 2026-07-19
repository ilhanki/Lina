"""Typed, shell-free process invocations for native and Windows shim CLIs."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
from typing import Mapping, Sequence


_ENV_ALLOWLIST = frozenset({
    "APPDATA", "COMSPEC", "HOMEDRIVE", "HOMEPATH", "LANG", "LC_ALL",
    "LOCALAPPDATA", "PATH", "PATHEXT", "SYSTEMDRIVE", "SYSTEMROOT",
    "TEMP", "TMP", "USERPROFILE", "WINDIR",
})
_BLOCKED_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "CREDENTIAL")


@dataclass(frozen=True, slots=True)
class WindowsCommandInvocation:
    """A fully materialized subprocess invocation; prompt data is never included."""

    argv: tuple[str, ...]
    environment: Mapping[str, str]
    display_args: tuple[str, ...]
    executable_kind: str
    uses_cmd_wrapper: bool = False
    command_line: str | None = None

    def __post_init__(self) -> None:
        if not self.argv:
            raise ValueError("Invocation argv cannot be empty")
        if any("\x00" in item or "\r" in item or "\n" in item for item in self.argv):
            raise ValueError("Invocation arguments contain control characters")

    def __iter__(self):
        return iter(self.argv)

    def __len__(self) -> int:
        return len(self.argv)

    def __getitem__(self, index: int) -> str:
        return self.argv[index]


def minimal_subprocess_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Retain only runtime-location variables and never inherit credential values."""

    values = source or os.environ
    safe: dict[str, str] = {}
    for key, value in values.items():
        upper = key.upper()
        if upper not in _ENV_ALLOWLIST or any(marker in upper for marker in _BLOCKED_ENV_MARKERS):
            continue
        if "\x00" not in value:
            safe[key] = value
    return safe


def _quote_cmd_argument(value: str) -> str:
    """Quote one trusted structural argument for cmd.exe without enabling expansion."""

    if value == "":
        return '""'
    if any(character in value for character in ('"', "\x00", "\r", "\n")):
        raise ValueError("Unsafe Windows command argument")
    return f'"{value.replace("%", "%%")}"'


def build_process_invocation(
    executable: str | Path,
    arguments: Sequence[str | Path] = (),
    *,
    kind: str = "unknown",
    environment: Mapping[str, str] | None = None,
) -> WindowsCommandInvocation:
    """Build the single audited command line used by every Codex subprocess."""

    executable_text = str(executable)
    argument_text = tuple(str(item) for item in arguments)
    structural = (executable_text, *argument_text)
    if any("\x00" in item or "\r" in item or "\n" in item for item in structural):
        raise ValueError("Invocation arguments contain control characters")
    safe_environment = minimal_subprocess_environment(environment)
    suffix = Path(executable_text).suffix.casefold()
    is_cmd = kind == "cmd_wrapper" or suffix in {".cmd", ".bat"}
    if os.name == "nt" and is_cmd:
        command = " ".join(_quote_cmd_argument(item) for item in structural)
        wrapped = f'"{command}"'
        comspec = safe_environment.get("ComSpec") or safe_environment.get("COMSPEC")
        launcher = comspec or shutil.which("cmd.exe") or "cmd.exe"
        argv = (launcher, "/d", "/s", "/c", wrapped)
        return WindowsCommandInvocation(
            argv, safe_environment, structural, kind, uses_cmd_wrapper=True,
            command_line=f'"{launcher}" /d /s /c {wrapped}',
        )
    return WindowsCommandInvocation(
        structural, safe_environment, structural, kind, uses_cmd_wrapper=False
    )
