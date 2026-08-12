"""Data models for the Document Management module.

Implements the complete document lifecycle for the SITADC Youth Organization:
categories, types, folders, tags, documents, versioning, checkout, sharing,
relationships, retention, holds, disposal, audit, timeline and settings.

Every primary record carries actor and timestamp metadata and supports
soft deletion and archival where appropriate.  Audit and history records are
immutable — ``save()`` and ``delete()`` raise ``ValidationError`` after
initial creation.
"""

from __future__ import annotations

from typing import ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    IsActiveModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)

from .constants import (
    ApprovalStatus,
    AuditAction,
    CheckoutStatus,
    ConfidentialityLevel,
    DisposalAction,
    DisposalMethod,
    DisposalStatus,
    DocumentStatus,
    HoldStatus,
    HoldType,
    PublicationStatus,
    RelationshipType,
    RetentionTrigger,
    ScanStatus,
    SharePermissionLevel,
    TimelineEventType,
    VersionType,
)
from .managers import DocumentManager

IMMUTABLE_AUDIT_MESSAGE = _(
    "Document audit and history records are immutable and cannot be modified."
)


# ---------------------------------------------------------------------------
# Document Category
# ---------------------------------------------------------------------------


class DocumentCategory(UUIDModel, TimeStampedModel, CreatedByModel, IsActiveModel):
    """A hierarchical category for organising documents."""

    code = models.SlugField(_("Code"), max_length=60, unique=True, db_index=True)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent category"),
    )
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    default_confidentiality = models.CharField(
        _("Default confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    default_retention_days = models.PositiveIntegerField(
        _("Default retention period (days)"),
        null=True,
        blank=True,
        help_text=_("Retention period in days. Null means no default."),
    )
    icon = models.CharField(_("Icon"), max_length=60, blank=True)

    class Meta:
        verbose_name = _("Document Category")
        verbose_name_plural = _("Document Categories")
        ordering = ("sort_order", "name")
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Document Type
# ---------------------------------------------------------------------------


class DocumentType(UUIDModel, TimeStampedModel, CreatedByModel, IsActiveModel):
    """A configuration-driven document type with file constraints."""

    code = models.SlugField(_("Code"), max_length=60, unique=True, db_index=True)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_types",
        verbose_name=_("Category"),
    )
    allowed_extensions = models.JSONField(
        _("Allowed extensions"), default=list, blank=True
    )
    max_file_size = models.PositiveIntegerField(
        _("Max file size (bytes)"), null=True, blank=True
    )
    requires_approval = models.BooleanField(_("Requires approval"), default=False)
    requires_versioning = models.BooleanField(_("Requires versioning"), default=True)
    default_confidentiality = models.CharField(
        _("Default confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    default_retention_days = models.PositiveIntegerField(
        _("Default retention period (days)"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("Document Type")
        verbose_name_plural = _("Document Types")
        ordering = ("name",)
        indexes = [
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Document Folder
# ---------------------------------------------------------------------------


class DocumentFolder(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
):
    """A soft-deletable folder for organising documents in a tree structure."""

    reference_number = models.CharField(
        _("Reference number"), max_length=100, unique=True, db_index=True
    )
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent folder"),
    )
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Document Folder")
        verbose_name_plural = _("Document Folders")
        ordering = ("sort_order", "name")
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} — {self.name}"


# ---------------------------------------------------------------------------
# Document Tag
# ---------------------------------------------------------------------------


class DocumentTag(UUIDModel, TimeStampedModel, CreatedByModel, IsActiveModel):
    """A tag for labelling and filtering documents."""

    name = models.CharField(_("Name"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tags",
        verbose_name=_("Category"),
    )

    class Meta:
        verbose_name = _("Document Tag")
        verbose_name_plural = _("Document Tags")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------


class Document(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    ArchivableModel,
):
    """The primary document record supporting full lifecycle management."""

    objects = DocumentManager()

    reference_number = models.CharField(
        _("Reference number"), max_length=200, unique=True, db_index=True
    )
    title = models.CharField(_("Title"), max_length=300)
    short_title = models.CharField(_("Short title"), max_length=150, blank=True)
    description = models.TextField(_("Description"), blank=True)

    # Classification
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("Category"),
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("Document type"),
    )
    folder = models.ForeignKey(
        DocumentFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("Folder"),
    )
    tags = models.ManyToManyField(
        DocumentTag,
        blank=True,
        related_name="documents",
        verbose_name=_("Tags"),
    )

    # File information
    file = models.FileField(_("File"), upload_to="documents/files/")
    original_filename = models.CharField(
        _("Original filename"), max_length=255
    )
    stored_filename = models.CharField(
        _("Stored filename"), max_length=255
    )
    file_extension = models.CharField(_("File extension"), max_length=10)
    mime_type = models.CharField(_("MIME type"), max_length=255)
    file_size = models.PositiveBigIntegerField(_("File size (bytes)"))
    checksum = models.CharField(
        _("Checksum"), max_length=64, help_text=_("SHA-256 hex digest")
    )

    # Versioning
    current_version_number = models.PositiveIntegerField(
        _("Current version number"), default=1
    )

    # Workflow
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=DocumentStatus.choices,
        default=DocumentStatus.DRAFT,
        db_index=True,
    )
    approval_status = models.CharField(
        _("Approval status"),
        max_length=30,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_SUBMITTED,
        db_index=True,
    )
    publication_status = models.CharField(
        _("Publication status"),
        max_length=30,
        choices=PublicationStatus.choices,
        default=PublicationStatus.NOT_PUBLISHED,
        db_index=True,
    )

    # Confidentiality
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
        db_index=True,
    )
    is_sensitive = models.BooleanField(_("Is sensitive"), default=False)

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_documents",
        verbose_name=_("Owner"),
    )
    responsible_unit = models.CharField(
        _("Responsible unit"), max_length=200, blank=True
    )

    # Cross-module links
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_documents",
        verbose_name=_("Program"),
    )
    stakeholder = models.ForeignKey(
        "stakeholders.Stakeholder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_documents",
        verbose_name=_("Stakeholder"),
    )
    report = models.ForeignKey(
        "reports.ReportTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("Report"),
    )

    # Dates
    effective_date = models.DateField(
        _("Effective date"), null=True, blank=True
    )
    expiry_date = models.DateField(
        _("Expiry date"), null=True, blank=True
    )
    review_date = models.DateField(
        _("Review date"), null=True, blank=True
    )
    renewal_date = models.DateField(
        _("Renewal date"), null=True, blank=True
    )

    # Retention
    retention_category = models.ForeignKey(
        "RetentionCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("Retention category"),
    )
    retention_end_date = models.DateField(
        _("Retention end date"), null=True, blank=True
    )

    # Holds
    legal_hold = models.BooleanField(_("Legal hold"), default=False)
    safeguarding_hold = models.BooleanField(_("Safeguarding hold"), default=False)

    # Access restrictions
    download_restricted = models.BooleanField(
        _("Download restricted"), default=False
    )
    print_restricted = models.BooleanField(
        _("Print restricted"), default=False
    )
    external_sharing_restricted = models.BooleanField(
        _("External sharing restricted"), default=True
    )

    # Approval / publication
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_approved",
        verbose_name=_("Approved by"),
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_published",
        verbose_name=_("Published by"),
    )
    approved_at = models.DateTimeField(
        _("Approved at"), null=True, blank=True
    )
    published_at = models.DateTimeField(
        _("Published at"), null=True, blank=True
    )
    archived_at = models.DateTimeField(
        _("Archived at"), null=True, blank=True
    )

    # Metadata
    keywords = models.JSONField(
        _("Keywords"), default=list, blank=True
    )
    metadata_snapshot = models.JSONField(
        _("Metadata snapshot"), default=dict, blank=True
    )

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["reference_number"], name="doc_ref_number_idx"),
            models.Index(fields=["title"], name="doc_title_idx"),
            models.Index(fields=["category"], name="doc_category_idx"),
            models.Index(fields=["document_type"], name="doc_type_idx"),
            models.Index(fields=["folder"], name="doc_folder_idx"),
            models.Index(fields=["status"], name="doc_status_idx"),
            models.Index(fields=["approval_status"], name="doc_approval_status_idx"),
            models.Index(
                fields=["publication_status"], name="doc_pub_status_idx"
            ),
            models.Index(
                fields=["confidentiality_level"], name="doc_conf_level_idx"
            ),
            models.Index(fields=["owner"], name="doc_owner_idx"),
            models.Index(fields=["effective_date"], name="doc_eff_date_idx"),
            models.Index(fields=["expiry_date"], name="doc_exp_date_idx"),
            models.Index(fields=["checksum"], name="doc_checksum_idx"),
            models.Index(fields=["created_at"], name="doc_created_at_idx"),
            models.Index(fields=["updated_at"], name="doc_updated_at_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["reference_number"],
                name="document_reference_number_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} — {self.title}"


# ---------------------------------------------------------------------------
# Document Version
# ---------------------------------------------------------------------------


class DocumentVersion(UUIDModel, TimeStampedModel, CreatedByModel):
    """An immutable version snapshot for a document."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("Document"),
    )
    version_number = models.PositiveIntegerField(_("Version number"))
    version_label = models.CharField(_("Version label"), max_length=50)
    version_type = models.CharField(
        _("Version type"),
        max_length=10,
        choices=VersionType.choices,
        default=VersionType.MAJOR,
    )

    # File information for this version
    file = models.FileField(_("File"), upload_to="documents/versions/")
    original_filename = models.CharField(
        _("Original filename"), max_length=255
    )
    stored_filename = models.CharField(
        _("Stored filename"), max_length=255
    )
    mime_type = models.CharField(_("MIME type"), max_length=255)
    file_size = models.PositiveBigIntegerField(_("File size (bytes)"))
    checksum = models.CharField(
        _("Checksum"), max_length=64, help_text=_("SHA-256 hex digest")
    )

    # Change tracking
    change_summary = models.TextField(_("Change summary"), blank=True)
    change_reason = models.TextField(_("Change reason"), blank=True)

    # Version status
    is_current = models.BooleanField(_("Is current"), default=False, db_index=True)
    approval_status = models.CharField(
        _("Approval status"),
        max_length=30,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_SUBMITTED,
    )
    publication_status = models.CharField(
        _("Publication status"),
        max_length=30,
        choices=PublicationStatus.choices,
        default=PublicationStatus.NOT_PUBLISHED,
    )

    # Dates
    effective_date = models.DateField(
        _("Effective date"), null=True, blank=True
    )
    superseded_date = models.DateField(
        _("Superseded date"), null=True, blank=True
    )

    # Security scan
    scan_status = models.CharField(
        _("Scan status"),
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
    )

    # Metadata
    metadata_snapshot = models.JSONField(
        _("Metadata snapshot"), default=dict, blank=True
    )

    class Meta:
        verbose_name = _("Document Version")
        verbose_name_plural = _("Document Versions")
        ordering = ("-version_number",)
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_number"],
                name="document_version_number_uniq",
            ),
            models.UniqueConstraint(
                fields=["document", "is_current"],
                condition=models.Q(is_current=True),
                name="document_single_current_version",
            ),
        ]
        indexes = [
            models.Index(fields=["document"], name="docver_document_idx"),
            models.Index(fields=["is_current"], name="docver_is_current_idx"),
            models.Index(fields=["version_number"], name="docver_version_num_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.document.reference_number} v{self.version_number}"


# ---------------------------------------------------------------------------
# Document Checkout
# ---------------------------------------------------------------------------


class DocumentCheckout(UUIDModel, TimeStampedModel, CreatedByModel):
    """Tracks document checkout/check-in cycles."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="checkouts",
        verbose_name=_("Document"),
    )
    version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkouts",
        verbose_name=_("Version"),
    )
    checked_out_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_checkouts",
        verbose_name=_("Checked out by"),
    )
    checked_out_at = models.DateTimeField(
        _("Checked out at"), auto_now_add=True
    )
    expected_return_date = models.DateField(
        _("Expected return date"), null=True, blank=True
    )
    checkout_reason = models.TextField(_("Checkout reason"), blank=True)

    # Return status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=CheckoutStatus.choices,
        default=CheckoutStatus.ACTIVE,
        db_index=True,
    )
    checked_in_at = models.DateTimeField(
        _("Checked in at"), null=True, blank=True
    )
    new_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkout_new_version",
        verbose_name=_("New version"),
    )
    cancelled_at = models.DateTimeField(
        _("Cancelled at"), null=True, blank=True
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_checkouts",
        verbose_name=_("Cancelled by"),
    )

    class Meta:
        verbose_name = _("Document Checkout")
        verbose_name_plural = _("Document Checkouts")
        constraints = [
            models.UniqueConstraint(
                fields=["document", "status"],
                condition=models.Q(status=CheckoutStatus.ACTIVE),
                name="document_single_active_checkout",
            ),
        ]
        indexes = [
            models.Index(fields=["document"], name="docck_document_idx"),
            models.Index(fields=["status"], name="docck_status_idx"),
            models.Index(fields=["checked_out_by"], name="docck_checked_out_by_idx"),
        ]

    def __str__(self) -> str:
        return (
            f"Checkout — {self.document.reference_number} "
            f"by {self.checked_out_by} [{self.status}]"
        )


# ---------------------------------------------------------------------------
# Document Share
# ---------------------------------------------------------------------------


class DocumentShare(UUIDModel, TimeStampedModel, CreatedByModel):
    """Tracks document sharing with users or roles."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="shares",
        verbose_name=_("Document"),
    )
    version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shares",
        verbose_name=_("Version"),
    )
    shared_with_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="document_shares_received",
        verbose_name=_("Shared with user"),
    )
    shared_with_role = models.CharField(
        _("Shared with role"), max_length=100, blank=True
    )
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_shares_granted",
        verbose_name=_("Shared by"),
    )
    shared_at = models.DateTimeField(_("Shared at"), auto_now_add=True)
    expiry_date = models.DateField(
        _("Expiry date"), null=True, blank=True
    )

    # Permissions
    permission_level = models.CharField(
        _("Permission level"),
        max_length=20,
        choices=SharePermissionLevel.choices,
        default=SharePermissionLevel.VIEW,
    )
    download_allowed = models.BooleanField(_("Download allowed"), default=False)
    print_allowed = models.BooleanField(_("Print allowed"), default=False)
    reshare_allowed = models.BooleanField(_("Reshare allowed"), default=False)

    # Lifecycle
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)
    revoked_at = models.DateTimeField(
        _("Revoked at"), null=True, blank=True
    )
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_shares_revoked",
        verbose_name=_("Revoked by"),
    )

    class Meta:
        verbose_name = _("Document Share")
        verbose_name_plural = _("Document Shares")
        ordering = ("-shared_at",)
        indexes = [
            models.Index(fields=["document"], name="docshare_document_idx"),
            models.Index(fields=["shared_with_user"], name="docshare_user_idx"),
            models.Index(fields=["shared_by"], name="docshare_shared_by_idx"),
            models.Index(fields=["is_active"], name="docshare_active_idx"),
        ]

    def __str__(self) -> str:
        target = self.shared_with_user or self.shared_with_role or _("—")
        return (
            f"Share — {self.document.reference_number} to {target} "
            f"[{self.permission_level}]"
        )


# ---------------------------------------------------------------------------
# Document Relationship
# ---------------------------------------------------------------------------


class DocumentRelationship(UUIDModel, TimeStampedModel, CreatedByModel):
    """A typed link between two documents."""

    source_document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
        verbose_name=_("Source document"),
    )
    target_document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
        verbose_name=_("Target document"),
    )
    relationship_type = models.CharField(
        _("Relationship type"),
        max_length=30,
        choices=RelationshipType.choices,
        db_index=True,
    )
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Document Relationship")
        verbose_name_plural = _("Document Relationships")
        constraints = [
            models.UniqueConstraint(
                fields=["source_document", "target_document", "relationship_type"],
                name="document_relationship_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["source_document"], name="docrel_source_idx"
            ),
            models.Index(
                fields=["target_document"], name="docrel_target_idx"
            ),
            models.Index(
                fields=["relationship_type"], name="docrel_type_idx"
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.source_document.reference_number} "
            f"--[{self.relationship_type}]--> "
            f"{self.target_document.reference_number}"
        )


# ---------------------------------------------------------------------------
# Retention Category
# ---------------------------------------------------------------------------


class RetentionCategory(UUIDModel, TimeStampedModel, CreatedByModel, IsActiveModel):
    """Configurable retention policy for document classes."""

    code = models.SlugField(_("Code"), max_length=60, unique=True, db_index=True)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    retention_period_days = models.PositiveIntegerField(
        _("Retention period (days)"),
        null=True,
        blank=True,
        help_text=_("Retention period in days. Null means permanent."),
    )
    retention_trigger = models.CharField(
        _("Retention trigger"),
        max_length=30,
        choices=RetentionTrigger.choices,
        default=RetentionTrigger.CREATION,
    )
    disposal_action = models.CharField(
        _("Disposal action"),
        max_length=20,
        choices=DisposalAction.choices,
        default=DisposalAction.NONE,
    )
    supports_legal_hold = models.BooleanField(
        _("Supports legal hold"), default=True
    )
    requires_review = models.BooleanField(_("Requires review"), default=False)
    requires_approval = models.BooleanField(_("Requires approval"), default=False)

    class Meta:
        verbose_name = _("Retention Category")
        verbose_name_plural = _("Retention Categories")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Document Hold
# ---------------------------------------------------------------------------


class DocumentHold(UUIDModel, TimeStampedModel, CreatedByModel):
    """Records a legal, safeguarding or other hold on a document."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="holds",
        verbose_name=_("Document"),
    )
    hold_type = models.CharField(
        _("Hold type"),
        max_length=20,
        choices=HoldType.choices,
        db_index=True,
    )
    reason = models.TextField(_("Reason"))
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applied_holds",
        verbose_name=_("Applied by"),
    )
    applied_at = models.DateTimeField(_("Applied at"), auto_now_add=True)
    review_date = models.DateField(
        _("Review date"), null=True, blank=True
    )
    released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="released_holds",
        verbose_name=_("Released by"),
    )
    released_at = models.DateTimeField(
        _("Released at"), null=True, blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=HoldStatus.choices,
        default=HoldStatus.ACTIVE,
        db_index=True,
    )
    restricted_notes = models.TextField(_("Restricted notes"), blank=True)

    class Meta:
        verbose_name = _("Document Hold")
        verbose_name_plural = _("Document Holds")
        ordering = ("-applied_at",)
        indexes = [
            models.Index(fields=["document"], name="dochold_document_idx"),
            models.Index(fields=["status"], name="dochold_status_idx"),
            models.Index(fields=["hold_type"], name="dochold_type_idx"),
        ]

    def __str__(self) -> str:
        return (
            f"Hold — {self.document.reference_number} "
            f"[{self.hold_type}] ({self.status})"
        )


# ---------------------------------------------------------------------------
# Document Disposal Request
# ---------------------------------------------------------------------------


class DocumentDisposalRequest(UUIDModel, TimeStampedModel, CreatedByModel):
    """Records a request to dispose of a document at end of retention."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="disposal_requests",
        verbose_name=_("Document"),
    )
    retention_category = models.ForeignKey(
        RetentionCategory,
        on_delete=models.CASCADE,
        related_name="disposal_requests",
        verbose_name=_("Retention category"),
    )
    retention_end_date = models.DateField(_("Retention end date"))
    disposal_reason = models.TextField(_("Disposal reason"))
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_disposals",
        verbose_name=_("Requested by"),
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_disposals",
        verbose_name=_("Reviewed by"),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_disposals",
        verbose_name=_("Approved by"),
    )
    has_legal_hold = models.BooleanField(_("Has legal hold"), default=False)
    has_safeguarding_hold = models.BooleanField(
        _("Has safeguarding hold"), default=False
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DisposalStatus.choices,
        default=DisposalStatus.REQUESTED,
        db_index=True,
    )
    disposal_date = models.DateField(
        _("Disposal date"), null=True, blank=True
    )
    disposal_method = models.CharField(
        _("Disposal method"),
        max_length=30,
        choices=DisposalMethod.choices,
        null=True,
        blank=True,
    )
    disposal_certificate_reference = models.CharField(
        _("Disposal certificate reference"), max_length=200, blank=True
    )

    class Meta:
        verbose_name = _("Document Disposal Request")
        verbose_name_plural = _("Document Disposal Requests")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["document"], name="docdisp_document_idx"),
            models.Index(fields=["status"], name="docdisp_status_idx"),
            models.Index(
                fields=["retention_category"], name="docdisp_retcat_idx"
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Disposal — {self.document.reference_number} [{self.status}]"
        )


# ---------------------------------------------------------------------------
# Document Audit Record
# ---------------------------------------------------------------------------


class DocumentAuditRecord(UUIDModel, TimeStampedModel):
    """Immutable audit trail for document management activity."""

    entity_type = models.CharField(_("Entity type"), max_length=100, db_index=True)
    entity_id = models.CharField(_("Entity ID"), max_length=200, db_index=True)
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=AuditAction.choices,
        db_index=True,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_audits",
        verbose_name=_("Changed by"),
    )
    from_data = models.JSONField(_("From data"), default=dict, blank=True)
    to_data = models.JSONField(_("To data"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Document Audit Record")
        verbose_name_plural = _("Document Audit Records")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["entity_type"], name="docaudit_entity_type_idx"),
            models.Index(fields=["entity_id"], name="docaudit_entity_id_idx"),
            models.Index(fields=["action"], name="docaudit_action_idx"),
            models.Index(fields=["changed_by"], name="docaudit_changed_by_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type} {self.entity_id}"

    def save(self, *args, **kwargs) -> NoReturn:
        if not self._state.adding:
            raise ValidationError(IMMUTABLE_AUDIT_MESSAGE, code="immutable_audit")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(IMMUTABLE_AUDIT_MESSAGE, code="immutable_audit")


# ---------------------------------------------------------------------------
# Document Timeline Event
# ---------------------------------------------------------------------------


class DocumentTimelineEvent(UUIDModel, TimeStampedModel):
    """Chronological event in a document's lifecycle."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="timeline_events",
        verbose_name=_("Document"),
    )
    event_type = models.CharField(
        _("Event type"),
        max_length=30,
        choices=TimelineEventType.choices,
        db_index=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_timeline_events",
        verbose_name=_("Actor"),
    )
    previous_status = models.CharField(
        _("Previous status"), max_length=30, blank=True
    )
    new_status = models.CharField(
        _("New status"), max_length=30, blank=True
    )
    comments = models.TextField(_("Comments"), blank=True)
    metadata = models.JSONField(
        _("Metadata"), default=dict, blank=True
    )

    class Meta:
        verbose_name = _("Document Timeline Event")
        verbose_name_plural = _("Document Timeline Events")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["document"], name="doctimeline_document_idx"),
            models.Index(fields=["event_type"], name="doctimeline_event_type_idx"),
            models.Index(fields=["created_at"], name="doctimeline_created_at_idx"),
        ]

    def __str__(self) -> str:
        return (
            f"{self.event_type} — {self.document.reference_number} "
            f"({self.created_at:%Y-%m-%d %H:%M})"
        )


# ---------------------------------------------------------------------------
# Document Settings (singleton)
# ---------------------------------------------------------------------------


class DocumentSettings(UUIDModel, TimeStampedModel):
    """Centralized document management configuration (singleton)."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")
    max_upload_size = models.PositiveBigIntegerField(
        _("Max upload size (bytes)"), default=20 * 1024 * 1024
    )
    allowed_extensions = models.JSONField(
        _("Allowed extensions"), default=list, blank=True
    )
    enable_checkout = models.BooleanField(_("Enable checkout"), default=True)
    enable_versioning = models.BooleanField(_("Enable versioning"), default=True)
    auto_increment_version = models.BooleanField(
        _("Auto-increment version"), default=True
    )
    require_change_summary = models.BooleanField(
        _("Require change summary"), default=False
    )
    default_confidentiality = models.CharField(
        _("Default confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    enable_external_sharing = models.BooleanField(
        _("Enable external sharing"), default=False
    )
    enable_qr_codes = models.BooleanField(_("Enable QR codes"), default=False)
    enable_barcodes = models.BooleanField(_("Enable barcodes"), default=False)
    storage_path_prefix = models.CharField(
        _("Storage path prefix"), max_length=200, default="documents"
    )

    class Meta:
        verbose_name = _("Document Settings")
        verbose_name_plural = _("Document Settings")

    def __str__(self) -> str:
        return "Document Settings"

    @classmethod
    def load(cls) -> DocumentSettings:
        """Return the singleton settings row, creating it if necessary."""
        return cls.objects.get_or_create(key="default")[0]
