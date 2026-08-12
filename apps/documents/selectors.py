"""Read-only query selectors for the Document Management module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404

from .models import (
    Document,
    DocumentCategory,
    DocumentCheckout,
    DocumentFolder,
    DocumentHold,
    DocumentShare,
    DocumentType,
    DocumentVersion,
    RetentionCategory,
)

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    User = get_user_model()


# ---------------------------------------------------------------------------
# Document Selectors
# ---------------------------------------------------------------------------


def get_document_by_id(document_id: str) -> Document:
    return get_object_or_404(Document, pk=document_id)


def get_documents_for_user(user: User):
    return (
        Document.objects.filter(
            Q(owner=user) | Q(created_by=user),
            is_deleted=False,
        )
        .select_related("category", "document_type", "folder", "owner", "created_by")
        .distinct()
    )


def get_recent_documents(limit: int = 20):
    return (
        Document.objects.filter(is_deleted=False)
        .select_related("category", "document_type", "owner")
        .order_by("-created_at")[:limit]
    )


def get_documents_expiring_soon(days: int = 30):
    return Document.objects.expiring_soon(days).select_related(
        "category", "document_type", "owner"
    )


def get_documents_by_status(status: str):
    return Document.objects.by_status(status).select_related(
        "category", "document_type", "owner"
    )


def get_published_documents():
    return Document.objects.published().select_related(
        "category", "document_type", "owner"
    )


def search_documents(query: str, user: User | None = None):
    qs = Document.objects.search(query).select_related(
        "category", "document_type", "folder", "owner"
    )
    if user:
        qs = qs.filter(Q(owner=user) | Q(created_by=user)).distinct()
    return qs


def get_document_library_queryset(
    category=None,
    document_type=None,
    folder=None,
    status=None,
    confidentiality=None,
    sort_by="-created_at",
):
    qs = Document.objects.filter(is_deleted=False).select_related(
        "category", "document_type", "folder", "owner", "created_by"
    )
    if category:
        qs = qs.filter(category=category)
    if document_type:
        qs = qs.filter(document_type=document_type)
    if folder:
        qs = qs.filter(folder=folder)
    if status:
        qs = qs.filter(status=status)
    if confidentiality:
        qs = qs.filter(confidentiality_level=confidentiality)
    return qs.order_by(sort_by)


# ---------------------------------------------------------------------------
# Category Selectors
# ---------------------------------------------------------------------------


def get_all_categories():
    return DocumentCategory.objects.filter(is_active=True).order_by(
        "sort_order", "name"
    )


def get_category_by_id(category_id: str) -> DocumentCategory:
    return get_object_or_404(DocumentCategory, pk=category_id)


def get_root_categories():
    return DocumentCategory.objects.filter(
        parent__isnull=True, is_active=True
    ).order_by("sort_order", "name")


# ---------------------------------------------------------------------------
# Document Type Selectors
# ---------------------------------------------------------------------------


def get_all_document_types():
    return DocumentType.objects.filter(is_active=True).order_by("name")


def get_document_types_for_category(category_id: str):
    return DocumentType.objects.filter(
        category_id=category_id, is_active=True
    ).order_by("name")


# ---------------------------------------------------------------------------
# Folder Selectors
# ---------------------------------------------------------------------------


def get_root_folders():
    return DocumentFolder.objects.filter(
        parent__isnull=True, is_deleted=False
    ).order_by("sort_order", "name")


def get_folder_children(folder):
    return DocumentFolder.objects.filter(parent=folder, is_deleted=False).order_by(
        "sort_order", "name"
    )


def get_folder_by_id(folder_id: str) -> DocumentFolder:
    return get_object_or_404(DocumentFolder, pk=folder_id, is_deleted=False)


def get_folder_breadcrumbs(folder) -> list:
    """Return list of parent folders from root to the given folder."""
    breadcrumbs = []
    current = folder
    while current is not None:
        breadcrumbs.insert(0, current)
        current = current.parent
    return breadcrumbs


# ---------------------------------------------------------------------------
# Version Selectors
# ---------------------------------------------------------------------------


def get_current_version(document: Document) -> DocumentVersion | None:
    return document.versions.filter(is_current=True).first()


def get_version_history(document: Document):
    return document.versions.all().order_by("-version_number")


def get_version_by_number(document: Document, version_number: int) -> DocumentVersion:
    return get_object_or_404(
        DocumentVersion, document=document, version_number=version_number
    )


# ---------------------------------------------------------------------------
# Checkout Selectors
# ---------------------------------------------------------------------------


def get_active_checkout(document: Document) -> DocumentCheckout | None:
    return document.checkouts.filter(status="ACTIVE").first()


def get_checked_out_documents(user: User | None = None):
    qs = DocumentCheckout.objects.filter(status="ACTIVE").select_related(
        "document", "checked_out_by"
    )
    if user:
        qs = qs.filter(checked_out_by=user)
    return qs


def get_overdue_checkouts():
    return DocumentCheckout.objects.overdue().select_related(
        "document", "checked_out_by"
    )


# ---------------------------------------------------------------------------
# Share Selectors
# ---------------------------------------------------------------------------


def get_document_shares(document: Document):
    return DocumentShare.objects.filter(
        document=document, is_active=True
    ).select_related("shared_with_user", "shared_by")


def get_shared_with_user(user: User):
    return DocumentShare.objects.for_user(user).select_related("document", "shared_by")


# ---------------------------------------------------------------------------
# Hold Selectors
# ---------------------------------------------------------------------------


def get_document_holds(document: Document):
    return DocumentHold.objects.filter(document=document).select_related(
        "applied_by", "released_by"
    )


def get_active_holds():
    return DocumentHold.objects.filter(status="ACTIVE").select_related(
        "document", "applied_by"
    )


# ---------------------------------------------------------------------------
# Dashboard Selectors
# ---------------------------------------------------------------------------


def get_document_dashboard_stats(user: User):
    """Return aggregated document statistics for the dashboard."""
    base_qs = Document.objects.filter(is_deleted=False)
    return {
        "total_documents": base_qs.count(),
        "my_documents": base_qs.filter(owner=user).count(),
        "drafts": base_qs.filter(status="DRAFT").count(),
        "pending_review": base_qs.filter(status="PENDING_REVIEW").count(),
        "pending_approval": base_qs.filter(status="PENDING_APPROVAL").count(),
        "published": base_qs.filter(status="PUBLISHED").count(),
        "archived": base_qs.filter(status="ARCHIVED").count(),
        "expiring_soon": Document.objects.expiring_soon(30).count(),
        "expired": Document.objects.expired_documents().count(),
        "checked_out": DocumentCheckout.objects.filter(status="ACTIVE").count(),
        "total_storage": base_qs.aggregate(total=Sum("file_size"))["total"] or 0,
        "documents_by_category": list(
            DocumentCategory.objects.filter(is_active=True)
            .annotate(count=Count("documents"))
            .order_by("-count")[:10]
        ),
    }


# ---------------------------------------------------------------------------
# Retention Selectors
# ---------------------------------------------------------------------------


def get_retention_categories():
    return RetentionCategory.objects.filter(is_active=True).order_by("name")


def get_documents_for_retention_review():
    """Get documents due for retention review."""
    from django.utils import timezone

    return Document.objects.filter(
        retention_category__requires_review=True,
        review_date__lte=timezone.now().date(),
        is_deleted=False,
    ).select_related("retention_category", "owner")
