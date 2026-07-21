"""Models for read-only file access."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AllowedFile:
    """A file that Lina is allowed to read."""

    path: str
    exists: bool


@dataclass(frozen=True)
class FileContent:
    """Content read from an allowed file."""

    path: str
    text: str
    truncated: bool


@dataclass(frozen=True, slots=True)
class DocumentAttachment:
    """Bounded text extracted from one user-selected, read-only document."""

    display_name: str
    format: str
    text: str
    size_bytes: int
    truncated: bool = False


class FileAccessError(Exception):
    """Base error for file access failures."""


class ForbiddenFilePathError(FileAccessError):
    """Raised when a path is unsafe or forbidden."""


class UnknownAllowedFileError(FileAccessError):
    """Raised when a file is not in the allowlist."""


class MissingAllowedFileError(FileAccessError):
    """Raised when an allowlisted file does not exist."""


class BinaryFileRejectedError(FileAccessError):
    """Raised when an allowed file cannot be read as UTF-8 text."""


class UnsupportedFileTypeError(FileAccessError):
    """Raised when an attachment format is outside Lina's explicit support list."""


class FileTooLargeError(FileAccessError):
    """Raised before reading an attachment beyond the configured byte limit."""


class DocumentExtractionError(FileAccessError):
    """Raised when a supported document cannot be parsed safely."""
