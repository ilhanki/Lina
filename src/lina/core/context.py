"""Application context for Lina."""

from dataclasses import dataclass
import logging

from lina.core.paths import AppPaths
from lina.core.settings import AppSettings


@dataclass(frozen=True)
class ApplicationContext:
    """Core application dependencies shared across the application."""

    settings: AppSettings
    paths: AppPaths
    logger: logging.Logger

