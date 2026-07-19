"""Safe discovery, capability and redacted diagnostics for the official Codex CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
from typing import Callable, Mapping

from lina.codex.transports.errors import CodexCliNotFound


MINIMUM_CODEX_CLI_VERSION = (0, 1, 0)
_VERSION = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?")
_SAFE_NAMES = frozenset({"codex", "codex.exe", "codex.cmd"})


@dataclass(frozen=True, slots=True)
class CodexExecutableCandidate:
    path: Path
    source: str
    kind: str
    exists: bool
    accessible: bool
    launchable: bool = False
    version: str | None = None
    capabilities: tuple[str, ...] = ()
    rejection_reason: str | None = None
    priority: int = 100
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def usable(self) -> bool:
        return self.exists and self.accessible and self.launchable and not self.rejection_reason


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
    supports_jsonl: bool = False
    supports_session_id: bool = False
    supports_read_only: bool = False
    supports_workspace_write: bool = False
    supports_runtime_approval: bool = False
    supports_model: bool = False
    supports_reasoning_effort: bool = False
    supports_output_schema: bool = False
    selected_candidate_source: str = "unknown"
    executable_kind: str = "unknown"
    candidates: tuple[CodexExecutableCandidate, ...] = ()
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


def candidate_kind(path: Path, *, configured: bool = False) -> str:
    if configured:
        return "configured_path"
    folded = str(path).casefold()
    if "windowsapps" in folded:
        return "packaged_app"
    if path.suffix.casefold() == ".cmd":
        return "cmd_wrapper"
    if path.suffix.casefold() == ".exe":
        return "native_exe"
    if path.name.casefold() == "codex":
        return "npm_shim"
    return "unknown"


def _candidate(path: Path, source: str, priority: int, *, configured: bool = False) -> CodexExecutableCandidate:
    try:
        resolved = path.expanduser().resolve(strict=False)
        exists = resolved.is_file()
        accessible = exists and os.access(resolved, os.R_OK)
    except (OSError, RuntimeError):
        resolved, exists, accessible = path, False, False
    reason = None if exists and accessible else ("not_found" if not exists else "access_denied")
    return CodexExecutableCandidate(
        resolved, source, candidate_kind(resolved, configured=configured), exists, accessible,
        rejection_reason=reason, priority=priority,
    )


def discover_candidates(
    configured_path: str | Path | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] | None = None,
) -> tuple[CodexExecutableCandidate, ...]:
    """Return bounded candidates in product priority order without launching them."""

    values = os.environ if environment is None else environment
    locate = which or shutil.which
    raw: list[tuple[Path, str, int, bool]] = []
    if configured_path:
        raw.append((Path(configured_path), "configured", 0, True))
    for priority, name in enumerate(("codex.cmd", "codex.exe", "codex"), start=10):
        found = locate(name)
        if found:
            raw.append((Path(found), f"path:{name}", priority, False))
    appdata = values.get("APPDATA")
    if appdata:
        npm = Path(appdata) / "npm"
        for offset, name in enumerate(("codex.cmd", "codex.exe", "codex")):
            raw.append((npm / name, "npm_global", 20 + offset, False))
    npm_prefix = values.get("NPM_CONFIG_PREFIX")
    if npm_prefix:
        prefix = Path(npm_prefix)
        for offset, name in enumerate(("codex.cmd", "codex.exe", "codex")):
            raw.append((prefix / name, "npm_prefix", 30 + offset, False))

    candidates: list[CodexExecutableCandidate] = []
    seen: set[str] = set()
    for path, source, priority, configured in raw:
        item = _candidate(path, source, priority, configured=configured)
        key = str(item.path).casefold()
        if key in seen:
            continue
        seen.add(key)
        if item.path.name.casefold() not in _SAFE_NAMES:
            item = CodexExecutableCandidate(
                item.path, item.source, item.kind, item.exists, item.accessible,
                rejection_reason="unexpected_executable_name", priority=item.priority,
            )
        candidates.append(item)
    return tuple(sorted(candidates, key=lambda item: item.priority))


def discover_executable(configured_path: str | Path | None = None) -> Path:
    """Compatibility helper returning the first accessible bounded candidate."""

    candidates = discover_candidates(configured_path)
    if configured_path:
        candidates = candidates[:1]
    for item in candidates:
        if item.exists and item.accessible and not item.rejection_reason:
            return item.path
    raise CodexCliNotFound("Codex CLI executable bulunamadı.")


def capabilities_from_help(
    root_help: str,
    exec_help: str,
    login_help: str,
    doctor_help: str = "",
    resume_help: str = "",
) -> dict[str, bool]:
    root = root_help.casefold()
    execute = exec_help.casefold()
    login = login_help.casefold()
    resume = resume_help.casefold()
    sandbox_values = execute + "\n" + root
    has_json = "--json" in execute
    has_resume = bool(re.search(r"(?:^|\s)resume(?:\s|$)", root + "\n" + execute))
    return {
        "supports_exec": bool(re.search(r"(?:^|\s)exec(?:\s|$)", root + "\n" + execute)),
        "supports_json": has_json,
        "supports_jsonl": has_json and ("jsonl" in execute or "events" in execute),
        "supports_resume": has_resume,
        "supports_session_id": has_resume and ("session_id" in resume or "session id" in resume),
        "supports_approval_flags": "--ask-for-approval" in execute or "--ask-for-approval" in root,
        "supports_runtime_approval": "--ask-for-approval" in execute or "--ask-for-approval" in root,
        "supports_device_auth": "--device-auth" in login,
        "supports_stdin": "stdin" in execute or re.search(r"(?:^|\s)-(?:,|\s).*stdin", execute) is not None,
        "supports_cd": "--cd" in execute or "--cd" in root,
        "supports_sandbox": "--sandbox" in execute or "--sandbox" in root,
        "supports_read_only": "read-only" in sandbox_values,
        "supports_workspace_write": "workspace-write" in sandbox_values,
        "supports_model": "--model" in execute or "--model" in root,
        "supports_reasoning_effort": "reasoning" in execute or "model_reasoning_effort" in execute,
        "supports_output_schema": "--output-schema" in execute or "--output-schema" in resume,
        "approval_flags_global": "--ask-for-approval" not in execute and "--ask-for-approval" in root,
        "sandbox_global": "--sandbox" not in execute and "--sandbox" in root,
        "cd_global": "--cd" not in execute and "--cd" in root,
        "supports_doctor": bool(re.search(r"(?:^|\s)doctor(?:\s|$)", root)),
        "supports_doctor_json": "--json" in doctor_help.casefold(),
        "supports_ephemeral": "--ephemeral" in execute,
    }


_SENSITIVE = re.compile(
    r"(?ix)(?:"
    r"(?:(?:bearer\s+|(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|password|cookie)\s*[:=]\s*))"
    r"([A-Za-z0-9._~+/=-]{8,})|"
    r"\b(?:sk-[A-Za-z0-9_-]{8,}|gh[opusr]_[A-Za-z0-9_]{12,})\b|"
    r"-----BEGIN\s+(?:RSA\s+|OPENSSH\s+|EC\s+)?PRIVATE\s+KEY-----"
    r")"
)
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b")
_CONNECTION_SECRET = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|amqp)://"
    r"([^\s:/@]{1,128}):([^\s@]{8,})@"
)
_EMAIL_PASSWORD = re.compile(
    r"(?i)(email\s*[:=]\s*[^\s,;]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
    r"([\s,;]+password\s*[:=]\s*)([^\s,;]{8,})"
)


def redact(text: str) -> str:
    value = str(text or "")
    value = _SENSITIVE.sub(lambda match: (
        match.group(0).replace(match.group(1), "[REDACTED]") if match.group(1) else "[REDACTED]"
    ), value)
    value = _JWT.sub("[REDACTED]", value)
    value = _CONNECTION_SECRET.sub(
        lambda match: match.group(0).replace(match.group(2), "[REDACTED]"), value
    )
    return _EMAIL_PASSWORD.sub(
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", value
    )


def contains_sensitive_text(text: str) -> bool:
    value = str(text or "")
    return any(pattern.search(value) is not None for pattern in (
        _SENSITIVE, _JWT, _CONNECTION_SECRET, _EMAIL_PASSWORD,
    ))


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
