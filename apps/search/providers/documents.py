"""Provider indexing documents."""

from __future__ import annotations

from apps.documents.constants import DocumentPermissions
from apps.documents.models import Document
from apps.documents.permissions import can_view_documents

from .base import SearchProvider, register


class DocumentProvider(SearchProvider):
    key = "documents.document"
    label = "Documents"
    model = Document
    detail_url_name = "documents:detail"
    view_permissions = (DocumentPermissions.VIEW, DocumentPermissions.VIEW_OWN)
    search_fields = (
        "reference_number",
        "title",
        "short_title",
        "description",
        "original_filename",
    )
    title_field = "title"
    subtitle_fields = ("reference_number", "category__name")
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        if not (getattr(user, "is_superuser", False) or can_view_documents(user)):
            return Document.objects.none()
        return Document.objects.filter(is_deleted=False).select_related(
            "category", "document_type", "owner"
        )


register(DocumentProvider())
