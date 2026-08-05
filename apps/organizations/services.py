"""
Business services for the organizational structure module.

Every state-changing organizational operation flows through these services so
that invariants are enforced transactionally and the immutable organizational
audit log records each structural change.
"""

from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission

from . import validators
from .constants import (
    ActingAppointmentStatus,
    AppointmentStatus,
    AppointmentType,
    OrganizationAuditAction,
    PositionStatus,
    TransferStatus,
    UnitStatus,
    VacancyStatus,
)
from .models import (
    ActingAppointment,
    OrganizationAuditRecord,
    OrganizationLevel,
    OrganizationUnit,
    Position,
    PositionAssignment,
    PositionClassification,
    ReportingRelationship,
    TransferRecord,
    Vacancy,
)
from .permissions import ORGANIZATIONS_ASSIGN, ORGANIZATIONS_MANAGE

logger = logging.getLogger(__name__)


def record_organization_audit(
    entity_type: str,
    entity_id,
    action: str,
    changed_by,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> OrganizationAuditRecord:
    """Append an immutable audit record for an organizational change."""
    return OrganizationAuditRecord.objects.create(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        changed_by=changed_by,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


def _require_permission(user, permission_code: str) -> None:
    """Raise PermissionDenied unless the user holds the permission."""
    if not user_has_permission(user, permission_code):
        raise PermissionDenied


def _require_protected_position_access(user, position: Position) -> None:
    """Protected executive positions require elevated manage authorization."""
    if position.is_protected:
        _require_permission(user, ORGANIZATIONS_MANAGE)


class OrganizationLevelService(BaseService):
    """Create an organizational level."""

    def _execute(
        self,
        name: str,
        code: str,
        description: str = "",
        sort_order: int = 0,
    ) -> OrganizationLevel:
        level = OrganizationLevel.objects.create(
            name=name,
            code=code,
            description=description,
            sort_order=sort_order,
            created_by=self.user,
            updated_by=self.user,
        )
        record_organization_audit(
            "OrganizationLevel",
            level.pk,
            OrganizationAuditAction.CREATED,
            self.user,
            to_data={"name": level.name, "code": level.code},
            notes="Organizational level created.",
        )
        logger.info(f"Created organizational level {level.code} by {self.user}")
        return level


class PositionClassificationService(BaseService):
    """Create a position classification."""

    def _execute(
        self,
        name: str,
        code: str,
        description: str = "",
        sort_order: int = 0,
    ) -> PositionClassification:
        classification = PositionClassification.objects.create(
            name=name,
            code=code,
            description=description,
            sort_order=sort_order,
            created_by=self.user,
            updated_by=self.user,
        )
        record_organization_audit(
            "PositionClassification",
            classification.pk,
            OrganizationAuditAction.CREATED,
            self.user,
            to_data={"name": classification.name, "code": classification.code},
            notes="Position classification created.",
        )
        logger.info(
            f"Created position classification {classification.code} by {self.user}"
        )
        return classification


class OrganizationUnitService(BaseService):
    """Manage organizational units and their hierarchy."""

    def _execute(
        self,
        *,
        identifier: str,
        name: str,
        unit_type: str,
        level=None,
        parent=None,
        short_name: str = "",
        description: str = "",
        unit_head=None,
        office_location: str = "",
        contact_email: str = "",
        contact_phone: str = "",
        status: str = UnitStatus.ACTIVE,
        effective_date=None,
        established_date=None,
        access_scope=None,
        notes: str = "",
    ) -> OrganizationUnit:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        unit = OrganizationUnit.objects.create(
            identifier=identifier,
            name=name,
            short_name=short_name,
            description=description,
            level=level,
            parent=parent,
            unit_type=unit_type,
            unit_head=unit_head,
            office_location=office_location,
            contact_email=contact_email,
            contact_phone=contact_phone,
            status=status,
            effective_date=effective_date,
            established_date=established_date,
            access_scope=access_scope,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        validators.validate_unit_hierarchy(parent, unit)
        record_organization_audit(
            "OrganizationUnit",
            unit.pk,
            OrganizationAuditAction.CREATED,
            self.user,
            to_data={"name": unit.name, "identifier": unit.identifier},
            notes="Organizational unit created.",
        )
        logger.info(f"Created organizational unit {unit.identifier} by {self.user}")
        return unit


class UpdateOrganizationUnitService(BaseService):
    """Update organizational unit metadata."""

    def _execute(
        self,
        unit: OrganizationUnit,
        *,
        name: str,
        short_name: str = "",
        description: str = "",
        level=None,
        parent=None,
        unit_head=None,
        office_location: str = "",
        contact_email: str = "",
        contact_phone: str = "",
        effective_date=None,
        established_date=None,
        access_scope=None,
        notes: str = "",
    ) -> OrganizationUnit:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        validators.validate_unit_hierarchy(parent, unit)
        from_data = {
            "name": unit.name,
            "short_name": unit.short_name,
            "parent": unit.parent.name if unit.parent else None,
            "unit_head": unit.unit_head_id,
            "status": unit.status,
        }
        unit.name = name
        unit.short_name = short_name
        unit.description = description
        unit.level = level
        unit.parent = parent
        unit.unit_head = unit_head
        unit.office_location = office_location
        unit.contact_email = contact_email
        unit.contact_phone = contact_phone
        unit.effective_date = effective_date
        unit.established_date = established_date
        unit.access_scope = access_scope
        unit.notes = notes
        unit.updated_by = self.user
        unit.save()
        record_organization_audit(
            "OrganizationUnit",
            unit.pk,
            OrganizationAuditAction.UPDATED,
            self.user,
            from_data=from_data,
            to_data={
                "name": unit.name,
                "short_name": unit.short_name,
                "parent": unit.parent.name if unit.parent else None,
                "unit_head": unit.unit_head_id,
                "status": unit.status,
            },
            notes="Organizational unit updated.",
        )
        logger.info(f"Updated organizational unit {unit.identifier} by {self.user}")
        return unit


class SetOrganizationUnitParentService(BaseService):
    """Change the parent (reporting) of an organizational unit."""

    def _execute(self, unit: OrganizationUnit, parent) -> OrganizationUnit:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        validators.validate_unit_hierarchy(parent, unit)
        from_data = {"parent": unit.parent.name if unit.parent else None}
        unit.parent = parent
        if parent is not None and unit.level_id is None:
            unit.level = parent.level
        unit.updated_by = self.user
        unit.save(update_fields=["parent", "level", "updated_by", "updated_at"])
        record_organization_audit(
            "OrganizationUnit",
            unit.pk,
            OrganizationAuditAction.PARENT_CHANGED,
            self.user,
            from_data=from_data,
            to_data={"parent": parent.name if parent else None},
            notes="Organizational unit parent changed.",
        )
        logger.info(f"Changed parent of {unit.identifier} by {self.user}")
        return unit


class ArchiveOrganizationUnitService(BaseService):
    """Archive an organizational unit."""

    def _execute(self, unit: OrganizationUnit) -> OrganizationUnit:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        if unit.status == UnitStatus.ARCHIVED:
            raise ValidationError(
                _("This unit is already archived."), code="already_archived"
            )
        from_data = {"status": unit.status, "is_archived": unit.is_archived}
        unit.archive(archived_by=self.user)
        record_organization_audit(
            "OrganizationUnit",
            unit.pk,
            OrganizationAuditAction.ARCHIVED,
            self.user,
            from_data=from_data,
            to_data={"status": unit.status, "is_archived": unit.is_archived},
            notes="Organizational unit archived.",
        )
        logger.info(f"Archived organizational unit {unit.identifier} by {self.user}")
        return unit


class RestoreOrganizationUnitService(BaseService):
    """Restore an archived organizational unit."""

    def _execute(self, unit: OrganizationUnit) -> OrganizationUnit:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        if not unit.is_archived:
            raise ValidationError(_("This unit is not archived."), code="not_archived")
        from_data = {"status": unit.status, "is_archived": unit.is_archived}
        unit.restore()
        unit.updated_by = self.user
        unit.save(
            update_fields=[
                "status",
                "is_archived",
                "archived_at",
                "archived_by",
                "updated_by",
                "updated_at",
            ]
        )
        record_organization_audit(
            "OrganizationUnit",
            unit.pk,
            OrganizationAuditAction.RESTORED,
            self.user,
            from_data=from_data,
            to_data={"status": unit.status, "is_archived": unit.is_archived},
            notes="Organizational unit restored.",
        )
        logger.info(f"Restored organizational unit {unit.identifier} by {self.user}")
        return unit


class SetOrganizationUnitStatusService(BaseService):
    """Activate or deactivate an organizational unit."""

    def _execute(self, unit: OrganizationUnit, status: str) -> OrganizationUnit:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        if status not in (UnitStatus.ACTIVE, UnitStatus.INACTIVE):
            raise ValidationError(_("Invalid unit status."), code="invalid_unit_status")
        if unit.status == status:
            raise ValidationError(
                _("The unit already has this status."), code="status_unchanged"
            )
        from_data = {"status": unit.status}
        unit.status = status
        unit.updated_by = self.user
        unit.save(update_fields=["status", "updated_by", "updated_at"])
        action = (
            OrganizationAuditAction.ACTIVATED
            if status == UnitStatus.ACTIVE
            else OrganizationAuditAction.DEACTIVATED
        )
        record_organization_audit(
            "OrganizationUnit",
            unit.pk,
            action,
            self.user,
            from_data=from_data,
            to_data={"status": unit.status},
            notes="Organizational unit status changed.",
        )
        logger.info(f"Set status of {unit.identifier} to {status} by {self.user}")
        return unit


class PositionService(BaseService):
    """Create an organizational position."""

    def _execute(
        self,
        *,
        title: str,
        organizational_unit: OrganizationUnit,
        classification=None,
        responsibilities: str = "",
        required_competencies: str = "",
        appointment_type: str = AppointmentType.PERMANENT,
        effective_date=None,
        is_protected: bool = False,
        notes: str = "",
    ) -> Position:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        slug = slugify(title)
        if Position.objects.filter(slug=slug).exists():
            raise ValidationError(
                _("A position with this title already exists."),
                code="duplicate_position_slug",
            )
        position = Position.objects.create(
            title=title,
            slug=slug,
            organizational_unit=organizational_unit,
            classification=classification,
            responsibilities=responsibilities,
            required_competencies=required_competencies,
            appointment_type=appointment_type,
            status=PositionStatus.ACTIVE,
            effective_date=effective_date,
            is_protected=is_protected,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        record_organization_audit(
            "Position",
            position.pk,
            OrganizationAuditAction.CREATED,
            self.user,
            to_data={"title": position.title, "unit": organizational_unit.name},
            notes="Position created.",
        )
        logger.info(f"Created position {position.slug} by {self.user}")
        return position


class UpdatePositionService(BaseService):
    """Update position metadata."""

    def _execute(
        self,
        position: Position,
        *,
        title: str,
        organizational_unit: OrganizationUnit,
        classification=None,
        responsibilities: str = "",
        required_competencies: str = "",
        appointment_type: str = AppointmentType.PERMANENT,
        effective_date=None,
        notes: str = "",
    ) -> Position:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        _require_protected_position_access(self.user, position)
        from_data = {
            "title": position.title,
            "unit": position.organizational_unit.name,
        }
        position.title = title
        position.slug = slugify(title)
        position.organizational_unit = organizational_unit
        position.classification = classification
        position.responsibilities = responsibilities
        position.required_competencies = required_competencies
        position.appointment_type = appointment_type
        position.effective_date = effective_date
        position.notes = notes
        position.updated_by = self.user
        position.save()
        record_organization_audit(
            "Position",
            position.pk,
            OrganizationAuditAction.UPDATED,
            self.user,
            from_data=from_data,
            to_data={"title": position.title, "unit": organizational_unit.name},
            notes="Position updated.",
        )
        logger.info(f"Updated position {position.slug} by {self.user}")
        return position


class ArchivePositionService(BaseService):
    """Archive a position."""

    def _execute(self, position: Position) -> Position:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        _require_protected_position_access(self.user, position)
        if position.is_archived:
            raise ValidationError(
                _("This position is already archived."), code="already_archived"
            )
        from_data = {"status": position.status, "is_archived": position.is_archived}
        position.archive(archived_by=self.user)
        record_organization_audit(
            "Position",
            position.pk,
            OrganizationAuditAction.ARCHIVED,
            self.user,
            from_data=from_data,
            to_data={"status": position.status, "is_archived": position.is_archived},
            notes="Position archived.",
        )
        logger.info(f"Archived position {position.slug} by {self.user}")
        return position


class RestorePositionService(BaseService):
    """Restore an archived position."""

    def _execute(self, position: Position) -> Position:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        _require_protected_position_access(self.user, position)
        if not position.is_archived:
            raise ValidationError(
                _("This position is not archived."), code="not_archived"
            )
        from_data = {"status": position.status, "is_archived": position.is_archived}
        position.restore()
        position.updated_by = self.user
        position.save(
            update_fields=[
                "status",
                "is_archived",
                "archived_at",
                "archived_by",
                "updated_by",
                "updated_at",
            ]
        )
        record_organization_audit(
            "Position",
            position.pk,
            OrganizationAuditAction.RESTORED,
            self.user,
            from_data=from_data,
            to_data={"status": position.status, "is_archived": position.is_archived},
            notes="Position restored.",
        )
        logger.info(f"Restored position {position.slug} by {self.user}")
        return position


class SetPositionStatusService(BaseService):
    """Activate or deactivate a position."""

    def _execute(self, position: Position, status: str) -> Position:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        _require_protected_position_access(self.user, position)
        if status not in (PositionStatus.ACTIVE, PositionStatus.INACTIVE):
            raise ValidationError(
                _("Invalid position status."), code="invalid_position_status"
            )
        if position.status == status:
            raise ValidationError(
                _("The position already has this status."), code="status_unchanged"
            )
        from_data = {"status": position.status}
        position.status = status
        position.updated_by = self.user
        position.save(update_fields=["status", "updated_by", "updated_at"])
        action = (
            OrganizationAuditAction.ACTIVATED
            if status == PositionStatus.ACTIVE
            else OrganizationAuditAction.DEACTIVATED
        )
        record_organization_audit(
            "Position",
            position.pk,
            action,
            self.user,
            from_data=from_data,
            to_data={"status": position.status},
            notes="Position status changed.",
        )
        logger.info(f"Set status of {position.slug} to {status} by {self.user}")
        return position


class SetReportingLineService(BaseService):
    """Set the primary reporting line for a position."""

    def _execute(self, position: Position, supervisor) -> Position:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        validators.validate_reporting_dates(timezone.localdate(), None)
        if supervisor is not None:
            if position.pk == supervisor.pk:
                raise ValidationError(
                    _("A position cannot report to itself."), code="self_reporting"
                )
            validators.validate_reporting_cycle(position, supervisor)

        previous = position.reporting_relationships.filter(
            is_primary=True, is_active=True
        ).first()
        previous_supervisor = previous.supervisor if previous else None
        if previous:
            previous.is_active = False
            previous.save(update_fields=["is_active"])

        if supervisor is not None:
            ReportingRelationship.objects.create(
                position=position,
                supervisor=supervisor,
                is_primary=True,
                is_active=True,
                effective_from=timezone.localdate(),
                created_by=self.user,
                updated_by=self.user,
            )
        record_organization_audit(
            "Position",
            position.pk,
            OrganizationAuditAction.REPORTING_LINE_CHANGED,
            self.user,
            from_data={
                "primary_supervisor": (
                    previous_supervisor.title if previous_supervisor else None
                )
            },
            to_data={"primary_supervisor": supervisor.title if supervisor else None},
            notes="Primary reporting line changed.",
        )
        logger.info(f"Set reporting line for {position.slug} by {self.user}")
        return position


class AddReportingRelationshipService(BaseService):
    """Add an alternate (non-primary) reporting relationship."""

    def _execute(
        self,
        position: Position,
        supervisor: Position,
        effective_from=None,
        effective_to=None,
    ) -> ReportingRelationship:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        if position.pk == supervisor.pk:
            raise ValidationError(
                _("A position cannot report to itself."), code="self_reporting"
            )
        validators.validate_reporting_dates(
            effective_from or timezone.localdate(), effective_to
        )
        validators.validate_reporting_cycle(position, supervisor)
        relationship = ReportingRelationship.objects.create(
            position=position,
            supervisor=supervisor,
            is_primary=False,
            is_active=True,
            effective_from=effective_from or timezone.localdate(),
            effective_to=effective_to,
            created_by=self.user,
            updated_by=self.user,
        )
        record_organization_audit(
            "Position",
            position.pk,
            OrganizationAuditAction.REPORTING_LINE_CHANGED,
            self.user,
            to_data={"alternate_supervisor": supervisor.title},
            notes="Alternate reporting line added.",
        )
        logger.info(f"Added reporting relationship for {position.slug} by {self.user}")
        return relationship


class AppointmentService(BaseService):
    """Appoint a person to a position."""

    def _execute(
        self,
        *,
        person,
        position: Position,
        organizational_unit: OrganizationUnit,
        appointment_type: str = AppointmentType.PERMANENT,
        appointment_date=None,
        effective_date=None,
        term_start=None,
        term_end=None,
        renewal_eligible: bool = False,
        supporting_document=None,
        notes: str = "",
    ) -> PositionAssignment:
        _require_permission(self.user, ORGANIZATIONS_ASSIGN)
        _require_protected_position_access(self.user, position)
        validators.validate_position_usable(position)
        validators.validate_unit_status_allows_assignments(organizational_unit)
        validators.validate_assignment_unique(position, person)

        assignment = PositionAssignment.objects.create(
            person=person,
            position=position,
            organizational_unit=organizational_unit,
            appointment_date=appointment_date or timezone.localdate(),
            effective_date=effective_date or timezone.localdate(),
            appointment_type=appointment_type,
            term_start=term_start,
            term_end=term_end,
            renewal_eligible=renewal_eligible,
            status=AppointmentStatus.ACTIVE,
            appointed_by=self.user,
            supporting_document=supporting_document,
            notes=notes,
        )

        _close_open_vacancy(position)
        _end_active_acting_appointments(position)
        record_organization_audit(
            "PositionAssignment",
            assignment.pk,
            OrganizationAuditAction.APPOINTED,
            self.user,
            to_data={
                "person": str(person),
                "position": position.title,
                "unit": organizational_unit.name,
            },
            notes="Person appointed to position.",
        )
        logger.info(f"Appointed {person} to {position.slug} by {self.user}")
        return assignment


class EndAppointmentService(BaseService):
    """End an active appointment."""

    def _execute(self, assignment: PositionAssignment) -> PositionAssignment:
        _require_permission(self.user, ORGANIZATIONS_ASSIGN)
        _require_protected_position_access(self.user, assignment.position)
        if assignment.status != AppointmentStatus.ACTIVE:
            raise ValidationError(
                _("This appointment is not active."), code="appointment_not_active"
            )
        assignment.status = AppointmentStatus.ENDED
        assignment.save(update_fields=["status"])
        record_organization_audit(
            "PositionAssignment",
            assignment.pk,
            OrganizationAuditAction.APPOINTMENT_ENDED,
            self.user,
            from_data={"status": AppointmentStatus.ACTIVE},
            to_data={"status": assignment.status},
            notes="Appointment ended.",
        )
        logger.info(f"Ended appointment for {assignment.person} by {self.user}")
        return assignment


class RevokeAppointmentService(BaseService):
    """Revoke an active appointment."""

    def _execute(self, assignment: PositionAssignment) -> PositionAssignment:
        _require_permission(self.user, ORGANIZATIONS_ASSIGN)
        _require_protected_position_access(self.user, assignment.position)
        if assignment.status != AppointmentStatus.ACTIVE:
            raise ValidationError(
                _("This appointment is not active."), code="appointment_not_active"
            )
        assignment.status = AppointmentStatus.REVOKED
        assignment.save(update_fields=["status"])
        record_organization_audit(
            "PositionAssignment",
            assignment.pk,
            OrganizationAuditAction.APPOINTMENT_REVOKED,
            self.user,
            to_data={"status": assignment.status},
            notes="Appointment revoked.",
        )
        logger.info(f"Revoked appointment for {assignment.person} by {self.user}")
        return assignment


class ActingAppointmentService(BaseService):
    """Create a temporary acting appointment."""

    def _execute(
        self,
        *,
        acting_officer,
        position: Position,
        effective_from,
        end_date,
        original_assignee=None,
        reason: str = "",
        approval_authority=None,
        supporting_document=None,
    ) -> ActingAppointment:
        _require_permission(self.user, ORGANIZATIONS_ASSIGN)
        _require_protected_position_access(self.user, position)
        effective_from = validators.coerce_date(effective_from)
        end_date = validators.coerce_date(end_date)
        validators.validate_acting_dates(effective_from, end_date)
        validators.validate_no_overlapping_acting(position)
        if PositionAssignment.objects.filter(
            person=acting_officer,
            position=position,
            status=AppointmentStatus.ACTIVE,
        ).exists():
            raise ValidationError(
                _("The acting officer already holds this position."),
                code="acting_officer_holds_position",
            )
        appointment = ActingAppointment.objects.create(
            acting_officer=acting_officer,
            position=position,
            original_assignee=original_assignee,
            effective_from=effective_from,
            end_date=end_date,
            reason=reason,
            approval_authority=approval_authority,
            status=ActingAppointmentStatus.ACTIVE,
            supporting_document=supporting_document,
            created_by=self.user,
        )
        record_organization_audit(
            "ActingAppointment",
            appointment.pk,
            OrganizationAuditAction.ACTING_APPOINTED,
            self.user,
            to_data={
                "acting_officer": str(acting_officer),
                "position": position.title,
                "end_date": end_date.isoformat(),
            },
            notes="Acting appointment created.",
        )
        logger.info(f"Created acting appointment for {position.slug} by {self.user}")
        return appointment


class EndActingAppointmentService(BaseService):
    """End or revoke an acting appointment."""

    def _execute(
        self, appointment: ActingAppointment, revoke: bool = False
    ) -> ActingAppointment:
        _require_permission(self.user, ORGANIZATIONS_ASSIGN)
        _require_protected_position_access(self.user, appointment.position)
        if appointment.status != ActingAppointmentStatus.ACTIVE:
            raise ValidationError(
                _("This acting appointment is not active."),
                code="acting_not_active",
            )
        appointment.status = (
            ActingAppointmentStatus.REVOKED if revoke else ActingAppointmentStatus.ENDED
        )
        appointment.save(update_fields=["status"])
        action = (
            OrganizationAuditAction.ACTING_ENDED
            if not revoke
            else OrganizationAuditAction.APPOINTMENT_REVOKED
        )
        record_organization_audit(
            "ActingAppointment",
            appointment.pk,
            action,
            self.user,
            to_data={"status": appointment.status},
            notes=(
                "Acting appointment ended."
                if not revoke
                else "Acting appointment revoked."
            ),
        )
        logger.info(
            f"Ended acting appointment for {appointment.position.slug} by {self.user}"
        )
        return appointment


class VacancyService(BaseService):
    """Open a vacancy for a vacant position."""

    def _execute(
        self,
        *,
        position: Position,
        organizational_unit: OrganizationUnit,
        vacancy_reason: str = "",
        date_vacant=None,
        expected_appointment_date=None,
        acting_appointment=None,
        notes: str = "",
    ) -> Vacancy:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        validators.validate_vacancy_consistency(position, organizational_unit)
        vacancy = Vacancy.objects.create(
            position=position,
            organizational_unit=organizational_unit,
            vacancy_reason=vacancy_reason,
            date_vacant=date_vacant or timezone.localdate(),
            expected_appointment_date=expected_appointment_date,
            acting_appointment=acting_appointment,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        record_organization_audit(
            "Vacancy",
            vacancy.pk,
            OrganizationAuditAction.VACANCY_OPENED,
            self.user,
            to_data={"position": position.title},
            notes="Vacancy opened.",
        )
        logger.info(f"Opened vacancy for {position.slug} by {self.user}")
        return vacancy


class SetVacancyStatusService(BaseService):
    """Update the recruitment status of a vacancy."""

    def _execute(self, vacancy: Vacancy, status: str) -> Vacancy:
        _require_permission(self.user, ORGANIZATIONS_MANAGE)
        if status == VacancyStatus.FILLED and vacancy.position.is_vacant:
            raise ValidationError(
                _(
                    "A vacancy cannot be marked filled while the position has no "
                    "active appointment."
                ),
                code="vacancy_filled_without_occupant",
            )
        from_data = {"recruitment_status": vacancy.recruitment_status}
        vacancy.recruitment_status = status
        vacancy.updated_by = self.user
        vacancy.save(update_fields=["recruitment_status", "updated_by", "updated_at"])
        action = (
            OrganizationAuditAction.VACANCY_FILLED
            if status == VacancyStatus.FILLED
            else OrganizationAuditAction.UPDATED
        )
        record_organization_audit(
            "Vacancy",
            vacancy.pk,
            action,
            self.user,
            from_data=from_data,
            to_data={"recruitment_status": status},
            notes="Vacancy recruitment status changed.",
        )
        logger.info(f"Set vacancy status for {vacancy.position.slug} by {self.user}")
        return vacancy


class TransferService(BaseService):
    """Record a personnel transfer request."""

    def _execute(
        self,
        *,
        person,
        previous_organizational_unit: OrganizationUnit,
        new_organizational_unit: OrganizationUnit,
        previous_position: Position,
        new_position: Position,
        effective_date,
        reason: str = "",
        approved_by=None,
        supporting_document=None,
    ) -> TransferRecord:
        _require_permission(self.user, ORGANIZATIONS_ASSIGN)
        effective_date = validators.coerce_date(effective_date)
        validators.validate_transfer_dates(effective_date)
        transfer = TransferRecord.objects.create(
            person=person,
            previous_organizational_unit=previous_organizational_unit,
            new_organizational_unit=new_organizational_unit,
            previous_position=previous_position,
            new_position=new_position,
            effective_date=effective_date,
            reason=reason,
            approved_by=approved_by,
            supporting_document=supporting_document,
            status=TransferStatus.PENDING,
            created_by=self.user,
        )
        record_organization_audit(
            "TransferRecord",
            transfer.pk,
            OrganizationAuditAction.CREATED,
            self.user,
            to_data={
                "person": str(person),
                "new_position": new_position.title,
                "effective_date": effective_date.isoformat(),
            },
            notes="Transfer requested.",
        )
        logger.info(f"Recorded transfer for {person} by {self.user}")
        return transfer


class ApproveTransferService(BaseService):
    """Approve a pending transfer."""

    def _execute(self, transfer: TransferRecord) -> TransferRecord:
        _require_permission(self.user, ORGANIZATIONS_ASSIGN)
        if transfer.status != TransferStatus.PENDING:
            raise ValidationError(
                _("Only pending transfers can be approved."),
                code="transfer_not_pending",
            )
        transfer.status = TransferStatus.APPROVED
        transfer.approved_by = self.user
        transfer.save(update_fields=["status", "approved_by"])
        logger.info(f"Approved transfer for {transfer.person} by {self.user}")
        return transfer


class CompleteTransferService(BaseService):
    """Execute an approved transfer: end the old appointment and assign the new."""

    def _execute(self, transfer: TransferRecord) -> TransferRecord:
        _require_permission(self.user, ORGANIZATIONS_ASSIGN)
        _require_protected_position_access(self.user, transfer.new_position)
        if transfer.status != TransferStatus.APPROVED:
            raise ValidationError(
                _("Only approved transfers can be completed."),
                code="transfer_not_approved",
            )
        previous = PositionAssignment.objects.filter(
            person=transfer.person,
            position=transfer.previous_position,
            status=AppointmentStatus.ACTIVE,
        ).first()
        if previous is not None:
            previous.status = AppointmentStatus.ENDED
            previous.save(update_fields=["status"])

        AppointmentService(user=self.user).execute(
            person=transfer.person,
            position=transfer.new_position,
            organizational_unit=transfer.new_organizational_unit,
            effective_date=transfer.effective_date,
            notes=f"Completed via transfer {transfer.pk}.",
        )

        if previous is not None and previous.position.is_vacant:
            Vacancy.objects.create(
                position=previous.position,
                organizational_unit=previous.organizational_unit,
                vacancy_reason="Position vacated by transfer.",
                date_vacant=timezone.localdate(),
                created_by=self.user,
                updated_by=self.user,
            )

        transfer.status = TransferStatus.COMPLETED
        transfer.save(update_fields=["status"])
        record_organization_audit(
            "TransferRecord",
            transfer.pk,
            OrganizationAuditAction.TRANSFERRED,
            self.user,
            to_data={"person": str(transfer.person)},
            notes="Transfer completed.",
        )
        logger.info(f"Completed transfer for {transfer.person} by {self.user}")
        return transfer


class OrganizationalMaintenanceService(BaseService):
    """Automated maintenance of the organizational structure."""

    def expire_due_acting_appointments(self) -> int:
        """Expire acting appointments whose end date has passed."""
        due = ActingAppointment.objects.filter(
            status=ActingAppointmentStatus.ACTIVE,
            end_date__lt=timezone.localdate(),
        )
        expired = 0
        for appointment in due:
            appointment.auto_expire()
            expired += 1
        if expired:
            logger.info(f"Expired {expired} due acting appointments.")
        return expired


def _close_open_vacancy(position: Position) -> None:
    """Close any open vacancy for a position that has just been filled."""
    vacancy = Vacancy.objects.filter(position=position).first()
    if vacancy and vacancy.recruitment_status != VacancyStatus.FILLED:
        vacancy.recruitment_status = VacancyStatus.FILLED
        vacancy.save(update_fields=["recruitment_status"])


def _end_active_acting_appointments(position: Position) -> None:
    """End active acting appointments when the position gains a full occupant."""
    ActingAppointment.objects.filter(
        position=position, status=ActingAppointmentStatus.ACTIVE
    ).update(status=ActingAppointmentStatus.ENDED)
