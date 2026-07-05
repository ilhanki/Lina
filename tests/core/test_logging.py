import logging
from collections.abc import Iterator

import pytest

from lina.core.logging import LOGGER_NAME, configure_logging


@pytest.fixture(autouse=True)
def clean_logger() -> Iterator[None]:
    logger = logging.getLogger(LOGGER_NAME)
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate

    logger.handlers.clear()

    yield

    logger.handlers.clear()
    logger.handlers.extend(original_handlers)
    logger.setLevel(original_level)
    logger.propagate = original_propagate


def test_configure_logging_returns_application_logger() -> None:
    logger = configure_logging("INFO")

    assert logger.name == LOGGER_NAME
    assert logger.level == logging.INFO


def test_configure_logging_adds_stream_handler() -> None:
    logger = configure_logging("DEBUG")

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert logger.handlers[0].level == logging.DEBUG


def test_configure_logging_disables_propagation() -> None:
    logger = configure_logging("WARNING")

    assert logger.propagate is False


def test_configure_logging_is_idempotent() -> None:
    logger = configure_logging("INFO")
    first_handler = logger.handlers[0]

    configure_logging("ERROR")

    assert logger.handlers == [first_handler]
    assert logger.level == logging.ERROR
    assert first_handler.level == logging.ERROR


def test_configure_logging_accepts_lowercase_level() -> None:
    logger = configure_logging("debug")

    assert logger.level == logging.DEBUG


def test_configure_logging_rejects_invalid_level() -> None:
    with pytest.raises(ValueError, match="Invalid log level"):
        configure_logging("LOUD")

