"""Safe discovery and capability diagnostics for the official Codex CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil

from lina.codex.transports.errors import CodexCliNotFound


MINIMUM_CODEX_CLI_VERSION = (0, 1, 0)
_VERSION = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?")


@dataclass(frozen=True, slots=True)
class CodexCliInfo:
    executable_path: Path | None = None
    version: str | None = None
    available: bool = False
    authenticated: bool = False
    auth_method_summary: str = "unknown"
    supports_exec: bool = False
    supports_json: bool = False
    supports_resume: bool = False
    supports_approval_flags: bool = False
    supports_device_auth: bool = False
    supports_stdin: bool = False
    supports_cd: bool = False
    supports_sandbox: bool = False
    approval_flags_global: bool = False
    sandbox_global: bool = False
    cd_global: bool = False
    supports_doctor: bool = False
    supports_doctor_json: bool = False
    supports_ephemeral: bool = False
    diagnostics: tuple[str, ...] = ()
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def ready(self) -> bool:
        return self.available and self.authenticated and self.supports_exec and self.supports_json


def parse_version(output: str) -> tuple[str | None, tuple[int, int, int] | None]:
    match = _VERSION.search(output or "")
    if not match:
        return None, None
    return match.group(0), tuple(int(part) for part in match.groups())


def discover_executable(configured_path: str | Path | None = None) -> Path:
    """Resolve only explicit/PATH/npm-bin candidates; never scan a drive."""
    candidates: list[Path] = []
    if configured_path:
        candidate = Path(configured_path).expanduser()
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise CodexCliNotFound("Configured Codex CLI executable is invalid") from error
        if not resolved.is_file() or resolved.name.casefold() not in {"codex", "codex.exe"}:
            raise CodexCliNotFound("Configured Codex CLI executable is invalid")
        return resolved
    for name in ("codex", "codex.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "npm" / "codex.exe")
    npm_prefix = os.environ.get("NPM_CONFIG_PREFIX")
    if npm_prefix:
        candidates.append(Path(npm_prefix) / "codex.exe")

    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        key = str(resolved).casefold()
        if key in seen:
            continue
        seen.add(key)
        if resolved.is_file() and resolved.name.casefold() in {"codex", "codex.exe"}:
            return resolved
    raise CodexCliNotFound("Codex CLI executable bulunamadı.")


def capabilities_from_help(root_help: str, exec_help: str, login_help: str,
                           doctor_help: str = "") -> dict[str, bool]:
    root = root_help.casefold()
    execute = exec_help.casefold()
    login = login_help.casefold()
    return {
        "supports_exec": bool(re.search(r"(?:^|\s)exec(?:\s|$)", root + "\n" + execute)),
        "supports_json": "--json" in execute,
        "supports_resume": "resume" in root or "resume" in execute,
        "supports_approval_flags": "--ask-for-approval" in execute or "--ask-for-approval" in root,
        "supports_device_auth": "--device-auth" in login,
        "supports_stdin": "stdin" in execute or re.search(r"(?:^|\s)-(?:,|\s).*stdin", execute) is not None,
        "supports_cd": "--cd" in execute or "-c," in execute or "--cd" in root or "-c," in root,
        "supports_sandbox": "--sandbox" in execute or "--sandbox" in root,
        "approval_flags_global": "--ask-for-approval" not in execute and "--ask-for-approval" in root,
        "sandbox_global": "--sandbox" not in execute and "--sandbox" in root,
        "cd_global": "--cd" not in execute and "--cd" in root,
        "supports_doctor": bool(re.search(r"(?:^|\s)doctor(?:\s|$)", root)),
        "supports_doctor_json": "--json" in doctor_help.casefold(),
        "supports_ephemeral": "--ephemeral" in execute,
    }


_SENSITIVE = re.compile(
    r"(?i)(?:(?:bearer|api[_ -]?key|access[_ -]?token|refresh[_ -]?token)\s*[:=]?\s*)"
    r"([A-Za-z0-9._~+/=-]{8,})|\b(?:sk-[A-Za-z0-9_-]{8,})\b"
)


def redact(text: str) -> str:
    value = str(text or "")
    return _SENSITIVE.sub(lambda match: match.group(0).replace(match.group(1), "[REDACTED]")
                          if match.group(1) else "[REDACTED]", value)


def contains_sensitive_text(text: str) -> bool:
    return _SENSITIVE.search(str(text or "")) is not None


def parse_auth_status(output: str, exit_code: int) -> tuple[bool, str]:
    safe = redact(output).casefold()
    if exit_code != 0 or any(token in safe for token in ("not logged", "signed out", "login required")):
        return False, "none"
    if "chatgpt" in safe:
        return True, "ChatGPT"
    if "api key" in safe or "api_key" in safe:
        return True, "API key"
    if "access token" in safe:
        return True, "access token"
    if any(token in safe for token in ("logged in", "signed in", "authenticated")):
        return True, "unknown"
    return False, "unknown"
