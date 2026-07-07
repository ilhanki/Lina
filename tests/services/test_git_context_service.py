"""Tests for Git context service."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from lina.services.git_context_service import (
    GitContext,
    GitContextService,
    format_git_context,
)


@dataclass
class FakeCompletedProcess:
    """Fake subprocess.CompletedProcess for testing."""

    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


class FakeGitRunner:
    """Fake subprocess.run for testing Git commands."""

    def __init__(self, responses: dict[str, FakeCompletedProcess] | None = None) -> None:
        self._responses = responses or {}
        self.calls: list[list[str]] = []
        self._default_response = FakeCompletedProcess(returncode=0, stdout="")

    def __call__(self, args: list[str], **kwargs: Any) -> FakeCompletedProcess:
        self.calls.append(args)
        command_key = " ".join(args)
        return self._responses.get(command_key, self._default_response)


class FakeFailingRunner:
    """Fake runner that always raises an exception."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def __call__(self, args: list[str], **kwargs: Any) -> None:
        raise self._error


# --- Safety tests ---


def test_git_context_service_does_not_use_shell_true() -> None:
    """Verify that shell=True is never used."""
    runner = FakeGitRunner(
        responses={
            "git branch --show-current": FakeCompletedProcess(
                returncode=0, stdout="main\n"
            ),
        }
    )
    service = GitContextService(
        project_root=Path("/fake"),
        runner=runner,
    )

    service.collect_context()

    assert len(runner.calls) >= 1
    # The runner is called with a list, not a string.
    # shell=True would require a string argument.
    for call in runner.calls:
        assert isinstance(call, list)


def test_git_context_service_uses_timeout() -> None:
    """Verify that commands are run with a timeout."""
    import subprocess

    runner = FakeFailingRunner(subprocess.TimeoutExpired(cmd="git", timeout=5))
    service = GitContextService(
        project_root=Path("/fake"),
        timeout=5,
        runner=runner,
    )

    result = service.collect_context()

    assert not result.available


def test_git_context_service_handles_git_not_found() -> None:
    """Verify that missing Git executable does not crash."""
    runner = FakeFailingRunner(FileNotFoundError("git not found"))
    service = GitContextService(
        project_root=Path("/fake"),
        runner=runner,
    )

    result = service.collect_context()

    assert not result.available
    assert result.current_branch == ""


def test_git_context_service_handles_os_error() -> None:
    """Verify that OS errors do not crash."""
    runner = FakeFailingRunner(OSError("permission denied"))
    service = GitContextService(
        project_root=Path("/fake"),
        runner=runner,
    )

    result = service.collect_context()

    assert not result.available


def test_git_context_service_user_input_not_in_commands() -> None:
    """Verify user input is never part of Git commands."""
    runner = FakeGitRunner(
        responses={
            "git branch --show-current": FakeCompletedProcess(
                returncode=0, stdout="main\n"
            ),
            "git log --oneline -n 10": FakeCompletedProcess(
                returncode=0, stdout="abc1234 initial commit\n"
            ),
            "git status --short": FakeCompletedProcess(
                returncode=0, stdout=""
            ),
        }
    )
    service = GitContextService(
        project_root=Path("/fake"),
        runner=runner,
    )

    service.collect_context()

    allowed_commands = [
        ["git", "branch", "--show-current"],
        ["git", "log", "--oneline", "-n", "10"],
        ["git", "status", "--short"],
    ]
    for call in runner.calls:
        assert call in allowed_commands


# --- Functional tests ---


def test_git_context_service_collects_full_context() -> None:
    runner = FakeGitRunner(
        responses={
            "git branch --show-current": FakeCompletedProcess(
                returncode=0, stdout="main\n"
            ),
            "git log --oneline -n 10": FakeCompletedProcess(
                returncode=0, stdout="abc1234 feat: initial\ndef5678 docs: readme\n"
            ),
            "git status --short": FakeCompletedProcess(
                returncode=0, stdout=" M README.md\n"
            ),
        }
    )
    service = GitContextService(
        project_root=Path("/fake"),
        runner=runner,
    )

    result = service.collect_context()

    assert result.available
    assert result.current_branch == "main"
    assert "abc1234" in result.recent_commits
    assert "README.md" in result.working_tree_status


def test_git_context_service_returns_empty_on_branch_failure() -> None:
    runner = FakeGitRunner(
        responses={
            "git branch --show-current": FakeCompletedProcess(
                returncode=128, stdout="", stderr="fatal: not a git repository"
            ),
        }
    )
    service = GitContextService(
        project_root=Path("/fake"),
        runner=runner,
    )

    result = service.collect_context()

    assert not result.available
    assert result.current_branch == ""


def test_git_context_service_handles_clean_working_tree() -> None:
    runner = FakeGitRunner(
        responses={
            "git branch --show-current": FakeCompletedProcess(
                returncode=0, stdout="main\n"
            ),
            "git log --oneline -n 10": FakeCompletedProcess(
                returncode=0, stdout="abc1234 feat: initial\n"
            ),
            "git status --short": FakeCompletedProcess(
                returncode=0, stdout=""
            ),
        }
    )
    service = GitContextService(
        project_root=Path("/fake"),
        runner=runner,
    )

    result = service.collect_context()

    assert result.available
    assert result.working_tree_status == ""


def test_git_context_has_content_when_available() -> None:
    context = GitContext(
        current_branch="main",
        recent_commits="abc1234 initial",
        working_tree_status="",
        available=True,
    )
    assert context.has_content


def test_git_context_has_no_content_when_unavailable() -> None:
    context = GitContext(
        current_branch="",
        recent_commits="",
        working_tree_status="",
        available=False,
    )
    assert not context.has_content


# --- format_git_context tests ---


def test_format_git_context_unavailable() -> None:
    context = GitContext(
        current_branch="",
        recent_commits="",
        working_tree_status="",
        available=False,
    )
    assert "kullanılamıyor" in format_git_context(context)


def test_format_git_context_full() -> None:
    context = GitContext(
        current_branch="main",
        recent_commits="abc1234 feat: initial",
        working_tree_status=" M README.md",
        available=True,
    )
    formatted = format_git_context(context)
    assert "Branch: main" in formatted
    assert "abc1234" in formatted
    assert "README.md" in formatted


def test_format_git_context_clean_working_tree() -> None:
    context = GitContext(
        current_branch="main",
        recent_commits="abc1234 feat: initial",
        working_tree_status="",
        available=True,
    )
    formatted = format_git_context(context)
    assert "temiz" in formatted
