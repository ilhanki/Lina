from pathlib import Path
import zipfile

import pytest

from lina.files.attachment_service import AttachmentService
from lina.files.models import (DocumentExtractionError, FileTooLargeError,
                               ForbiddenFilePathError, UnsupportedFileTypeError)


def test_loads_utf8_text_json_and_csv(tmp_path: Path) -> None:
    service = AttachmentService()
    text = tmp_path / "notes.md"
    text.write_text("Başlık\nİçerik", encoding="utf-8")
    assert service.load(text).text == "Başlık\nİçerik"
    payload = tmp_path / "data.json"
    payload.write_text('{"durum": "hazır"}', encoding="utf-8")
    assert "hazır" in service.load(payload).text
    table = tmp_path / "table.csv"
    table.write_text("ad,değer\nLina,14", encoding="utf-8")
    assert service.load(table).text == "ad | değer\nLina | 14"


def test_extracts_docx_text_without_external_dependency(tmp_path: Path) -> None:
    path = tmp_path / "brief.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", (
            '<w:document xmlns:w="urn:w"><w:body><w:p><w:r><w:t>Merhaba Lina</w:t>'
            '</w:r></w:p></w:body></w:document>'
        ))
    assert AttachmentService().load(path).text == "Merhaba Lina"


def test_extracts_xlsx_shared_strings_without_external_dependency(tmp_path: Path) -> None:
    path = tmp_path / "table.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", (
            '<sst xmlns="urn:x"><si><t>Başlık</t></si><si><t>Değer</t></si></sst>'
        ))
        archive.writestr("xl/worksheets/sheet1.xml", (
            '<worksheet xmlns="urn:x"><sheetData><row><c t="s"><v>0</v></c>'
            '<c t="s"><v>1</v></c></row></sheetData></worksheet>'
        ))
    assert AttachmentService().load(path).text == "Başlık | Değer"


def test_extracts_simple_pdf_text_and_rejects_encrypted_pdf(tmp_path: Path) -> None:
    plain = tmp_path / "plain.pdf"
    plain.write_bytes(b"%PDF-1.4\nBT (Lina report) Tj ET\n%%EOF")
    assert AttachmentService().load(plain).text == "Lina report"
    encrypted = tmp_path / "encrypted.pdf"
    encrypted.write_bytes(b"%PDF-1.4\n/Encrypt 1 0 R\n%%EOF")
    with pytest.raises(DocumentExtractionError):
        AttachmentService().load(encrypted)


def test_rejects_large_unsupported_sensitive_and_empty_documents(tmp_path: Path) -> None:
    large = tmp_path / "large.txt"
    large.write_bytes(b"x" * 2049)
    with pytest.raises(FileTooLargeError):
        AttachmentService(max_bytes=2048).load(large)
    unsupported = tmp_path / "archive.zip"
    unsupported.write_bytes(b"zip")
    with pytest.raises(UnsupportedFileTypeError):
        AttachmentService().load(unsupported)
    secret = tmp_path / "credentials.json"
    secret.write_text("{}", encoding="utf-8")
    with pytest.raises(ForbiddenFilePathError):
        AttachmentService().load(secret)
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(DocumentExtractionError):
        AttachmentService().load(empty)


def test_truncation_is_explicit(tmp_path: Path) -> None:
    path = tmp_path / "long.txt"
    path.write_text("x" * 1500, encoding="utf-8")
    result = AttachmentService(max_characters=1000).load(path)
    assert result.truncated
    assert len(result.text) == 1000
