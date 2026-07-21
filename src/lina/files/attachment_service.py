"""Safe, bounded extraction for explicit user-selected document attachments."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
import zlib

from lina.files.models import (
    DocumentAttachment,
    DocumentExtractionError,
    FileTooLargeError,
    ForbiddenFilePathError,
    UnsupportedFileTypeError,
)


TEXT_SUFFIXES = frozenset({".txt", ".md", ".py", ".json", ".csv"})
DOCUMENT_SUFFIXES = frozenset({".pdf", ".docx", ".xlsx"})
SUPPORTED_DOCUMENT_SUFFIXES = TEXT_SUFFIXES | DOCUMENT_SUFFIXES
_SENSITIVE_NAMES = re.compile(
    r"(?:^|[._-])(?:\.env|credentials?|secrets?|private[_-]?key|id_rsa|auth)(?:[._-]|$)",
    re.IGNORECASE,
)


class AttachmentService:
    def __init__(self, *, max_bytes: int = 10 * 1024 * 1024,
                 max_characters: int = 24_000) -> None:
        self.max_bytes = max(1024, int(max_bytes))
        self.max_characters = max(1000, int(max_characters))

    def load(self, path: Path) -> DocumentAttachment:
        selected = path.expanduser().resolve(strict=False)
        if not selected.is_file():
            raise DocumentExtractionError("Seçilen dosya bulunamadı.")
        suffix = selected.suffix.casefold()
        if suffix not in SUPPORTED_DOCUMENT_SUFFIXES:
            raise UnsupportedFileTypeError(f"Desteklenmeyen dosya türü: {suffix or 'uzantısız'}")
        if _SENSITIVE_NAMES.search(selected.name) or suffix in {".key", ".pem", ".pfx"}:
            raise ForbiddenFilePathError("Kimlik bilgisi veya anahtar dosyası eklenemez.")
        size = selected.stat().st_size
        if size > self.max_bytes:
            raise FileTooLargeError(f"Dosya {self.max_bytes} bayt sınırını aşıyor.")
        try:
            if suffix in TEXT_SUFFIXES:
                text = self._read_text(selected, suffix)
            elif suffix == ".docx":
                text = self._read_docx(selected)
            elif suffix == ".xlsx":
                text = self._read_xlsx(selected)
            else:
                text = self._read_pdf(selected)
        except (OSError, UnicodeError, ValueError, ET.ParseError, zipfile.BadZipFile) as error:
            raise DocumentExtractionError("Belge güvenli biçimde okunamadı.") from error
        normalized = _normalize_text(text)
        if not normalized:
            raise DocumentExtractionError("Belgeden okunabilir metin çıkarılamadı.")
        truncated = len(normalized) > self.max_characters
        return DocumentAttachment(
            selected.name, suffix.removeprefix("."), normalized[:self.max_characters],
            size, truncated,
        )

    @staticmethod
    def _read_text(path: Path, suffix: str) -> str:
        text = path.read_text(encoding="utf-8-sig")
        if suffix == ".json":
            json.loads(text)
        elif suffix == ".csv":
            rows = csv.reader(io.StringIO(text))
            return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
        return text

    def _read_docx(self, path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            data = _read_zip_member(archive, "word/document.xml", self.max_bytes * 2)
        root = ET.fromstring(data)
        paragraphs: list[str] = []
        for paragraph in root.iter():
            if paragraph.tag.endswith("}p"):
                line = "".join(node.text or "" for node in paragraph.iter()
                               if node.tag.endswith("}t"))
                if line.strip():
                    paragraphs.append(line.strip())
        return "\n".join(paragraphs)

    def _read_xlsx(self, path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                root = ET.fromstring(_read_zip_member(
                    archive, "xl/sharedStrings.xml", self.max_bytes * 2
                ))
                shared = ["".join(node.text or "" for node in item.iter()
                                  if node.tag.endswith("}t"))
                          for item in root if item.tag.endswith("}si")]
            sheets = sorted(name for name in archive.namelist()
                            if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name))
            lines: list[str] = []
            for sheet in sheets[:20]:
                root = ET.fromstring(_read_zip_member(archive, sheet, self.max_bytes * 2))
                for row in (node for node in root.iter() if node.tag.endswith("}row")):
                    cells: list[str] = []
                    for cell in (node for node in row if node.tag.endswith("}c")):
                        value_node = next((node for node in cell.iter()
                                           if node.tag.endswith(("}v", "}t"))), None)
                        value = value_node.text if value_node is not None else ""
                        if cell.attrib.get("t") == "s" and value and value.isdigit():
                            index = int(value)
                            value = shared[index] if index < len(shared) else ""
                        cells.append(value or "")
                    if any(cell.strip() for cell in cells):
                        lines.append(" | ".join(cells))
            return "\n".join(lines)

    @staticmethod
    def _read_pdf(path: Path) -> str:
        data = path.read_bytes()
        if not data.startswith(b"%PDF-") or b"/Encrypt" in data:
            raise DocumentExtractionError("PDF geçersiz veya şifreli.")
        chunks = [data]
        for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
            stream = match.group(1)
            try:
                chunks.append(zlib.decompress(stream))
            except zlib.error:
                chunks.append(stream)
        literals: list[str] = []
        for chunk in chunks:
            for value in re.findall(rb"\(((?:\\.|[^\\)])*)\)\s*(?:Tj|['\"])", chunk):
                value = re.sub(rb"\\([()\\])", rb"\1", value)
                literals.append(value.decode("latin-1", errors="replace"))
        return "\n".join(literals)


def _read_zip_member(archive: zipfile.ZipFile, name: str, limit: int) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError as error:
        raise DocumentExtractionError("Belge yapısı eksik.") from error
    if info.file_size > limit:
        raise FileTooLargeError("Sıkıştırılmış belge içeriği sınırı aşıyor.")
    with archive.open(info) as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise FileTooLargeError("Sıkıştırılmış belge içeriği sınırı aşıyor.")
    return data


def _normalize_text(text: str) -> str:
    text = str(text or "").replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
