"""Official Codex CLI adapter implementing Lina's narrow client contract."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import threading
import time

from lina.codex.models import (CodexEvent, CodexExecutionMode, CodexRemoteSessionReference,
                                CodexResult, CodexRiskLevel, CodexTask, ProjectContext)
from lina.codex.permissions import ensure_within_workspace, is_secret_path
from lina.codex.transports.diagnostics import (MINIMUM_CODEX_CLI_VERSION, CodexCliInfo,
                                               CodexExecutableCandidate, capabilities_from_help,
                                               discover_candidates,
                                               parse_auth_status, parse_version, redact)
from lina.codex.transports.errors import (CodexApprovalRequired, CodexCancelled, CodexCliTooOld,
                                          CodexExecutionFailed, CodexLoginRequired,
                                          CodexNetworkUnavailable, CodexOutputInvalid,
                                          CodexProviderUnavailable, CodexRateLimited)
from lina.codex.transports.parser import CodexJsonlParser
from lina.codex.transports.process import CodexProcessRunner, ProcessResult
from lina.codex.transports.invocation import (WindowsCommandInvocation,
                                              build_process_invocation)
from lina.codex.transports.prompt import build_task_prompt
from lina.codex.transports.verification import build_evidence, capture_workspace, changed_paths
from lina.codex.snapshot import build_change_set
from lina.codex.resume import assess_resume, workspace_fingerprint


class CodexCommandBuilder:
    def __init__(self, info: CodexCliInfo) -> None:
        self.info = info

    def execution(self, workspace: Path, mode: CodexExecutionMode, *,
                  ephemeral: bool = True) -> tuple[str, ...]:
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
        if ephemeral and self.info.supports_ephemeral:
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

    def execution_invocation(self, workspace: Path, mode: CodexExecutionMode, *,
                             ephemeral: bool = True) -> WindowsCommandInvocation:
        command = self.execution(workspace, mode, ephemeral=ephemeral)
        return build_process_invocation(
            command[0], command[1:], kind=self.info.executable_kind
        )

    def resume_invocation(
        self,
        workspace: Path,
        session_id: str,
        mode: CodexExecutionMode,
    ) -> WindowsCommandInvocation:
        if not self.info.supports_resume or not self.info.supports_session_id:
            raise CodexOutputInvalid("Codex resume capability is unavailable")
        if not _valid_session_id(session_id):
            raise ValueError("Invalid Codex session identifier")
        if not self.info.resume_supports_json or not self.info.resume_supports_stdin:
            raise CodexOutputInvalid("Codex resume JSON/stdin capability is unavailable")
        if not (self.info.root_supports_cd and self.info.root_supports_sandbox):
            raise CodexOutputInvalid("Codex resume workspace sandbox cannot be enforced")
        sandbox = ("workspace-write" if mode is CodexExecutionMode.CONTROLLED_MODIFICATION
                   else "read-only")
        base = [str(self.info.executable_path), "--cd", str(workspace),
                "--sandbox", sandbox]
        if self.info.root_supports_approval:
            base.extend(("--ask-for-approval", "on-request"))
        elif mode is CodexExecutionMode.CONTROLLED_MODIFICATION:
            raise CodexApprovalRequired("Codex resume approval policy is unavailable")
        base.extend(("exec", "resume", "--json", session_id, "-"))
        return build_process_invocation(
            base[0], base[1:], kind=self.info.executable_kind
        )


class CodexCliClient:
    _failed_candidate_cache: dict[str, tuple[float, CodexExecutableCandidate]] = {}
    _candidate_cache_ttl_seconds = 30.0

    def __init__(self, info: CodexCliInfo, *, runner: CodexProcessRunner | None = None,
                 timeout_seconds: int = 300, resume_enabled: bool = True,
                 session_retention_days: int = 30) -> None:
        self.info = info
        self.runner = runner or CodexProcessRunner()
        self.timeout_seconds = max(15, min(int(timeout_seconds), 3600))
        self.resume_enabled = bool(resume_enabled)
        self.session_retention_days = max(1, min(int(session_retention_days), 90))
        self._session_id = ""
        self._on_event = None
        self._parser: CodexJsonlParser | None = None
        self._lock = threading.Lock()

    @classmethod
    def probe(cls, configured_path: str | Path | None = None, *, timeout_seconds: int = 300,
              runner: CodexProcessRunner | None = None) -> "CodexCliClient":
        process = runner or CodexProcessRunner()
        candidates = list(discover_candidates(configured_path))
        checked: list[CodexExecutableCandidate] = []
        saw_old_version = False
        now = time.monotonic()
        for candidate in candidates:
            cache_key = str(candidate.path).casefold()
            cached = cls._failed_candidate_cache.get(cache_key)
            if cached and cached[0] > now:
                checked.append(cached[1])
                continue
            if candidate.rejection_reason:
                checked.append(candidate)
                cls._failed_candidate_cache[cache_key] = (
                    now + cls._candidate_cache_ttl_seconds, candidate
                )
                continue
            try:
                version_result = process.run(
                    _candidate_invocation(candidate, "--version"), timeout=5
                )
                version, parsed = parse_version(
                    version_result.stdout + "\n" + version_result.stderr
                )
                if version_result.exit_code != 0 or parsed is None:
                    saw_old_version = True
                    rejected = replace(
                        candidate, launchable=False, rejection_reason="version_probe_failed"
                    )
                    checked.append(rejected)
                    cls._failed_candidate_cache[cache_key] = (
                        now + cls._candidate_cache_ttl_seconds, rejected
                    )
                    continue
                if parsed < MINIMUM_CODEX_CLI_VERSION:
                    saw_old_version = True
                    rejected = replace(
                        candidate, launchable=True, version=version,
                        rejection_reason="unsupported_version",
                    )
                    checked.append(rejected)
                    cls._failed_candidate_cache[cache_key] = (
                        now + cls._candidate_cache_ttl_seconds, rejected
                    )
                    continue
                root_help = process.run(_candidate_invocation(candidate, "--help"), timeout=5)
                exec_help = process.run(
                    _candidate_invocation(candidate, "exec", "--help"), timeout=5
                )
                login_help = process.run(
                    _candidate_invocation(candidate, "login", "--help"), timeout=5
                )
                resume_help_text = ""
                if "resume" in (root_help.stdout + exec_help.stdout).casefold():
                    resume_help = process.run(
                        _candidate_invocation(candidate, "exec", "resume", "--help"),
                        timeout=5,
                    )
                    resume_help_text = resume_help.stdout + "\n" + resume_help.stderr
                doctor_help_text = ""
                if "doctor" in root_help.stdout.casefold():
                    doctor_help = process.run(
                        _candidate_invocation(candidate, "doctor", "--help"), timeout=5
                    )
                    doctor_help_text = doctor_help.stdout
                capabilities = capabilities_from_help(
                    root_help.stdout, exec_help.stdout, login_help.stdout,
                    doctor_help_text, resume_help_text,
                )
                auth = process.run(
                    _candidate_invocation(candidate, "login", "status"), timeout=10
                )
            except (OSError, subprocess.SubprocessError, CodexCancelled):
                rejected = replace(
                    candidate, launchable=False, rejection_reason="launch_failed"
                )
                checked.append(rejected)
                cls._failed_candidate_cache[cache_key] = (
                    now + cls._candidate_cache_ttl_seconds, rejected
                )
                continue
            authenticated, method = parse_auth_status(
                auth.stdout + "\n" + auth.stderr, auth.exit_code
            )
            diagnostics = []
            if not capabilities["supports_exec"]:
                diagnostics.append("exec_not_supported")
            if not capabilities["supports_json"]:
                diagnostics.append("json_not_supported")
            if not capabilities["supports_stdin"]:
                diagnostics.append("stdin_not_documented")
            selected = replace(
                candidate, launchable=True, version=version,
                capabilities=tuple(name for name, enabled in capabilities.items() if enabled),
                rejection_reason=None,
            )
            checked.append(selected)
            checked.extend(
                replace(item, rejection_reason=item.rejection_reason or "not_checked_lower_priority")
                for item in candidates if item not in checked and item != candidate
            )
            info = CodexCliInfo(
                candidate.path, version, True, authenticated, method,
                selected_candidate_source=candidate.source,
                executable_kind=candidate.kind,
                candidates=tuple(checked), diagnostics=tuple(diagnostics), **capabilities,
            )
            return cls(info, runner=process, timeout_seconds=timeout_seconds)
        if saw_old_version:
            raise CodexCliTooOld("Codex CLI version could not be verified")
        from lina.codex.transports.errors import CodexCliNotFound
        raise CodexCliNotFound("No launchable Codex CLI candidate was found")

    def refresh(self) -> CodexCliInfo:
        type(self)._failed_candidate_cache.clear()
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
        command = CodexCommandBuilder(self.info).execution_invocation(
            context.root_path, mode,
            ephemeral=not (self.resume_enabled and self.info.supports_resume),
        )
        return self._execute_invocation(command, task, context, on_event, mode=mode)

    def resume(
        self,
        task: CodexTask,
        context: ProjectContext,
        reference: CodexRemoteSessionReference,
        on_event,
        *,
        approved: bool = False,
    ) -> CodexResult:
        eligibility = assess_resume(
            reference, context.root_path, cli_version=self.info.version,
            authenticated=self.info.authenticated,
            capability_supported=(self.info.supports_resume and self.info.supports_session_id),
            user_approved=approved, maximum_age_days=self.session_retention_days,
        )
        if not eligibility.allowed:
            if "authentication_required" in eligibility.reasons:
                raise CodexLoginRequired()
            if "user_approval_required" in eligibility.reasons:
                raise CodexApprovalRequired("Codex resume requires explicit user approval")
            raise CodexOutputInvalid(eligibility.primary_reason or "Codex resume is unavailable")
        mode = (CodexExecutionMode.CONTROLLED_MODIFICATION
                if task.risk_level is CodexRiskLevel.MODIFICATION else CodexExecutionMode.READ_ONLY)
        command = CodexCommandBuilder(self.info).resume_invocation(
            context.root_path, reference.cli_session_id, mode
        )
        return self._execute_invocation(
            command, task, context, on_event, mode=mode, reference=reference
        )

    def _execute_invocation(
        self,
        command: WindowsCommandInvocation,
        task: CodexTask,
        context: ProjectContext,
        on_event,
        *,
        mode: CodexExecutionMode,
        reference: CodexRemoteSessionReference | None = None,
    ) -> CodexResult:
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
                                         timeout=self.timeout_seconds, on_stdout=consume,
                                         on_stderr=parser.feed_stderr)
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
            change_set = build_change_set(before, after)
            evidence = build_evidence(before, after, result.exit_code,
                                      sensitive_output_detected=result.sensitive_output_detected)
            if parser.git_action_signals:
                evidence = replace(
                    evidence,
                    integrity_reasons=tuple(dict.fromkeys((
                        *evidence.integrity_reasons, *sorted(parser.git_action_signals),
                    ))),
                )
            changed = changed_paths(evidence, context.root_path)
            now = datetime.now(timezone.utc)
            remote_id = parser.remote_session_id or (
                reference.cli_session_id if reference is not None else None
            )
            remote = None
            if remote_id and self.resume_enabled and self.info.supports_resume:
                remote = CodexRemoteSessionReference(
                    provider="openai-codex-cli", cli_session_id=remote_id,
                    local_session_id=task.task_id, conversation_id=None,
                    workspace_fingerprint=workspace_fingerprint(context.root_path),
                    workspace_display_name=context.root_path.name[:120],
                    task_summary=task.title[:160], mode=mode,
                    created_at=reference.created_at if reference else now,
                    last_used_at=now, cli_version=self.info.version or "unknown",
                )
            notes = (f"cli_exit={result.exit_code}", *parser.diagnostics)
            return CodexResult(summary, changed_files=changed,
                               verification_notes=notes,
                               evidence=evidence, remote_session=remote,
                               change_set=change_set)
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
        args = ["login"]
        if device_auth:
            if not self.info.supports_device_auth:
                raise CodexExecutionFailed("Device authentication is unsupported")
            args.append("--device-auth")
        flags = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0
        invocation = build_process_invocation(
            self.info.executable_path, args, kind=self.info.executable_kind
        )
        launch_args = invocation.command_line or list(invocation.argv)
        subprocess.Popen(launch_args, shell=False, creationflags=flags,
                         env=dict(invocation.environment))

    def logout(self, *, confirmed: bool = False) -> CodexCliInfo:
        if not confirmed or not self.info.executable_path:
            raise PermissionError("Codex logout açık kullanıcı onayı gerektirir.")
        result = self.runner.run(build_process_invocation(
            self.info.executable_path, ("logout",), kind=self.info.executable_kind
        ), timeout=30)
        if result.exit_code != 0:
            raise CodexExecutionFailed()
        self.info = replace(self.info, authenticated=False, auth_method_summary="none")
        return self.info

    def diagnostics_report(self) -> str:
        """Return only the CLI's documented redacted JSON support report."""
        if not self.info.executable_path or not self.info.supports_doctor_json:
            return "Codex CLI diagnostic JSON desteği bulunmuyor."
        result = self.runner.run(build_process_invocation(
            self.info.executable_path, ("doctor", "--json"), kind=self.info.executable_kind
        ), timeout=30)
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


def _candidate_invocation(
    candidate: CodexExecutableCandidate, *arguments: str
) -> WindowsCommandInvocation:
    return build_process_invocation(candidate.path, arguments, kind=candidate.kind)


def _valid_session_id(value: str) -> bool:
    import re
    return re.fullmatch(
        r"(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
        r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|[A-Za-z0-9][A-Za-z0-9._-]{2,63})",
        value,
    ) is not None
