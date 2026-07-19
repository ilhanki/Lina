from pathlib import Path

import pytest

from lina.codex.transports.invocation import (
    build_process_invocation,
    minimal_subprocess_environment,
)


def test_native_invocation_is_shell_free_argv(tmp_path: Path) -> None:
    executable = tmp_path / "codex.exe"
    invocation = build_process_invocation(executable, ("exec", "--json", "-"), kind="native_exe")
    assert invocation.argv == (str(executable), "exec", "--json", "-")
    assert not invocation.uses_cmd_wrapper


def test_cmd_invocation_uses_hardened_wrapper_on_windows(tmp_path: Path) -> None:
    invocation = build_process_invocation(tmp_path / "codex.cmd", ("--version",), kind="cmd_wrapper")
    assert invocation.argv[1:4] == ("/d", "/s", "/c")
    assert invocation.uses_cmd_wrapper


@pytest.mark.parametrize(
    "folder",
    ("space path", "amp&path", "pipe|path", "caret^path", "percent%path",
     "paren(path)", "bang!path", "Türkçe klasör"),
)
def test_cmd_invocation_quotes_workspace_metacharacters(tmp_path: Path, folder: str) -> None:
    workspace = tmp_path / folder
    invocation = build_process_invocation(
        tmp_path / "codex.cmd", ("exec", "--cd", workspace, "--json", "-"),
        kind="cmd_wrapper",
    )
    command = invocation.argv[-1]
    assert f'"{workspace}"' in command.replace("%%", "%")
    assert command.startswith('""') and command.endswith('""')


def test_prompt_never_enters_invocation_arguments(tmp_path: Path) -> None:
    prompt = "secret-looking user prompt & do not expose"
    invocation = build_process_invocation(
        tmp_path / "codex.cmd", ("exec", "--json", "-"), kind="cmd_wrapper"
    )
    assert all(prompt not in item for item in invocation.argv)
    assert prompt not in invocation.display_args


def test_minimal_environment_drops_credentials() -> None:
    safe = minimal_subprocess_environment({
        "PATH": "C:/Tools", "USERPROFILE": "C:/User", "OPENAI_API_KEY": "secret",
        "CODEX_ACCESS_TOKEN": "secret", "RANDOM_SETTING": "value",
    })
    assert safe == {"PATH": "C:/Tools", "USERPROFILE": "C:/User"}


@pytest.mark.parametrize("unsafe", ('bad"quote', "bad\nline", "bad\x00value"))
def test_invocation_rejects_control_or_quote_in_cmd_argument(tmp_path: Path, unsafe: str) -> None:
    with pytest.raises(ValueError):
        build_process_invocation(tmp_path / "codex.cmd", (unsafe,), kind="cmd_wrapper")
