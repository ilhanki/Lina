"""Application path definitions for Lina."""

from dataclasses import dataclass
from pathlib import Path


_CONFIG_DIR_NAME = "config"
_DATA_DIR_NAME = "data"
_LOGS_DIR_NAME = "logs"
_MODELS_DIR_NAME = "models"
_CACHE_DIR_NAME = "cache"


@dataclass(frozen=True)
class AppPaths:
    """Immutable application paths derived from a project root."""

    project_root: Path
    config_dir: Path
    data_dir: Path
    logs_dir: Path
    models_dir: Path
    cache_dir: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "AppPaths":
        resolved_root = project_root.resolve(strict=False)

        return cls(
            project_root=resolved_root,
            config_dir=resolved_root / _CONFIG_DIR_NAME,
            data_dir=resolved_root / _DATA_DIR_NAME,
            logs_dir=resolved_root / _LOGS_DIR_NAME,
            models_dir=resolved_root / _MODELS_DIR_NAME,
            cache_dir=resolved_root / _CACHE_DIR_NAME,
        )

