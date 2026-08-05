"""
Data models for the organizational structure module.

The models establish the official hierarchy of the SITADC Youth Organization:
organizational levels and units, directorates, departments, geographical
structures, teams, positions, reporting relationships, appointments, acting
appointments, vacancies, transfers and the immutable organizational audit log.
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
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
from apps.rbac.models import AccessScope

from .constants import (
    ActingAppointmentStatus,
    AppointmentStatus,
    AppointmentType,
    OrganizationAuditAction,
    PositionStatus,
    RenewalStatus,
    TransferStatus,
    UnitStatus,
    UnitType,
    VacancyStatus,
)
from .managers import OrganizationUnitManager, PositionManager

IMMUTABLE_RECORD_MESSAGE = _(
    "This record is an immutable organizational history record and cannot be modified."
)


class OrganizationLevel(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """
    A named layer in the organizational hierarchy (e.g. National, Regional,
    District, Community, Team).
    """

    name = models.CharField(_("Name"), max_length=150)
    code = models.SlugField(_("Code"), max_length=50, unique=True)
    description = models.TextField(_("Description"), blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Organizational Level")
        verbose_name_plural = _("Organizational Levels")
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class PositionClassification(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """A configurable classification for positions (e.g. Senior Management)."""

    name = models.CharField(_("Name"), max_length=150)
    code = models.SlugField(_("Code"), max_length=50, unique=True)
    description = models.TextField(_("Description"), blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Position Classification")
        verbose_name_plural = _("Position Classifications")
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class OrganizationUnit(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    ArchivableModel,
    NotesModel,
):
    """
    A formal section of the organization (board, directorate, department,
    region, district, community, team, programme or project unit).
    """

    identifier = models.CharField(
        _("Identifier"),
        max_length=50,
        unique=True,
        help_text=_("Stable organizational identifier that never changes."),
    )
    name = models.CharField(_("Name"), max_length=150)
    short_name = models.CharField(_("Short name"), max_length=60, blank=True)
    description = models.TextField(_("Description"), blank=True)
    level = models.ForeignKey(
        OrganizationLevel,
        on_delete=models.PROTECT,
        related_name="units",
        verbose_name=_("Organizational level"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent unit"),
        help_text=_("Every unit has at most one parent unit."),
    )
    unit_type = models.CharField(
        _("Unit type"),
        max_length=40,
        choices=UnitType.choices,
        db_index=True,
    )
    unit_head = models.ForeignKey(
        "Position",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_units",
        verbose_name=_("Unit head"),
        help_text=_("The position that heads this unit."),
    )
    office_location = models.CharField(_("Office location"), max_length=200, blank=True)
    contact_email = models.EmailField(_("Contact email"), blank=True)
    contact_phone = models.CharField(_("Contact phone"), max_length=30, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=UnitStatus.choices,
        default=UnitStatus.ACTIVE,
        db_index=True,
    )
    effective_date = models.DateField(_("Effective date"), null=True, blank=True)
    established_date = models.DateField(_("Date established"), null=True, blank=True)
    access_scope = models.ForeignKey(
        AccessScope,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_units",
        verbose_name=_("Access scope"),
        help_text=_("The RBAC access scope this unit maps onto."),
    )

    objects: ClassVar[OrganizationUnitManager] = OrganizationUnitManager()

    class Meta:
        verbose_name = _("Organizational Unit")
        verbose_name_plural = _("Organizational Units")
        ordering = ("name",)
        indexes: ClassVar[list] = [
            models.Index(fields=["status", "unit_type"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if self._state.adding and self.level_id is None and self.parent_id is not None:
            self.level = self.parent.level
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(
                _("A unit cannot be its own parent."), code="self_parent"
            )

    def archive(self, archived_by=None) -> None:
        """Archive the unit and mark its status as archived."""
        super().archive(archived_by=archived_by)
        self.status = UnitStatus.ARCHIVED
        self.save(update_fields=["status"])

    def restore(self) -> None:
        """Restore an archived unit back to an active status."""
        super().unarchive()
        self.status = UnitStatus.ACTIVE
        self.save(update_fields=["status"])

    @property
    def is_vacant_leadership(self) -> bool:
        unit_head = self.unit_head
        return unit_head is None or (
            not unit_head.assignments.filter(status=AppointmentStatus.ACTIVE).exists()
            and not unit_head.acting_appointments.filter(
                status=ActingAppointmentStatus.ACTIVE
            ).exists()
        )

    def get_ancestor_chain(self) -> list[OrganizationUnit]:
        """Return the ancestors from the root down to this unit."""
        chain: list[OrganizationUnit] = []
        current: OrganizationUnit | None = self
        seen: set = set()
        while current is not None and current.pk not in seen:
            chain.append(current)
            seen.add(current.pk)
            current = current.parent
        return list(reversed(chain))


class Position(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    ArchivableModel,
    NotesModel,
):
    """
    An official organizational position, independent of the person occupying it.
    """

    title = models.CharField(_("Title"), max_length=150)
    slug = models.SlugField(_("Slug"), max_length=150, unique=True)
    organizational_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.PROTECT,
        related_name="positions",
        verbose_name=_("Organizational unit"),
    )
    classification = models.ForeignKey(
        PositionClassification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="positions",
        verbose_name=_("Classification"),
    )
    responsibilities = models.TextField(_("Responsibilities"), blank=True)
    required_competencies = models.TextField(_("Required competencies"), blank=True)
    appointment_type = models.CharField(
        _("Appointment type"),
        max_length=30,
        choices=AppointmentType.choices,
        default=AppointmentType.PERMANENT,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=PositionStatus.choices,
        default=PositionStatus.ACTIVE,
        db_index=True,
    )
    effective_date = models.DateField(_("Effective date"), null=True, blank=True)
    is_protected = models.BooleanField(
        _("Protected position"),
        default=False,
        help_text=_(
            "Protected executive positions require elevated authorization to modify."
        ),
    )

    objects: ClassVar[PositionManager] = PositionManager()

    class Meta:
        verbose_name = _("Position")
        verbose_name_plural = _("Positions")
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def archive(self, archived_by=None) -> None:
        """Archive the position and mark its status as archived."""
        super().archive(archived_by=archived_by)
        self.status = PositionStatus.ARCHIVED
        self.save(update_fields=["status"])

    def restore(self) -> None:
        """Restore an archived position back to active duty."""
        super().unarchive()
        self.status = PositionStatus.ACTIVE
        self.save(update_fields=["status"])

    @property
    def primary_supervisor(self) -> Position | None:
        """Return the active primary supervisor, if any."""
        relationship = (
            self.reporting_relationships.filter(is_primary=True, is_active=True)
            .select_related("supervisor")
            .first()
        )
        return relationship.supervisor if relationship else None

    @property
    def supervisor_relationships(self) -> models.QuerySet:
        """Return all active reporting relationships above this position."""
        return self.reporting_relationships.filter(is_active=True).select_related(
            "supervisor"
        )

    @property
    def subordinates(self) -> models.QuerySet[Position]:
        """Return the positions that report to this position."""
        return Position.objects.filter(
            reporting_relationships__supervisor=self,
            reporting_relationships__is_active=True,
        )

    @property
    def is_vacant(self) -> bool:
        """A position is vacant when it has no active appointment."""
        return not self.assignments.filter(status=AppointmentStatus.ACTIVE).exists()

    def get_reporting_chain(self) -> list[Position]:
        """Return the reporting chain from this position up to the root."""
        chain: list[Position] = []
        current: Position | None = self
        seen: set = set()
        while current is not None and current.pk not in seen:
            chain.append(current)
            seen.add(current.pk)
            current = current.primary_supervisor
        return chain


class ReportingRelationship(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """
    A configurable reporting line between two positions.

    The primary relationship identifies the direct supervisor; additional
    active relationships model alternate or matrix reporting lines.
    """

    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="reporting_relationships",
        verbose_name=_("Position"),
    )
    supervisor = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="supervised_relationships",
        verbose_name=_("Supervisor"),
    )
    is_primary = models.BooleanField(_("Primary reporting line"), default=False)
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)
    effective_from = models.DateField(_("Effective from"), default=timezone.localdate)
    effective_to = models.DateField(_("Effective to"), null=True, blank=True)

    class Meta:
        verbose_name = _("Reporting Relationship")
        verbose_name_plural = _("Reporting Relationships")
        ordering = ("position", "-is_primary", "effective_from")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["position", "supervisor"],
                condition=models.Q(is_active=True),
                name="unique_active_reporting_relationship",
            ),
            models.UniqueConstraint(
                fields=["position"],
                condition=models.Q(is_primary=True, is_active=True),
                name="unique_primary_reporting_line_per_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.position.title} reports to {self.supervisor.title}"

    def clean(self) -> None:
        super().clean()
        from .validators import validate_reporting_cycle, validate_reporting_dates

        validate_reporting_dates(self.effective_from, self.effective_to)
        if self.position_id and self.supervisor_id:
            if self.position_id == self.supervisor_id:
                raise ValidationError(
                    _("A position cannot report to itself."), code="self_reporting"
                )
            validate_reporting_cycle(self.position, self.supervisor, exclude_pk=self.pk)


class PositionAssignment(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """
    A formal appointment of a person to a position within an organizational unit.

    Historical assignments are immutable and must never be deleted.
    """

    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="position_assignments",
        verbose_name=_("Person"),
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Position"),
    )
    organizational_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.PROTECT,
        related_name="assignments",
        verbose_name=_("Organizational unit"),
    )
    appointment_date = models.DateField(
        _("Appointment date"), default=timezone.localdate
    )
    effective_date = models.DateField(_("Effective date"), default=timezone.localdate)
    appointment_type = models.CharField(
        _("Appointment type"),
        max_length=30,
        choices=AppointmentType.choices,
        default=AppointmentType.PERMANENT,
        db_index=True,
    )
    term_start = models.DateField(_("Term start"), null=True, blank=True)
    term_end = models.DateField(_("Term end"), null=True, blank=True)
    renewal_eligible = models.BooleanField(_("Renewal eligible"), default=False)
    renewal_status = models.CharField(
        _("Renewal status"),
        max_length=30,
        choices=RenewalStatus.choices,
        default=RenewalStatus.NOT_ELIGIBLE,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.ACTIVE,
        db_index=True,
    )
    appointed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments_made",
        verbose_name=_("Appointed by"),
    )
    supporting_document = models.FileField(
        _("Supporting document"),
        upload_to="organizations/appointments/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Position Assignment")
        verbose_name_plural = _("Position Assignments")
        ordering = ("-effective_date", "-created_at")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["position"],
                condition=models.Q(status=AppointmentStatus.ACTIVE),
                name="unique_active_assignment_per_position",
            ),
            models.UniqueConstraint(
                fields=["person"],
                condition=models.Q(status=AppointmentStatus.ACTIVE),
                name="unique_active_assignment_per_person",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.person} -> {self.position.title}"

    def clean(self) -> None:
        super().clean()
        if self.term_start and self.term_end and self.term_end < self.term_start:
            raise ValidationError(
                _("The term end date must be on or after the term start date."),
                code="invalid_term_dates",
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            _("Historical position assignments cannot be deleted."),
            code="immutable_position_assignment",
        )


class ActingAppointment(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """
    A temporary appointment of a person to act in a position.

    Acting appointments require defined start and end dates and expire
    automatically once the end date passes.
    """

    acting_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="acting_appointments",
        verbose_name=_("Acting officer"),
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="acting_appointments",
        verbose_name=_("Position"),
    )
    original_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="covered_acting_appointments",
        verbose_name=_("Original assignee"),
    )
    effective_from = models.DateField(_("Effective start date"))
    end_date = models.DateField(_("End date"))
    reason = models.TextField(_("Reason"), blank=True)
    approval_authority = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acting_approvals",
        verbose_name=_("Approval authority"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ActingAppointmentStatus.choices,
        default=ActingAppointmentStatus.ACTIVE,
        db_index=True,
    )
    supporting_document = models.FileField(
        _("Supporting document"),
        upload_to="organizations/acting/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Acting Appointment")
        verbose_name_plural = _("Acting Appointments")
        ordering = ("-effective_from", "-created_at")

    def __str__(self) -> str:
        return f"{self.acting_officer} acting for {self.position.title}"

    def clean(self) -> None:
        super().clean()
        if (
            self.effective_from
            and self.end_date
            and self.end_date <= self.effective_from
        ):
            raise ValidationError(
                _("The end date must be after the effective start date."),
                code="invalid_acting_dates",
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            _("Acting appointment records cannot be deleted."),
            code="immutable_acting_appointment",
        )

    @property
    def is_expired(self) -> bool:
        return self.end_date < timezone.localdate()

    def auto_expire(self) -> None:
        """Automatically expire an acting appointment once its end date passes."""
        if self.is_expired and self.status == ActingAppointmentStatus.ACTIVE:
            self.status = ActingAppointmentStatus.EXPIRED
            self.save(update_fields=["status"])


class Vacancy(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel):
    """Tracks a vacant position separately from occupied positions."""

    position = models.OneToOneField(
        Position,
        on_delete=models.CASCADE,
        related_name="vacancy",
        verbose_name=_("Position"),
    )
    organizational_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.PROTECT,
        related_name="vacancies",
        verbose_name=_("Organizational unit"),
    )
    vacancy_reason = models.TextField(_("Vacancy reason"), blank=True)
    date_vacant = models.DateField(_("Date vacant"), default=timezone.localdate)
    recruitment_status = models.CharField(
        _("Recruitment status"),
        max_length=30,
        choices=VacancyStatus.choices,
        default=VacancyStatus.OPEN,
        db_index=True,
    )
    expected_appointment_date = models.DateField(
        _("Expected appointment date"), null=True, blank=True
    )
    acting_appointment = models.ForeignKey(
        ActingAppointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="covering_vacancies",
        verbose_name=_("Acting appointment"),
    )

    class Meta:
        verbose_name = _("Vacancy")
        verbose_name_plural = _("Vacancies")
        ordering = ("-date_vacant", "-created_at")

    def __str__(self) -> str:
        return f"Vacancy: {self.position.title}"

    def clean(self) -> None:
        super().clean()
        if self.recruitment_status == VacancyStatus.FILLED and self.position.is_vacant:
            raise ValidationError(
                _(
                    "A vacancy cannot be marked filled while the position has no "
                    "active appointment."
                ),
                code="vacancy_filled_without_occupant",
            )


class TransferRecord(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """
    A personnel transfer between organizational units and positions.

    Transfer history must remain permanently available for audit purposes.
    """

    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transfer_records",
        verbose_name=_("Person"),
    )
    previous_organizational_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("Previous organizational unit"),
    )
    new_organizational_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("New organizational unit"),
    )
    previous_position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("Previous position"),
    )
    new_position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("New position"),
    )
    effective_date = models.DateField(_("Effective date"))
    reason = models.TextField(_("Transfer reason"), blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Approved by"),
    )
    supporting_document = models.FileField(
        _("Supporting document"),
        upload_to="organizations/transfers/",
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Transfer Record")
        verbose_name_plural = _("Transfer Records")
        ordering = ("-effective_date", "-created_at")

    def __str__(self) -> str:
        return f"Transfer of {self.person} to {self.new_position.title}"

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            _("Transfer records cannot be deleted."),
            code="immutable_transfer_record",
        )


class OrganizationAuditRecord(UUIDModel, TimeStampedModel):
    """Immutable audit trail of every structural organizational change."""

    entity_type = models.CharField(_("Entity type"), max_length=60, db_index=True)
    entity_id = models.CharField(_("Entity ID"), max_length=50, db_index=True)
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=OrganizationAuditAction.choices,
        db_index=True,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_audit_records",
        verbose_name=_("Changed by"),
    )
    from_data = models.JSONField(_("From data"), default=dict, blank=True)
    to_data = models.JSONField(_("To data"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Organization Audit Record")
        verbose_name_plural = _("Organization Audit Records")
        ordering = ("-created_at",)
        indexes: ClassVar[list] = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type} {self.entity_id} - {self.get_action_display()}"

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(
                IMMUTABLE_RECORD_MESSAGE, code="immutable_organization_audit"
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            IMMUTABLE_RECORD_MESSAGE, code="immutable_organization_audit"
        )
