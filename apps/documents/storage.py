"""Secure storage backend for the Document Management module."""

from __future__ import annotations

import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class DocumentStorage(FileSystemStorage):
    """Secure storage for documents with safe filename generation."""

    def __init__(self, **kwargs):
        kwargs.setdefault("location", os.path.join(settings.MEDIA_ROOT, "documents"))
        kwargs.setdefault("base_url", settings.MEDIA_URL + "documents/")
        super().__init__(**kwargs)

    def get_available_name(self, name: str, max_length: int | None = None) -> str:
        """Generate a safe, unique stored filename."""
        ext = os.path.splitext(name)[1].lower()
        safe_name = f"{uuid.uuid4().hex}{ext}"
        year = str(__import__("datetime").datetime.now().year)
        month = str(__import__("datetime").datetime.now().month).zfill(2)
        return os.path.join(year, month, safe_name)


class PrivateDocumentStorage(FileSystemStorage):
    """Storage for highly confidential documents."""

    def __init__(self, **kwargs):
        kwargs.setdefault(
            "location", os.path.join(settings.PRIVATE_MEDIA_ROOT, "documents")
        )
        kwargs.setdefault("base_url", "/private/documents/")
        super().__init__(**kwargs)

    def url(self, name):
        raise ValueError("Private documents have no public URL.")

    def get_available_name(self, name: str, max_length: int | None = None) -> str:
        ext = os.path.splitext(name)[1].lower()
        safe_name = f"{uuid.uuid4().hex}{ext}"
        year = str(__import__("datetime").datetime.now().year)
        month = str(__import__("datetime").datetime.now().month).zfill(2)
        return os.path.join(year, month, safe_name)


document_storage = DocumentStorage()
private_document_storage = PrivateDocumentStorage()
