from pathlib import Path

import pytest

from lina.codex.transports.diagnostics import (
    capabilities_from_help,
    discover_executable,
    parse_auth_status,
    parse_version,
    redact,
)
from lina.codex.transports.errors import CodexCliNotFound


def test_discovery_prefers_configured_executable(monkeypatch, tmp_path: Path) -> None:
    configured = tmp_path / "codex.exe"
    configured.write_bytes(b"fixture")
    monkeypatch.setattr("shutil.which", lambda _name: str(tmp_path / "other" / "codex.exe"))
    assert discover_executable(configured) == configured.resolve()


def test_discovery_finds_codex_and_codex_exe(monkeypatch, tmp_path: Path) -> None:
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"fixture")
    monkeypatch.setattr("shutil.which", lambda name: str(executable) if name == "codex.exe" else None)
    assert discover_executable() == executable.resolve()


@pytest.mark.parametrize("configured", ("missing.exe", "other.exe"))
def test_discovery_rejects_missing_or_unexpected_name(tmp_path: Path, monkeypatch, configured: str) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: None)
    candidate = tmp_path / configured
    if configured == "other.exe":
        candidate.write_bytes(b"fixture")
    with pytest.raises(CodexCliNotFound):
        discover_executable(candidate)


@pytest.mark.parametrize(
    ("raw", "expected"),
    (("codex-cli 1.2.3", (1, 2, 3)), ("codex 0.9.0-alpha.1", (0, 9, 0))),
)
def test_semantic_version_parsing(raw: str, expected: tuple[int, int, int]) -> None:
    assert parse_version(raw)[1] == expected


def test_malformed_version_is_graceful() -> None:
    assert parse_version("codex development") == (None, None)


def test_capabilities_are_derived_from_help_and_scope() -> None:
    capabilities = capabilities_from_help(
        "Commands: exec resume doctor\n--sandbox MODE\n--ask-for-approval POLICY\n--cd DIR",
        "Usage: codex exec [OPTIONS] [PROMPT]\n--json\nUse - to read stdin",
        "--device-auth",
    )
    assert capabilities["supports_exec"]
    assert capabilities["supports_json"]
    assert capabilities["supports_resume"]
    assert capabilities["supports_device_auth"]
    assert capabilities["supports_stdin"]
    assert capabilities["approval_flags_global"]
    assert capabilities["sandbox_global"]
    assert capabilities["cd_global"]


@pytest.mark.parametrize(
    ("status", "code", "expected"),
    (("Logged in with ChatGPT", 0, (True, "ChatGPT")),
     ("Authenticated with API key", 0, (True, "API key")),
     ("Not logged in", 1, (False, "none"))),
)
def test_auth_status_parsing(status: str, code: int, expected: tuple[bool, str]) -> None:
    assert parse_auth_status(status, code) == expected


def test_sensitive_diagnostics_are_redacted() -> None:
    safe = redact("Authorization: Bearer abcdefghijklmnop\napi key=sk-secret12345")
    assert "abcdefghijklmnop" not in safe
    assert "sk-secret12345" not in safe
    assert "[REDACTED]" in safe

