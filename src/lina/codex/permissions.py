"""Workspace containment, permission lifetime, and secret filtering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lina.codex.models import WorkspacePermissionLevel


SECRET_NAMES = {".env", "credentials", "credentials.json", "secrets", "secrets.json"}
SECRET_SUFFIXES = {".key", ".pem", ".pfx"}


class WorkspaceAccessError(ValueError):
    pass


def is_secret_path(path: Path) -> bool:
    name = path.name.casefold()
    return (name in SECRET_NAMES or name.startswith(".env.")
            or path.suffix.casefold() in SECRET_SUFFIXES
            or any(part.casefold() in {"credentials", "secrets"} for part in path.parts))


def ensure_within_workspace(root: Path, candidate: Path) -> Path:
    resolved_root = root.expanduser().resolve()
    resolved = candidate.expanduser().resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise WorkspaceAccessError("Dosya izin verilen çalışma alanının dışında.") from error
    if is_secret_path(resolved):
        raise WorkspaceAccessError("Gizli veya kimlik bilgisi içerebilecek dosya engellendi.")
    return resolved


@dataclass(frozen=True, slots=True)
class WorkspaceGrant:
    root: Path
    level: WorkspacePermissionLevel
    session_id: str | None = None


class WorkspacePermissionStore:
    """In-memory grants; only remembered roots may be serialized by settings."""

    def __init__(self) -> None:
        self._grants: list[WorkspaceGrant] = []

    def grant(self, root: Path, level: WorkspacePermissionLevel = WorkspacePermissionLevel.ONE_TIME,
              session_id: str | None = None) -> WorkspaceGrant:
        resolved = root.expanduser().resolve()
        if not resolved.is_dir():
            raise WorkspaceAccessError("Geçerli bir çalışma klasörü seçilmeli.")
        grant = WorkspaceGrant(resolved, WorkspacePermissionLevel(level), session_id)
        self._grants.append(grant)
        return grant

    def allows(self, root: Path, session_id: str | None = None) -> bool:
        resolved = root.expanduser().resolve()
        return any(grant.root == resolved and (
            grant.level is WorkspacePermissionLevel.REMEMBERED
            or grant.session_id is None or grant.session_id == session_id
        ) for grant in self._grants)

    def consume_one_time(self, root: Path, session_id: str | None = None) -> None:
        resolved = root.expanduser().resolve()
        for grant in tuple(self._grants):
            if grant.root == resolved and grant.level is WorkspacePermissionLevel.ONE_TIME and (
                    grant.session_id is None or grant.session_id == session_id):
                self._grants.remove(grant)
                return

    def close_session(self, session_id: str) -> None:
        self._grants = [grant for grant in self._grants if not (
            grant.level is WorkspacePermissionLevel.SESSION and grant.session_id == session_id)]

    @property
    def remembered_roots(self) -> tuple[Path, ...]:
        return tuple(grant.root for grant in self._grants
                     if grant.level is WorkspacePermissionLevel.REMEMBERED)

