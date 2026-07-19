from pathlib import Path

import pytest

from lina.codex.transports.diagnostics import (
    candidate_kind,
    capabilities_from_help,
    discover_candidates,
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


def test_discovery_orders_cmd_before_exe_and_extensionless(tmp_path: Path) -> None:
    paths = {name: str(tmp_path / name) for name in ("codex.cmd", "codex.exe", "codex")}
    for path in paths.values():
        Path(path).write_bytes(b"fixture")
    candidates = discover_candidates(environment={}, which=paths.get)
    assert [item.path.name for item in candidates] == ["codex.cmd", "codex.exe", "codex"]


def test_discovery_includes_bounded_appdata_npm_candidates(tmp_path: Path) -> None:
    npm = tmp_path / "npm"
    npm.mkdir()
    (npm / "codex.cmd").write_bytes(b"fixture")
    candidates = discover_candidates(environment={"APPDATA": str(tmp_path)}, which=lambda _name: None)
    assert candidates[0].source == "npm_global"
    assert candidates[0].kind == "cmd_wrapper"


def test_discovery_deduplicates_same_path_from_path_and_npm(tmp_path: Path) -> None:
    npm = tmp_path / "npm"
    npm.mkdir()
    command = npm / "codex.cmd"
    command.write_bytes(b"fixture")
    candidates = discover_candidates(
        environment={"APPDATA": str(tmp_path)},
        which=lambda name: str(command) if name == "codex.cmd" else None,
    )
    assert [item.path for item in candidates].count(command.resolve()) == 1


@pytest.mark.parametrize(
    ("value", "expected"),
    (("C:/Tools/codex.cmd", "cmd_wrapper"),
     ("C:/Tools/codex.exe", "native_exe"),
     ("C:/Tools/codex", "npm_shim"),
     ("C:/Program Files/WindowsApps/vendor/codex.exe", "packaged_app")),
)
def test_candidate_kind_classification(value: str, expected: str) -> None:
    assert candidate_kind(Path(value)) == expected


def test_capability_v2_uses_help_not_guesses() -> None:
    result = capabilities_from_help(
        "Commands: exec resume doctor\n--sandbox [read-only, workspace-write]\n--cd\n--model",
        "--json Print events as JSONL\nstdin -\n--output-schema\n--ask-for-approval",
        "--device-auth",
        "--json",
        "SESSION_ID Session id\n--json\n--output-schema",
    )
    assert result["supports_jsonl"]
    assert result["supports_session_id"]
    assert result["supports_read_only"]
    assert result["supports_workspace_write"]
    assert result["supports_runtime_approval"]
    assert result["supports_model"]
    assert result["supports_output_schema"]


@pytest.mark.parametrize(
    "text",
    ("ghp_abcdefghijklmnopqrstuvwxyz", "password=hunterhunter", "cookie=abcdefghijkl"),
)
def test_extended_sensitive_diagnostics_are_redacted(text: str) -> None:
    assert text not in redact(text)


@pytest.mark.parametrize(
    "text",
    ("API_KEY=example", "token_count=120", "password policy documentation"),
)
def test_redaction_preserves_safe_technical_examples(text: str) -> None:
    assert redact(text) == text
