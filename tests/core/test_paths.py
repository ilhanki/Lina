from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from lina.core.paths import AppPaths


def test_app_paths_are_created_from_project_root(tmp_path: Path) -> None:
    paths = AppPaths.from_project_root(tmp_path)

    assert paths.project_root == tmp_path.resolve(strict=False)
    assert paths.config_dir == tmp_path / "config"
    assert paths.data_dir == tmp_path / "data"
    assert paths.logs_dir == tmp_path / "logs"
    assert paths.models_dir == tmp_path / "models"
    assert paths.cache_dir == tmp_path / "cache"


def test_app_paths_use_path_instances(tmp_path: Path) -> None:
    paths = AppPaths.from_project_root(tmp_path)

    assert isinstance(paths.project_root, Path)
    assert isinstance(paths.config_dir, Path)
    assert isinstance(paths.data_dir, Path)
    assert isinstance(paths.logs_dir, Path)
    assert isinstance(paths.models_dir, Path)
    assert isinstance(paths.cache_dir, Path)


def test_project_root_is_resolved_without_requiring_existing_path(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing" / ".." / "project"

    paths = AppPaths.from_project_root(missing_root)

    assert paths.project_root == missing_root.resolve(strict=False)


def test_app_paths_are_immutable(tmp_path: Path) -> None:
    paths = AppPaths.from_project_root(tmp_path)

    with pytest.raises(FrozenInstanceError):
        paths.project_root = tmp_path / "other"

