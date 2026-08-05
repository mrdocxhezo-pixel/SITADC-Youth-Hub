"""Transactional business services for volunteer management."""

from __future__ import annotations

import logging
from datetime import date, datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission
from apps.references.constants import ReferenceModules
from apps.references.services import (
    ConfirmReferenceAssignmentService,
    ReferenceNumberService,
)

from .constants import (
    ApplicationStatus,
    AttendanceStatus,
    CommunicationChannel,
    DisciplinaryStatus,
    ExitStatus,
    LeaveStatus,
    VolunteerAuditAction,
    VolunteerDocumentStatus,
    VolunteerStatus,
)
from .models import (
    VolunteerActivityLog,
    VolunteerApplication,
    VolunteerAssignment,
    VolunteerAttendance,
    VolunteerAuditRecord,
    VolunteerCommunication,
    VolunteerDeploymentHistory,
    VolunteerDisciplinaryRecord,
    VolunteerDocument,
    VolunteerExit,
    VolunteerInterview,
    VolunteerLeave,
    VolunteerOnboarding,
    VolunteerPerformance,
    VolunteerProfile,
    VolunteerRecognition,
    VolunteerRecruitment,
    VolunteerScreening,
    VolunteerStatusHistory,
    VolunteerTraining,
)
from .permissions import (
    VOLUNTEERS_ASSIGN,
    VOLUNTEERS_CREATE,
    VOLUNTEERS_MANAGE,
    VOLUNTEERS_MANAGE_ACTIVITY,
    VOLUNTEERS_MANAGE_ATTENDANCE,
    VOLUNTEERS_MANAGE_COMMUNICATIONS,
    VOLUNTEERS_MANAGE_DISCIPLINARY,
    VOLUNTEERS_MANAGE_DOCUMENTS,
    VOLUNTEERS_MANAGE_EXIT,
    VOLUNTEERS_MANAGE_LEAVE,
    VOLUNTEERS_MANAGE_PERFORMANCE,
    VOLUNTEERS_MANAGE_TRAINING,
    VOLUNTEERS_UPDATE,
)

logger = logging.getLogger(__name__)

ALLOWED_PROFILE_TRANSITIONS: dict[str, set[str]] = {
    VolunteerStatus.APPLICANT: {VolunteerStatus.PENDING_REVIEW},
    VolunteerStatus.PENDING_REVIEW: {
        VolunteerStatus.INTERVIEW_SCHEDULED,
        VolunteerStatus.SUSPENDED,
    },
    VolunteerStatus.INTERVIEW_SCHEDULED: {
        VolunteerStatus.APPROVED,
        VolunteerStatus.SUSPENDED,
    },
    VolunteerStatus.APPROVED: {VolunteerStatus.REGISTERED},
    VolunteerStatus.REGISTERED: {
        VolunteerStatus.ONBOARDING,
        VolunteerStatus.ACTIVE,
        VolunteerStatus.SUSPENDED,
    },
    VolunteerStatus.ONBOARDING: {
        VolunteerStatus.ACTIVE,
        VolunteerStatus.SUSPENDED,
    },
    VolunteerStatus.ACTIVE: {
        VolunteerStatus.ASSIGNED,
        VolunteerStatus.ON_LEAVE,
        VolunteerStatus.SUSPENDED,
        VolunteerStatus.INACTIVE,
        VolunteerStatus.EXITED,
        VolunteerStatus.ALUMNI,
    },
    VolunteerStatus.ASSIGNED: {
        VolunteerStatus.ACTIVE,
        VolunteerStatus.ON_LEAVE,
        VolunteerStatus.SUSPENDED,
        VolunteerStatus.INACTIVE,
        VolunteerStatus.EXITED,
        VolunteerStatus.ALUMNI,
    },
    VolunteerStatus.ON_LEAVE: {
        VolunteerStatus.ACTIVE,
        VolunteerStatus.ASSIGNED,
        VolunteerStatus.EXITED,
    },
    VolunteerStatus.SUSPENDED: {
        VolunteerStatus.ACTIVE,
        VolunteerStatus.INACTIVE,
        VolunteerStatus.EXITED,
    },
    VolunteerStatus.INACTIVE: {
        VolunteerStatus.ACTIVE,
        VolunteerStatus.EXITED,
        VolunteerStatus.ARCHIVED,
    },
    VolunteerStatus.EXITED: {VolunteerStatus.ALUMNI, VolunteerStatus.ARCHIVED},
    VolunteerStatus.ALUMNI: {VolunteerStatus.ARCHIVED},
    VolunteerStatus.ARCHIVED: set(),
}


def _coerce_date(value) -> date | None:
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    parsed = parse_date(str(value))
    if parsed is None:
        raise ValidationError(_("Enter a valid date."), code="invalid_date")
    return parsed


def _required_date(value) -> date:
    parsed = _coerce_date(value)
    if parsed is None:
        raise ValidationError(_("This date is required."), code="required_date")
    return parsed


def _coerce_taxonomy(model, value):
    """Resolve a taxonomy reference from an instance, pk, or code string."""
    if value is None:
        return None
    if isinstance(value, model):
        return value
    queryset = model.objects.all()
    if isinstance(value, str):
        return queryset.filter(code=value.upper()).first()
    return queryset.filter(pk=value).first()


def _coerce_profile_taxonomies(kwargs: dict) -> dict:
    """Resolve category/type/level references inside a kwargs mapping."""
    from .models import VolunteerCategory, VolunteerLevel, VolunteerType

    for key, model in (
        ("category", VolunteerCategory),
        ("volunteer_type", VolunteerType),
        ("volunteer_level", VolunteerLevel),
    ):
        if key in kwargs:
            kwargs[key] = _coerce_taxonomy(model, kwargs[key])
    return kwargs


def record_volunteer_audit(
    entity_type: str,
    entity_id,
    action: str,
    changed_by,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> VolunteerAuditRecord:
    """Append an immutable audit record without sensitive field values."""
    return VolunteerAuditRecord.objects.create(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        changed_by=changed_by,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


def _require_permission(user, permission_code: str) -> None:
    if user is None or not getattr(user, "is_authenticated", False):
        raise PermissionDenied(_("An authenticated actor is required."))
    if not (
        user_has_permission(user, permission_code)
        or user_has_permission(user, VOLUNTEERS_MANAGE)
    ):
        raise PermissionDenied(_("Permission denied for this action."))


def _reserve_reference(user, record_type: str, notes: str):
    return ReferenceNumberService(user=user).execute(
        module=ReferenceModules.VOLUNTEERS,
        record_type=record_type,
        notes=notes,
    )


def _confirm_reference(user, reference, record_id, notes: str) -> None:
    ConfirmReferenceAssignmentService(user=user).execute(
        reference=reference,
        record_id=record_id,
        notes=notes,
    )


def _snapshot_profile(profile: VolunteerProfile) -> dict:
    category = profile.category
    volunteer_type = profile.volunteer_type
    volunteer_level = profile.volunteer_level
    return {
        "category": category.code if category else None,
        "volunteer_type": volunteer_type.code if volunteer_type else None,
        "volunteer_level": volunteer_level.code if volunteer_level else None,
        "availability": profile.availability,
        "team_id": str(profile.team_id) if profile.team_id else None,
        "supervisor_id": str(profile.supervisor_id) if profile.supervisor_id else None,
    }


class VolunteerProfileService(BaseService):
    """Register, update, transition, archive, and restore volunteer profiles."""

    @transaction.atomic
    def create_profile(self, user_account, **kwargs) -> VolunteerProfile:
        _require_permission(self.user, VOLUNTEERS_CREATE)
        if VolunteerProfile.all_objects.filter(user=user_account).exists():
            raise ValidationError(
                _("This user already has a volunteer profile."),
                code="duplicate_volunteer_profile",
            )

        reference = _reserve_reference(
            self.user,
            record_type="volunteer",
            notes="Volunteer profile registration.",
        )
        status = kwargs.pop("status", VolunteerStatus.REGISTERED)
        _coerce_profile_taxonomies(kwargs)
        profile = VolunteerProfile(
            user=user_account,
            reference_number=reference.reference_number,
            status=status,
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        profile.full_clean()
        profile.save()
        _confirm_reference(
            self.user,
            reference,
            profile.pk,
            notes="Volunteer profile reference assigned.",
        )
        VolunteerStatusHistory.objects.create(
            profile=profile,
            from_status=status,
            to_status=status,
            changed_by=self.user,
            created_by=self.user,
            notes="Volunteer profile registered.",
        )
        record_volunteer_audit(
            "VolunteerProfile",
            profile.pk,
            VolunteerAuditAction.CREATED,
            self.user,
            to_data={
                "reference_number": profile.reference_number,
                "status": status,
                "user_id": str(user_account.pk),
            },
            notes="Volunteer profile registered.",
        )
        return profile

    @transaction.atomic
    def update_profile(self, profile: VolunteerProfile, **fields) -> VolunteerProfile:
        _require_permission(self.user, VOLUNTEERS_UPDATE)
        profile = VolunteerProfile.objects.select_for_update().get(pk=profile.pk)
        if profile.is_archived:
            raise ValidationError(_("Archived profiles cannot be updated."))
        before = _snapshot_profile(profile)
        _coerce_profile_taxonomies(fields)
        allowed_fields = {
            "national_id",
            "membership_number",
            "profile_photo",
            "date_of_birth",
            "gender",
            "nationality",
            "phone_number",
            "email",
            "residential_address",
            "region",
            "district",
            "community",
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
            "education_level",
            "occupation",
            "languages",
            "category",
            "volunteer_type",
            "volunteer_level",
            "availability",
            "team",
            "supervisor",
            "biography",
        }
        for name, value in fields.items():
            if name in allowed_fields:
                setattr(profile, name, value)
        profile.updated_by = self.user
        profile.full_clean()
        profile.save()
        record_volunteer_audit(
            "VolunteerProfile",
            profile.pk,
            VolunteerAuditAction.UPDATED,
            self.user,
            from_data=before,
            to_data=_snapshot_profile(profile),
            notes="Volunteer profile updated.",
        )
        return profile

    @transaction.atomic
    def update_status(
        self,
        profile: VolunteerProfile,
        new_status: str,
        notes: str = "",
    ) -> VolunteerProfile:
        _require_permission(self.user, VOLUNTEERS_UPDATE)
        profile = VolunteerProfile.objects.select_for_update().get(pk=profile.pk)
        if profile.is_archived or profile.status == VolunteerStatus.ARCHIVED:
            raise ValidationError(_("Archived profiles cannot transition status."))
        if new_status not in VolunteerStatus.values:
            raise ValidationError(_("Invalid volunteer status."))
        old_status = profile.status
        if (
            new_status == old_status
            or new_status not in ALLOWED_PROFILE_TRANSITIONS.get(old_status, set())
        ):
            raise ValidationError(
                _("Transition from %(old)s to %(new)s is not allowed.")
                % {"old": old_status, "new": new_status},
                code="invalid_status_transition",
            )
        profile.status = new_status
        profile.updated_by = self.user
        profile.full_clean()
        profile.save(update_fields=["status", "updated_by", "updated_at"])
        VolunteerStatusHistory.objects.create(
            profile=profile,
            from_status=old_status,
            to_status=new_status,
            changed_by=self.user,
            created_by=self.user,
            notes=notes,
        )
        record_volunteer_audit(
            "VolunteerProfile",
            profile.pk,
            VolunteerAuditAction.STATUS_CHANGED,
            self.user,
            from_data={"status": old_status},
            to_data={"status": new_status},
            notes=notes,
        )
        return profile

    @transaction.atomic
    def archive(self, profile: VolunteerProfile, notes: str = "") -> VolunteerProfile:
        _require_permission(self.user, "volunteers.archive")
        profile = VolunteerProfile.objects.select_for_update().get(pk=profile.pk)
        if profile.status not in {
            VolunteerStatus.INACTIVE,
            VolunteerStatus.EXITED,
            VolunteerStatus.ALUMNI,
        }:
            raise ValidationError(
                _("Only inactive or exited profiles may be archived.")
            )
        previous_status = profile.status
        profile.status = VolunteerStatus.ARCHIVED
        profile.archive(archived_by=self.user)
        profile.updated_by = self.user
        profile.save(update_fields=["status", "updated_by", "updated_at"])
        VolunteerStatusHistory.objects.create(
            profile=profile,
            from_status=previous_status,
            to_status=VolunteerStatus.ARCHIVED,
            changed_by=self.user,
            created_by=self.user,
            notes=notes,
        )
        record_volunteer_audit(
            "VolunteerProfile",
            profile.pk,
            VolunteerAuditAction.ARCHIVED,
            self.user,
            notes=notes,
        )
        return profile

    @transaction.atomic
    def restore(self, profile: VolunteerProfile, notes: str = "") -> VolunteerProfile:
        _require_permission(self.user, "volunteers.restore")
        profile = VolunteerProfile.all_objects.select_for_update().get(pk=profile.pk)
        if not profile.is_archived:
            raise ValidationError(_("This profile is not archived."))
        profile.unarchive()
        profile.status = VolunteerStatus.INACTIVE
        profile.updated_by = self.user
        profile.save(update_fields=["status", "updated_by", "updated_at"])
        VolunteerStatusHistory.objects.create(
            profile=profile,
            from_status=VolunteerStatus.ARCHIVED,
            to_status=VolunteerStatus.INACTIVE,
            changed_by=self.user,
            created_by=self.user,
            notes=notes,
        )
        record_volunteer_audit(
            "VolunteerProfile",
            profile.pk,
            VolunteerAuditAction.RESTORED,
            self.user,
            notes=notes,
        )
        return profile


class VolunteerRecruitmentService(BaseService):
    """Create recruitment campaigns and accept public applications."""

    @transaction.atomic
    def create_campaign(self, title: str, deadline, **kwargs) -> VolunteerRecruitment:
        _require_permission(self.user, VOLUNTEERS_CREATE)
        reference = _reserve_reference(
            self.user,
            record_type="recruitment",
            notes="Volunteer recruitment campaign.",
        )
        campaign = VolunteerRecruitment(
            title=title,
            reference_number=reference.reference_number,
            application_deadline=_required_date(deadline),
            created_by=self.user,
            updated_by=self.user,
            **_coerce_profile_taxonomies(kwargs),
        )
        campaign.full_clean()
        campaign.save()
        _confirm_reference(
            self.user,
            reference,
            campaign.pk,
            notes="Recruitment campaign reference assigned.",
        )
        record_volunteer_audit(
            "VolunteerRecruitment",
            campaign.pk,
            VolunteerAuditAction.CREATED,
            self.user,
            to_data={"reference_number": campaign.reference_number},
            notes="Recruitment campaign created.",
        )
        return campaign

    @transaction.atomic
    def submit_application(
        self,
        applicant_name: str,
        email: str,
        phone: str,
        **kwargs,
    ) -> VolunteerApplication:
        if not kwargs.get("consent_confirmed"):
            raise ValidationError(
                {
                    "consent_confirmed": _(
                        "Consent is required to submit an application."
                    )
                }
            )
        reference = _reserve_reference(
            self.user,
            record_type="application",
            notes="Volunteer application submission.",
        )
        application = VolunteerApplication(
            reference_number=reference.reference_number,
            applicant_name=applicant_name,
            email=email,
            phone_number=phone,
            created_by=self.user,
            updated_by=self.user,
            **_coerce_profile_taxonomies(kwargs),
        )
        application.full_clean()
        application.save()
        _confirm_reference(
            self.user,
            reference,
            application.pk,
            notes="Volunteer application reference assigned.",
        )
        record_volunteer_audit(
            "VolunteerApplication",
            application.pk,
            VolunteerAuditAction.APPLICATION_SUBMITTED,
            self.user,
            to_data={
                "reference_number": application.reference_number,
                "status": application.status,
            },
            notes="Volunteer application submitted.",
        )
        return application


class VolunteerApplicationWorkflowService(BaseService):
    """Validate the recruitment, screening, interview, and onboarding workflow."""

    @transaction.atomic
    def review_application(
        self,
        application: VolunteerApplication,
        new_status: str,
        notes: str = "",
    ) -> VolunteerApplication:
        _require_permission(self.user, VOLUNTEERS_UPDATE)
        application = VolunteerApplication.objects.select_for_update().get(
            pk=application.pk
        )
        transitions: dict[str, set[str]] = {
            ApplicationStatus.SUBMITTED: {
                ApplicationStatus.UNDER_SCREENING,
                ApplicationStatus.RETURNED,
                ApplicationStatus.REJECTED,
                ApplicationStatus.WITHDRAWN,
            },
            ApplicationStatus.RETURNED: {
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.WITHDRAWN,
            },
            ApplicationStatus.UNDER_SCREENING: {
                ApplicationStatus.SHORTLISTED,
                ApplicationStatus.REJECTED,
            },
            ApplicationStatus.SHORTLISTED: {
                ApplicationStatus.INTERVIEWED,
                ApplicationStatus.REJECTED,
            },
            ApplicationStatus.INTERVIEWED: {
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED,
            },
        }
        if new_status not in transitions.get(application.status, set()):
            raise ValidationError(
                _("This application transition is not allowed."),
                code="invalid_application_transition",
            )
        old_status = application.status
        application.status = new_status
        application.reviewed_by = self.user
        application.reviewed_at = timezone.now()
        application.decision_notes = notes
        application.updated_by = self.user
        application.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "decision_notes",
                "updated_by",
                "updated_at",
            ]
        )
        record_volunteer_audit(
            "VolunteerApplication",
            application.pk,
            VolunteerAuditAction.APPLICATION_REVIEWED,
            self.user,
            from_data={"status": old_status},
            to_data={"status": new_status},
            notes=notes,
        )
        return application

    @transaction.atomic
    def complete_screening(
        self,
        application: VolunteerApplication,
        **checks,
    ) -> VolunteerScreening:
        _require_permission(self.user, VOLUNTEERS_UPDATE)
        application = VolunteerApplication.objects.select_for_update().get(
            pk=application.pk
        )
        if application.status != ApplicationStatus.UNDER_SCREENING:
            raise ValidationError(_("Application is not under screening."))
        screening, _created = VolunteerScreening.objects.get_or_create(
            application=application,
            defaults={"reviewer": self.user, "created_by": self.user},
        )
        for field in (
            "identity_verified",
            "references_checked",
            "qualifications_verified",
            "safeguarding_cleared",
            "passed",
            "notes",
        ):
            if field in checks:
                setattr(screening, field, checks[field])
        screening.reviewer = self.user
        screening.full_clean()
        screening.save()
        next_status = (
            ApplicationStatus.SHORTLISTED
            if screening.passed
            else ApplicationStatus.REJECTED
        )
        application.status = next_status
        application.reviewed_by = self.user
        application.reviewed_at = timezone.now()
        application.updated_by = self.user
        application.save()
        record_volunteer_audit(
            "VolunteerScreening",
            screening.pk,
            VolunteerAuditAction.SCREENING_COMPLETED,
            self.user,
            to_data={"passed": screening.passed},
            notes="Volunteer screening completed.",
        )
        return screening

    @transaction.atomic
    def complete_interview(
        self,
        application: VolunteerApplication,
        **fields,
    ) -> VolunteerInterview:
        _require_permission(self.user, VOLUNTEERS_UPDATE)
        application = VolunteerApplication.objects.select_for_update().get(
            pk=application.pk
        )
        if application.status != ApplicationStatus.SHORTLISTED:
            raise ValidationError(_("Application is not shortlisted."))
        interview = VolunteerInterview(
            application=application,
            interviewer=self.user,
            created_by=self.user,
            completed=True,
            **fields,
        )
        interview.full_clean()
        interview.save()
        application.status = ApplicationStatus.INTERVIEWED
        application.reviewed_by = self.user
        application.reviewed_at = timezone.now()
        application.updated_by = self.user
        application.save()
        record_volunteer_audit(
            "VolunteerInterview",
            interview.pk,
            VolunteerAuditAction.INTERVIEW_COMPLETED,
            self.user,
            to_data={"passed": interview.passed, "score": interview.score},
            notes="Volunteer interview completed.",
        )
        return interview

    @transaction.atomic
    def register_approved_application(
        self,
        application: VolunteerApplication,
        user_account,
        **profile_fields,
    ) -> VolunteerProfile:
        _require_permission(self.user, VOLUNTEERS_CREATE)
        application = VolunteerApplication.objects.select_for_update().get(
            pk=application.pk
        )
        if application.status != ApplicationStatus.APPROVED:
            raise ValidationError(_("Only approved applications can be registered."))
        defaults = {
            "email": application.email,
            "phone_number": application.phone_number,
            "date_of_birth": application.date_of_birth,
            "gender": application.gender,
            "residential_address": application.address,
            "category": application.category,
            "volunteer_type": application.volunteer_type,
            "biography": application.motivation,
            "status": VolunteerStatus.REGISTERED,
        }
        defaults.update(profile_fields)
        return VolunteerProfileService(user=self.user).create_profile(
            user_account=user_account,
            **defaults,
        )

    @transaction.atomic
    def complete_onboarding(
        self,
        profile: VolunteerProfile,
        **fields,
    ) -> VolunteerOnboarding:
        _require_permission(self.user, VOLUNTEERS_UPDATE)
        profile = VolunteerProfile.objects.select_for_update().get(pk=profile.pk)
        if profile.status not in {
            VolunteerStatus.REGISTERED,
            VolunteerStatus.ONBOARDING,
        }:
            raise ValidationError(_("Profile is not eligible for onboarding."))
        onboarding, _created = VolunteerOnboarding.objects.get_or_create(
            profile=profile,
            defaults={"created_by": self.user},
        )
        for field, value in fields.items():
            if hasattr(onboarding, field):
                setattr(onboarding, field, value)
        onboarding.completed = True
        onboarding.completion_date = onboarding.completion_date or timezone.localdate()
        onboarding.full_clean()
        onboarding.save()
        if profile.status == VolunteerStatus.REGISTERED:
            VolunteerProfileService(user=self.user).update_status(
                profile,
                VolunteerStatus.ONBOARDING,
                notes="Onboarding started.",
            )
            profile.refresh_from_db()
        VolunteerProfileService(user=self.user).update_status(
            profile,
            VolunteerStatus.ACTIVE,
            notes="Onboarding completed.",
        )
        record_volunteer_audit(
            "VolunteerOnboarding",
            onboarding.pk,
            VolunteerAuditAction.ONBOARDING_COMPLETED,
            self.user,
            notes="Volunteer onboarding completed.",
        )
        return onboarding


class VolunteerAssignmentService(BaseService):
    @transaction.atomic
    def create_assignment(
        self,
        profile: VolunteerProfile,
        title: str,
        start_date,
        **kwargs,
    ) -> VolunteerAssignment:
        _require_permission(self.user, VOLUNTEERS_ASSIGN)
        profile = VolunteerProfile.objects.select_for_update().get(pk=profile.pk)
        if profile.status not in {
            VolunteerStatus.REGISTERED,
            VolunteerStatus.ACTIVE,
            VolunteerStatus.ASSIGNED,
        }:
            raise ValidationError(_("Volunteer is not eligible for assignment."))
        assignment = VolunteerAssignment(
            profile=profile,
            title=title,
            start_date=_required_date(start_date),
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        assignment.end_date = _coerce_date(assignment.end_date)
        assignment.full_clean()
        assignment.save()
        if profile.status != VolunteerStatus.ASSIGNED:
            VolunteerProfileService(user=self.user).update_status(
                profile,
                VolunteerStatus.ASSIGNED,
                notes=f"Assigned to {title}.",
            )
        record_volunteer_audit(
            "VolunteerAssignment",
            assignment.pk,
            VolunteerAuditAction.DEPLOYED,
            self.user,
            to_data={"profile_id": str(profile.pk), "title": title},
            notes=f"Volunteer assigned to {title}.",
        )
        return assignment

    @transaction.atomic
    def complete_assignment(
        self,
        assignment: VolunteerAssignment,
        end_date,
        outcomes_summary: str = "",
    ) -> VolunteerAssignment:
        _require_permission(self.user, VOLUNTEERS_ASSIGN)
        assignment = (
            VolunteerAssignment.objects.select_for_update()
            .select_related("profile", "supervisor")
            .get(pk=assignment.pk)
        )
        if not assignment.is_active:
            raise ValidationError(_("Assignment is already closed."))
        assignment.end_date = _required_date(end_date)
        assignment.is_active = False
        assignment.updated_by = self.user
        assignment.full_clean()
        assignment.save()
        VolunteerDeploymentHistory.objects.create(
            profile=assignment.profile,
            assignment_title=assignment.title,
            program_or_project=assignment.program_name or assignment.project_name,
            start_date=assignment.start_date,
            end_date=assignment.end_date,
            supervisor_name=(
                str(assignment.supervisor) if assignment.supervisor else ""
            ),
            outcomes_summary=outcomes_summary,
            created_by=self.user,
        )
        return assignment


class VolunteerAttendanceService(BaseService):
    @transaction.atomic
    def log_attendance(
        self,
        profile: VolunteerProfile,
        date,
        activity_name: str,
        status: str = AttendanceStatus.PRESENT,
        hours=0.00,
        **kwargs,
    ) -> VolunteerAttendance:
        _require_permission(self.user, VOLUNTEERS_MANAGE_ATTENDANCE)
        attendance = VolunteerAttendance(
            profile=profile,
            date=_required_date(date),
            activity_name=activity_name,
            status=status,
            hours_served=hours,
            created_by=self.user,
            **kwargs,
        )
        attendance.full_clean()
        attendance.save()
        record_volunteer_audit(
            "VolunteerAttendance",
            attendance.pk,
            VolunteerAuditAction.ATTENDANCE_LOGGED,
            self.user,
            to_data={
                "date": str(attendance.date),
                "hours": float(attendance.hours_served),
                "status": status,
            },
            notes=f"Attendance recorded for {activity_name}.",
        )
        return attendance


class VolunteerTrainingService(BaseService):
    @transaction.atomic
    def record_training(
        self,
        profile: VolunteerProfile,
        title: str,
        start_date,
        **kwargs,
    ) -> VolunteerTraining:
        _require_permission(self.user, VOLUNTEERS_MANAGE_TRAINING)
        training = VolunteerTraining(
            profile=profile,
            title=title,
            start_date=_required_date(start_date),
            created_by=self.user,
            **kwargs,
        )
        training.completion_date = _coerce_date(training.completion_date)
        training.full_clean()
        training.save()
        record_volunteer_audit(
            "VolunteerTraining",
            training.pk,
            VolunteerAuditAction.TRAINING_COMPLETED,
            self.user,
            to_data={"title": title, "completed": bool(training.completion_date)},
            notes="Volunteer training recorded.",
        )
        return training


class VolunteerPerformanceService(BaseService):
    @transaction.atomic
    def record_review(
        self,
        profile: VolunteerProfile,
        review_period: str,
        score: int,
        **kwargs,
    ) -> VolunteerPerformance:
        _require_permission(self.user, VOLUNTEERS_MANAGE_PERFORMANCE)
        review = VolunteerPerformance(
            profile=profile,
            review_period=review_period,
            overall_score=score,
            reviewer=self.user,
            created_by=self.user,
            **kwargs,
        )
        review.full_clean()
        review.save()
        record_volunteer_audit(
            "VolunteerPerformance",
            review.pk,
            VolunteerAuditAction.REVIEWED,
            self.user,
            to_data={"review_period": review_period, "score": score},
            notes="Volunteer performance review recorded.",
        )
        return review


class VolunteerRecognitionService(BaseService):
    @transaction.atomic
    def award_recognition(
        self,
        profile: VolunteerProfile,
        title: str,
        **kwargs,
    ) -> VolunteerRecognition:
        _require_permission(self.user, VOLUNTEERS_CREATE)
        recognition = VolunteerRecognition(
            profile=profile,
            title=title,
            created_by=self.user,
            **kwargs,
        )
        recognition.full_clean()
        recognition.save()
        record_volunteer_audit(
            "VolunteerRecognition",
            recognition.pk,
            VolunteerAuditAction.AWARDED,
            self.user,
            to_data={"title": title},
            notes="Volunteer recognition awarded.",
        )
        return recognition


class VolunteerLeaveService(BaseService):
    @transaction.atomic
    def apply_leave(
        self,
        profile: VolunteerProfile,
        leave_type: str,
        start_date,
        end_date,
        reason: str,
    ) -> VolunteerLeave:
        if self.user != profile.user:
            _require_permission(self.user, VOLUNTEERS_MANAGE_LEAVE)
        leave = VolunteerLeave(
            profile=profile,
            leave_type=leave_type,
            start_date=_required_date(start_date),
            end_date=_required_date(end_date),
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        leave.full_clean()
        if VolunteerLeave.objects.filter(
            profile=profile,
            status__in=[LeaveStatus.SUBMITTED, LeaveStatus.APPROVED],
            start_date__lte=leave.end_date,
            end_date__gte=leave.start_date,
        ).exists():
            raise ValidationError(_("This leave overlaps an existing leave request."))
        leave.save()
        return leave

    @transaction.atomic
    def approve_leave(
        self,
        leave: VolunteerLeave,
        approve: bool = True,
        notes: str = "",
    ) -> VolunteerLeave:
        _require_permission(self.user, VOLUNTEERS_MANAGE_LEAVE)
        leave = (
            VolunteerLeave.objects.select_for_update()
            .select_related("profile")
            .get(pk=leave.pk)
        )
        if leave.status != LeaveStatus.SUBMITTED:
            raise ValidationError(_("Only submitted leave can be decided."))
        leave.status = LeaveStatus.APPROVED if approve else LeaveStatus.REJECTED
        leave.approver = self.user
        leave.approval_notes = notes
        leave.updated_by = self.user
        leave.save()
        if approve and leave.start_date <= timezone.localdate() <= leave.end_date:
            VolunteerProfileService(user=self.user).update_status(
                leave.profile,
                VolunteerStatus.ON_LEAVE,
                notes="Approved leave is active.",
            )
        record_volunteer_audit(
            "VolunteerLeave",
            leave.pk,
            (
                VolunteerAuditAction.LEAVE_APPROVED
                if approve
                else VolunteerAuditAction.LEAVE_REJECTED
            ),
            self.user,
            to_data={"status": leave.status},
            notes=notes,
        )
        return leave


class VolunteerExitService(BaseService):
    @transaction.atomic
    def initiate_exit(
        self,
        profile: VolunteerProfile,
        reason: str,
        effective_date,
        **kwargs,
    ) -> VolunteerExit:
        _require_permission(self.user, VOLUNTEERS_MANAGE_EXIT)
        if VolunteerExit.objects.filter(profile=profile).exists():
            raise ValidationError(
                _("An exit process already exists for this volunteer.")
            )
        exit_record = VolunteerExit(
            profile=profile,
            reason=reason,
            effective_date=_required_date(effective_date),
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        exit_record.full_clean()
        exit_record.save()
        return exit_record

    @transaction.atomic
    def complete_exit(self, exit_rec: VolunteerExit) -> VolunteerExit:
        _require_permission(self.user, VOLUNTEERS_MANAGE_EXIT)
        exit_rec = (
            VolunteerExit.objects.select_for_update()
            .select_related("profile")
            .get(pk=exit_rec.pk)
        )
        if exit_rec.status not in {
            ExitStatus.INITIATED,
            ExitStatus.INTERVIEW_COMPLETED,
            ExitStatus.CLEARANCE_PENDING,
            ExitStatus.APPROVED,
        }:
            raise ValidationError(_("This exit record is already final."))
        if not (exit_rec.assets_returned and exit_rec.documents_returned):
            raise ValidationError(_("Asset and document clearance must be completed."))
        exit_rec.clearance_approved = True
        exit_rec.status = (
            ExitStatus.ALUMNI if exit_rec.transition_to_alumni else ExitStatus.EXITED
        )
        exit_rec.updated_by = self.user
        exit_rec.save()
        profile = exit_rec.profile
        target_status = (
            VolunteerStatus.ALUMNI
            if exit_rec.transition_to_alumni
            else VolunteerStatus.EXITED
        )
        if profile.status in ALLOWED_PROFILE_TRANSITIONS and target_status in (
            ALLOWED_PROFILE_TRANSITIONS[profile.status]
        ):
            VolunteerProfileService(user=self.user).update_status(
                profile,
                target_status,
                notes="Volunteer exit completed.",
            )
        else:
            raise ValidationError(_("Volunteer status is not eligible for exit."))
        profile.refresh_from_db()
        profile.exit_date = exit_rec.effective_date
        profile.exit_reason = exit_rec.reason
        profile.updated_by = self.user
        profile.save(
            update_fields=["exit_date", "exit_reason", "updated_by", "updated_at"]
        )
        for assignment in VolunteerAssignment.objects.filter(
            profile=profile,
            is_active=True,
        ):
            VolunteerAssignmentService(user=self.user).complete_assignment(
                assignment,
                end_date=exit_rec.effective_date,
                outcomes_summary="Closed during volunteer exit.",
            )
        record_volunteer_audit(
            "VolunteerExit",
            exit_rec.pk,
            VolunteerAuditAction.EXITED,
            self.user,
            to_data={"status": target_status},
            notes="Volunteer exit completed.",
        )
        return exit_rec


class VolunteerActivityService(BaseService):
    """Record and manage volunteer service activity logs."""

    @transaction.atomic
    def log_activity(
        self,
        profile: VolunteerProfile,
        activity_title: str,
        activity_date,
        **kwargs,
    ) -> VolunteerActivityLog:
        _require_permission(self.user, VOLUNTEERS_MANAGE_ACTIVITY)
        profile = VolunteerProfile.objects.select_for_update().get(pk=profile.pk)
        if profile.is_archived or profile.status in {
            VolunteerStatus.EXITED,
            VolunteerStatus.ALUMNI,
        }:
            raise ValidationError(
                _("Inactive or exited volunteers cannot have activity logged.")
            )
        entry = VolunteerActivityLog(
            profile=profile,
            activity_title=activity_title,
            activity_date=_required_date(activity_date),
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        entry.full_clean()
        entry.save()
        record_volunteer_audit(
            "VolunteerActivityLog",
            entry.pk,
            VolunteerAuditAction.ACTIVITY_LOGGED,
            self.user,
            to_data={
                "activity_title": entry.activity_title,
                "activity_date": str(entry.activity_date),
                "hours_served": str(entry.hours_served),
            },
            notes="Volunteer activity logged.",
        )
        return entry

    @transaction.atomic
    def update_activity_log(
        self,
        entry: VolunteerActivityLog,
        **fields,
    ) -> VolunteerActivityLog:
        _require_permission(self.user, VOLUNTEERS_MANAGE_ACTIVITY)
        entry = VolunteerActivityLog.objects.select_for_update().get(pk=entry.pk)
        for name, value in fields.items():
            if hasattr(entry, name):
                setattr(entry, name, value)
        entry.updated_by = self.user
        entry.full_clean()
        entry.save()
        record_volunteer_audit(
            "VolunteerActivityLog",
            entry.pk,
            VolunteerAuditAction.UPDATED,
            self.user,
            notes="Volunteer activity log updated.",
        )
        return entry


class VolunteerDisciplinaryService(BaseService):
    """Open, review, and resolve volunteer disciplinary records."""

    @transaction.atomic
    def open_disciplinary(
        self,
        profile: VolunteerProfile,
        incident_date,
        nature_of_concern: str,
        **kwargs,
    ) -> VolunteerDisciplinaryRecord:
        _require_permission(self.user, VOLUNTEERS_MANAGE_DISCIPLINARY)
        profile = VolunteerProfile.objects.select_for_update().get(pk=profile.pk)
        reference = _reserve_reference(
            self.user,
            record_type="disciplinary",
            notes="Volunteer disciplinary record.",
        )
        record = VolunteerDisciplinaryRecord(
            profile=profile,
            reference_number=reference.reference_number,
            incident_date=_required_date(incident_date),
            nature_of_concern=nature_of_concern,
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        record.full_clean()
        record.save()
        _confirm_reference(
            self.user,
            reference,
            record.pk,
            notes="Disciplinary reference assigned.",
        )
        record_volunteer_audit(
            "VolunteerDisciplinaryRecord",
            record.pk,
            VolunteerAuditAction.DISCIPLINARY_OPENED,
            self.user,
            to_data={"reference_number": record.reference_number},
            notes="Disciplinary record opened.",
        )
        return record

    @transaction.atomic
    def decide_disciplinary(
        self,
        record: VolunteerDisciplinaryRecord,
        status: str,
        decision: str = "",
        investigation_summary: str = "",
        corrective_action: str = "",
        effective_date=None,
    ) -> VolunteerDisciplinaryRecord:
        _require_permission(self.user, VOLUNTEERS_MANAGE_DISCIPLINARY)
        record = VolunteerDisciplinaryRecord.objects.select_for_update().get(
            pk=record.pk
        )
        if status not in DisciplinaryStatus.values:
            raise ValidationError(_("Invalid disciplinary status."))
        record.status = status
        record.decision = decision
        record.investigation_summary = investigation_summary
        record.corrective_action = corrective_action
        record.effective_date = _coerce_date(effective_date)
        record.decided_by = self.user
        record.decided_at = timezone.now()
        record.updated_by = self.user
        record.full_clean()
        record.save()
        record_volunteer_audit(
            "VolunteerDisciplinaryRecord",
            record.pk,
            VolunteerAuditAction.DISCIPLINARY_DECIDED,
            self.user,
            to_data={"status": status, "decision": decision},
            notes="Disciplinary record decided.",
        )
        if status in {DisciplinaryStatus.RESOLVED, DisciplinaryStatus.APPLIED}:
            self._apply_profile_consequence(record.profile, status, decision)
        return record

    @transaction.atomic
    def reopen_disciplinary(
        self,
        record: VolunteerDisciplinaryRecord,
        notes: str = "",
    ) -> VolunteerDisciplinaryRecord:
        _require_permission(self.user, VOLUNTEERS_MANAGE_DISCIPLINARY)
        record = VolunteerDisciplinaryRecord.objects.select_for_update().get(
            pk=record.pk
        )
        record.status = DisciplinaryStatus.UNDER_REVIEW
        record.decision = ""
        record.decided_by = None
        record.decided_at = None
        record.updated_by = self.user
        record.notes = notes or record.notes
        record.save(
            update_fields=[
                "status",
                "decision",
                "decided_by",
                "decided_at",
                "updated_by",
                "notes",
            ]
        )
        record_volunteer_audit(
            "VolunteerDisciplinaryRecord",
            record.pk,
            VolunteerAuditAction.DISCIPLINARY_REOPENED,
            self.user,
            notes="Disciplinary record reopened.",
        )
        return record

    def _apply_profile_consequence(
        self,
        profile: VolunteerProfile,
        status: str,
        decision: str,
    ) -> None:
        if decision == "SUSPENSION":
            profile.status = VolunteerStatus.SUSPENDED
            profile.updated_by = self.user
            profile.save(update_fields=["status", "updated_by", "updated_at"])
        elif decision == "TERMINATION":
            profile.exit_date = timezone.localdate()
            profile.exit_reason = "DISMISSAL"
            profile.status = VolunteerStatus.EXITED
            profile.updated_by = self.user
            profile.save(
                update_fields=[
                    "status",
                    "exit_date",
                    "exit_reason",
                    "updated_by",
                    "updated_at",
                ]
            )


class VolunteerCommunicationService(BaseService):
    """Record communications sent to volunteers."""

    @transaction.atomic
    def record_communication(
        self,
        profile: VolunteerProfile,
        channel: str,
        subject: str,
        body: str = "",
        **kwargs,
    ) -> VolunteerCommunication:
        _require_permission(self.user, VOLUNTEERS_MANAGE_COMMUNICATIONS)
        if channel not in CommunicationChannel.values:
            raise ValidationError(_("Invalid communication channel."))
        message = VolunteerCommunication(
            profile=profile,
            channel=channel,
            subject=subject,
            body=body,
            sent_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        message.full_clean()
        message.save()
        record_volunteer_audit(
            "VolunteerCommunication",
            message.pk,
            VolunteerAuditAction.COMMUNICATION_SENT,
            self.user,
            to_data={"channel": channel, "subject": subject},
            notes="Volunteer communication recorded.",
        )
        return message


class VolunteerDocumentService(BaseService):
    """Upload, version, approve, and retain volunteer documents."""

    @transaction.atomic
    def upload_document(
        self,
        profile: VolunteerProfile,
        title: str,
        file,
        document_type: str = "General",
        is_confidential: bool = True,
        retention_until=None,
        status: str = VolunteerDocumentStatus.PENDING_APPROVAL,
    ) -> VolunteerDocument:
        _require_permission(self.user, VOLUNTEERS_MANAGE_DOCUMENTS)
        profile = VolunteerProfile.objects.select_for_update().get(pk=profile.pk)
        latest = (
            VolunteerDocument.objects.filter(profile=profile)
            .order_by("-version")
            .first()
        )
        next_version = latest.version + 1 if latest else 1
        document = VolunteerDocument(
            profile=profile,
            title=title,
            document_type=document_type,
            file=file,
            is_confidential=is_confidential,
            retention_until=_coerce_date(retention_until),
            status=status,
            version=next_version,
            supersedes=latest,
            created_by=self.user,
            updated_by=self.user,
        )
        document.full_clean()
        document.save()
        record_volunteer_audit(
            "VolunteerDocument",
            document.pk,
            VolunteerAuditAction.DOCUMENT_UPLOADED,
            self.user,
            to_data={"title": title, "version": document.version},
            notes="Volunteer document uploaded.",
        )
        return document

    @transaction.atomic
    def approve_document(
        self,
        document: VolunteerDocument,
        notes: str = "",
    ) -> VolunteerDocument:
        _require_permission(self.user, VOLUNTEERS_MANAGE_DOCUMENTS)
        document = VolunteerDocument.objects.select_for_update().get(pk=document.pk)
        if document.status != VolunteerDocumentStatus.PENDING_APPROVAL:
            raise ValidationError(_("Only pending documents can be approved."))
        document.status = VolunteerDocumentStatus.APPROVED
        document.approved_by = self.user
        document.approved_at = timezone.now()
        document.updated_by = self.user
        document.notes = notes or document.notes
        document.save()
        record_volunteer_audit(
            "VolunteerDocument",
            document.pk,
            VolunteerAuditAction.DOCUMENT_APPROVED,
            self.user,
            notes="Volunteer document approved.",
        )
        return document

    @transaction.atomic
    def reject_document(
        self,
        document: VolunteerDocument,
        notes: str = "",
    ) -> VolunteerDocument:
        _require_permission(self.user, VOLUNTEERS_MANAGE_DOCUMENTS)
        document = VolunteerDocument.objects.select_for_update().get(pk=document.pk)
        document.status = VolunteerDocumentStatus.REJECTED
        document.updated_by = self.user
        document.notes = notes or document.notes
        document.save()
        record_volunteer_audit(
            "VolunteerDocument",
            document.pk,
            VolunteerAuditAction.DOCUMENT_REJECTED,
            self.user,
            notes="Volunteer document rejected.",
        )
        return document

    @transaction.atomic
    def archive_document(
        self,
        document: VolunteerDocument,
        notes: str = "",
    ) -> VolunteerDocument:
        _require_permission(self.user, VOLUNTEERS_MANAGE_DOCUMENTS)
        document = VolunteerDocument.objects.select_for_update().get(pk=document.pk)
        document.status = VolunteerDocumentStatus.ARCHIVED
        document.updated_by = self.user
        document.notes = notes or document.notes
        document.save()
        record_volunteer_audit(
            "VolunteerDocument",
            document.pk,
            VolunteerAuditAction.DOCUMENT_ARCHIVED,
            self.user,
            notes="Volunteer document archived.",
        )
        return document
