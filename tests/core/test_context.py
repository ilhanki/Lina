import logging
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from lina.core.context import ApplicationContext
from lina.core.paths import AppPaths
from lina.core.settings import (
    AppSettings,
    ApplicationSettings,
    LoggingSettings,
    OllamaSettings,
    PathSettings,
)


def test_application_context_stores_core_dependencies(tmp_path: Path) -> None:
    settings = _create_settings()
    paths = AppPaths.from_project_root(tmp_path)
    logger = logging.getLogger("lina.test")

    context = ApplicationContext(settings=settings, paths=paths, logger=logger)

    assert context.settings is settings
    assert context.paths is paths
    assert context.logger is logger


def test_application_context_is_immutable(tmp_path: Path) -> None:
    context = ApplicationContext(
        settings=_create_settings(),
        paths=AppPaths.from_project_root(tmp_path),
        logger=logging.getLogger("lina.test"),
    )

    with pytest.raises(FrozenInstanceError):
        context.logger = logging.getLogger("lina.other")


def test_application_context_has_no_service_locator_methods() -> None:
    public_names = {
        name for name in dir(ApplicationContext) if not name.startswith("_")
    }

    assert "get" not in public_names
    assert "register" not in public_names
    assert "resolve" not in public_names


def _create_settings() -> AppSettings:
    return AppSettings(
        app=ApplicationSettings(name="Lina", environment="test"),
        logging=LoggingSettings(level="INFO"),
        paths=PathSettings(data="data", logs="logs", models="models", cache="cache"),
        ollama=OllamaSettings(base_url="http://localhost:11434", default_model=""),
    )

