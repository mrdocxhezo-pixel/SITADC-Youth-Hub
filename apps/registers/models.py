"""Normalized data model for the Phase 23 Organizational Registers module.

The module provides a centralized, secure and configurable register management
system.  Registers and entries follow a documented lifecycle, every entry
carries standardized metadata and a confidentiality level, and all state
changes are captured on an immutable activity timeline.
"""

# ruff: noqa: RUF012 - Django Meta options are declarative class attributes.

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    NotesModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)
from apps.references.models import ReferenceNumberScheme

from .constants import (
    ConfidentialityLevel,
    RegisterActivityAction,
    RegisterApprovalStatus,
    RegisterEntryStatus,
    RegisterStatus,
    RelationshipType,
    RetentionPolicy,
)
from .managers import ActiveRegisterManager, AllRegisterManager
from .storage import private_register_storage


class RegisterRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Common actor and timestamp metadata for register domain rows."""

    class Meta:
        abstract = True


class RegisterCategory(RegisterRecord, SoftDeleteModel, ArchivableModel, NotesModel):
    """
    A configurable register category (e.g. Membership, Volunteer, Assets).

    Categories are the highest-level grouping of organizational registers and
    provide the default numbering prefix, confidentiality and retention policy
    that new registers in the category inherit.
    """

    name = models.CharField(_("Name"), max_length=160)
    code = models.SlugField(_("Code"), max_length=80, unique=True)
    description = models.TextField(_("Description"), blank=True)
    number_prefix = models.CharField(
        _("Number prefix"),
        max_length=10,
        blank=True,
        help_text=_(
            "Prefix used when generating reference numbers for registers in "
            "this category (e.g. MEM for Membership)."
        ),
    )
    default_confidentiality = models.CharField(
        _("Default confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    retention_policy = models.CharField(
        _("Retention policy"),
        max_length=40,
        choices=RetentionPolicy.choices,
        default=RetentionPolicy.PERMANENT,
    )
    retention_years = models.PositiveIntegerField(
        _("Retention years"), null=True, blank=True
    )
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    objects: ClassVar[ActiveRegisterManager] = ActiveRegisterManager()
    all_objects: ClassVar[AllRegisterManager] = AllRegisterManager()

    class Meta:
        verbose_name = _("Register Category")
        verbose_name_plural = _("Register Categories")
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if (
            self.retention_policy
            in (
                RetentionPolicy.FIXED_TERM,
                RetentionPolicy.SCHEDULED_DISPOSAL,
            )
            and not self.retention_years
        ):
            raise ValidationError(
                _("A retention period in years is required for this policy."),
                code="retention_years_required",
            )


class Register(RegisterRecord, SoftDeleteModel, ArchivableModel, NotesModel):
    """
    An official organizational register.

    A register is the authoritative source of truth for its records.  It is
    owned by a designated owner, belongs to a category, follows a numbering
    scheme and defaults the confidentiality and approval behaviour of its
    entries.
    """

    reference_number = models.CharField(
        _("Register ID"), max_length=80, unique=True, db_index=True
    )
    name = models.CharField(_("Register name"), max_length=200)
    code = models.SlugField(_("Register code"), max_length=80, unique=True)
    category = models.ForeignKey(
        RegisterCategory,
        on_delete=models.PROTECT,
        related_name="registers",
        verbose_name=_("Register category"),
    )
    description = models.TextField(_("Description"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_registers",
        verbose_name=_("Register owner"),
    )
    responsible_department = models.CharField(
        _("Responsible department"), max_length=160, blank=True
    )
    numbering_scheme = models.ForeignKey(
        ReferenceNumberScheme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registers",
        verbose_name=_("Numbering scheme"),
        help_text=_(
            "Scheme used to number this register's entries.  Defaults to the "
            "category prefix scheme when left empty."
        ),
    )
    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    approval_required = models.BooleanField(
        _("Approval required"),
        default=True,
        help_text=_("Entries must be approved before they become active."),
    )
    retention_policy = models.CharField(
        _("Retention policy"),
        max_length=40,
        choices=RetentionPolicy.choices,
        default=RetentionPolicy.PERMANENT,
    )
    retention_years = models.PositiveIntegerField(
        _("Retention years"), null=True, blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=RegisterStatus.choices,
        default=RegisterStatus.DRAFT,
        db_index=True,
    )
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    objects: ClassVar[ActiveRegisterManager] = ActiveRegisterManager()
    all_objects: ClassVar[AllRegisterManager] = AllRegisterManager()

    class Meta:
        verbose_name = _("Register")
        verbose_name_plural = _("Registers")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if (
            self.retention_policy
            in (
                RetentionPolicy.FIXED_TERM,
                RetentionPolicy.SCHEDULED_DISPOSAL,
            )
            and not self.retention_years
        ):
            raise ValidationError(
                _("A retention period in years is required for this policy."),
                code="retention_years_required",
            )

    def archive(self, archived_by=None) -> None:
        """Archive the register and mark its status as archived."""
        super().archive(archived_by=archived_by)
        self.status = RegisterStatus.ARCHIVED
        self.save(update_fields=["status"])

    def restore(self) -> None:
        """Restore an archived register back to active use."""
        super().unarchive()
        self.status = RegisterStatus.ACTIVE
        self.save(update_fields=["status"])

    @property
    def entry_count(self) -> int:
        return self.entries.filter(is_deleted=False).count()

    @property
    def active_entry_count(self) -> int:
        return self.entries.filter(is_deleted=False, is_archived=False).count()

    @property
    def is_confidential(self) -> bool:
        return self.confidentiality in (
            ConfidentialityLevel.RESTRICTED,
            ConfidentialityLevel.CONFIDENTIAL,
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
        )


class RegisterTemplate(RegisterRecord, SoftDeleteModel, ArchivableModel, NotesModel):
    """
    A configurable template applied to register entries.

    Templates define the metadata fields, validation rules, numbering rules
    and approval settings that entries in a register must conform to,
    guaranteeing consistency across the register.
    """

    name = models.CharField(_("Name"), max_length=160)
    code = models.SlugField(_("Code"), max_length=80, unique=True)
    register = models.ForeignKey(
        Register,
        on_delete=models.CASCADE,
        related_name="templates",
        verbose_name=_("Register"),
    )
    description = models.TextField(_("Description"), blank=True)
    fields = models.JSONField(
        _("Fields"),
        default=list,
        blank=True,
        help_text=_("List of field definitions: key, label, type, required, options."),
    )
    validation_rules = models.JSONField(_("Validation rules"), default=list, blank=True)
    default_confidentiality = models.CharField(
        _("Default confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    is_default = models.BooleanField(_("Default template"), default=False)
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    objects: ClassVar[ActiveRegisterManager] = ActiveRegisterManager()
    all_objects: ClassVar[AllRegisterManager] = AllRegisterManager()

    class Meta:
        verbose_name = _("Register Template")
        verbose_name_plural = _("Register Templates")
        ordering = ("register", "name")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["register"],
                condition=models.Q(is_default=True),
                name="unique_default_template_per_register",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class RegisterEntry(RegisterRecord, SoftDeleteModel, ArchivableModel, NotesModel):
    """
    An individual record stored in a register.

    Entries carry standardized metadata, a confidentiality level and follow the
    approval workflow defined by their register.  Every change is captured on
    the activity timeline and, where enabled, in a version history.
    """

    reference_number = models.CharField(
        _("Reference Number"), max_length=200, unique=True, db_index=True
    )
    register = models.ForeignKey(
        Register,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name=_("Register"),
    )
    template = models.ForeignKey(
        RegisterTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entries",
        verbose_name=_("Template"),
    )
    title = models.CharField(_("Entry title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="register_entries",
        verbose_name=_("Owner"),
    )
    directorate = models.ForeignKey(
        "organizations.OrganizationUnit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="register_entries",
        verbose_name=_("Directorate"),
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="register_entries",
        verbose_name=_("Program"),
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="register_entries",
        verbose_name=_("Project"),
    )
    reporting_period_start = models.DateField(
        _("Reporting period start"), null=True, blank=True
    )
    reporting_period_end = models.DateField(
        _("Reporting period end"), null=True, blank=True
    )
    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
        db_index=True,
    )
    approval_status = models.CharField(
        _("Approval status"),
        max_length=40,
        choices=RegisterApprovalStatus.choices,
        default=RegisterApprovalStatus.DRAFT,
        db_index=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=RegisterEntryStatus.choices,
        default=RegisterEntryStatus.DRAFT,
        db_index=True,
    )
    field_data = models.JSONField(_("Field data"), default=dict, blank=True)
    tags = models.JSONField(_("Tags"), default=list, blank=True)
    keywords = models.CharField(_("Keywords"), max_length=255, blank=True)
    submitted_at = models.DateTimeField(_("Submitted at"), null=True, blank=True)
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="register_entries_approved",
        verbose_name=_("Approved by"),
    )

    objects: ClassVar[ActiveRegisterManager] = ActiveRegisterManager()
    all_objects: ClassVar[AllRegisterManager] = AllRegisterManager()

    class Meta:
        verbose_name = _("Register Entry")
        verbose_name_plural = _("Register Entries")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if (
            self.reporting_period_start
            and self.reporting_period_end
            and self.reporting_period_end < self.reporting_period_start
        ):
            raise ValidationError(
                _("The reporting period end must be on or after its start."),
                code="invalid_reporting_period",
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_confidential(self) -> bool:
        return self.confidentiality in (
            ConfidentialityLevel.RESTRICTED,
            ConfidentialityLevel.CONFIDENTIAL,
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
        )


class RegisterVersion(RegisterRecord):
    """Read-only snapshot of a register entry at a point in time."""

    entry = models.ForeignKey(
        RegisterEntry,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("Entry"),
    )
    version_number = models.PositiveIntegerField(_("Version number"), default=1)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="register_entry_versions",
        verbose_name=_("Author"),
    )
    change_summary = models.TextField(_("Change summary"), blank=True)
    data_snapshot = models.JSONField(_("Data snapshot"), default=dict, blank=True)
    is_restored = models.BooleanField(_("Restored version"), default=False)

    class Meta:
        verbose_name = _("Register Version")
        verbose_name_plural = _("Register Versions")
        ordering = ("entry", "-version_number")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["entry", "version_number"],
                name="unique_version_per_entry",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.entry.reference_number} v{self.version_number}"

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            _("Register versions are immutable and cannot be deleted."),
            code="immutable_register_version",
        )


class RegisterAttachment(RegisterRecord):
    """A supporting file attached to a register entry."""

    entry = models.ForeignKey(
        RegisterEntry,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Entry"),
    )
    file = models.FileField(
        _("File"),
        upload_to="registers/attachments/%Y/%m/",
        storage=private_register_storage,
    )
    original_filename = models.CharField(_("Original filename"), max_length=255)
    content_type = models.CharField(_("Content type"), max_length=150, blank=True)
    size = models.PositiveBigIntegerField(_("Size (bytes)"), default=0)
    description = models.CharField(_("Description"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Register Attachment")
        verbose_name_plural = _("Register Attachments")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.original_filename


class RegisterRelationship(RegisterRecord):
    """A link between a register entry and a related organizational record."""

    entry = models.ForeignKey(
        RegisterEntry,
        on_delete=models.CASCADE,
        related_name="relationships",
        verbose_name=_("Entry"),
    )
    relationship_type = models.CharField(
        _("Relationship type"),
        max_length=30,
        choices=RelationshipType.choices,
        default=RelationshipType.OTHER,
    )
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        related_name="register_relationships",
    )
    object_id = models.UUIDField(_("Related record ID"))
    related_entry = models.ForeignKey(
        RegisterEntry,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="incoming_relationships",
        verbose_name=_("Related register entry"),
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Register Relationship")
        verbose_name_plural = _("Register Relationships")
        ordering = ("-created_at",)
        indexes: ClassVar[list] = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.entry.reference_number} -> "
            f"{self.get_relationship_type_display()}"
        )


class RegisterReview(RegisterRecord, NotesModel):
    """A review decision recorded against a register entry."""

    entry = models.ForeignKey(
        RegisterEntry,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Entry"),
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="register_reviews_made",
        verbose_name=_("Reviewer"),
    )
    decision = models.CharField(
        _("Decision"),
        max_length=40,
        choices=RegisterApprovalStatus.choices,
    )
    comments = models.TextField(_("Comments"), blank=True)
    reviewed_at = models.DateTimeField(_("Reviewed at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Register Review")
        verbose_name_plural = _("Register Reviews")
        ordering = ("-reviewed_at",)

    def __str__(self) -> str:
        return f"{self.entry.reference_number} - {self.get_decision_display()}"


class RegisterActivity(RegisterRecord):
    """Immutable chronological activity timeline for registers and entries."""

    register = models.ForeignKey(
        Register,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activity",
        verbose_name=_("Register"),
    )
    entry = models.ForeignKey(
        RegisterEntry,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activity",
        verbose_name=_("Entry"),
    )
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=RegisterActivityAction.choices,
        db_index=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="register_activities",
        verbose_name=_("Actor"),
    )
    previous_status = models.CharField(_("Previous status"), max_length=40, blank=True)
    new_status = models.CharField(_("New status"), max_length=40, blank=True)
    comment = models.TextField(_("Comment"), blank=True)

    class Meta:
        verbose_name = _("Register Activity")
        verbose_name_plural = _("Register Activities")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        target = self.entry or self.register
        return f"{target} - {self.get_action_display()}"

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            _("Register activity records are immutable and cannot be deleted."),
            code="immutable_register_activity",
        )


class RegisterValidation(RegisterRecord):
    """Result of a validation rule applied to a register entry."""

    entry = models.ForeignKey(
        RegisterEntry,
        on_delete=models.CASCADE,
        related_name="validations",
        verbose_name=_("Entry"),
    )
    rule_code = models.CharField(_("Rule code"), max_length=80)
    passed = models.BooleanField(_("Passed"), default=False)
    message = models.TextField(_("Message"), blank=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="register_validations",
        verbose_name=_("Checked by"),
    )
    checked_at = models.DateTimeField(_("Checked at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Register Validation")
        verbose_name_plural = _("Register Validations")
        ordering = ("-checked_at",)

    def __str__(self) -> str:
        return f"{self.entry.reference_number} - {self.rule_code}"
