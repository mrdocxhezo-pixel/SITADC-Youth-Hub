"""Provider for document metadata (source type DOCUMENT)."""

from __future__ import annotations

from apps.documents.constants import DocumentPermissions
from apps.documents.models import Document
from apps.documents.selectors import get_documents_for_user

from ..constants import ExportSourceType
from ..renderers.base import ExportColumn
from .base import BaseProvider, register


class DocumentProvider(BaseProvider):
    """Export document metadata (never the files themselves)."""

    key = "documents.metadata"
    source_type = ExportSourceType.DOCUMENT
    label = "Documents"
    model = Document
    view_permissions = (DocumentPermissions.VIEW, DocumentPermissions.VIEW_OWN)
    manage_permissions = (DocumentPermissions.VIEW,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("title", "Document Title"),
        ExportColumn(
            "document_type",
            "Document Type",
            accessor=lambda obj: obj.document_type.name
            if obj.document_type_id
            else "",
        ),
        ExportColumn(
            "category",
            "Category",
            accessor=lambda obj: obj.category.name if obj.category_id else "",
        ),
        ExportColumn("file_extension", "Extension"),
        ExportColumn("mime_type", "MIME Type"),
        ExportColumn("status", "Status"),
        ExportColumn("approval_status", "Approval Status"),
        ExportColumn("publication_status", "Publication Status"),
        ExportColumn("confidentiality_level", "Confidentiality"),
        ExportColumn("effective_date", "Effective Date"),
        ExportColumn("expiry_date", "Expiry Date"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return get_documents_for_user(user)


register(DocumentProvider())
