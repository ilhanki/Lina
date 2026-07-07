"""Read-only Git context service for Lina."""

from dataclasses import dataclass
import subprocess
from pathlib import Path


@dataclass(frozen=True)
class GitContext:
    """Read-only Git information collected from the repository."""

    current_branch: str
    recent_commits: str
    working_tree_status: str
    available: bool

    @property
    def has_content(self) -> bool:
        return self.available and bool(
            self.current_branch or self.recent_commits or self.working_tree_status
        )


_EMPTY_CONTEXT = GitContext(
    current_branch="",
    recent_commits="",
    working_tree_status="",
    available=False,
)

_GIT_TIMEOUT = 5


class GitContextService:
    """Collects read-only Git information from the project repository.

    Safety constraints:
    - Only read-only Git commands are used.
    - shell=True is never used.
    - User input is never included in commands.
    - All commands use fixed argument lists.
    - cwd is always the project root.
    - Timeout is enforced on all commands.
    - Git failures do not crash the application.
    """

    def __init__(
        self,
        project_root: Path,
        timeout: int = _GIT_TIMEOUT,
        runner: object | None = None,
    ) -> None:
        self._project_root = project_root.resolve(strict=False)
        self._timeout = timeout
        self._runner = runner or subprocess.run

    def collect_context(self) -> GitContext:
        """Collect read-only Git context from the repository."""
        current_branch = self._run_git_command(
            ["git", "branch", "--show-current"]
        )
        if current_branch is None:
            return _EMPTY_CONTEXT

        recent_commits = self._run_git_command(
            ["git", "log", "--oneline", "-n", "10"]
        ) or ""

        working_tree_status = self._run_git_command(
            ["git", "status", "--short"]
        ) or ""

        return GitContext(
            current_branch=current_branch,
            recent_commits=recent_commits,
            working_tree_status=working_tree_status,
            available=True,
        )

    def _run_git_command(self, args: list[str]) -> str | None:
        """Run a read-only Git command and return its output.

        Returns None if the command fails for any reason.
        """
        try:
            result = self._runner(
                args,
                capture_output=True,
                text=True,
                cwd=str(self._project_root),
                timeout=self._timeout,
            )
        except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
            return None

        if result.returncode != 0:
            return None

        return result.stdout.strip()


def format_git_context(context: GitContext) -> str:
    """Format Git context for inclusion in a prompt."""
    if not context.available:
        return "Git bilgisi şu anda kullanılamıyor."

    sections: list[str] = []

    if context.current_branch:
        sections.append(f"Branch: {context.current_branch}")

    if context.working_tree_status:
        sections.append(
            f"Working tree durumu:\n{context.working_tree_status}"
        )
    else:
        sections.append("Working tree: temiz")

    if context.recent_commits:
        sections.append(f"Son commitler:\n{context.recent_commits}")

    return "\n\n".join(sections)
