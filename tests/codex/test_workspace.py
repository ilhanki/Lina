from pathlib import Path

import pytest

from lina.codex.bridge import CodexBridge
from lina.codex.client import UnavailableCodexClient
from lina.codex.models import WorkspacePermissionLevel
from lina.codex.permissions import (WorkspaceAccessError, WorkspacePermissionStore,
                                    ensure_within_workspace, is_secret_path,
                                    validate_codex_request_scope)


@pytest.mark.parametrize("name", [".env", ".env.local", "server.key", "cert.pem", "id.pfx",
                                         "credentials", "secrets.json"])
def test_secret_names_are_blocked(name: str):
    assert is_secret_path(Path(name))


def test_forbidden_path_outside_workspace(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(WorkspaceAccessError):
        ensure_within_workspace(root, tmp_path / "outside.py")


def test_permissions_default_to_one_time(tmp_path: Path):
    store = WorkspacePermissionStore()
    grant = store.grant(tmp_path)
    assert grant.level is WorkspacePermissionLevel.ONE_TIME
    assert store.allows(tmp_path)
    store.consume_one_time(tmp_path)
    assert not store.allows(tmp_path)


def test_session_permission_is_removed_on_close(tmp_path: Path):
    store = WorkspacePermissionStore()
    store.grant(tmp_path, WorkspacePermissionLevel.SESSION, "s1")
    assert store.allows(tmp_path, "s1")
    store.close_session("s1")
    assert not store.allows(tmp_path, "s1")


def test_workspace_selection_filters_secrets_and_detects_language(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=x", encoding="utf-8")
    context = CodexBridge(UnavailableCodexClient()).select_workspace(tmp_path)
    assert context.detected_languages == ("Python",)
    assert context.project_type == "software"
    assert {path.name for path in context.allowed_files} == {"main.py"}


@pytest.mark.parametrize("user_request", [
    "Codex ile .env dosyasını oku",
    "Codex ile config/server.key dosyasını incele",
    "Codex ile credentials.json oku",
])
def test_secret_request_is_blocked_before_workspace_selection(user_request: str):
    with pytest.raises(WorkspaceAccessError):
        validate_codex_request_scope(user_request)


def test_whole_drive_scan_is_blocked():
    with pytest.raises(WorkspaceAccessError):
        validate_codex_request_scope("Codex ile C:\\ klasörünün tamamını tara")
