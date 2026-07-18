"""Official Codex CLI adapter implementing Lina's narrow client contract."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
import threading

from lina.codex.models import (CodexEvent, CodexExecutionMode, CodexResult, CodexRiskLevel,
                                CodexTask, ProjectContext)
from lina.codex.permissions import ensure_within_workspace, is_secret_path
from lina.codex.transports.diagnostics import (MINIMUM_CODEX_CLI_VERSION, CodexCliInfo,
                                               capabilities_from_help, discover_executable,
                                               parse_auth_status, parse_version, redact)
from lina.codex.transports.errors import (CodexApprovalRequired, CodexCancelled, CodexCliTooOld,
                                          CodexExecutionFailed, CodexLoginRequired,
                                          CodexNetworkUnavailable, CodexOutputInvalid,
                                          CodexProviderUnavailable, CodexRateLimited)
from lina.codex.transports.parser import CodexJsonlParser
from lina.codex.transports.process import CodexProcessRunner, ProcessResult
from lina.codex.transports.prompt import build_task_prompt
from lina.codex.transports.verification import build_evidence, capture_workspace, changed_paths


class CodexCommandBuilder:
    def __init__(self, info: CodexCliInfo) -> None:
        self.info = info

    def execution(self, workspace: Path, mode: CodexExecutionMode) -> tuple[str, ...]:
        if not self.info.executable_path or not self.info.supports_exec or not self.info.supports_json:
            raise CodexOutputInvalid("Codex exec JSON capability is unavailable")
        if not self.info.supports_stdin:
            raise CodexOutputInvalid("Codex CLI documented stdin input is unavailable")
        if not self.info.supports_sandbox:
            raise CodexOutputInvalid("Codex CLI sandbox capability is unavailable")
        if mode is CodexExecutionMode.CONTROLLED_MODIFICATION and not self.info.supports_approval_flags:
            raise CodexApprovalRequired("Codex runtime approval policy is unavailable")
        args = [str(self.info.executable_path)]
        sandbox = "workspace-write" if mode is CodexExecutionMode.CONTROLLED_MODIFICATION else "read-only"
        if self.info.cd_global:
            args.extend(("--cd", str(workspace)))
        if self.info.sandbox_global:
            args.extend(("--sandbox", sandbox))
        if self.info.approval_flags_global:
            args.extend(("--ask-for-approval", "on-request"))
        args.append("exec")
        if self.info.supports_cd and not self.info.cd_global:
            args.extend(("--cd", str(workspace)))
        args.append("--json")
        if self.info.supports_ephemeral:
            args.append("--ephemeral")
        if self.info.supports_sandbox and not self.info.sandbox_global:
            args.extend(("--sandbox", sandbox))
        if self.info.supports_approval_flags and not self.info.approval_flags_global:
            args.extend(("--ask-for-approval", "on-request"))
        args.append("-")
        forbidden = {"--dangerously-bypass-approvals-and-sandbox", "--yolo", "--add-dir", "never"}
        if any(value.casefold() in forbidden for value in args):
            raise ValueError("Dangerous Codex CLI flag blocked")
        return tuple(args)


class CodexCliClient:
    def __init__(self, info: CodexCliInfo, *, runner: CodexProcessRunner | None = None,
                 timeout_seconds: int = 300) -> None:
        self.info = info
        self.runner = runner or CodexProcessRunner()
        self.timeout_seconds = max(15, min(int(timeout_seconds), 3600))
        self._session_id = ""
        self._on_event = None
        self._parser: CodexJsonlParser | None = None
        self._lock = threading.Lock()

    @classmethod
    def probe(cls, configured_path: str | Path | None = None, *, timeout_seconds: int = 300,
              runner: CodexProcessRunner | None = None) -> "CodexCliClient":
        process = runner or CodexProcessRunner()
        executable = discover_executable(configured_path)
        version_result = process.run((executable, "--version"), timeout=5)
        version, parsed = parse_version(version_result.stdout + "\n" + version_result.stderr)
        if version_result.exit_code != 0 or parsed is None:
            raise CodexCliTooOld("Codex CLI version could not be verified")
        if parsed < MINIMUM_CODEX_CLI_VERSION:
            raise CodexCliTooOld(version)
        root_help = process.run((executable, "--help"), timeout=5)
        exec_help = process.run((executable, "exec", "--help"), timeout=5)
        login_help = process.run((executable, "login", "--help"), timeout=5)
        doctor_help_text = ""
        if "doctor" in root_help.stdout.casefold():
            doctor_help = process.run((executable, "doctor", "--help"), timeout=5)
            doctor_help_text = doctor_help.stdout
        capabilities = capabilities_from_help(
            root_help.stdout, exec_help.stdout, login_help.stdout, doctor_help_text
        )
        auth = process.run((executable, "login", "status"), timeout=10)
        authenticated, method = parse_auth_status(auth.stdout + "\n" + auth.stderr, auth.exit_code)
        diagnostics = []
        if not capabilities["supports_exec"]:
            diagnostics.append("exec_not_supported")
        if not capabilities["supports_json"]:
            diagnostics.append("json_not_supported")
        if not capabilities["supports_stdin"]:
            diagnostics.append("stdin_not_documented")
        info = CodexCliInfo(executable, version, True, authenticated, method,
                            diagnostics=tuple(diagnostics), **capabilities)
        return cls(info, runner=process, timeout_seconds=timeout_seconds)

    def refresh(self) -> CodexCliInfo:
        refreshed = type(self).probe(self.info.executable_path, timeout_seconds=self.timeout_seconds)
        self.info = refreshed.info
        return self.info

    def execute(self, task: CodexTask, context: ProjectContext, on_event) -> CodexResult:
        if not self.info.authenticated:
            raise CodexLoginRequired()
        ensure_within_workspace(context.root_path, task.workspace)
        for path in context.allowed_files:
            ensure_within_workspace(context.root_path, path)
        mode = (CodexExecutionMode.CONTROLLED_MODIFICATION
                if task.risk_level is CodexRiskLevel.MODIFICATION else CodexExecutionMode.READ_ONLY)
        command = CodexCommandBuilder(self.info).execution(context.root_path, mode)
        prompt = build_task_prompt(task, context, mode)
        parser = CodexJsonlParser(task.task_id)
        before = capture_workspace(context)
        with self._lock:
            self._session_id = task.task_id
            self._parser = parser
            self._on_event = on_event

        def consume(line: str) -> None:
            for event in parser.feed(line):
                on_event(event)
            if parser.runtime_approval_requested:
                self.runner.cancel()

        try:
            try:
                result = self.runner.run(command, cwd=context.root_path, stdin_text=prompt,
                                         timeout=self.timeout_seconds, on_stdout=consume)
            except CodexCancelled:
                if parser.runtime_approval_requested:
                    raise CodexApprovalRequired() from None
                raise
            for event in parser.finish():
                on_event(event)
            if parser.runtime_approval_requested:
                raise CodexApprovalRequired()
            if result.exit_code != 0:
                raise self._map_failure(result)
            if parser.invalid_lines and not parser.events:
                raise CodexOutputInvalid()
            summary = redact(parser.summary).strip()
            if not summary:
                raise CodexOutputInvalid("Codex CLI returned no final message")
            after = capture_workspace(context)
            evidence = build_evidence(before, after, result.exit_code,
                                      sensitive_output_detected=result.sensitive_output_detected)
            changed = changed_paths(evidence, context.root_path)
            return CodexResult(summary, changed_files=changed,
                               verification_notes=(f"cli_exit={result.exit_code}",), evidence=evidence)
        finally:
            with self._lock:
                self._parser = None
                self._on_event = None

    def cancel(self) -> None:
        self.runner.cancel()

    def shutdown(self) -> None:
        self.runner.shutdown()

    def launch_login(self, *, device_auth: bool = False) -> None:
        if not self.info.executable_path:
            raise CodexExecutionFailed()
        args = [str(self.info.executable_path), "login"]
        if device_auth:
            if not self.info.supports_device_auth:
                raise CodexExecutionFailed("Device authentication is unsupported")
            args.append("--device-auth")
        flags = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0
        subprocess.Popen(args, shell=False, creationflags=flags)

    def logout(self, *, confirmed: bool = False) -> CodexCliInfo:
        if not confirmed or not self.info.executable_path:
            raise PermissionError("Codex logout açık kullanıcı onayı gerektirir.")
        result = self.runner.run((self.info.executable_path, "logout"), timeout=30)
        if result.exit_code != 0:
            raise CodexExecutionFailed()
        self.info = replace(self.info, authenticated=False, auth_method_summary="none")
        return self.info

    def diagnostics_report(self) -> str:
        """Return only the CLI's documented redacted JSON support report."""
        if not self.info.executable_path or not self.info.supports_doctor_json:
            return "Codex CLI diagnostic JSON desteği bulunmuyor."
        result = self.runner.run((self.info.executable_path, "doctor", "--json"), timeout=30)
        if result.exit_code != 0:
            raise CodexExecutionFailed()
        return redact(result.stdout)[:20_000]

    @staticmethod
    def _safe_changed_files(root: Path) -> tuple[str, ...]:
        try:
            result = subprocess.run(("git", "status", "--porcelain"), cwd=root, shell=False,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    timeout=10, check=False)
        except (OSError, subprocess.SubprocessError):
            return ()
        files: list[str] = []
        for line in result.stdout.splitlines():
            relative = line[3:].strip().split(" -> ")[-1]
            candidate = ensure_within_workspace(root, root / relative)
            if not is_secret_path(candidate):
                files.append(str(candidate))
        return tuple(files)

    @staticmethod
    def _map_failure(result: ProcessResult) -> Exception:
        safe = (result.stderr + "\n" + result.stdout).casefold()
        if "rate limit" in safe or "too many requests" in safe:
            return CodexRateLimited()
        if any(item in safe for item in ("network", "connection", "dns")):
            return CodexNetworkUnavailable()
        if any(item in safe for item in ("provider unavailable", "service unavailable")):
            return CodexProviderUnavailable()
        if any(item in safe for item in ("login", "not authenticated", "unauthorized")):
            return CodexLoginRequired()
        return CodexExecutionFailed()
