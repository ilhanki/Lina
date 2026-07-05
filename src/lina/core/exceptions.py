"""Core exception types for Lina."""


class LinaError(Exception):
    """Base exception for all Lina-specific errors."""


class ConfigurationError(LinaError):
    """Raised when application configuration cannot be loaded or validated."""


class PathResolutionError(LinaError):
    """Raised when an application path cannot be resolved or validated."""


class ApplicationLifecycleError(LinaError):
    """Raised when the application lifecycle enters an invalid state."""

