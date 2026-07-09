"""Read-only allowlisted file access service."""

from pathlib import Path, PureWindowsPath

from lina.files.models import (
    AllowedFile,
    BinaryFileRejectedError,
    FileContent,
    ForbiddenFilePathError,
    MissingAllowedFileError,
    UnknownAllowedFileError,
)


DEFAULT_ALLOWED_FILE_PATHS: tuple[str, ...] = (
    "README.md",
    "contributing.md",
    "docs/architecture.md",
    "docs/roadmap.md",
    "docs/development-log.md",
    "docs/vision.md",
    "docs/brain-specification-v1.md",
    "docs/conversation-flow-v1.md",
    "docs/release-notes-v0.3.0-alpha.md",
    "docs/release-notes-v0.3.1-alpha.md",
    "docs/release-notes-v0.4.0-alpha.md",
    "docs/release-notes-v0.4.1-alpha.md",
)


DEFAULT_FILE_ALIASES: dict[str, str] = {
    "readme": "README.md",
    "README": "README.md",
    "contributing": "contributing.md",
    "katkı": "contributing.md",
    "roadmap": "docs/roadmap.md",
    "yol haritası": "docs/roadmap.md",
    "development log": "docs/development-log.md",
    "dev log": "docs/development-log.md",
    "geliştirme günlüğü": "docs/development-log.md",
    "architecture": "docs/architecture.md",
    "mimari": "docs/architecture.md",
    "vision": "docs/vision.md",
    "vizyon": "docs/vision.md",
    "brain spec": "docs/brain-specification-v1.md",
    "brain specification": "docs/brain-specification-v1.md",
    "conversation flow": "docs/conversation-flow-v1.md",
    "release notes v0.3.0": "docs/release-notes-v0.3.0-alpha.md",
    "v0.3.0 release notes": "docs/release-notes-v0.3.0-alpha.md",
    "release notes v0.3.1": "docs/release-notes-v0.3.1-alpha.md",
    "v0.3.1 release notes": "docs/release-notes-v0.3.1-alpha.md",
    "release notes v0.4.0": "docs/release-notes-v0.4.0-alpha.md",
    "v0.4.0 release notes": "docs/release-notes-v0.4.0-alpha.md",
    "release notes v0.4.1": "docs/release-notes-v0.4.1-alpha.md",
    "v0.4.1 release notes": "docs/release-notes-v0.4.1-alpha.md",
}


class FileAccessService:
    """Safely reads only explicitly allowlisted project files."""

    def __init__(
        self,
        project_root: Path,
        allowed_paths: tuple[str, ...] = DEFAULT_ALLOWED_FILE_PATHS,
        aliases: dict[str, str] | None = None,
        max_preview_characters: int = 4000,
        max_context_characters: int = 8000,
    ) -> None:
        self._project_root = project_root.resolve(strict=False)
        self._allowed_paths = tuple(_normalize_allowed_path(path) for path in allowed_paths)
        self._allowed_set = set(self._allowed_paths)
        self._aliases = {
            _normalize_alias(alias): _normalize_allowed_path(target)
            for alias, target in (aliases or DEFAULT_FILE_ALIASES).items()
        }
        self._max_preview_characters = max_preview_characters
        self._max_context_characters = max_context_characters

    def list_allowed_files(self) -> tuple[AllowedFile, ...]:
        """List allowlisted files and whether they currently exist."""
        return tuple(
            AllowedFile(path=path, exists=self._resolve_project_file(path).is_file())
            for path in self._allowed_paths
        )

    def is_allowed(self, path_or_alias: str) -> bool:
        """Return whether a path or alias resolves to an allowlisted file."""
        try:
            self._resolve_allowed_path(path_or_alias)
        except (ForbiddenFilePathError, UnknownAllowedFileError):
            return False
        return True

    def read_allowed_file(self, path_or_alias: str) -> FileContent:
        """Read an allowed file with the preview character limit."""
        return self._read_limited(path_or_alias, self._max_preview_characters)

    def build_file_context(self, path_or_alias: str, max_characters: int | None = None) -> FileContent:
        """Read an allowed file for model context with a bounded size."""
        limit = max_characters if max_characters is not None else self._max_context_characters
        return self._read_limited(path_or_alias, limit)

    def _read_limited(self, path_or_alias: str, max_characters: int) -> FileContent:
        allowed_path = self._resolve_allowed_path(path_or_alias)
        file_path = self._resolve_project_file(allowed_path)
        if not file_path.is_file():
            raise MissingAllowedFileError(f"Allowed file does not exist: {allowed_path}")

        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise BinaryFileRejectedError(f"Allowed file is not UTF-8 text: {allowed_path}") from error

        truncated = len(text) > max_characters
        return FileContent(
            path=allowed_path,
            text=text[:max_characters],
            truncated=truncated,
        )

    def _resolve_allowed_path(self, path_or_alias: str) -> str:
        requested = path_or_alias.strip()
        if not requested:
            raise UnknownAllowedFileError("Empty file path")

        normalized_alias = _normalize_alias(requested)
        if normalized_alias in self._aliases:
            allowed_path = self._aliases[normalized_alias]
        else:
            allowed_path = _normalize_requested_path(requested)

        if allowed_path not in self._allowed_set:
            raise UnknownAllowedFileError(f"File is not allowlisted: {requested}")

        self._resolve_project_file(allowed_path)
        return allowed_path

    def _resolve_project_file(self, allowed_path: str) -> Path:
        candidate = (self._project_root / allowed_path).resolve(strict=False)
        try:
            candidate.relative_to(self._project_root)
        except ValueError as error:
            raise ForbiddenFilePathError(f"Path escapes project root: {allowed_path}") from error
        return candidate


def _normalize_alias(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _normalize_allowed_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if not normalized or normalized.startswith("/") or ".." in Path(normalized).parts:
        raise ForbiddenFilePathError(f"Unsafe allowlist path: {path}")
    if PureWindowsPath(normalized).is_absolute():
        raise ForbiddenFilePathError(f"Unsafe allowlist path: {path}")
    return normalized


def _normalize_requested_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("/") or PureWindowsPath(normalized).is_absolute():
        raise ForbiddenFilePathError(f"Absolute paths are not allowed: {path}")
    if ".." in Path(normalized).parts:
        raise ForbiddenFilePathError(f"Path traversal is not allowed: {path}")
    return normalized

