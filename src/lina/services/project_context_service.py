"""Project context reading for Lina."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectContext:
    """Context collected from allowed project documents."""

    text: str

    @property
    def has_content(self) -> bool:
        return bool(self.text.strip())


class ProjectContextService:
    """Reads a limited set of project documents from the repository."""

    _ALLOWED_DOCUMENTS = (
        Path("README.md"),
        Path("docs/development-log.md"),
        Path("docs/roadmap.md"),
    )
    _DEFAULT_MAX_CHARACTERS_PER_FILE = 6000
    _EMPTY_CONTEXT_MESSAGE = (
        "İzinli proje dokümanlarından okunabilir bir bağlam bulunamadı."
    )

    def __init__(
        self,
        project_root: Path,
        max_characters_per_file: int = _DEFAULT_MAX_CHARACTERS_PER_FILE,
    ) -> None:
        self._project_root = project_root.resolve(strict=False)
        self._max_characters_per_file = max_characters_per_file

    def collect_context(self) -> ProjectContext:
        sections: list[str] = []

        for relative_path in self._ALLOWED_DOCUMENTS:
            content = self._read_allowed_document(relative_path)
            if content:
                sections.append(f"## {relative_path.as_posix()}\n{content}")

        if not sections:
            return ProjectContext(text=self._EMPTY_CONTEXT_MESSAGE)

        return ProjectContext(text="\n\n".join(sections))

    def read_document(self, relative_path: Path) -> str:
        if relative_path not in self._ALLOWED_DOCUMENTS:
            return ""

        return self._read_allowed_document(relative_path)

    def _read_allowed_document(self, relative_path: Path) -> str:
        if relative_path.is_absolute() or ".." in relative_path.parts:
            return ""

        resolved_path = (self._project_root / relative_path).resolve(strict=False)
        if not resolved_path.is_relative_to(self._project_root):
            return ""
        if not resolved_path.exists() or not resolved_path.is_file():
            return ""

        try:
            content = resolved_path.read_text(encoding="utf-8")
        except OSError:
            return ""

        return content[: self._max_characters_per_file].strip()
