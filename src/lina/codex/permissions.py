"""Workspace containment, permission lifetime, and secret filtering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from lina.codex.models import WorkspacePermissionLevel


SECRET_NAMES = {
    ".env", "auth.json", "credentials", "credentials.json", "secrets", "secrets.json",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".git-credentials", ".netrc",
    ".npmrc", ".pypirc", "pip.conf", "pip.ini", "login data", "cookies",
    "web credentials", "local state", "known_hosts.old", "credentials.db",
}
SECRET_SUFFIXES = {".key", ".pem", ".pfx", ".p12", ".crt"}
_SECRET_REQUEST = re.compile(
    r"(?:^|[\\/\s])(?:\.env(?:\.[\w.-]+)?|auth\.json|credentials[^\s]*|secrets[^\s]*|"
    r"id_(?:rsa|dsa|ecdsa|ed25519)|\.npmrc|\.pypirc|pip\.(?:conf|ini)|"
    r"[^\s]+\.(?:key|pem|pfx|p12|crt))(?:$|[\s,.;])",
    re.IGNORECASE,
)
_WHOLE_DRIVE_REQUEST = re.compile(
    r"(?:[a-z]:[\\/](?=\s|$)|tüm\s+bilgisayar|tum\s+bilgisayar|bütün\s+disk|butun\s+disk)"
    r".*\b(?:tara|incele|analiz)", re.IGNORECASE,
)


class WorkspaceAccessError(ValueError):
    pass


def is_secret_path(path: Path) -> bool:
    name = path.name.casefold()
    return (name in SECRET_NAMES or name.startswith(".env.")
            or name.startswith("credentials") or name.startswith("secrets")
            or path.suffix.casefold() in SECRET_SUFFIXES
            or any(part.casefold() in {
                "credentials", "secrets", ".ssh", ".aws", ".azure", ".gcloud",
                "gcloud", "browser", "user data", "windows credentials",
                "credential manager", "git credential manager", "password-store",
                "keychains", "cookies", "login data",
            } for part in path.parts))


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


def validate_codex_request_scope(text: str) -> None:
    normalized = " ".join(str(text or "").split())
    if _SECRET_REQUEST.search(f" {normalized} "):
        raise WorkspaceAccessError("Gizli veya kimlik bilgisi içerebilecek dosya isteği engellendi.")
    if _WHOLE_DRIVE_REQUEST.search(normalized):
        raise WorkspaceAccessError("Tüm disk taranamaz; yalnız seçtiğin proje klasörü kullanılabilir.")


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
        if resolved.parent == resolved:
            raise WorkspaceAccessError("Disk kökü çalışma alanı olarak seçilemez.")
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
