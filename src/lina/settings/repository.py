"""Atomic local JSON persistence for user preferences."""

from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile

from lina.settings.models import UserSettings


class UserSettingsRepository:
    """Load and save user preferences without touching project data."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path.resolve(strict=False)

    def load(self) -> UserSettings:
        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeError):
            return UserSettings()
        return UserSettings.from_dict(raw)

    def save(self, settings: UserSettings) -> None:
        payload = json.dumps(settings.to_dict(), ensure_ascii=False, indent=2)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.file_path.parent,
                prefix=f".{self.file_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(payload)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.file_path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def default_user_settings_path(app_name: str = "Lina") -> Path:
    """Return the Windows local application-data location for Lina settings."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return root / app_name / "user-settings.json"
