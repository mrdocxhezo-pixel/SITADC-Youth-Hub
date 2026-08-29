"""
Business services for the leadership management module.

Every state-changing leadership operation flows through these services so that
invariants are enforced transactionally, reference numbers are issued through
the centralized numbering service, and every event is appended to the
immutable leadership audit log.
"""

from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission
from apps.references.constants import ReferenceModules
from apps.references.services import (
    ConfirmReferenceAssignmentService,
    ReferenceNumberService,
)

from . import validators
from .constants import (
    AppointmentStatus,
    AppointmentType,
    AttendanceStatus,
    LeadershipAuditAction,
    LeadershipStatus,
    LeaveStatus,
    MentorshipStatus,
    RatingScale,
    RenewalStatus,
    ReviewStatus,
    ScorecardStatus,
    TermStatus,
)
from .models import (
    CoachingRecord,
    DisciplinaryRecord,
    LeadershipAppointment,
    LeadershipAttendance,
    LeadershipAuditRecord,
    LeadershipDocument,
    LeadershipGoal,
    LeadershipKPI,
    LeadershipLeave,
    LeadershipProfile,
    LeadershipScorecard,
    LeadershipStatusHistory,
    LeadershipTask,
    MentorshipRecord,
    PerformanceReview,
    RecognitionRecord,
    SuccessionPlan,
)
from .permissions import (
    LEADERSHIP_ASSIGN,
    LEADERSHIP_CREATE,
    LEADERSHIP_MANAGE,
    LEADERSHIP_UPDATE,
)

logger = logging.getLogger(__name__)


def record_leadership_audit(
    entity_type: str,
    entity_id,
    action: str,
    changed_by,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> LeadershipAuditRecord:
    """Append an immutable audit record for a leadership event."""
    return LeadershipAuditRecord.objects.create(
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


def issue_leadership_reference(user, record_type: str, notes: str = ""):
    """
    Issue a leadership reference number and return its value.

    Public entry point reused by both the service layer and the model layer
    (``LeadershipProfile.save`` / ``LeadershipAppointment.save``) so every
    creation path flows through the centralized numbering service.
    """
    generated = ReferenceNumberService(user=user).execute(
        module=ReferenceModules.LEADERS,
        record_type=record_type,
        notes=notes,
    )
    return generated.reference_number


def confirm_leadership_reference(
    user, reference_number: str, record_id, notes: str = ""
) -> None:
    """Confirm a reserved reference against a persisted leadership record."""
    from apps.references.models import GeneratedReferenceNumber

    try:
        generated = GeneratedReferenceNumber.objects.get(
            reference_number=reference_number
        )
    except GeneratedReferenceNumber.DoesNotExist:
        return
    ConfirmReferenceAssignmentService(user=user).execute(
        reference=generated, record_id=record_id, notes=notes
    )


class CreateLeadershipProfileService(BaseService):
    """Create a leadership profile and issue its reference number."""

    def _execute(
        self,
        *,
        user,
        leadership_level: str,
        position=None,
        organizational_unit=None,
        directorate=None,
        supervisor=None,
        profile_photo=None,
        national_id: str = "",
        gender: str = "",
        date_of_birth=None,
        phone_number: str = "",
        email: str = "",
        residential_address: str = "",
        emergency_contact_name: str = "",
        emergency_contact_phone: str = "",
        appointment_date=None,
        term_expiry_date=None,
        region=None,
        district=None,
        community=None,
        terms_completed: int = 0,
        term_status: str = TermStatus.CURRENT,
        renewal_eligible: bool = False,
        renewal_status: str = RenewalStatus.NOT_ELIGIBLE,
        max_terms: int = 2,
        qualifications: str = "",
        professional_skills: str = "",
        areas_of_expertise: str = "",
        biography: str = "",
        status: str = LeadershipStatus.NOMINATED,
        notes: str = "",
    ) -> LeadershipProfile:
        _require_permission(self.user, LEADERSHIP_CREATE)
        # Query the database instead of using hasattr(): assigning a user to an
        # unsaved profile (e.g. during ModelForm validation) writes the reverse
        # one-to-one cache on the user object, which makes hasattr() report a
        # profile that does not exist in the database.
        if LeadershipProfile.objects.filter(user=user).exists():
            raise ValidationError(
                _("This user already has a leadership profile."),
                code="duplicate_leadership_profile",
            )

        reference_number = issue_leadership_reference(
            self.user, "leader", notes="Leadership profile registration."
        )
        profile = LeadershipProfile.objects.create(
            reference_number=reference_number,
            user=user,
            leadership_level=leadership_level,
            position=position,
            organizational_unit=organizational_unit,
            directorate=directorate,
            supervisor=supervisor,
            profile_photo=profile_photo,
            national_id=national_id,
            gender=gender,
            date_of_birth=validators.coerce_date(date_of_birth),
            phone_number=phone_number,
            email=email,
            residential_address=residential_address,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            appointment_date=validators.coerce_date(appointment_date),
            term_expiry_date=validators.coerce_date(term_expiry_date),
            region=region,
            district=district,
            community=community,
            terms_completed=terms_completed,
            term_status=term_status,
            renewal_eligible=renewal_eligible,
            renewal_status=renewal_status,
            max_terms=max_terms,
            qualifications=qualifications,
            professional_skills=professional_skills,
            areas_of_expertise=areas_of_expertise,
            biography=biography,
            status=status,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        confirm_leadership_reference(
            self.user, reference_number, profile.pk, notes="Profile registration."
        )
        LeadershipStatusHistory.objects.create(
            profile=profile,
            from_status=status,
            to_status=status,
            changed_by=self.user,
            notes="Leadership profile created.",
        )
        record_leadership_audit(
            "LeadershipProfile",
            profile.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={
                "reference_number": profile.reference_number,
                "user": str(user),
                "leadership_level": profile.leadership_level,
            },
            notes="Leadership profile created.",
        )
        logger.info(
            f"Created leadership profile {profile.reference_number} by {self.user}"
        )
        return profile


class UpdateLeadershipProfileService(BaseService):
    """Update leadership profile metadata."""

    def _execute(
        self,
        profile: LeadershipProfile,
        *,
        leadership_level: str,
        position=None,
        organizational_unit=None,
        directorate=None,
        supervisor=None,
        profile_photo=None,
        national_id: str = "",
        gender: str = "",
        date_of_birth=None,
        phone_number: str = "",
        email: str = "",
        residential_address: str = "",
        emergency_contact_name: str = "",
        emergency_contact_phone: str = "",
        appointment_date=None,
        term_expiry_date=None,
        max_terms: int = 2,
        qualifications: str = "",
        professional_skills: str = "",
        areas_of_expertise: str = "",
        biography: str = "",
        notes: str = "",
    ) -> LeadershipProfile:
        _require_permission(self.user, LEADERSHIP_UPDATE)
        from_data = {
            "leadership_level": profile.leadership_level,
            "position": profile.position.title if profile.position else None,
            "supervisor": str(profile.supervisor) if profile.supervisor else None,
        }
        profile.leadership_level = leadership_level
        profile.position = position
        profile.organizational_unit = organizational_unit
        profile.directorate = directorate
        if supervisor is not None:
            profile.supervisor = supervisor
        if profile_photo:
            profile.profile_photo = profile_photo
        profile.national_id = national_id
        profile.gender = gender
        profile.date_of_birth = validators.coerce_date(date_of_birth)
        profile.phone_number = phone_number
        profile.email = email
        profile.residential_address = residential_address
        profile.emergency_contact_name = emergency_contact_name
        profile.emergency_contact_phone = emergency_contact_phone
        profile.appointment_date = validators.coerce_date(appointment_date)
        profile.term_expiry_date = validators.coerce_date(term_expiry_date)
        profile.max_terms = max_terms
        profile.qualifications = qualifications
        profile.professional_skills = professional_skills
        profile.areas_of_expertise = areas_of_expertise
        profile.biography = biography
        profile.notes = notes
        profile.updated_by = self.user
        profile.full_clean()
        profile.save()
        record_leadership_audit(
            "LeadershipProfile",
            profile.pk,
            LeadershipAuditAction.UPDATED,
            self.user,
            from_data=from_data,
            to_data={
                "leadership_level": profile.leadership_level,
                "position": profile.position.title if profile.position else None,
                "supervisor": str(profile.supervisor) if profile.supervisor else None,
            },
            notes="Leadership profile updated.",
        )
        logger.info(
            f"Updated leadership profile {profile.reference_number} by {self.user}"
        )
        return profile


class ChangeLeadershipStatusService(BaseService):
    """Change a leadership profile status and record the transition."""

    def _execute(
        self,
        profile: LeadershipProfile,
        new_status: str,
        notes: str = "",
    ) -> LeadershipProfile:
        _require_permission(self.user, LEADERSHIP_UPDATE)
        if profile.status == new_status:
            raise ValidationError(
                _("The profile already has this status."), code="status_unchanged"
            )
        validators.validate_active_profile_has_appointment(profile)

        from_status = profile.status
        profile.status = new_status
        profile.updated_by = self.user
        profile.save(update_fields=["status", "updated_by", "updated_at"])
        LeadershipStatusHistory.objects.create(
            profile=profile,
            from_status=from_status,
            to_status=new_status,
            changed_by=self.user,
            notes=notes,
        )
        record_leadership_audit(
            "LeadershipProfile",
            profile.pk,
            LeadershipAuditAction.STATUS_CHANGED,
            self.user,
            from_data={"status": from_status},
            to_data={"status": new_status},
            notes=notes or "Leadership status changed.",
        )
        logger.info(
            "Changed status of %s to %s by %s",
            profile.reference_number,
            new_status,
            self.user,
        )
        return profile


class ArchiveLeadershipProfileService(BaseService):
    """Archive a leadership profile."""

    def _execute(self, profile: LeadershipProfile) -> LeadershipProfile:
        _require_permission(self.user, LEADERSHIP_MANAGE)
        if profile.is_archived:
            raise ValidationError(
                _("This profile is already archived."), code="already_archived"
            )
        from_data = {"status": profile.status, "is_archived": profile.is_archived}
        profile.status = LeadershipStatus.ARCHIVED
        profile.archive(archived_by=self.user)
        record_leadership_audit(
            "LeadershipProfile",
            profile.pk,
            LeadershipAuditAction.ARCHIVED,
            self.user,
            from_data=from_data,
            to_data={"status": profile.status, "is_archived": profile.is_archived},
            notes="Leadership profile archived.",
        )
        logger.info(
            f"Archived leadership profile {profile.reference_number} by {self.user}"
        )
        return profile


class RestoreLeadershipProfileService(BaseService):
    """Restore an archived leadership profile."""

    def _execute(self, profile: LeadershipProfile) -> LeadershipProfile:
        _require_permission(self.user, LEADERSHIP_MANAGE)
        if not profile.is_archived:
            raise ValidationError(
                _("This profile is not archived."), code="not_archived"
            )
        from_data = {"status": profile.status, "is_archived": profile.is_archived}
        profile.restore()
        profile.status = LeadershipStatus.NOMINATED
        profile.updated_by = self.user
        profile.save(update_fields=["status", "updated_by", "updated_at"])
        record_leadership_audit(
            "LeadershipProfile",
            profile.pk,
            LeadershipAuditAction.RESTORED,
            self.user,
            from_data=from_data,
            to_data={"status": profile.status, "is_archived": profile.is_archived},
            notes="Leadership profile restored.",
        )
        logger.info(
            f"Restored leadership profile {profile.reference_number} by {self.user}"
        )
        return profile


class SetSupervisorService(BaseService):
    """Set the immediate supervisor for a leadership profile."""

    def _execute(self, profile: LeadershipProfile, supervisor) -> LeadershipProfile:
        _require_permission(self.user, LEADERSHIP_ASSIGN)
        validators.validate_supervisor_not_self(profile, supervisor)
        from_data = {
            "supervisor": str(profile.supervisor) if profile.supervisor else None
        }
        profile.supervisor = supervisor
        profile.updated_by = self.user
        profile.save(update_fields=["supervisor", "updated_by", "updated_at"])
        record_leadership_audit(
            "LeadershipProfile",
            profile.pk,
            LeadershipAuditAction.SUPERVISOR_CHANGED,
            self.user,
            from_data=from_data,
            to_data={"supervisor": str(supervisor) if supervisor else None},
            notes="Immediate supervisor changed.",
        )
        logger.info(f"Set supervisor for {profile.reference_number} by {self.user}")
        return profile


class CreateLeadershipAppointmentService(BaseService):
    """Create a leadership appointment and issue its reference number."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        position,
        organizational_unit,
        appointment_type: str = AppointmentType.PERMANENT,
        appointing_authority=None,
        appointment_date=None,
        effective_date=None,
        term_start=None,
        term_end=None,
        renewal_eligible: bool = False,
        max_terms: int = 2,
        appointment_letter=None,
        status: str = AppointmentStatus.DRAFT,
        notes: str = "",
    ) -> LeadershipAppointment:
        _require_permission(self.user, LEADERSHIP_ASSIGN)
        if profile.status == LeadershipStatus.ARCHIVED:
            raise ValidationError(
                _("An appointment cannot be created for an archived leader."),
                code="profile_archived",
            )
        validators.validate_no_overlapping_active_appointment(profile, position)
        validators.validate_appointment_dates(
            validators.coerce_date(effective_date),
            validators.coerce_date(term_start),
            validators.coerce_date(term_end),
        )

        reference_number = issue_leadership_reference(
            self.user, "appointment", notes="Leadership appointment."
        )
        appointment = LeadershipAppointment.objects.create(
            reference_number=reference_number,
            profile=profile,
            position=position,
            organizational_unit=organizational_unit,
            appointment_type=appointment_type,
            appointing_authority=appointing_authority,
            appointment_date=validators.coerce_date(appointment_date)
            or timezone.localdate(),
            effective_date=validators.coerce_date(effective_date)
            or timezone.localdate(),
            term_start=validators.coerce_date(term_start),
            term_end=validators.coerce_date(term_end),
            renewal_eligible=renewal_eligible,
            max_terms=max_terms,
            appointment_letter=appointment_letter,
            status=status,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        confirm_leadership_reference(
            self.user,
            reference_number,
            appointment.pk,
            notes="Leadership appointment created.",
        )
        record_leadership_audit(
            "LeadershipAppointment",
            appointment.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={
                "reference_number": appointment.reference_number,
                "profile": str(profile),
                "position": position.title,
            },
            notes="Leadership appointment created.",
        )
        logger.info(
            "Created leadership appointment %s by %s",
            appointment.reference_number,
            self.user,
        )
        return appointment


class TransitionAppointmentService(BaseService):
    """Apply an allowed workflow transition to an appointment."""

    def _execute(
        self,
        appointment: LeadershipAppointment,
        target_status: str,
        notes: str = "",
    ) -> LeadershipAppointment:
        _require_permission(self.user, LEADERSHIP_ASSIGN)
        validators.validate_appointment_transition(appointment, target_status)
        from_data = {"status": appointment.status}
        appointment.status = target_status
        appointment.updated_by = self.user
        appointment.save(update_fields=["status", "updated_by", "updated_at"])

        action_map = {
            AppointmentStatus.PENDING_REVIEW: LeadershipAuditAction.UPDATED,
            AppointmentStatus.PENDING_APPROVAL: LeadershipAuditAction.UPDATED,
            AppointmentStatus.APPROVED: LeadershipAuditAction.APPOINTMENT_APPROVED,
            AppointmentStatus.ACTIVE: LeadershipAuditAction.APPOINTMENT_ACTIVATED,
            AppointmentStatus.COMPLETED: LeadershipAuditAction.APPOINTMENT_COMPLETED,
            AppointmentStatus.TERMINATED: LeadershipAuditAction.APPOINTMENT_TERMINATED,
            AppointmentStatus.REVOKED: LeadershipAuditAction.APPOINTMENT_TERMINATED,
        }
        action = action_map.get(target_status, LeadershipAuditAction.UPDATED)
        record_leadership_audit(
            "LeadershipAppointment",
            appointment.pk,
            action,
            self.user,
            from_data=from_data,
            to_data={"status": target_status},
            notes=notes or "Appointment status changed.",
        )
        logger.info(
            "Transitioned appointment %s to %s by %s",
            appointment.reference_number,
            target_status,
            self.user,
        )
        return appointment


class RenewLeadershipAppointmentService(BaseService):
    """Renew a completed or expiring appointment for another term."""

    def _execute(
        self,
        appointment: LeadershipAppointment,
        new_term_start,
        new_term_end,
        notes: str = "",
    ) -> LeadershipAppointment:
        _require_permission(self.user, LEADERSHIP_ASSIGN)
        if appointment.status not in (
            AppointmentStatus.ACTIVE,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.EXPIRED,
        ):
            raise ValidationError(
                _("This appointment cannot be renewed in its current state."),
                code="appointment_not_renewable",
            )
        if not appointment.renewal_eligible:
            raise ValidationError(
                _("This appointment is not eligible for renewal."),
                code="renewal_not_eligible",
            )
        if appointment.terms_completed >= appointment.max_terms:
            raise ValidationError(
                _("The maximum number of terms has been reached."),
                code="max_terms_reached",
            )
        validators.validate_appointment_dates(
            appointment.effective_date,
            validators.coerce_date(new_term_start),
            validators.coerce_date(new_term_end),
        )
        from_data = {
            "status": appointment.status,
            "term_start": appointment.term_start,
            "term_end": appointment.term_end,
        }
        appointment.term_start = validators.coerce_date(new_term_start)
        appointment.term_end = validators.coerce_date(new_term_end)
        appointment.status = AppointmentStatus.ACTIVE
        appointment.terms_completed += 1
        appointment.updated_by = self.user
        appointment.save(
            update_fields=[
                "term_start",
                "term_end",
                "status",
                "terms_completed",
                "updated_by",
                "updated_at",
            ]
        )
        record_leadership_audit(
            "LeadershipAppointment",
            appointment.pk,
            LeadershipAuditAction.APPOINTMENT_RENEWED,
            self.user,
            from_data=from_data,
            to_data={
                "status": appointment.status,
                "term_start": appointment.term_start,
                "term_end": appointment.term_end,
            },
            notes=notes or "Leadership appointment renewed.",
        )
        logger.info(
            f"Renewed appointment {appointment.reference_number} by {self.user}"
        )
        return appointment


class LeadershipAttendanceService(BaseService):
    """Record leadership attendance for an activity."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        attendance_type: str,
        attendance_date=None,
        activity_name: str = "",
        venue: str = "",
        status: str = AttendanceStatus.PRESENT,
        notes: str = "",
    ) -> LeadershipAttendance:
        _require_permission(self.user, LEADERSHIP_CREATE)
        attendance = LeadershipAttendance.objects.create(
            profile=profile,
            attendance_type=attendance_type,
            attendance_date=validators.coerce_date(attendance_date)
            or timezone.localdate(),
            activity_name=activity_name,
            venue=venue,
            status=status,
            notes=notes,
            created_by=self.user,
        )
        record_leadership_audit(
            "LeadershipAttendance",
            attendance.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={
                "profile": str(profile),
                "attendance_type": attendance.attendance_type,
                "attendance_date": attendance.attendance_date.isoformat(),
            },
            notes="Leadership attendance recorded.",
        )
        logger.info(f"Recorded attendance for {profile} by {self.user}")
        return attendance


class LeadershipLeaveService(BaseService):
    """Create a leadership leave request."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        leave_type: str,
        start_date,
        end_date,
        reason: str = "",
        notes: str = "",
    ) -> LeadershipLeave:
        _require_permission(self.user, LEADERSHIP_CREATE)
        validators.validate_leave_dates(start_date, end_date)
        validators.validate_overlapping_leave(profile, start_date, end_date)
        leave = LeadershipLeave.objects.create(
            profile=profile,
            leave_type=leave_type,
            start_date=validators.coerce_date(start_date),
            end_date=validators.coerce_date(end_date),
            reason=reason,
            status=LeaveStatus.PENDING,
            notes=notes,
            created_by=self.user,
        )
        record_leadership_audit(
            "LeadershipLeave",
            leave.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={
                "profile": str(profile),
                "leave_type": leave.leave_type,
                "start_date": leave.start_date.isoformat(),
                "end_date": leave.end_date.isoformat(),
            },
            notes="Leadership leave requested.",
        )
        logger.info(f"Requested leave for {profile} by {self.user}")
        return leave


class ApproveLeadershipLeaveService(BaseService):
    """Approve or reject a pending leadership leave request."""

    def _execute(
        self, leave: LeadershipLeave, approve: bool, notes: str = ""
    ) -> LeadershipLeave:
        _require_permission(self.user, LEADERSHIP_ASSIGN)
        if leave.status != LeaveStatus.PENDING:
            raise ValidationError(
                _("Only pending leave requests can be approved or rejected."),
                code="leave_not_pending",
            )
        from_data = {"status": leave.status}
        leave.status = LeaveStatus.APPROVED if approve else LeaveStatus.REJECTED
        leave.approved_by = self.user
        leave.approved_at = timezone.now()
        leave.save(update_fields=["status", "approved_by", "approved_at"])
        record_leadership_audit(
            "LeadershipLeave",
            leave.pk,
            LeadershipAuditAction.UPDATED,
            self.user,
            from_data=from_data,
            to_data={"status": leave.status},
            notes=notes or ("Leave approved." if approve else "Leave rejected."),
        )
        logger.info(
            "%s leave for %s by %s",
            "Approved" if approve else "Rejected",
            leave.profile,
            self.user,
        )
        return leave


class LeadershipTaskService(BaseService):
    """Create a leadership task."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        title: str,
        description: str = "",
        priority: str = "MEDIUM",
        due_date=None,
        status: str = "NOT_STARTED",
        progress: int = 0,
        supporting_document=None,
        notes: str = "",
    ) -> LeadershipTask:
        _require_permission(self.user, LEADERSHIP_CREATE)
        task = LeadershipTask.objects.create(
            profile=profile,
            title=title,
            description=description,
            priority=priority,
            due_date=validators.coerce_date(due_date),
            status=status,
            progress=progress,
            supporting_document=supporting_document,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        record_leadership_audit(
            "LeadershipTask",
            task.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"title": task.title, "profile": str(profile)},
            notes="Leadership task created.",
        )
        logger.info(f"Created task for {profile} by {self.user}")
        return task


class UpdateLeadershipTaskService(BaseService):
    """Update task status and progress."""

    def _execute(
        self,
        task: LeadershipTask,
        *,
        status: str,
        progress: int,
        notes: str = "",
    ) -> LeadershipTask:
        _require_permission(self.user, LEADERSHIP_UPDATE)
        if not 0 <= progress <= 100:
            raise ValidationError(
                _("Progress must be between 0 and 100."), code="invalid_progress"
            )
        from_data = {"status": task.status, "progress": task.progress}
        task.status = status
        task.progress = progress
        task.notes = notes
        task.updated_by = self.user
        task.save()
        record_leadership_audit(
            "LeadershipTask",
            task.pk,
            LeadershipAuditAction.UPDATED,
            self.user,
            from_data=from_data,
            to_data={"status": task.status, "progress": task.progress},
            notes="Leadership task updated.",
        )
        logger.info(f"Updated task {task.title} by {self.user}")
        return task


class LeadershipGoalService(BaseService):
    """Create or update a leadership goal."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        title: str,
        strategic_objective: str = "",
        performance_indicator: str = "",
        target_value=None,
        current_value=None,
        due_date=None,
        status: str = "NOT_STARTED",
        notes: str = "",
        goal: LeadershipGoal | None = None,
    ) -> LeadershipGoal:
        _require_permission(self.user, LEADERSHIP_CREATE)
        if goal is not None:
            from_data = {
                "status": goal.status,
                "current_value": str(goal.current_value),
            }
            goal.title = title
            goal.strategic_objective = strategic_objective
            goal.performance_indicator = performance_indicator
            goal.target_value = target_value
            goal.current_value = current_value
            goal.due_date = validators.coerce_date(due_date)
            goal.status = status
            goal.notes = notes
            goal.updated_by = self.user
            goal.save()
            record_leadership_audit(
                "LeadershipGoal",
                goal.pk,
                LeadershipAuditAction.UPDATED,
                self.user,
                from_data=from_data,
                to_data={
                    "status": goal.status,
                    "current_value": str(goal.current_value),
                },
                notes="Leadership goal updated.",
            )
            logger.info(f"Updated goal {goal.title} by {self.user}")
            return goal

        goal = LeadershipGoal.objects.create(
            profile=profile,
            title=title,
            strategic_objective=strategic_objective,
            performance_indicator=performance_indicator,
            target_value=target_value,
            current_value=current_value,
            due_date=validators.coerce_date(due_date),
            status=status,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        record_leadership_audit(
            "LeadershipGoal",
            goal.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"title": goal.title, "profile": str(profile)},
            notes="Leadership goal created.",
        )
        logger.info(f"Created goal for {profile} by {self.user}")
        return goal


class LeadershipKpiService(BaseService):
    """Create or update a leadership KPI."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        name: str,
        period_start,
        period_end,
        category: str = "",
        target_value=None,
        actual_value=None,
        status: str = "ON_TRACK",
        notes: str = "",
        kpi: LeadershipKPI | None = None,
    ) -> LeadershipKPI:
        _require_permission(self.user, LEADERSHIP_CREATE)
        validators.validate_date_order(period_start, period_end, "KPI period")
        if kpi is not None:
            kpi.name = name
            kpi.category = category
            kpi.target_value = target_value
            kpi.actual_value = actual_value
            kpi.period_start = validators.coerce_date(period_start)
            kpi.period_end = validators.coerce_date(period_end)
            kpi.status = status
            kpi.notes = notes
            kpi.updated_by = self.user
            kpi.save()
            record_leadership_audit(
                "LeadershipKPI",
                kpi.pk,
                LeadershipAuditAction.UPDATED,
                self.user,
                to_data={"name": kpi.name, "status": kpi.status},
                notes="Leadership KPI updated.",
            )
            logger.info(f"Updated KPI {kpi.name} by {self.user}")
            return kpi

        kpi = LeadershipKPI.objects.create(
            profile=profile,
            name=name,
            category=category,
            target_value=target_value,
            actual_value=actual_value,
            period_start=validators.coerce_date(period_start),
            period_end=validators.coerce_date(period_end),
            status=status,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        record_leadership_audit(
            "LeadershipKPI",
            kpi.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"name": kpi.name, "profile": str(profile)},
            notes="Leadership KPI created.",
        )
        logger.info(f"Created KPI for {profile} by {self.user}")
        return kpi


class CoachingService(BaseService):
    """Create a coaching record."""

    def _execute(
        self,
        *,
        coach,
        leader: LeadershipProfile,
        category: str,
        session_date=None,
        objectives: str = "",
        topics_discussed: str = "",
        agreed_actions: str = "",
        follow_up_date=None,
        outcomes: str = "",
        is_confidential: bool = True,
        notes: str = "",
    ) -> CoachingRecord:
        _require_permission(self.user, LEADERSHIP_CREATE)
        record = CoachingRecord.objects.create(
            coach=coach,
            leader=leader,
            category=category,
            session_date=validators.coerce_date(session_date) or timezone.localdate(),
            objectives=objectives,
            topics_discussed=topics_discussed,
            agreed_actions=agreed_actions,
            follow_up_date=validators.coerce_date(follow_up_date),
            outcomes=outcomes,
            is_confidential=is_confidential,
            notes=notes,
            created_by=self.user,
        )
        record_leadership_audit(
            "CoachingRecord",
            record.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"leader": str(leader), "category": record.category},
            notes="Coaching record created.",
        )
        logger.info(f"Created coaching record for {leader} by {self.user}")
        return record


class MentorshipService(BaseService):
    """Create, update or complete a mentorship relationship."""

    def _execute(
        self,
        *,
        mentor,
        mentee: LeadershipProfile,
        start_date=None,
        end_date=None,
        development_objectives: str = "",
        progress_notes: str = "",
        outcomes: str = "",
        evaluation: str = "",
        status: str = MentorshipStatus.ACTIVE,
        notes: str = "",
        record: MentorshipRecord | None = None,
    ) -> MentorshipRecord:
        _require_permission(self.user, LEADERSHIP_CREATE)
        validators.validate_date_order(start_date, end_date, "Mentorship")
        if record is not None:
            record.mentor = mentor
            record.mentee = mentee
            record.start_date = validators.coerce_date(start_date)
            record.end_date = validators.coerce_date(end_date)
            record.development_objectives = development_objectives
            record.progress_notes = progress_notes
            record.outcomes = outcomes
            record.evaluation = evaluation
            record.status = status
            record.notes = notes
            record.save()
            record_leadership_audit(
                "MentorshipRecord",
                record.pk,
                LeadershipAuditAction.UPDATED,
                self.user,
                to_data={"mentee": str(mentee), "status": record.status},
                notes="Mentorship record updated.",
            )
            logger.info(f"Updated mentorship for {mentee} by {self.user}")
            return record

        record = MentorshipRecord.objects.create(
            mentor=mentor,
            mentee=mentee,
            start_date=validators.coerce_date(start_date) or timezone.localdate(),
            end_date=validators.coerce_date(end_date),
            development_objectives=development_objectives,
            progress_notes=progress_notes,
            outcomes=outcomes,
            evaluation=evaluation,
            status=status,
            notes=notes,
            created_by=self.user,
        )
        record_leadership_audit(
            "MentorshipRecord",
            record.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"mentee": str(mentee), "status": record.status},
            notes="Mentorship record created.",
        )
        logger.info(f"Created mentorship for {mentee} by {self.user}")
        return record


class PerformanceReviewService(BaseService):
    """Create, submit, return or approve a leadership performance review."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        review_cycle: str,
        period_start,
        period_end,
        reviewer=None,
        performance_ratings: dict | None = None,
        achievements: str = "",
        challenges: str = "",
        recommendations: str = "",
        improvement_plan: str = "",
        overall_assessment: str = "",
        overall_rating: int | None = None,
        status: str = ReviewStatus.DRAFT,
        notes: str = "",
        review: PerformanceReview | None = None,
    ) -> PerformanceReview:
        _require_permission(self.user, LEADERSHIP_CREATE)
        validators.validate_date_order(period_start, period_end, "Review period")
        if overall_rating is not None and overall_rating not in RatingScale.values:
            raise ValidationError(
                _("Overall rating must be on the 1-5 scale."), code="invalid_rating"
            )
        if review is not None:
            review.profile = profile
            review.review_cycle = review_cycle
            review.period_start = validators.coerce_date(period_start)
            review.period_end = validators.coerce_date(period_end)
            review.reviewer = reviewer
            review.performance_ratings = performance_ratings or {}
            review.achievements = achievements
            review.challenges = challenges
            review.recommendations = recommendations
            review.improvement_plan = improvement_plan
            review.overall_assessment = overall_assessment
            review.overall_rating = overall_rating
            review.status = status
            review.notes = notes
            review.updated_by = self.user
            review.save()
            action = (
                LeadershipAuditAction.REVIEW_SUBMITTED
                if status == ReviewStatus.SUBMITTED
                else LeadershipAuditAction.UPDATED
            )
            record_leadership_audit(
                "PerformanceReview",
                review.pk,
                action,
                self.user,
                to_data={"status": review.status, "profile": str(profile)},
                notes="Performance review updated.",
            )
            logger.info(f"Updated performance review for {profile} by {self.user}")
            return review

        review = PerformanceReview.objects.create(
            profile=profile,
            review_cycle=review_cycle,
            period_start=validators.coerce_date(period_start),
            period_end=validators.coerce_date(period_end),
            reviewer=reviewer,
            performance_ratings=performance_ratings or {},
            achievements=achievements,
            challenges=challenges,
            recommendations=recommendations,
            improvement_plan=improvement_plan,
            overall_assessment=overall_assessment,
            overall_rating=overall_rating,
            status=status,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        record_leadership_audit(
            "PerformanceReview",
            review.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"status": review.status, "profile": str(profile)},
            notes="Performance review created.",
        )
        logger.info(f"Created performance review for {profile} by {self.user}")
        return review


class RecognitionService(BaseService):
    """Create a leadership recognition or award."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        award_name: str,
        category: str,
        date_awarded=None,
        awarding_authority=None,
        citation: str = "",
        supporting_document=None,
        notes: str = "",
    ) -> RecognitionRecord:
        _require_permission(self.user, LEADERSHIP_CREATE)
        record = RecognitionRecord.objects.create(
            profile=profile,
            award_name=award_name,
            category=category,
            date_awarded=validators.coerce_date(date_awarded) or timezone.localdate(),
            awarding_authority=awarding_authority,
            citation=citation,
            supporting_document=supporting_document,
            notes=notes,
            created_by=self.user,
        )
        record_leadership_audit(
            "RecognitionRecord",
            record.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"award_name": record.award_name, "profile": str(profile)},
            notes="Recognition record created.",
        )
        logger.info(f"Created recognition for {profile} by {self.user}")
        return record


class DisciplinaryService(BaseService):
    """Create or resolve a leadership disciplinary record."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        record_type: str,
        description: str = "",
        incident_date=None,
        status: str = "OPEN",
        resolution: str = "",
        supporting_document=None,
        is_confidential: bool = True,
        notes: str = "",
        record: DisciplinaryRecord | None = None,
    ) -> DisciplinaryRecord:
        _require_permission(self.user, LEADERSHIP_UPDATE)
        if record is not None:
            record.record_type = record_type
            record.description = description
            record.incident_date = validators.coerce_date(incident_date)
            record.status = status
            record.resolution = resolution
            record.notes = notes
            record.save()
            record_leadership_audit(
                "DisciplinaryRecord",
                record.pk,
                LeadershipAuditAction.UPDATED,
                self.user,
                to_data={"status": record.status, "profile": str(profile)},
                notes="Disciplinary record updated.",
            )
            logger.info(f"Updated disciplinary record for {profile} by {self.user}")
            return record

        record = DisciplinaryRecord.objects.create(
            profile=profile,
            record_type=record_type,
            description=description,
            incident_date=validators.coerce_date(incident_date) or timezone.localdate(),
            status=status,
            resolution=resolution,
            supporting_document=supporting_document,
            is_confidential=is_confidential,
            notes=notes,
            created_by=self.user,
        )
        record_leadership_audit(
            "DisciplinaryRecord",
            record.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"record_type": record.record_type, "profile": str(profile)},
            notes="Disciplinary record created.",
        )
        logger.info(f"Created disciplinary record for {profile} by {self.user}")
        return record


class SuccessionPlanService(BaseService):
    """Create or update a succession plan for a critical position."""

    def _execute(
        self,
        *,
        position,
        current_holder=None,
        potential_successors=None,
        readiness_level: str = "DEVELOPING",
        required_competencies: str = "",
        development_activities: str = "",
        target_readiness_date=None,
        risk: str = "MEDIUM",
        is_active: bool = True,
        notes: str = "",
        plan: SuccessionPlan | None = None,
    ) -> SuccessionPlan:
        _require_permission(self.user, LEADERSHIP_MANAGE)
        if plan is not None:
            plan.position = position
            plan.current_holder = current_holder
            plan.readiness_level = readiness_level
            plan.required_competencies = required_competencies
            plan.development_activities = development_activities
            plan.target_readiness_date = validators.coerce_date(target_readiness_date)
            plan.risk = risk
            plan.is_active = is_active
            plan.notes = notes
            plan.updated_by = self.user
            plan.save()
            record_leadership_audit(
                "SuccessionPlan",
                plan.pk,
                LeadershipAuditAction.UPDATED,
                self.user,
                to_data={
                    "position": position.title,
                    "readiness_level": plan.readiness_level,
                },
                notes="Succession plan updated.",
            )
            logger.info(f"Updated succession plan for {position.title} by {self.user}")
            return plan

        plan = SuccessionPlan.objects.create(
            position=position,
            current_holder=current_holder,
            readiness_level=readiness_level,
            required_competencies=required_competencies,
            development_activities=development_activities,
            target_readiness_date=validators.coerce_date(target_readiness_date),
            risk=risk,
            is_active=is_active,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        if potential_successors:
            plan.potential_successors.set(potential_successors)
        record_leadership_audit(
            "SuccessionPlan",
            plan.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"position": position.title, "risk": plan.risk},
            notes="Succession plan created.",
        )
        logger.info(f"Created succession plan for {position.title} by {self.user}")
        return plan


class LeadershipDocumentService(BaseService):
    """Upload a versioned leadership document."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        category: str,
        title: str,
        file,
        version: str = "1.0",
        confidentiality: str = "INTERNAL",
        notes: str = "",
    ) -> LeadershipDocument:
        _require_permission(self.user, LEADERSHIP_CREATE)
        if file is None:
            raise ValidationError(
                _("A document file is required."), code="document_file_required"
            )
        document = LeadershipDocument.objects.create(
            profile=profile,
            category=category,
            title=title,
            file=file,
            version=version,
            confidentiality=confidentiality,
            notes=notes,
            created_by=self.user,
        )
        record_leadership_audit(
            "LeadershipDocument",
            document.pk,
            LeadershipAuditAction.DOCUMENT_UPLOADED,
            self.user,
            to_data={"title": document.title, "profile": str(profile)},
            notes="Leadership document uploaded.",
        )
        logger.info(f"Uploaded document {document.title} by {self.user}")
        return document


class LeadershipScorecardService(BaseService):
    """Create or update a leadership performance scorecard."""

    def _execute(
        self,
        *,
        profile: LeadershipProfile,
        period_start,
        period_end,
        attendance_score: float = 0,
        report_submission_score: float = 0,
        goal_achievement_score: float = 0,
        kpi_performance_score: float = 0,
        team_supervision_score: float = 0,
        program_oversight_score: float = 0,
        community_engagement_score: float = 0,
        stakeholder_engagement_score: float = 0,
        training_participation_score: float = 0,
        status: str = ScorecardStatus.DRAFT,
        notes: str = "",
        scorecard: LeadershipScorecard | None = None,
    ) -> LeadershipScorecard:
        _require_permission(self.user, LEADERSHIP_CREATE)
        validators.validate_date_order(period_start, period_end, "Scorecard period")
        scores = {
            "attendance_score": attendance_score,
            "report_submission_score": report_submission_score,
            "goal_achievement_score": goal_achievement_score,
            "kpi_performance_score": kpi_performance_score,
            "team_supervision_score": team_supervision_score,
            "program_oversight_score": program_oversight_score,
            "community_engagement_score": community_engagement_score,
            "stakeholder_engagement_score": stakeholder_engagement_score,
            "training_participation_score": training_participation_score,
        }
        for value in scores.values():
            validators.validate_score_range(value)

        kwargs = {
            "profile": profile,
            "period_start": validators.coerce_date(period_start),
            "period_end": validators.coerce_date(period_end),
            "status": status,
            "notes": notes,
            **scores,
        }
        if scorecard is not None:
            for field, value in scores.items():
                setattr(scorecard, field, value)
            scorecard.period_start = kwargs["period_start"]
            scorecard.period_end = kwargs["period_end"]
            scorecard.status = status
            scorecard.notes = notes
            scorecard.updated_by = self.user
            scorecard.calculate_overall_rating()
            scorecard.save()
            record_leadership_audit(
                "LeadershipScorecard",
                scorecard.pk,
                LeadershipAuditAction.UPDATED,
                self.user,
                to_data={
                    "status": scorecard.status,
                    "overall_rating": str(scorecard.overall_rating),
                },
                notes="Leadership scorecard updated.",
            )
            logger.info(f"Updated scorecard for {profile} by {self.user}")
            return scorecard

        scorecard = LeadershipScorecard(**kwargs)
        scorecard.calculate_overall_rating()
        scorecard.created_by = self.user
        scorecard.updated_by = self.user
        scorecard.save()
        record_leadership_audit(
            "LeadershipScorecard",
            scorecard.pk,
            LeadershipAuditAction.CREATED,
            self.user,
            to_data={"profile": str(profile), "status": scorecard.status},
            notes="Leadership scorecard created.",
        )
        logger.info(f"Created scorecard for {profile} by {self.user}")
        return scorecard


class LeadershipMaintenanceService(BaseService):
    """Automated maintenance of leadership records."""

    def expire_due_appointments(self) -> int:
        """Expire appointments whose term end has passed."""
        due = LeadershipAppointment.objects.filter(
            status=AppointmentStatus.ACTIVE, term_end__lt=timezone.localdate()
        )
        expired = 0
        for appointment in due:
            appointment.auto_expire()
            expired += 1
        if expired:
            logger.info(f"Expired {expired} due leadership appointments.")
        return expired

    def recalculate_scorecards(self) -> int:
        """Recompute overall ratings for draft scorecards."""
        updated = 0
        for scorecard in LeadershipScorecard.objects.filter(
            status=ScorecardStatus.DRAFT
        ):
            scorecard.calculate_overall_rating()
            scorecard.save(update_fields=["overall_rating", "updated_at"])
            updated += 1
        if updated:
            logger.info(f"Recalculated {updated} leadership scorecards.")
        return updated
