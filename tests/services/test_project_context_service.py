from pathlib import Path

from lina.services.project_context_service import ProjectContextService


def test_project_context_service_reads_allowed_documents(tmp_path: Path) -> None:
    _write_project_file(tmp_path, "README.md", "README content")
    _write_project_file(tmp_path, "docs/development-log.md", "Log content")
    _write_project_file(tmp_path, "docs/roadmap.md", "Roadmap content")
    service = ProjectContextService(project_root=tmp_path)

    context = service.collect_context()

    assert context.has_content
    assert "README content" in context.text
    assert "Log content" in context.text
    assert "Roadmap content" in context.text


def test_project_context_service_ignores_unallowed_documents(tmp_path: Path) -> None:
    _write_project_file(tmp_path, "secret.md", "Secret content")
    service = ProjectContextService(project_root=tmp_path)

    content = service.read_document(Path("secret.md"))

    assert content == ""


def test_project_context_service_blocks_path_traversal(tmp_path: Path) -> None:
    service = ProjectContextService(project_root=tmp_path)

    content = service.read_document(Path("../README.md"))

    assert content == ""


def test_project_context_service_handles_missing_documents(tmp_path: Path) -> None:
    service = ProjectContextService(project_root=tmp_path)

    context = service.collect_context()

    assert context.has_content
    assert "okunabilir bir bağlam bulunamadı" in context.text


def test_project_context_service_limits_document_length(tmp_path: Path) -> None:
    _write_project_file(tmp_path, "README.md", "a" * 7000)
    service = ProjectContextService(project_root=tmp_path)

    content = service.read_document(Path("README.md"))

    assert len(content) == 6000


def _write_project_file(tmp_path: Path, relative_path: str, content: str) -> None:
    file_path = tmp_path / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
