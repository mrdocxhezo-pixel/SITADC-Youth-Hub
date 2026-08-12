"""Business services for the Document Management module.

Every state-changing document operation flows through these services so that
invariants are enforced transactionally, reference numbers are generated
through a private helper, and every event is appended to the immutable
audit log and document timeline.
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.rbac.authorization import user_has_permission

from .constants import (
    AuditAction,
    CheckoutStatus,
    ConfidentialityLevel,
    DisposalStatus,
    DocumentStatus,
    DocumentPermissions,
    HoldStatus,
    HoldType,
    PublicationStatus,
    TimelineEventType,
    VersionType,
)
from .exceptions import (
    CircularFolderError,
    DocumentAccessDeniedError,
    DocumentApprovalError,
    DocumentArchiveError,
    DocumentCheckoutError,
    DocumentDisposalError,
    DocumentHoldError,
    DocumentManagementError,
    DocumentPublicationError,
    DocumentReferenceError,
    DocumentShareError,
    DocumentStorageError,
    DocumentVersionError,
    DocumentWorkflowError,
    FileSizeExceededError,
    UnsupportedFileTypeError,
    UnsafeFileError,
)
from .models import (
    Document,
    DocumentAuditRecord,
    DocumentCategory,
    DocumentCheckout,
    DocumentDisposalRequest,
    DocumentFolder,
    DocumentHold,
    DocumentShare,
    DocumentTag,
    DocumentTimelineEvent,
    DocumentType,
    DocumentVersion,
    RetentionCategory,
)
from .validators import (
    generate_checksum,
    safe_filename,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
)

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    from django.core.files.uploadedfile import UploadedFile

    User = get_user_model()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private Helpers — Reference Number Generation
# ---------------------------------------------------------------------------


_TYPE_PREFIX_MAP: dict[str, str] = {
    "POL": "POL",
    "MOU": "MOU",
    "MIN": "MIN",
    "EVD": "EVD",
    "RPT": "RPT",
    "FRM": "FRM",
    "LTR": "LTR",
    "SOP": "SOP",
    "CON": "CON",
    "AGR": "AGR",
    "FIN": "FIN",
    "HR": "HR",
    "PRO": "PRO",
}


@transaction.atomic
def _generate_document_reference_number(
    document_type: DocumentType | None = None,
    category: DocumentCategory | None = None,
) -> str:
    """Generate a unique document reference number.

    Format: ``SITADC/{TYPE_PREFIX}/{YEAR}/{SEQUENCE:06d}``

    The sequence is derived from the total count of ``DocumentAuditRecord``
    rows plus one for simplicity.  The result is guaranteed unique within a
    single transaction.
    """
    year = timezone.localdate().year
    prefix = "DOC"

    if document_type and document_type.code:
        mapped = _TYPE_PREFIX_MAP.get(document_type.code.upper())
        if mapped:
            prefix = mapped
        else:
            prefix = document_type.code.upper()[:3]
    elif category and category.code:
        prefix = category.code.upper()[:3]

    sequence = DocumentAuditRecord.objects.count() + 1
    reference = f"SITADC/{prefix}/{year}/{sequence:06d}"

    while Document.objects.filter(reference_number=reference).exists() or \
            DocumentFolder.objects.filter(reference_number=reference).exists():
        sequence += 1
        reference = f"SITADC/{prefix}/{year}/{sequence:06d}"

    return reference


# ---------------------------------------------------------------------------
# Private Helpers — Audit & Timeline
# ---------------------------------------------------------------------------


def _build_audit_snapshot(document: Document) -> dict:
    """Return a dict with key document fields for audit from_data/to_data."""
    return {
        "reference_number": document.reference_number,
        "title": document.title,
        "status": document.status,
        "approval_status": document.approval_status,
        "publication_status": document.publication_status,
        "confidentiality_level": document.confidentiality_level,
        "is_sensitive": document.is_sensitive,
        "owner": str(document.owner_id) if document.owner_id else None,
        "category": str(document.category_id) if document.category_id else None,
        "document_type": str(document.document_type_id) if document.document_type_id else None,
        "folder": str(document.folder_id) if document.folder_id else None,
        "current_version_number": document.current_version_number,
    }


def _record_audit(
    entity_type: str,
    entity_id,
    action: str,
    user,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> DocumentAuditRecord:
    """Create an immutable audit record for a document management event."""
    return DocumentAuditRecord.objects.create(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        changed_by=user,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


def _record_timeline(
    document: Document,
    event_type: str,
    actor,
    previous_status: str = "",
    new_status: str = "",
    comments: str = "",
) -> DocumentTimelineEvent:
    """Create a chronological event in a document's lifecycle."""
    return DocumentTimelineEvent.objects.create(
        document=document,
        event_type=event_type,
        actor=actor,
        previous_status=previous_status,
        new_status=new_status,
        comments=comments,
    )


def _require_permission(user, permission_code: str) -> None:
    """Raise PermissionDenied unless the user holds the permission."""
    if not user or not getattr(user, "is_authenticated", False):
        raise PermissionDenied(_("An authenticated actor is required."))
    if not user_has_permission(user, permission_code):
        raise PermissionDenied


# ---------------------------------------------------------------------------
# Document Upload
# ---------------------------------------------------------------------------


@transaction.atomic
def upload_document(
    user,
    file_obj: UploadedFile,
    title: str,
    description: str = "",
    category: DocumentCategory | None = None,
    document_type: DocumentType | None = None,
    folder: DocumentFolder | None = None,
    confidentiality_level: str = ConfidentialityLevel.INTERNAL,
    tags=None,
    effective_date=None,
    expiry_date=None,
    keywords: list[str] | None = None,
) -> Document:
    """Upload a new document with initial version.

    Validates file extension, size, and MIME type.  Generates a safe stored
    filename and SHA-256 checksum.  Creates the ``Document`` and its first
    ``DocumentVersion`` (version 1, is_current=True).  Records audit and
    timeline events.

    Returns the created ``Document``.
    """
    _require_permission(user, DocumentPermissions.UPLOAD)

    validate_file_extension(file_obj.name)
    validate_file_size(file_obj, document_type)
    mime_type = validate_mime_type(file_obj)

    checksum = generate_checksum(file_obj)
    ext = os.path.splitext(file_obj.name)[1].lower()
    stored_name = safe_filename(file_obj.name)

    reference_number = _generate_document_reference_number(document_type, category)

    document = Document(
        reference_number=reference_number,
        title=title,
        description=description,
        category=category,
        document_type=document_type,
        folder=folder,
        file=file_obj,
        original_filename=file_obj.name,
        stored_filename=stored_name,
        file_extension=ext.lstrip("."),
        mime_type=mime_type,
        file_size=file_obj.size,
        checksum=checksum,
        confidentiality_level=confidentiality_level,
        status=DocumentStatus.UPLOADED,
        current_version_number=1,
        effective_date=effective_date,
        expiry_date=expiry_date,
        keywords=keywords or [],
        owner=user,
        created_by=user,
        updated_by=user,
    )
    document.full_clean()
    document.save()

    if tags:
        document.tags.set(tags)

    version = DocumentVersion(
        document=document,
        version_number=1,
        version_label="1.0",
        version_type=VersionType.MAJOR,
        file=file_obj,
        original_filename=file_obj.name,
        stored_filename=stored_name,
        mime_type=mime_type,
        file_size=file_obj.size,
        checksum=checksum,
        is_current=True,
        effective_date=effective_date,
        created_by=user,
    )
    version.full_clean()
    version.save()

    _record_audit(
        "Document",
        document.pk,
        AuditAction.FILE_UPLOADED,
        user,
        to_data=_build_audit_snapshot(document),
        notes="Document uploaded.",
    )
    _record_timeline(
        document,
        TimelineEventType.UPLOADED,
        user,
        new_status=DocumentStatus.UPLOADED,
        comments="Document uploaded.",
    )

    logger.info("Uploaded document %s by %s", document.reference_number, user)
    return document


# ---------------------------------------------------------------------------
# Document Metadata
# ---------------------------------------------------------------------------


@transaction.atomic
def update_document_metadata(
    user,
    document: Document,
    **kwargs,
) -> Document:
    """Update document metadata fields.

    Validates user permission, records the audit trail, and returns the
    updated document.
    """
    _require_permission(user, DocumentPermissions.UPDATE_METADATA)

    from_data = _build_audit_snapshot(document)

    allowed_fields = {
        "title",
        "short_title",
        "description",
        "category",
        "document_type",
        "folder",
        "confidentiality_level",
        "is_sensitive",
        "owner",
        "responsible_unit",
        "effective_date",
        "expiry_date",
        "review_date",
        "renewal_date",
        "keywords",
        "retention_category",
        "retention_end_date",
        "download_restricted",
        "print_restricted",
        "external_sharing_restricted",
    }

    for field, value in kwargs.items():
        if field not in allowed_fields:
            raise ValidationError(
                _("Unsupported field: %(field)s") % {"field": field}
            )
        setattr(document, field, value)

    document.updated_by = user
    document.full_clean()
    document.save()

    if "tags" in kwargs:
        document.tags.set(kwargs["tags"])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.METADATA_CHANGED,
        user,
        from_data=from_data,
        to_data=_build_audit_snapshot(document),
        notes="Document metadata updated.",
    )
    _record_timeline(
        document,
        TimelineEventType.METADATA_UPDATED,
        user,
        comments="Document metadata updated.",
    )

    logger.info("Updated metadata for %s by %s", document.reference_number, user)
    return document


# ---------------------------------------------------------------------------
# Document Versioning
# ---------------------------------------------------------------------------


@transaction.atomic
def upload_new_version(
    user,
    document: Document,
    file_obj: UploadedFile,
    version_type: str = VersionType.MAJOR,
    change_summary: str = "",
    change_reason: str = "",
) -> DocumentVersion:
    """Upload a new version of an existing document.

    Validates that the document is not archived or disposed, validates
    checkout status, increments the version number, marks the previous
    current version as not current, and creates a new ``DocumentVersion``
    with ``is_current=True``.

    Returns the new ``DocumentVersion``.
    """
    _require_permission(user, DocumentPermissions.UPLOAD_VERSION)

    if document.status in (DocumentStatus.ARCHIVED, DocumentStatus.DISPOSED):
        raise DocumentVersionError(
            _("Cannot upload a version for an archived or disposed document.")
        )

    active_checkout = document.checkouts.filter(status=CheckoutStatus.ACTIVE).first()
    if active_checkout and active_checkout.checked_out_by_id != user.pk:
        raise DocumentCheckoutError(
            _("Document is checked out by another user and cannot be modified.")
        )

    validate_file_extension(file_obj.name)
    validate_file_size(file_obj, document.document_type)
    mime_type = validate_mime_type(file_obj)
    checksum = generate_checksum(file_obj)
    stored_name = safe_filename(file_obj.name)
    ext = os.path.splitext(file_obj.name)[1].lower()

    previous_version = document.versions.filter(is_current=True).first()

    if previous_version:
        previous_version.is_current = False
        previous_version.superseded_date = timezone.localdate()
        previous_version.save(update_fields=["is_current", "superseded_date", "updated_at"])

    new_version_number = document.current_version_number + 1
    if version_type == VersionType.MAJOR:
        version_label = f"{new_version_number}.0"
    else:
        minor_seq = document.versions.filter(
            version_type=VersionType.MINOR,
        ).count() + 1
        version_label = f"{document.current_version_number}.{minor_seq}"

    version = DocumentVersion(
        document=document,
        version_number=new_version_number,
        version_label=version_label,
        version_type=version_type,
        file=file_obj,
        original_filename=file_obj.name,
        stored_filename=stored_name,
        mime_type=mime_type,
        file_size=file_obj.size,
        checksum=checksum,
        change_summary=change_summary,
        change_reason=change_reason,
        is_current=True,
        effective_date=document.effective_date,
        created_by=user,
    )
    version.full_clean()
    version.save()

    document.current_version_number = new_version_number
    document.file = file_obj
    document.original_filename = file_obj.name
    document.stored_filename = stored_name
    document.file_extension = ext.lstrip(".")
    document.mime_type = mime_type
    document.file_size = file_obj.size
    document.checksum = checksum
    document.updated_by = user
    document.save(update_fields=[
        "current_version_number",
        "file",
        "original_filename",
        "stored_filename",
        "file_extension",
        "mime_type",
        "file_size",
        "checksum",
        "updated_by",
        "updated_at",
    ])

    from_data = _build_audit_snapshot(document) if previous_version else {}
    _record_audit(
        "DocumentVersion",
        version.pk,
        AuditAction.NEW_VERSION,
        user,
        from_data=from_data,
        to_data={
            "version_number": new_version_number,
            "version_type": version_type,
            "change_summary": change_summary,
        },
        notes=f"Version {new_version_number} uploaded.",
    )
    _record_timeline(
        document,
        TimelineEventType.VERSION_UPLOADED,
        user,
        comments=f"Version {new_version_number} uploaded. {change_summary}".strip(),
    )

    logger.info(
        "Uploaded version %d for %s by %s",
        new_version_number,
        document.reference_number,
        user,
    )
    return version


# ---------------------------------------------------------------------------
# Checkout / Checkin
# ---------------------------------------------------------------------------


@transaction.atomic
def checkout_document(
    user,
    document: Document,
    expected_return_date=None,
    checkout_reason: str = "",
) -> DocumentCheckout:
    """Check out a document for exclusive editing.

    Validates that no active checkout already exists.  Creates a
    ``DocumentCheckout`` with status ACTIVE.  Records audit and timeline.
    """
    _require_permission(user, DocumentPermissions.CHECKOUT)

    if document.status in (DocumentStatus.ARCHIVED, DocumentStatus.DISPOSED):
        raise DocumentCheckoutError(
            _("Cannot check out an archived or disposed document.")
        )

    active = document.checkouts.filter(status=CheckoutStatus.ACTIVE).first()
    if active:
        raise DocumentCheckoutError(
            _("Document is already checked out by %(user)s.")
            % {"user": active.checked_out_by}
        )

    current_version = document.versions.filter(is_current=True).first()

    checkout = DocumentCheckout(
        document=document,
        version=current_version,
        checked_out_by=user,
        expected_return_date=expected_return_date,
        checkout_reason=checkout_reason,
        status=CheckoutStatus.ACTIVE,
        created_by=user,
    )
    checkout.full_clean()
    checkout.save()

    _record_audit(
        "DocumentCheckout",
        checkout.pk,
        AuditAction.CHECKED_OUT,
        user,
        to_data={
            "document": document.reference_number,
            "expected_return_date": str(expected_return_date) if expected_return_date else None,
        },
        notes="Document checked out.",
    )
    _record_timeline(
        document,
        TimelineEventType.CHECKED_OUT,
        user,
        comments=f"Document checked out. {checkout_reason}".strip(),
    )

    logger.info("Checked out %s by %s", document.reference_number, user)
    return checkout


@transaction.atomic
def checkin_document(
    user,
    checkout: DocumentCheckout,
    file_obj: UploadedFile | None = None,
    checkin_notes: str = "",
) -> DocumentVersion:
    """Check in a document, optionally uploading a new version.

    Validates that the user is the one who checked out or has admin
    permission.  Marks the checkout as RETURNED.  If ``file_obj`` is
    provided, creates a new version.

    Returns the current or new ``DocumentVersion``.
    """
    if checkout.status != CheckoutStatus.ACTIVE:
        raise DocumentCheckoutError(
            _("This checkout is not active and cannot be checked in.")
        )

    is_owner = checkout.checked_out_by_id == user.pk
    if not is_owner:
        _require_permission(user, DocumentPermissions.CANCEL_CHECKOUT)

    checkout.status = CheckoutStatus.RETURNED
    checkout.checked_in_at = timezone.now()
    checkout.save(update_fields=["status", "checked_in_at", "updated_at"])

    document = checkout.document

    _record_audit(
        "DocumentCheckout",
        checkout.pk,
        AuditAction.CHECKED_IN,
        user,
        notes=checkin_notes or "Document checked in.",
    )
    _record_timeline(
        document,
        TimelineEventType.CHECKED_IN,
        user,
        comments=checkin_notes or "Document checked in.",
    )

    if file_obj is not None:
        new_version = upload_new_version(
            user,
            document,
            file_obj,
            version_type=VersionType.MAJOR,
            change_summary="Uploaded during check-in.",
            change_reason=checkin_notes,
        )
        checkout.new_version = new_version
        checkout.save(update_fields=["new_version", "updated_at"])
        logger.info(
            "Checked in %s with new version by %s",
            document.reference_number,
            user,
        )
        return new_version

    current_version = document.versions.filter(is_current=True).first()
    logger.info("Checked in %s by %s", document.reference_number, user)
    return current_version


@transaction.atomic
def cancel_checkout(user, checkout: DocumentCheckout) -> None:
    """Cancel an active checkout.

    Validates that the user has permission.  Marks the checkout as
    CANCELLED and records the audit event.
    """
    if checkout.status != CheckoutStatus.ACTIVE:
        raise DocumentCheckoutError(
            _("This checkout is not active and cannot be cancelled.")
        )

    is_owner = checkout.checked_out_by_id == user.pk
    if not is_owner:
        _require_permission(user, DocumentPermissions.CANCEL_CHECKOUT)

    checkout.status = CheckoutStatus.CANCELLED
    checkout.cancelled_at = timezone.now()
    checkout.cancelled_by = user
    checkout.save(update_fields=["status", "cancelled_at", "cancelled_by", "updated_at"])

    _record_audit(
        "DocumentCheckout",
        checkout.pk,
        AuditAction.CHECKOUT_CANCELLED,
        user,
        notes="Checkout cancelled.",
    )

    logger.info(
        "Cancelled checkout for %s by %s",
        checkout.document.reference_number,
        user,
    )


@transaction.atomic
def force_release_checkout(user, checkout: DocumentCheckout) -> None:
    """Admin force-release of a document checkout.

    Marks the checkout as FORCE_RELEASED and records the audit event.
    """
    _require_permission(user, DocumentPermissions.CANCEL_CHECKOUT)

    if checkout.status != CheckoutStatus.ACTIVE:
        raise DocumentCheckoutError(
            _("This checkout is not active and cannot be force-released.")
        )

    checkout.status = CheckoutStatus.FORCE_RELEASED
    checkout.checked_in_at = timezone.now()
    checkout.cancelled_by = user
    checkout.save(update_fields=["status", "checked_in_at", "cancelled_by", "updated_at"])

    _record_audit(
        "DocumentCheckout",
        checkout.pk,
        AuditAction.CHECKOUT_CANCELLED,
        user,
        notes="Checkout force-released by administrator.",
    )

    logger.info(
        "Force-released checkout for %s by %s",
        checkout.document.reference_number,
        user,
    )


# ---------------------------------------------------------------------------
# Workflow — Submit, Review, Approve
# ---------------------------------------------------------------------------


@transaction.atomic
def submit_for_review(user, document: Document) -> Document:
    """Submit a document for review.

    Validates that the current status is DRAFT, UPLOADED, or
    RETURNED_FOR_CORRECTION.  Transitions status to PENDING_REVIEW and
    approval_status to PENDING_REVIEW.
    """
    _require_permission(user, DocumentPermissions.SUBMIT)

    allowed_statuses = {
        DocumentStatus.DRAFT,
        DocumentStatus.UPLOADED,
        DocumentStatus.RETURNED_FOR_CORRECTION,
    }
    if document.status not in allowed_statuses:
        raise DocumentWorkflowError(
            _("Document in status '%(status)s' cannot be submitted for review.")
            % {"status": document.status}
        )

    from_data = _build_audit_snapshot(document)
    old_status = document.status

    document.status = DocumentStatus.PENDING_REVIEW
    document.approval_status = "PENDING_REVIEW"
    document.updated_by = user
    document.save(update_fields=["status", "approval_status", "updated_by", "updated_at"])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.SUBMITTED_FOR_REVIEW,
        user,
        from_data=from_data,
        to_data=_build_audit_snapshot(document),
        notes="Document submitted for review.",
    )
    _record_timeline(
        document,
        TimelineEventType.REVIEWED,
        user,
        previous_status=old_status,
        new_status=DocumentStatus.PENDING_REVIEW,
        comments="Document submitted for review.",
    )

    logger.info("Submitted %s for review by %s", document.reference_number, user)
    return document


@transaction.atomic
def review_document(
    user,
    document: Document,
    approve: bool = True,
    comments: str = "",
) -> Document:
    """Review a document, either approving or returning it for correction.

    Validates that the current status is PENDING_REVIEW or UNDER_REVIEW.
    If approving, transitions to PENDING_APPROVAL.
    If rejecting, transitions to RETURNED_FOR_CORRECTION.
    """
    _require_permission(user, DocumentPermissions.REVIEW)

    allowed_statuses = {
        DocumentStatus.PENDING_REVIEW,
        DocumentStatus.UNDER_REVIEW,
    }
    if document.status not in allowed_statuses:
        raise DocumentWorkflowError(
            _("Document in status '%(status)s' cannot be reviewed.")
            % {"status": document.status}
        )

    from_data = _build_audit_snapshot(document)
    old_status = document.status

    if approve:
        document.status = DocumentStatus.PENDING_APPROVAL
        document.approval_status = "PENDING_APPROVAL"
        action = AuditAction.APPROVED
        notes = comments or "Document reviewed and forwarded for approval."
    else:
        document.status = DocumentStatus.RETURNED_FOR_CORRECTION
        document.approval_status = "RETURNED"
        action = AuditAction.RETURNED
        notes = comments or "Document returned for correction."

    document.updated_by = user
    document.save(update_fields=["status", "approval_status", "updated_by", "updated_at"])

    _record_audit(
        "Document",
        document.pk,
        action,
        user,
        from_data=from_data,
        to_data=_build_audit_snapshot(document),
        notes=notes,
    )
    event_type = TimelineEventType.APPROVED if approve else TimelineEventType.RETURNED
    _record_timeline(
        document,
        event_type,
        user,
        previous_status=old_status,
        new_status=document.status,
        comments=notes,
    )

    logger.info(
        "Reviewed %s (%s) by %s",
        document.reference_number,
        "approved" if approve else "returned",
        user,
    )
    return document


@transaction.atomic
def approve_document(
    user,
    document: Document,
    comments: str = "",
) -> Document:
    """Approve a document pending approval.

    Validates that the current status is PENDING_APPROVAL.  Sets status to
    APPROVED, approval_status to APPROVED, and records approved_by and
    approved_at.
    """
    _require_permission(user, DocumentPermissions.APPROVE)

    if document.status != DocumentStatus.PENDING_APPROVAL:
        raise DocumentApprovalError(
            _("Document in status '%(status)s' cannot be approved.")
            % {"status": document.status}
        )

    from_data = _build_audit_snapshot(document)
    old_status = document.status

    now = timezone.now()
    document.status = DocumentStatus.APPROVED
    document.approval_status = "APPROVED"
    document.approved_by = user
    document.approved_at = now
    document.updated_by = user
    document.save(update_fields=[
        "status",
        "approval_status",
        "approved_by",
        "approved_at",
        "updated_by",
        "updated_at",
    ])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.APPROVED,
        user,
        from_data=from_data,
        to_data=_build_audit_snapshot(document),
        notes=comments or "Document approved.",
    )
    _record_timeline(
        document,
        TimelineEventType.APPROVED,
        user,
        previous_status=old_status,
        new_status=DocumentStatus.APPROVED,
        comments=comments or "Document approved.",
    )

    logger.info("Approved %s by %s", document.reference_number, user)
    return document


# ---------------------------------------------------------------------------
# Publication
# ---------------------------------------------------------------------------


@transaction.atomic
def publish_document(user, document: Document) -> Document:
    """Publish an approved document.

    Validates that the current status is APPROVED.  Sets status to
    PUBLISHED, publication_status to PUBLISHED, and records published_by
    and published_at.
    """
    _require_permission(user, DocumentPermissions.PUBLISH)

    if document.status != DocumentStatus.APPROVED:
        raise DocumentPublicationError(
            _("Document in status '%(status)s' cannot be published.")
            % {"status": document.status}
        )

    from_data = _build_audit_snapshot(document)
    old_status = document.status

    now = timezone.now()
    document.status = DocumentStatus.PUBLISHED
    document.publication_status = PublicationStatus.PUBLISHED
    document.published_by = user
    document.published_at = now
    document.updated_by = user
    document.save(update_fields=[
        "status",
        "publication_status",
        "published_by",
        "published_at",
        "updated_by",
        "updated_at",
    ])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.PUBLISHED,
        user,
        from_data=from_data,
        to_data=_build_audit_snapshot(document),
        notes="Document published.",
    )
    _record_timeline(
        document,
        TimelineEventType.PUBLISHED,
        user,
        previous_status=old_status,
        new_status=DocumentStatus.PUBLISHED,
        comments="Document published.",
    )

    logger.info("Published %s by %s", document.reference_number, user)
    return document


@transaction.atomic
def unpublish_document(user, document: Document) -> Document:
    """Unpublish a published document.

    Validates that the current status is PUBLISHED.  Sets status back to
    APPROVED and publication_status to NOT_PUBLISHED.
    """
    _require_permission(user, DocumentPermissions.UNPUBLISH)

    if document.status != DocumentStatus.PUBLISHED:
        raise DocumentPublicationError(
            _("Document in status '%(status)s' cannot be unpublished.")
            % {"status": document.status}
        )

    from_data = _build_audit_snapshot(document)
    old_status = document.status

    document.status = DocumentStatus.APPROVED
    document.publication_status = PublicationStatus.NOT_PUBLISHED
    document.updated_by = user
    document.save(update_fields=[
        "status",
        "publication_status",
        "updated_by",
        "updated_at",
    ])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.UNPUBLISHED,
        user,
        from_data=from_data,
        to_data=_build_audit_snapshot(document),
        notes="Document unpublished.",
    )
    _record_timeline(
        document,
        TimelineEventType.RETURNED,
        user,
        previous_status=old_status,
        new_status=DocumentStatus.APPROVED,
        comments="Document unpublished.",
    )

    logger.info("Unpublished %s by %s", document.reference_number, user)
    return document


# ---------------------------------------------------------------------------
# Archival & Restoration
# ---------------------------------------------------------------------------


@transaction.atomic
def archive_document(user, document: Document, reason: str = "") -> Document:
    """Archive a document.

    Validates that the document is not under legal or safeguarding hold.
    Sets status to ARCHIVED and records archived_at.
    """
    _require_permission(user, DocumentPermissions.ARCHIVE)

    if document.legal_hold or document.safeguarding_hold:
        raise DocumentArchiveError(
            _("Cannot archive a document under legal or safeguarding hold.")
        )

    if document.status == DocumentStatus.ARCHIVED:
        raise DocumentArchiveError(_("Document is already archived."))

    from_data = _build_audit_snapshot(document)
    old_status = document.status

    now = timezone.now()
    document.status = DocumentStatus.ARCHIVED
    document.archived_at = now
    document.is_archived = True
    document.updated_by = user
    document.save(update_fields=[
        "status",
        "archived_at",
        "is_archived",
        "updated_by",
        "updated_at",
    ])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.ARCHIVED,
        user,
        from_data=from_data,
        to_data=_build_audit_snapshot(document),
        notes=reason or "Document archived.",
    )
    _record_timeline(
        document,
        TimelineEventType.ARCHIVED,
        user,
        previous_status=old_status,
        new_status=DocumentStatus.ARCHIVED,
        comments=reason or "Document archived.",
    )

    logger.info("Archived %s by %s", document.reference_number, user)
    return document


@transaction.atomic
def restore_document(user, document: Document, reason: str = "") -> Document:
    """Restore an archived document to its previous active status.

    Validates that the document is currently ARCHIVED.  Sets status to
    PUBLISHED if it was previously published, otherwise to DRAFT.  Clears
    archived_at.
    """
    _require_permission(user, DocumentPermissions.RESTORE)

    if document.status != DocumentStatus.ARCHIVED:
        raise DocumentArchiveError(
            _("Document in status '%(status)s' is not archived.")
            % {"status": document.status}
        )

    from_data = _build_audit_snapshot(document)

    if document.published_at:
        new_status = DocumentStatus.PUBLISHED
        document.publication_status = PublicationStatus.PUBLISHED
    else:
        new_status = DocumentStatus.DRAFT
        document.publication_status = PublicationStatus.NOT_PUBLISHED

    document.status = new_status
    document.archived_at = None
    document.is_archived = False
    document.updated_by = user
    document.save(update_fields=[
        "status",
        "publication_status",
        "archived_at",
        "is_archived",
        "updated_by",
        "updated_at",
    ])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.RESTORED,
        user,
        from_data=from_data,
        to_data=_build_audit_snapshot(document),
        notes=reason or "Document restored from archive.",
    )
    _record_timeline(
        document,
        TimelineEventType.RESTORED,
        user,
        previous_status=DocumentStatus.ARCHIVED,
        new_status=new_status,
        comments=reason or "Document restored from archive.",
    )

    logger.info("Restored %s by %s", document.reference_number, user)
    return document


# ---------------------------------------------------------------------------
# Sharing
# ---------------------------------------------------------------------------


@transaction.atomic
def share_document(
    user,
    document: Document,
    shared_with_user,
    permission_level: str = "VIEW",
    download_allowed: bool = False,
    print_allowed: bool = False,
    expiry_date=None,
) -> DocumentShare:
    """Share a document with another user.

    Validates permission, creates a ``DocumentShare``, and records audit
    and timeline events.
    """
    _require_permission(user, DocumentPermissions.SHARE_INTERNAL)

    if document.confidentiality_level in {
        ConfidentialityLevel.CONFIDENTIAL,
        ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
        ConfidentialityLevel.BOARD,
        ConfidentialityLevel.EXECUTIVE,
    }:
        _require_permission(user, DocumentPermissions.SHARE_EXTERNAL)

    share = DocumentShare(
        document=document,
        shared_with_user=shared_with_user,
        shared_by=user,
        permission_level=permission_level,
        download_allowed=download_allowed,
        print_allowed=print_allowed,
        expiry_date=expiry_date,
        is_active=True,
        created_by=user,
    )
    share.full_clean()
    share.save()

    _record_audit(
        "DocumentShare",
        share.pk,
        AuditAction.SHARED,
        user,
        to_data={
            "document": document.reference_number,
            "shared_with": str(shared_with_user),
            "permission_level": permission_level,
        },
        notes="Document shared.",
    )
    _record_timeline(
        document,
        TimelineEventType.SHARED,
        user,
        comments=f"Document shared with {shared_with_user}.",
    )

    logger.info(
        "Shared %s with %s by %s",
        document.reference_number,
        shared_with_user,
        user,
    )
    return share


@transaction.atomic
def revoke_share(user, share: DocumentShare) -> None:
    """Revoke an active document share.

    Validates that the user has permission (the original granter or an
    administrator).  Sets is_active=False and records revoked_at and
    revoked_by.
    """
    if share.created_by_id != user.pk:
        _require_permission(user, DocumentPermissions.SHARE_INTERNAL)

    if not share.is_active:
        raise DocumentShareError(_("This share is already revoked."))

    share.is_active = False
    share.revoked_at = timezone.now()
    share.revoked_by = user
    share.save(update_fields=["is_active", "revoked_at", "revoked_by", "updated_at"])

    _record_audit(
        "DocumentShare",
        share.pk,
        AuditAction.SHARE_REVOKED,
        user,
        notes="Document share revoked.",
    )

    logger.info(
        "Revoked share for %s by %s",
        share.document.reference_number,
        user,
    )


# ---------------------------------------------------------------------------
# Holds
# ---------------------------------------------------------------------------


@transaction.atomic
def apply_hold(
    user,
    document: Document,
    hold_type: str,
    reason: str,
    review_date=None,
    restricted_notes: str = "",
) -> DocumentHold:
    """Apply a legal, safeguarding, or other hold on a document.

    Creates a ``DocumentHold`` and sets the corresponding hold flag on the
    document.  Records audit and timeline events.
    """
    _require_permission(user, DocumentPermissions.ARCHIVE)

    if hold_type not in HoldType.values:
        raise ValidationError(_("Invalid hold type: %(type)s") % {"type": hold_type})

    hold = DocumentHold(
        document=document,
        hold_type=hold_type,
        reason=reason,
        applied_by=user,
        review_date=review_date,
        restricted_notes=restricted_notes,
        status=HoldStatus.ACTIVE,
        created_by=user,
    )
    hold.full_clean()
    hold.save()

    if hold_type == HoldType.LEGAL:
        document.legal_hold = True
    elif hold_type == HoldType.SAFEGUARDING:
        document.safeguarding_hold = True
    else:
        document.legal_hold = True
    document.updated_by = user
    document.save(update_fields=["legal_hold", "safeguarding_hold", "updated_by", "updated_at"])

    _record_audit(
        "DocumentHold",
        hold.pk,
        AuditAction.HOLD_APPLIED,
        user,
        to_data={
            "document": document.reference_number,
            "hold_type": hold_type,
            "reason": reason,
        },
        notes=f"{hold_type} hold applied.",
    )
    _record_timeline(
        document,
        TimelineEventType.HOLD_APPLIED,
        user,
        comments=f"{hold_type} hold applied: {reason}",
    )

    logger.info(
        "Applied %s hold on %s by %s",
        hold_type,
        document.reference_number,
        user,
    )
    return hold


@transaction.atomic
def release_hold(user, hold: DocumentHold, reason: str = "") -> None:
    """Release a document hold.

    Validates that the user has permission.  Sets hold status to RELEASED
    and clears the corresponding hold flag on the document if no other
    active holds remain.
    """
    _require_permission(user, DocumentPermissions.ARCHIVE)

    if hold.status != HoldStatus.ACTIVE:
        raise DocumentHoldError(_("This hold is already released."))

    hold.status = HoldStatus.RELEASED
    hold.released_by = user
    hold.released_at = timezone.now()
    hold.save(update_fields=["status", "released_by", "released_at", "updated_at"])

    document = hold.document
    other_active_holds = document.holds.filter(
        status=HoldStatus.ACTIVE,
    ).exclude(pk=hold.pk)

    has_other_legal = other_active_holds.filter(
        hold_type__in={HoldType.LEGAL, HoldType.REGULATORY, HoldType.INVESTIGATION, HoldType.OTHER},
    ).exists()
    has_other_safeguarding = other_active_holds.filter(
        hold_type=HoldType.SAFEGUARDING,
    ).exists()

    updates = ["updated_by", "updated_at"]
    if not has_other_legal:
        document.legal_hold = False
        updates.append("legal_hold")
    if not has_other_safeguarding:
        document.safeguarding_hold = False
        updates.append("safeguarding_hold")

    document.updated_by = user
    document.save(update_fields=updates)

    _record_audit(
        "DocumentHold",
        hold.pk,
        AuditAction.HOLD_RELEASED,
        user,
        notes=reason or f"{hold.hold_type} hold released.",
    )
    _record_timeline(
        document,
        TimelineEventType.HOLD_RELEASED,
        user,
        comments=reason or f"{hold.hold_type} hold released.",
    )

    logger.info(
        "Released %s hold on %s by %s",
        hold.hold_type,
        document.reference_number,
        user,
    )


# ---------------------------------------------------------------------------
# Disposal
# ---------------------------------------------------------------------------


@transaction.atomic
def request_disposal(
    user,
    document: Document,
    disposal_reason: str = "",
) -> DocumentDisposalRequest:
    """Request disposal of a document at end of retention.

    Validates that no active holds exist and that the retention period has
    elapsed.  Creates a ``DocumentDisposalRequest`` and records the audit.
    """
    _require_permission(user, DocumentPermissions.REQUEST_DISPOSAL)

    if document.legal_hold or document.safeguarding_hold:
        raise DocumentDisposalError(
            _("Cannot request disposal for a document under hold.")
        )

    if document.status in (DocumentStatus.DISPOSED, DocumentStatus.DISPOSAL_PENDING):
        raise DocumentDisposalError(
            _("Document is already pending disposal or has been disposed.")
        )

    retention_category = document.retention_category
    if not retention_category:
        raise DocumentDisposalError(
            _("Document has no retention category assigned.")
        )

    if retention_category.retention_period_days is not None:
        trigger_date = document.created_at.date() if hasattr(document.created_at, "date") else timezone.localdate()
        retention_end = trigger_date + timedelta(days=retention_category.retention_period_days)
        if timezone.localdate() < retention_end:
            raise DocumentDisposalError(
                _("Retention period has not yet elapsed. Retention ends: %(date)s.")
                % {"date": retention_end.isoformat()}
            )
        retention_end_date = retention_end
    else:
        retention_end_date = timezone.localdate()

    disposal_request = DocumentDisposalRequest(
        document=document,
        retention_category=retention_category,
        retention_end_date=retention_end_date,
        disposal_reason=disposal_reason,
        requested_by=user,
        has_legal_hold=document.legal_hold,
        has_safeguarding_hold=document.safeguarding_hold,
        status=DisposalStatus.REQUESTED,
        created_by=user,
    )
    disposal_request.full_clean()
    disposal_request.save()

    document.status = DocumentStatus.DISPOSAL_PENDING
    document.updated_by = user
    document.save(update_fields=["status", "updated_by", "updated_at"])

    _record_audit(
        "DocumentDisposalRequest",
        disposal_request.pk,
        AuditAction.DISPOSAL_REQUESTED,
        user,
        to_data={
            "document": document.reference_number,
            "disposal_reason": disposal_reason,
        },
        notes="Disposal requested.",
    )

    logger.info(
        "Disposal requested for %s by %s",
        document.reference_number,
        user,
    )
    return disposal_request


@transaction.atomic
def approve_disposal(
    user,
    disposal_request: DocumentDisposalRequest,
) -> DocumentDisposalRequest:
    """Approve a disposal request.

    Validates that the user has permission.  Sets status to APPROVED and
    records the audit event.
    """
    _require_permission(user, DocumentPermissions.APPROVE_DISPOSAL)

    if disposal_request.status != DisposalStatus.REQUESTED:
        raise DocumentDisposalError(
            _("Only requested disposals can be approved.")
        )

    disposal_request.status = DisposalStatus.APPROVED
    disposal_request.approved_by = user
    disposal_request.updated_by = user
    disposal_request.save(update_fields=["status", "approved_by", "updated_by", "updated_at"])

    _record_audit(
        "DocumentDisposalRequest",
        disposal_request.pk,
        AuditAction.DISPOSAL_APPROVED,
        user,
        notes="Disposal request approved.",
    )

    logger.info(
        "Approved disposal for %s by %s",
        disposal_request.document.reference_number,
        user,
    )
    return disposal_request


@transaction.atomic
def complete_disposal(
    user,
    disposal_request: DocumentDisposalRequest,
    disposal_method: str,
) -> DocumentDisposalRequest:
    """Complete the disposal of a document.

    Sets status to COMPLETED, records disposal_method and disposal_date.
    Sets the document status to DISPOSED.
    """
    if disposal_request.status != DisposalStatus.APPROVED:
        raise DocumentDisposalError(
            _("Only approved disposals can be completed.")
        )

    valid_methods = {m[0] for m in DocumentDisposalRequest._meta.get_field("disposal_method").choices}
    if disposal_method not in valid_methods:
        raise ValidationError(
            _("Invalid disposal method: %(method)s") % {"method": disposal_method}
        )

    now = timezone.now()
    disposal_request.status = DisposalStatus.COMPLETED
    disposal_request.disposal_method = disposal_method
    disposal_request.disposal_date = now.date()
    disposal_request.updated_by = user
    disposal_request.save(update_fields=[
        "status",
        "disposal_method",
        "disposal_date",
        "updated_by",
        "updated_at",
    ])

    document = disposal_request.document
    document.status = DocumentStatus.DISPOSED
    document.updated_by = user
    document.save(update_fields=["status", "updated_by", "updated_at"])

    _record_audit(
        "DocumentDisposalRequest",
        disposal_request.pk,
        AuditAction.DISPOSED,
        user,
        notes=f"Document disposed via {disposal_method}.",
    )
    _record_timeline(
        document,
        TimelineEventType.DISPOSED,
        user,
        previous_status=DocumentStatus.DISPOSAL_PENDING,
        new_status=DocumentStatus.DISPOSED,
        comments=f"Document disposed via {disposal_method}.",
    )

    logger.info(
        "Completed disposal for %s via %s by %s",
        document.reference_number,
        disposal_method,
        user,
    )
    return disposal_request


# ---------------------------------------------------------------------------
# Soft Delete & Restore
# ---------------------------------------------------------------------------


@transaction.atomic
def delete_document(user, document: Document) -> None:
    """Soft-delete a document.

    Sets is_deleted=True, deleted_at, and deleted_by.  Records audit.
    """
    if document.is_deleted:
        raise DocumentManagementError(_("Document is already deleted."))

    document.is_deleted = True
    document.deleted_at = timezone.now()
    document.deleted_by = user
    document.updated_by = user
    document.save(update_fields=[
        "is_deleted",
        "deleted_at",
        "deleted_by",
        "updated_by",
        "updated_at",
    ])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.CREATED,
        user,
        from_data=_build_audit_snapshot(document),
        notes="Document soft-deleted.",
    )

    logger.info("Soft-deleted %s by %s", document.reference_number, user)


@transaction.atomic
def restore_deleted_document(user, document: Document) -> None:
    """Restore a soft-deleted document.

    Clears is_deleted, deleted_at, and deleted_by.  Records audit.
    """
    if not document.is_deleted:
        raise DocumentManagementError(_("Document is not deleted."))

    document.is_deleted = False
    document.deleted_at = None
    document.deleted_by = None
    document.updated_by = user
    document.save(update_fields=[
        "is_deleted",
        "deleted_at",
        "deleted_by",
        "updated_by",
        "updated_at",
    ])

    _record_audit(
        "Document",
        document.pk,
        AuditAction.RESTORED,
        user,
        notes="Soft-deleted document restored.",
    )

    logger.info("Restored deleted %s by %s", document.reference_number, user)


# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------


def _folder_has_descendant(folder: DocumentFolder, target: DocumentFolder) -> bool:
    """Check if ``target`` is a descendant of ``folder``."""
    current = target.parent
    while current is not None:
        if current.pk == folder.pk:
            return True
        current = current.parent
    return False


@transaction.atomic
def create_folder(
    user,
    name: str,
    description: str = "",
    parent: DocumentFolder | None = None,
    confidentiality_level: str = ConfidentialityLevel.INTERNAL,
) -> DocumentFolder:
    """Create a document folder.

    Validates that no circular hierarchy would be created.  Returns the
    created ``DocumentFolder``.
    """
    _require_permission(user, DocumentPermissions.MANAGE_FOLDERS)

    from django.utils.text import slugify

    slug = slugify(name)
    reference_number = _generate_document_reference_number()

    folder = DocumentFolder(
        reference_number=reference_number,
        name=name,
        slug=slug,
        description=description,
        parent=parent,
        confidentiality_level=confidentiality_level,
        is_active=True,
        created_by=user,
        updated_by=user,
    )
    folder.full_clean()
    folder.save()

    logger.info("Created folder '%s' by %s", name, user)
    return folder


@transaction.atomic
def move_folder(folder: DocumentFolder, new_parent: DocumentFolder | None) -> DocumentFolder:
    """Move a folder to a new parent.

    Validates that no circular hierarchy would be created.
    """
    if new_parent is not None:
        if new_parent.pk == folder.pk:
            raise CircularFolderError(_("A folder cannot be its own parent."))
        if _folder_has_descendant(folder, new_parent):
            raise CircularFolderError(
                _("Moving to this parent would create a circular hierarchy.")
            )

    folder.parent = new_parent
    folder.save(update_fields=["parent", "updated_at"])

    logger.info("Moved folder '%s' to parent %s", folder.name, new_parent)
    return folder


# ---------------------------------------------------------------------------
# Categories & Tags
# ---------------------------------------------------------------------------


@transaction.atomic
def create_category(
    user,
    code: str,
    name: str,
    description: str = "",
    parent: DocumentCategory | None = None,
) -> DocumentCategory:
    """Create a document category.

    Returns the created ``DocumentCategory``.
    """
    _require_permission(user, DocumentPermissions.MANAGE_CATEGORIES)

    category = DocumentCategory(
        code=code,
        name=name,
        description=description,
        parent=parent,
        created_by=user,
        is_active=True,
    )
    category.full_clean()
    category.save()

    logger.info("Created category '%s' by %s", name, user)
    return category


@transaction.atomic
def create_document_tag(
    user,
    name: str,
    description: str = "",
    category: DocumentCategory | None = None,
) -> DocumentTag:
    """Create a document tag with auto-slugified name.

    Returns the created ``DocumentTag``.
    """
    _require_permission(user, DocumentPermissions.MANAGE_TAGS)

    from django.utils.text import slugify

    slug = slugify(name)
    tag = DocumentTag(
        name=name,
        slug=slug,
        description=description,
        category=category,
        created_by=user,
        is_active=True,
    )
    tag.full_clean()
    tag.save()

    logger.info("Created tag '%s' by %s", name, user)
    return tag


# ---------------------------------------------------------------------------
# File Retrieval & Integrity
# ---------------------------------------------------------------------------


def get_document_download_path(
    document: Document,
    version: DocumentVersion | None = None,
) -> str:
    """Return the file system path for downloading a document version.

    If ``version`` is None, returns the path of the current version.
    """
    if version is None:
        version = document.versions.filter(is_current=True).first()
    if version is None:
        raise DocumentStorageError(_("No version available for this document."))
    if version.file:
        return version.file.path
    raise DocumentStorageError(_("No file found for version %(version)s.") % {"version": version.version_number})


def verify_document_checksum(
    document: Document,
    version: DocumentVersion | None = None,
) -> bool:
    """Verify file integrity against the stored checksum.

    Returns True if the file's SHA-256 checksum matches, False otherwise.
    """
    if version is None:
        version = document.versions.filter(is_current=True).first()
    if version is None:
        return False

    if not version.file:
        return False

    try:
        file_path = version.file.path
        if not os.path.exists(file_path):
            return False

        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        computed = hasher.hexdigest()
        return computed == version.checksum
    except (OSError, IOError):
        return False
