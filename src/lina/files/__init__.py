"""Read-only allowlisted file access and explicit attachment extraction."""

from lina.files.attachment_service import AttachmentService, SUPPORTED_DOCUMENT_SUFFIXES
from lina.files.models import DocumentAttachment

__all__ = ["AttachmentService", "DocumentAttachment", "SUPPORTED_DOCUMENT_SUFFIXES"]
