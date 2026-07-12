from pathlib import Path

import pytest

from lina.files.file_access_service import FileAccessService
from lina.files.models import (
    BinaryFileRejectedError,
    ForbiddenFilePathError,
    MissingAllowedFileError,
    UnknownAllowedFileError,
)


def test_file_access_service_lists_allowed_existing_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Readme", encoding="utf-8")
    service = FileAccessService(
        project_root=tmp_path,
        allowed_paths=("README.md", "docs/roadmap.md"),
    )

    files = service.list_allowed_files()

    assert files[0].path == "README.md"
    assert files[0].exists is True
    assert files[1].path == "docs/roadmap.md"
    assert files[1].exists is False


def test_file_access_service_reads_readme(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Hello Lina", encoding="utf-8")
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    content = service.read_allowed_file("README.md")

    assert content.path == "README.md"
    assert content.text == "Hello Lina"
    assert content.truncated is False


def test_file_access_service_matches_allowlist_case_insensitively(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Hello Lina", encoding="utf-8")
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",), aliases={})
    assert service.read_allowed_file("readme.md").path == "README.md"


def test_file_access_service_reads_nested_allowed_file(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "roadmap.md").write_text("Roadmap", encoding="utf-8")
    service = FileAccessService(
        project_root=tmp_path,
        allowed_paths=("docs/roadmap.md",),
    )

    content = service.read_allowed_file("docs/roadmap.md")

    assert content.path == "docs/roadmap.md"
    assert content.text == "Roadmap"


def test_file_access_service_resolves_readme_alias(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Readme", encoding="utf-8")
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    content = service.read_allowed_file("readme")

    assert content.path == "README.md"


def test_file_access_service_resolves_roadmap_alias(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "roadmap.md").write_text("Roadmap", encoding="utf-8")
    service = FileAccessService(
        project_root=tmp_path,
        allowed_paths=("docs/roadmap.md",),
    )

    content = service.read_allowed_file("roadmap")

    assert content.path == "docs/roadmap.md"


def test_file_access_service_rejects_unknown_file(tmp_path: Path) -> None:
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    with pytest.raises(UnknownAllowedFileError):
        service.read_allowed_file("secret.txt")


def test_file_access_service_rejects_absolute_path(tmp_path: Path) -> None:
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    with pytest.raises(ForbiddenFilePathError):
        service.read_allowed_file("C:/Users/Ilhan/Desktop/test.txt")


def test_file_access_service_rejects_path_traversal(tmp_path: Path) -> None:
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    with pytest.raises(ForbiddenFilePathError):
        service.read_allowed_file("../README.md")


def test_file_access_service_rejects_backslash_path_traversal(tmp_path: Path) -> None:
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    with pytest.raises(ForbiddenFilePathError):
        service.read_allowed_file("..\\README.md")


@pytest.mark.parametrize(
    "path",
    [
        "../../README.md",
        "docs/../README.md",
        "C:/Users/Ilhan/Desktop/test.txt",
        "C:\\Users\\Ilhan\\Desktop\\test.txt",
        "/etc/passwd",
        "./../README.md",
    ],
)
def test_file_access_service_rejects_forbidden_path_syntax_before_alias(
    tmp_path: Path,
    path: str,
) -> None:
    (tmp_path / "README.md").write_text("Readme", encoding="utf-8")
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    with pytest.raises(ForbiddenFilePathError):
        service.read_allowed_file(path)


def test_file_access_service_enforces_project_root_boundary(tmp_path: Path) -> None:
    with pytest.raises(ForbiddenFilePathError):
        FileAccessService(
            project_root=tmp_path,
            allowed_paths=("../outside.md",),
        )


def test_file_access_service_enforces_preview_limit(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("abcdef", encoding="utf-8")
    service = FileAccessService(
        project_root=tmp_path,
        allowed_paths=("README.md",),
        max_preview_characters=3,
    )

    content = service.read_allowed_file("README.md")

    assert content.text == "abc"
    assert content.truncated is True


def test_file_access_service_enforces_context_limit(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("abcdef", encoding="utf-8")
    service = FileAccessService(
        project_root=tmp_path,
        allowed_paths=("README.md",),
        max_context_characters=4,
    )

    content = service.build_file_context("README.md")

    assert content.text == "abcd"
    assert content.truncated is True


def test_file_access_service_handles_missing_allowlisted_file(tmp_path: Path) -> None:
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    with pytest.raises(MissingAllowedFileError):
        service.read_allowed_file("README.md")


def test_file_access_service_rejects_binary_file(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_bytes(b"\xff\xfe\x00")
    service = FileAccessService(project_root=tmp_path, allowed_paths=("README.md",))

    with pytest.raises(BinaryFileRejectedError):
        service.read_allowed_file("README.md")
