"""Custom managers and querysets for the Document Management module."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    User = get_user_model()


# ---------------------------------------------------------------------------
# Document Manager
# ---------------------------------------------------------------------------


class DocumentQuerySet(models.QuerySet):
    """QuerySet with document-specific filters."""

    def active(self) -> models.QuerySet:
        return self.filter(is_deleted=False, is_archived=False)

    def drafts(self) -> models.QuerySet:
        return self.filter(status="DRAFT")

    def uploaded(self) -> models.QuerySet:
        return self.filter(status="UPLOADED")

    def pending_review(self) -> models.QuerySet:
        return self.filter(status="PENDING_REVIEW")

    def under_review(self) -> models.QuerySet:
        return self.filter(status="UNDER_REVIEW")

    def returned(self) -> models.QuerySet:
        return self.filter(status="RETURNED_FOR_CORRECTION")

    def pending_approval(self) -> models.QuerySet:
        return self.filter(status="PENDING_APPROVAL")

    def approved(self) -> models.QuerySet:
        return self.filter(status="APPROVED")

    def published(self) -> models.QuerySet:
        return self.filter(status="PUBLISHED")

    def active_status(self) -> models.QuerySet:
        return self.filter(status="ACTIVE")

    def superseded(self) -> models.QuerySet:
        return self.filter(status="SUPERSEDED")

    def expired(self) -> models.QuerySet:
        return self.filter(status="EXPIRED")

    def archived(self) -> models.QuerySet:
        return self.filter(status="ARCHIVED")

    def disposal_pending(self) -> models.QuerySet:
        return self.filter(status="DISPOSAL_PENDING")

    def expiring_soon(self, days: int = 30) -> models.QuerySet:
        threshold = timezone.now().date() + timezone.timedelta(days=days)
        return self.filter(
            expiry_date__isnull=False,
            expiry_date__lte=threshold,
            expiry_date__gte=timezone.now().date(),
        )

    def expired_documents(self) -> models.QuerySet:
        return self.filter(
            expiry_date__isnull=False,
            expiry_date__lt=timezone.now().date(),
        )

    def checked_out(self) -> models.QuerySet:
        return self.filter(checkouts__status="ACTIVE")

    def by_category(self, category_id: str) -> models.QuerySet:
        return self.filter(category_id=category_id)

    def by_type(self, type_id: str) -> models.QuerySet:
        return self.filter(document_type_id=type_id)

    def by_folder(self, folder_id: str) -> models.QuerySet:
        return self.filter(folder_id=folder_id)

    def by_owner(self, user: "User") -> models.QuerySet:
        return self.filter(owner=user)

    def by_status(self, status: str) -> models.QuerySet:
        return self.filter(status=status)

    def by_confidentiality(self, level: str) -> models.QuerySet:
        return self.filter(confidentiality_level=level)

    def sensitive(self) -> models.QuerySet:
        return self.filter(is_sensitive=True)

    def under_hold(self) -> models.QuerySet:
        return self.filter(legal_hold=True) | self.filter(safeguarding_hold=True)

    def downloadable(self) -> models.QuerySet:
        return self.filter(download_restricted=False)

    def recently_uploaded(self, days: int = 7) -> models.QuerySet:
        threshold = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=threshold)

    def for_user(self, user: "User") -> models.QuerySet:
        """Return documents accessible to the given user based on ownership."""
        return self.filter(
            models.Q(owner=user) | models.Q(created_by=user)
        ).distinct()

    def search(self, query: str) -> models.QuerySet:
        """Simple search across title, description, reference_number, keywords."""
        return self.filter(
            models.Q(title__icontains=query)
            | models.Q(description__icontains=query)
            | models.Q(reference_number__icontains=query)
            | models.Q(short_title__icontains=query)
        )


class DocumentManager(models.Manager):
    """Manager for Document model."""

    def get_queryset(self) -> DocumentQuerySet:
        return DocumentQuerySet(self.model, using=self._db)

    def active(self) -> models.QuerySet:
        return self.get_queryset().active()

    def drafts(self) -> models.QuerySet:
        return self.get_queryset().drafts()

    def published(self) -> models.QuerySet:
        return self.get_queryset().published()

    def expiring_soon(self, days: int = 30) -> models.QuerySet:
        return self.get_queryset().expiring_soon(days)

    def expired_documents(self) -> models.QuerySet:
        return self.get_queryset().expired_documents()

    def search(self, query: str) -> models.QuerySet:
        return self.get_queryset().search(query)


# ---------------------------------------------------------------------------
# DocumentVersion Manager
# ---------------------------------------------------------------------------


class DocumentVersionQuerySet(models.QuerySet):
    def current(self) -> models.QuerySet:
        return self.filter(is_current=True)

    def major_versions(self) -> models.QuerySet:
        return self.filter(version_type="MAJOR")

    def minor_versions(self) -> models.QuerySet:
        return self.filter(version_type="MINOR")

    def for_document(self, document) -> models.QuerySet:
        return self.filter(document=document).order_by("-version_number")


# ---------------------------------------------------------------------------
# DocumentFolder Manager
# ---------------------------------------------------------------------------


class DocumentFolderQuerySet(models.QuerySet):
    def active(self) -> models.QuerySet:
        return self.filter(is_deleted=False)

    def root_folders(self) -> models.QuerySet:
        return self.filter(parent__isnull=True)

    def children(self, parent) -> models.QuerySet:
        return self.filter(parent=parent)


# ---------------------------------------------------------------------------
# DocumentCheckout Manager
# ---------------------------------------------------------------------------


class DocumentCheckoutQuerySet(models.QuerySet):
    def active(self) -> models.QuerySet:
        return self.filter(status="ACTIVE")

    def for_document(self, document) -> models.QuerySet:
        return self.filter(document=document)

    def overdue(self) -> models.QuerySet:
        return self.filter(
            status="ACTIVE",
            expected_return_date__isnull=False,
            expected_return_date__lt=timezone.now().date(),
        )


# ---------------------------------------------------------------------------
# DocumentShare Manager
# ---------------------------------------------------------------------------


class DocumentShareQuerySet(models.QuerySet):
    def active(self) -> models.QuerySet:
        return self.filter(is_active=True)

    def for_document(self, document) -> models.QuerySet:
        return self.filter(document=document)

    def for_user(self, user: "User") -> models.QuerySet:
        return self.filter(shared_with_user=user, is_active=True)

    def expired(self) -> models.QuerySet:
        return self.filter(
            is_active=True,
            expiry_date__isnull=False,
            expiry_date__lt=timezone.now().date(),
        )


# ---------------------------------------------------------------------------
# DocumentAuditRecord Manager
# ---------------------------------------------------------------------------


class DocumentAuditRecordManager(models.Manager):
    def for_entity(self, entity_type: str, entity_id: str) -> models.QuerySet:
        return self.filter(entity_type=entity_type, entity_id=entity_id)

    def for_user(self, user: "User") -> models.QuerySet:
        return self.filter(changed_by=user)


# ---------------------------------------------------------------------------
# DocumentTimelineEvent Manager
# ---------------------------------------------------------------------------


class DocumentTimelineEventManager(models.Manager):
    def for_document(self, document) -> models.QuerySet:
        return self.filter(document=document).order_by("-created_at")
