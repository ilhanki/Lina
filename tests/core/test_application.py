import logging
from pathlib import Path

import pytest

from lina.core.application import Application, ApplicationState, LinaApplication
from lina.core.context import ApplicationContext
from lina.core.exceptions import ApplicationLifecycleError
from lina.core.paths import AppPaths
from lina.core.settings import (
    AppSettings,
    ApplicationSettings,
    LoggingSettings,
    OllamaSettings,
    PathSettings,
)


def test_application_starts_initialized(tmp_path: Path) -> None:
    application = LinaApplication(context=_create_context(tmp_path))

    assert application.state is ApplicationState.INITIALIZED


def test_application_start_moves_to_running(tmp_path: Path) -> None:
    application = LinaApplication(context=_create_context(tmp_path))

    application.start()

    assert application.state is ApplicationState.RUNNING


def test_application_stop_moves_to_stopped(tmp_path: Path) -> None:
    application = LinaApplication(context=_create_context(tmp_path))

    application.start()
    application.stop()

    assert application.state is ApplicationState.STOPPED


def test_application_cannot_start_twice(tmp_path: Path) -> None:
    application = LinaApplication(context=_create_context(tmp_path))
    application.start()

    with pytest.raises(ApplicationLifecycleError, match="Cannot start application"):
        application.start()


def test_application_cannot_stop_before_start(tmp_path: Path) -> None:
    application = LinaApplication(context=_create_context(tmp_path))

    with pytest.raises(ApplicationLifecycleError, match="Cannot stop application"):
        application.stop()


def test_application_cannot_restart_after_stop(tmp_path: Path) -> None:
    application = LinaApplication(context=_create_context(tmp_path))
    application.start()
    application.stop()

    with pytest.raises(ApplicationLifecycleError, match="Cannot start application"):
        application.start()


def test_application_keeps_context_reference(tmp_path: Path) -> None:
    context = _create_context(tmp_path)

    application = LinaApplication(context=context)

    assert application.context is context


def test_application_public_alias_preserves_lifecycle_contract(tmp_path: Path) -> None:
    application = Application(context=_create_context(tmp_path))
    assert isinstance(application, LinaApplication)
    application.start()
    application.stop()
    assert application.state is ApplicationState.STOPPED


def _create_context(tmp_path: Path) -> ApplicationContext:
    return ApplicationContext(
        settings=_create_settings(),
        paths=AppPaths.from_project_root(tmp_path),
        logger=logging.getLogger("lina.test"),
    )


def _create_settings() -> AppSettings:
    return AppSettings(
        app=ApplicationSettings(name="Lina", environment="test"),
        logging=LoggingSettings(level="INFO"),
        paths=PathSettings(data="data", logs="logs", models="models", cache="cache"),
        ollama=OllamaSettings(base_url="http://localhost:11434", default_model=""),
    )
