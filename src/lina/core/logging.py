"""Logging setup for Lina."""

import logging


LOGGER_NAME = "lina"
_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_LINA_HANDLER_MARKER = "_lina_managed_handler"


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the application logger."""
    log_level = _parse_log_level(level)
    logger = logging.getLogger(LOGGER_NAME)

    logger.setLevel(log_level)
    logger.propagate = False

    managed_handlers = [
        handler
        for handler in logger.handlers
        if getattr(handler, _LINA_HANDLER_MARKER, False)
    ]

    if not managed_handlers:
        logger.handlers.clear()
        logger.addHandler(_create_stream_handler(log_level))
        return logger

    logger.handlers.clear()
    logger.handlers.extend(managed_handlers[:1])
    logger.handlers[0].setLevel(log_level)

    return logger


def _create_stream_handler(level: int) -> logging.StreamHandler:
    handler = logging.StreamHandler()
    setattr(handler, _LINA_HANDLER_MARKER, True)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    return handler


def _parse_log_level(level: str) -> int:
    normalized_level = level.strip().upper()
    log_level = logging.getLevelName(normalized_level)

    if not isinstance(log_level, int):
        raise ValueError(f"Invalid log level: {level}")

    return log_level
