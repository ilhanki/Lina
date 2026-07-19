from pathlib import Path

import pytest

from lina.codex.models import (
    CodexExecutionMode,
    CodexRiskLevel,
    CodexTask,
    ExpectedOutput,
    ProjectContext,
    RequestedAction,
)
from lina.codex.transports.cli import CodexCliClient, CodexCommandBuilder
from lina.codex.transports.diagnostics import CodexCliInfo, CodexExecutableCandidate
from lina.codex.transports.errors import (
    CodexApprovalRequired,
    CodexCliTooOld,
    CodexLoginRequired,
    CodexOutputInvalid,
)
from lina.codex.transports.process import ProcessResult
from lina.codex.transports.prompt import build_task_prompt


def info(path: Path, **changes) -> CodexCliInfo:
    values = dict(
        executable_path=path, version="1.2.3", available=True, authenticated=True,
        auth_method_summary="ChatGPT", supports_exec=True, supports_json=True,
        supports_approval_flags=True, supports_stdin=True, supports_cd=True,
        supports_sandbox=True, root_supports_cd=True, root_supports_sandbox=True,
        root_supports_approval=True, resume_supports_json=True,
        resume_supports_stdin=True,
    )
    values.update(changes)
    return CodexCliInfo(**values)


def task(tmp_path: Path, risk: CodexRiskLevel = CodexRiskLevel.READ_ONLY) -> CodexTask:
    return CodexTask.create(
        "Analiz", "Projeyi analiz et", "Projeyi analiz et", tmp_path,
        (RequestedAction("inspect"),), risk_level=risk,
        expected_output=ExpectedOutput("Kısa özet"),
    )


class FakeRunner:
    def __init__(self, result: ProcessResult) -> None:
        self.result = result
        self.calls = []
        self.cancelled = False

    def run(self, args, **kwargs):
        self.calls.append((tuple(str(item) for item in args), kwargs))
        callback = kwargs.get("on_stdout")
        if callback:
            for line in self.result.stdout.splitlines(keepends=True):
                callback(line)
        return self.result

    def cancel(self):
        self.cancelled = True

    def shutdown(self):
        self.cancelled = True


class ProbeRunner:
    def __init__(self, version: str = "codex-cli 1.2.3", auth: str = "Logged in with ChatGPT") -> None:
        self.version = version
        self.auth = auth
        self.calls = []

    def run(self, args, **kwargs):
        command = tuple(str(item) for item in args)
        self.calls.append((command, kwargs))
        outputs = {
            ("--version",): self.version,
            ("--help",): "Commands: exec resume doctor\n--ask-for-approval\n--sandbox\n--cd",
            ("exec", "--help"): "--json --sandbox --cd --ephemeral\nPROMPT or - read stdin",
            ("login", "--help"): "--device-auth",
            ("doctor", "--help"): "--json",
            ("login", "status"): self.auth,
        }
        return ProcessResult(command, 0, outputs.get(command[1:], ""), "", 0.01)

    def cancel(self):
        return

    def shutdown(self):
        return


def test_command_builder_uses_list_safe_modes_and_stdin(tmp_path: Path) -> None:
    command = CodexCommandBuilder(info(tmp_path / "codex.exe")).execution(
        tmp_path, CodexExecutionMode.READ_ONLY
    )
    assert command[0].endswith("codex.exe")
    assert command[-1] == "-"
    assert "--json" in command
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert command[command.index("--ask-for-approval") + 1] == "on-request"
    assert not any(flag in command for flag in (
        "--dangerously-bypass-approvals-and-sandbox", "--yolo", "--add-dir", "never"
    ))


def test_global_flags_are_placed_before_exec(tmp_path: Path) -> None:
    command = CodexCommandBuilder(info(
        tmp_path / "codex.exe", approval_flags_global=True,
        sandbox_global=True, cd_global=True,
    )).execution(tmp_path, CodexExecutionMode.CONTROLLED_MODIFICATION)
    exec_index = command.index("exec")
    assert command.index("--cd") < exec_index
    assert command.index("--sandbox") < exec_index
    assert command.index("--ask-for-approval") < exec_index


def test_builder_refuses_unverified_sandbox_or_modification_approval(tmp_path: Path) -> None:
    with pytest.raises(CodexOutputInvalid):
        CodexCommandBuilder(info(tmp_path / "codex.exe", supports_sandbox=False)).execution(
            tmp_path, CodexExecutionMode.READ_ONLY
        )
    with pytest.raises(CodexApprovalRequired):
        CodexCommandBuilder(info(tmp_path / "codex.exe", supports_approval_flags=False)).execution(
            tmp_path, CodexExecutionMode.CONTROLLED_MODIFICATION
        )


def test_client_uses_stdin_and_parses_typed_result(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("print('ok')", encoding="utf-8")
    output = '{"type":"item.completed","item":{"type":"agent_message","text":"Analiz tamamlandı"}}\n'
    runner = FakeRunner(ProcessResult(("codex",), 0, output, "", 0.1))
    client = CodexCliClient(info(tmp_path / "codex.exe"), runner=runner)
    context = ProjectContext(tmp_path, (source,))
    result = client.execute(task(tmp_path), context, lambda _event: None)
    assert result.summary == "Analiz tamamlandı"
    assert runner.calls[0][1]["stdin_text"]
    assert "Projeyi analiz et" not in runner.calls[0][0]
    assert result.evidence and result.evidence.exit_code == 0


def test_client_blocks_execution_when_signed_out(tmp_path: Path) -> None:
    client = CodexCliClient(info(tmp_path / "codex.exe", authenticated=False), runner=FakeRunner(
        ProcessResult(("codex",), 0, "", "", 0.1)
    ))
    with pytest.raises(CodexLoginRequired):
        client.execute(task(tmp_path), ProjectContext(tmp_path), lambda _event: None)


def test_prompt_is_minimal_and_contains_security_boundaries(tmp_path: Path) -> None:
    prompt = build_task_prompt(task(tmp_path), ProjectContext(tmp_path), CodexExecutionMode.READ_ONLY)
    assert "salt-okunur" in prompt
    assert "Workspace dışına çıkma" in prompt
    assert "Secret" in prompt
    assert "Git push" in prompt
    assert "conversation history" not in prompt
    assert "system prompt" not in prompt


def test_probe_detects_version_auth_and_documented_capabilities(monkeypatch, tmp_path: Path) -> None:
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"fixture")
    monkeypatch.setattr("lina.codex.transports.cli.discover_candidates", lambda _path=None: (
        CodexExecutableCandidate(executable, "test", "native_exe", True, True),
    ))
    client = CodexCliClient.probe(runner=ProbeRunner())
    assert client.info.version == "1.2.3"
    assert client.info.authenticated
    assert client.info.auth_method_summary == "ChatGPT"
    assert client.info.supports_doctor_json
    assert client.info.supports_ephemeral


@pytest.mark.parametrize("version", ("codex development", "codex-cli 0.0.1"))
def test_probe_rejects_malformed_or_old_version(monkeypatch, tmp_path: Path, version: str) -> None:
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"fixture")
    monkeypatch.setattr("lina.codex.transports.cli.discover_candidates", lambda _path=None: (
        CodexExecutableCandidate(executable, "test", "native_exe", True, True),
    ))
    with pytest.raises(CodexCliTooOld):
        CodexCliClient.probe(runner=ProbeRunner(version=version))


def test_runtime_approval_event_stops_noninteractive_task(tmp_path: Path) -> None:
    output = '{"type":"command.approval_requested","message":"run command"}\n'
    client = CodexCliClient(
        info(tmp_path / "codex.exe"),
        runner=FakeRunner(ProcessResult(("codex",), 0, output, "", 0.1)),
    )
    with pytest.raises(CodexApprovalRequired):
        client.execute(task(tmp_path), ProjectContext(tmp_path), lambda _event: None)


def test_login_launch_never_passes_api_key(monkeypatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr("lina.codex.transports.cli.subprocess.Popen",
                        lambda args, **kwargs: calls.append((args, kwargs)))
    client = CodexCliClient(info(tmp_path / "codex.exe", supports_device_auth=True))
    client.launch_login(device_auth=True)
    assert calls[0][0][-2:] == ["login", "--device-auth"]
    assert calls[0][1]["shell"] is False
    assert not any("key" in item.casefold() for item in calls[0][0])


def test_logout_requires_confirmation_and_refreshes_local_state(tmp_path: Path) -> None:
    runner = FakeRunner(ProcessResult(("codex", "logout"), 0, "", "", 0.1))
    client = CodexCliClient(info(tmp_path / "codex.exe"), runner=runner)
    with pytest.raises(PermissionError):
        client.logout()
    assert not client.logout(confirmed=True).authenticated


def test_shutdown_cancels_active_runner(tmp_path: Path) -> None:
    runner = FakeRunner(ProcessResult(("codex",), 0, "", "", 0.1))
    client = CodexCliClient(info(tmp_path / "codex.exe"), runner=runner)
    client.shutdown()
    assert runner.cancelled


def test_execute_captures_resumable_remote_session_metadata(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("pass", encoding="utf-8")
    output = (
        '{"type":"thread.started","thread_id":"123e4567-e89b-42d3-a456-426614174000"}\n'
        '{"type":"item.completed","item":{"type":"agent_message","text":"Done"}}\n'
    )
    client = CodexCliClient(info(
        tmp_path / "codex.exe", supports_resume=True, supports_session_id=True
    ), runner=FakeRunner(ProcessResult(("codex",), 0, output, "", 0.1)))
    result = client.execute(task(tmp_path), ProjectContext(tmp_path, (source,)), lambda _event: None)
    assert result.remote_session is not None
    assert result.remote_session.cli_session_id.startswith("123e4567")
    assert result.remote_session.task_summary == "Analiz"


def test_resume_builder_places_validated_session_id_before_stdin(tmp_path: Path) -> None:
    cli_info = info(tmp_path / "codex.exe", supports_resume=True, supports_session_id=True)
    invocation = CodexCommandBuilder(cli_info).resume_invocation(
        tmp_path, "123e4567-e89b-42d3-a456-426614174000", CodexExecutionMode.READ_ONLY
    )
    assert invocation.display_args[-2:] == ("123e4567-e89b-42d3-a456-426614174000", "-")
    resume_index = invocation.display_args.index("resume")
    assert invocation.display_args.index("--cd") < resume_index
    assert invocation.display_args.index("--sandbox") < resume_index


@pytest.mark.parametrize("unsafe", ("../bad", "bad&id", "two words"))
def test_resume_builder_rejects_unsafe_session_id(tmp_path: Path, unsafe: str) -> None:
    cli_info = info(tmp_path / "codex.exe", supports_resume=True, supports_session_id=True)
    with pytest.raises(ValueError):
        CodexCommandBuilder(cli_info).resume_invocation(
            tmp_path, unsafe, CodexExecutionMode.READ_ONLY
        )
