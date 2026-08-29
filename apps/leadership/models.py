"""
Data models for the leadership management module.

The module implements the official leadership registry for the SITADC Youth
Organization: leadership profiles, appointments and terms of office, reporting
lines, attendance, leave, tasks, goals, KPIs, coaching, mentorship, performance
reviews, recognition, disciplinary records, succession plans, documents,
scorecards, status history and the immutable leadership audit log.
"""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
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
from apps.organizations.models import OrganizationUnit, Position

from .constants import (
    AppointmentStatus,
    AppointmentType,
    AttendanceStatus,
    AttendanceType,
    CoachingCategory,
    ConfidentialityLevel,
    DisciplinaryStatus,
    DisciplinaryType,
    DocumentCategory,
    GoalStatus,
    KpiStatus,
    LeadershipAuditAction,
    LeadershipLevel,
    LeadershipStatus,
    LeaveStatus,
    LeaveType,
    MentorshipStatus,
    RatingScale,
    RecognitionCategory,
    RenewalStatus,
    ReviewCycle,
    ReviewStatus,
    ScorecardStatus,
    SuccessionReadiness,
    SuccessionRisk,
    TaskPriority,
    TaskStatus,
    TermStatus,
)
from .managers import LeadershipAppointmentManager, LeadershipProfileManager

IMMUTABLE_LEADERSHIP_RECORD_MESSAGE = _(
    "Leadership audit and history records are immutable and cannot be modified."
)


class LeadershipProfile(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    ArchivableModel,
    NotesModel,
):
    """
    A comprehensive leadership record for an individual leader.

    Each profile is linked to an authenticated user and optionally references
    the organizational structure (position and unit) for integration with the
    Phase 08 organizational structure module.
    """

    reference_number = models.CharField(
        _("Leadership reference number"),
        max_length=60,
        unique=True,
        db_index=True,
        help_text=_("Immutable reference number issued by the numbering service."),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leadership_profile",
        verbose_name=_("Linked user"),
        help_text=_("The authenticated user this leader is linked to."),
    )
    profile_photo = models.ImageField(
        _("Profile photograph"),
        upload_to="leadership/profiles/",
        null=True,
        blank=True,
    )
    national_id = models.CharField(
        _("National ID or identification number"), max_length=60, blank=True
    )
    gender = models.CharField(_("Gender"), max_length=20, blank=True)
    date_of_birth = models.DateField(_("Date of birth"), null=True, blank=True)
    phone_number = models.CharField(_("Phone number"), max_length=30, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    residential_address = models.TextField(_("Residential address"), blank=True)
    emergency_contact_name = models.CharField(
        _("Emergency contact name"), max_length=150, blank=True
    )
    emergency_contact_phone = models.CharField(
        _("Emergency contact phone"), max_length=30, blank=True
    )

    leadership_level = models.CharField(
        _("Leadership level"),
        max_length=40,
        choices=LeadershipLevel.choices,
        db_index=True,
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_profiles",
        verbose_name=_("Leadership position"),
    )
    organizational_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_profiles",
        verbose_name=_("Organizational unit"),
    )
    directorate = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_profiles_in_directorate",
        verbose_name=_("Directorate"),
        help_text=_("The directorate the leader reports into, where applicable."),
    )
    region = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_profiles_in_region",
        verbose_name=_("Region"),
        help_text=_("The region the leader is assigned to, where applicable."),
    )
    district = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_profiles_in_district",
        verbose_name=_("District"),
        help_text=_("The district the leader is assigned to, where applicable."),
    )
    community = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_profiles_in_community",
        verbose_name=_("Community"),
        help_text=_("The community the leader is assigned to, where applicable."),
    )
    supervisor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
        verbose_name=_("Immediate supervisor"),
        help_text=_("The leader this record reports to."),
    )
    reporting_line = models.JSONField(
        _("Reporting line"),
        default=list,
        blank=True,
        help_text=_(
            "JSON array representing the full reporting chain "
            "from top to this leader."
        ),
    )

    appointment_date = models.DateField(_("Appointment date"), null=True, blank=True)
    term_expiry_date = models.DateField(_("Term expiry date"), null=True, blank=True)
    terms_completed = models.PositiveSmallIntegerField(
        _("Number of completed terms"), default=0
    )
    max_terms = models.PositiveSmallIntegerField(
        _("Maximum permitted terms"), default=2
    )
    term_status = models.CharField(
        _("Term status"),
        max_length=20,
        choices=TermStatus.choices,
        default=TermStatus.CURRENT,
        db_index=True,
    )
    renewal_eligible = models.BooleanField(_("Renewal eligible"), default=False)
    renewal_status = models.CharField(
        _("Renewal status"),
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.NOT_ELIGIBLE,
    )

    qualifications = models.TextField(_("Qualifications"), blank=True)
    professional_skills = models.TextField(_("Professional skills"), blank=True)
    areas_of_expertise = models.TextField(_("Areas of expertise"), blank=True)
    biography = models.TextField(_("Biography"), blank=True)

    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=LeadershipStatus.choices,
        default=LeadershipStatus.NOMINATED,
        db_index=True,
    )

    objects: ClassVar[LeadershipProfileManager] = LeadershipProfileManager()

    class Meta:
        verbose_name = _("Leadership Profile")
        verbose_name_plural = _("Leadership Profiles")
        ordering = ("user__last_name", "user__first_name")
        indexes: ClassVar[list] = [
            models.Index(fields=["status", "leadership_level"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.full_name} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        from .validators import validate_profile_dates, validate_supervisor_not_self

        validate_profile_dates(self.appointment_date, self.term_expiry_date)
        validate_supervisor_not_self(self, self.supervisor)

    def save(self, *args, **kwargs) -> None:
        generated_reference = None
        if not self.reference_number:
            # System-generated identifier: issue through the centralized
            # numbering service before validation requires the value.  This
            # keeps every creation path (web form, Django admin, shell)
            # consistent without ever regenerating an established reference.
            from .services import issue_leadership_reference

            # Use created_by if available, otherwise fall back to a system user
            # to ensure reference generation works even when saved via forms
            # without explicit created_by (e.g., Django admin, ModelForm).
            created_by_user = self.created_by
            if created_by_user is None:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                # Try to get a superuser as fallback for reference generation
                created_by_user = User.objects.filter(is_superuser=True).first()

            self.reference_number = issue_leadership_reference(
                created_by_user,
                "leader",
                notes="Leadership profile registration.",
            )
            generated_reference = self.reference_number
        self.full_clean()
        super().save(*args, **kwargs)
        if generated_reference:
            from .services import confirm_leadership_reference

            confirm_leadership_reference(
                self.created_by,
                generated_reference,
                self.pk,
                notes="Profile registration.",
            )

    @property
    def current_appointment(self):
        """Return the active appointment, if any."""
        return (
            self.appointments.filter(status=AppointmentStatus.ACTIVE)
            .select_related("position")
            .first()
        )

    @property
    def is_currently_active(self) -> bool:
        return self.status in (
            LeadershipStatus.ACTIVE,
            LeadershipStatus.ACTING,
            LeadershipStatus.PROBATION,
        )


class LeadershipAppointment(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """
    A formal leadership appointment with a tracked workflow lifecycle.

    Historical appointments are immutable and must never be deleted.
    """

    reference_number = models.CharField(
        _("Appointment reference number"),
        max_length=60,
        unique=True,
        db_index=True,
        help_text=_("Immutable reference number issued by the numbering service."),
    )
    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name=_("Leader"),
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="leadership_appointments",
        verbose_name=_("Position"),
    )
    organizational_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.PROTECT,
        related_name="leadership_appointments",
        verbose_name=_("Organizational unit"),
    )
    appointment_type = models.CharField(
        _("Appointment type"),
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.PERMANENT,
        db_index=True,
    )
    appointing_authority = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_appointments_authorized",
        verbose_name=_("Appointing authority"),
    )
    appointment_date = models.DateField(
        _("Appointment date"), default=timezone.localdate
    )
    effective_date = models.DateField(_("Effective date"), default=timezone.localdate)
    term_start = models.DateField(_("Term start"), null=True, blank=True)
    term_end = models.DateField(_("Term end"), null=True, blank=True)
    renewal_eligible = models.BooleanField(_("Renewal eligible"), default=False)
    renewal_status = models.CharField(
        _("Renewal status"),
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.NOT_ELIGIBLE,
    )
    terms_completed = models.PositiveSmallIntegerField(
        _("Number of completed terms"), default=0
    )
    max_terms = models.PositiveSmallIntegerField(
        _("Maximum permitted terms"), default=2
    )
    appointment_letter = models.FileField(
        _("Appointment letter"),
        upload_to="leadership/appointments/letters/",
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.DRAFT,
        db_index=True,
    )

    objects = LeadershipAppointmentManager()

    class Meta:
        verbose_name = _("Leadership Appointment")
        verbose_name_plural = _("Leadership Appointments")
        ordering = ("-effective_date", "-created_at")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["profile", "position"],
                condition=models.Q(status=AppointmentStatus.ACTIVE),
                name="unique_active_leadership_appointment_per_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.profile} - {self.position.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        from .validators import (
            validate_appointment_dates,
            validate_no_overlapping_active_appointment,
        )

        validate_appointment_dates(self.effective_date, self.term_start, self.term_end)
        if self.profile_id and self.position_id:
            validate_no_overlapping_active_appointment(
                self.profile, self.position, exclude_pk=self.pk
            )

    def save(self, *args, **kwargs) -> None:
        generated_reference = None
        if not self.reference_number:
            from .services import issue_leadership_reference

            # Use created_by if available, otherwise fall back to a system user
            # to ensure reference generation works even when saved via forms
            # without explicit created_by (e.g., Django admin, ModelForm).
            created_by_user = self.created_by
            if created_by_user is None:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                # Try to get a superuser as fallback for reference generation
                created_by_user = User.objects.filter(is_superuser=True).first()

            self.reference_number = issue_leadership_reference(
                created_by_user,
                "appointment",
                notes="Leadership appointment.",
            )
            generated_reference = self.reference_number
        self.full_clean()
        super().save(*args, **kwargs)
        if generated_reference:
            from .services import confirm_leadership_reference

            confirm_leadership_reference(
                self.created_by,
                generated_reference,
                self.pk,
                notes="Leadership appointment created.",
            )

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            _("Leadership appointment records cannot be deleted."),
            code="immutable_leadership_appointment",
        )

    @property
    def is_expired(self) -> bool:
        return bool(self.term_end and self.term_end < timezone.localdate())

    @property
    def is_expiring(self, days: int = 30) -> bool:
        """Whether the term ends within the given number of days."""
        if not self.term_end:
            return False
        return (
            timezone.localdate()
            <= self.term_end
            <= timezone.localdate() + timedelta(days=days)
        )

    def auto_expire(self) -> None:
        """Automatically expire an appointment once its term end passes."""
        if self.is_expired and self.status == AppointmentStatus.ACTIVE:
            self.status = AppointmentStatus.EXPIRED
            self.save(update_fields=["status"])


class LeadershipStatusHistory(UUIDModel, TimeStampedModel, NotesModel):
    """Immutable record of every leadership profile status change."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name=_("Leader"),
    )
    from_status = models.CharField(
        _("From status"), max_length=30, choices=LeadershipStatus.choices
    )
    to_status = models.CharField(
        _("To status"), max_length=30, choices=LeadershipStatus.choices
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_status_changes",
        verbose_name=_("Changed by"),
    )
    changed_at = models.DateTimeField(_("Changed at"), default=timezone.now)

    class Meta:
        verbose_name = _("Leadership Status History")
        verbose_name_plural = _("Leadership Status History")
        ordering = ("-changed_at", "-created_at")
        indexes: ClassVar[list] = [
            models.Index(fields=["profile", "changed_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.profile}: {self.get_from_status_display()} "
            f"-> {self.get_to_status_display()}"
        )

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(
                IMMUTABLE_LEADERSHIP_RECORD_MESSAGE,
                code="immutable_leadership_status_history",
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_LEADERSHIP_RECORD_MESSAGE,
            code="immutable_leadership_status_history",
        )


class LeadershipAttendance(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Attendance record for a leadership activity."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("Leader"),
    )
    attendance_type = models.CharField(
        _("Attendance type"),
        max_length=40,
        choices=AttendanceType.choices,
        db_index=True,
    )
    attendance_date = models.DateField(_("Attendance date"), default=timezone.localdate)
    activity_name = models.CharField(_("Activity name"), max_length=200, blank=True)
    venue = models.CharField(_("Venue / location"), max_length=200, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )

    class Meta:
        verbose_name = _("Leadership Attendance")
        verbose_name_plural = _("Leadership Attendance")
        ordering = ("-attendance_date", "-created_at")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=[
                    "profile",
                    "attendance_type",
                    "attendance_date",
                    "activity_name",
                ],
                name="unique_leadership_attendance_record",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.profile} - {self.get_attendance_type_display()} "
            f"({self.attendance_date})"
        )


class LeadershipLeave(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Leave request and record for a leader."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="leave_records",
        verbose_name=_("Leader"),
    )
    leave_type = models.CharField(
        _("Leave type"), max_length=30, choices=LeaveType.choices, db_index=True
    )
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    reason = models.TextField(_("Reason"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=LeaveStatus.choices,
        default=LeaveStatus.PENDING,
        db_index=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_leave_approvals",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Leadership Leave")
        verbose_name_plural = _("Leadership Leave")
        ordering = ("-start_date", "-created_at")

    def __str__(self) -> str:
        return (
            f"{self.profile} - {self.get_leave_type_display()} "
            f"({self.start_date} to {self.end_date})"
        )

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def clean(self) -> None:
        super().clean()
        from .validators import validate_leave_dates, validate_overlapping_leave

        validate_leave_dates(self.start_date, self.end_date)
        if self.profile_id:
            validate_overlapping_leave(
                self.profile, self.start_date, self.end_date, exclude_pk=self.pk
            )


class LeadershipTask(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """Task assigned to a leader."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("Assigned leader"),
    )
    title = models.CharField(_("Task title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
        db_index=True,
    )
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.NOT_STARTED,
        db_index=True,
    )
    progress = models.PositiveSmallIntegerField(_("Progress (%)"), default=0)
    supporting_document = models.FileField(
        _("Supporting document"),
        upload_to="leadership/tasks/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Leadership Task")
        verbose_name_plural = _("Leadership Tasks")
        ordering = ("-due_date", "-created_at")
        indexes: ClassVar[list] = [
            models.Index(fields=["profile", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.profile})"

    def clean(self) -> None:
        super().clean()
        if self.progress < 0 or self.progress > 100:
            raise ValidationError(
                _("Progress must be between 0 and 100."), code="invalid_progress"
            )
        if self.progress == 100 and self.status != TaskStatus.COMPLETED:
            self.status = TaskStatus.COMPLETED


class LeadershipGoal(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """A measurable goal for a leader aligned with the strategic plan."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="goals",
        verbose_name=_("Leader"),
    )
    title = models.CharField(_("Goal title"), max_length=200)
    strategic_objective = models.CharField(
        _("Strategic objective"), max_length=250, blank=True
    )
    performance_indicator = models.CharField(
        _("Performance indicator"), max_length=250, blank=True
    )
    target_value = models.DecimalField(
        _("Target value"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    current_value = models.DecimalField(
        _("Current value"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=GoalStatus.choices,
        default=GoalStatus.NOT_STARTED,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Leadership Goal")
        verbose_name_plural = _("Leadership Goals")
        ordering = ("-due_date", "-created_at")

    def __str__(self) -> str:
        return f"{self.title} ({self.profile})"


class LeadershipKPI(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """A tracked Key Performance Indicator for a leader."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="kpis",
        verbose_name=_("Leader"),
    )
    name = models.CharField(_("KPI name"), max_length=200)
    category = models.CharField(_("Category"), max_length=150, blank=True)
    target_value = models.DecimalField(
        _("Target value"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    actual_value = models.DecimalField(
        _("Actual value"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    period_start = models.DateField(_("Period start"))
    period_end = models.DateField(_("Period end"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=KpiStatus.choices,
        default=KpiStatus.ON_TRACK,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Leadership KPI")
        verbose_name_plural = _("Leadership KPIs")
        ordering = ("-period_end", "-created_at")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["profile", "name", "period_start", "period_end"],
                name="unique_leadership_kpi_per_period",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.profile})"

    def clean(self) -> None:
        super().clean()
        from .validators import validate_date_order

        validate_date_order(self.period_start, self.period_end, "KPI period")


class CoachingRecord(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """A confidential coaching record for leadership development."""

    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leadership_coaching_sessions",
        verbose_name=_("Coach"),
    )
    leader = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="coaching_records",
        verbose_name=_("Leader"),
    )
    category = models.CharField(
        _("Category"),
        max_length=30,
        choices=CoachingCategory.choices,
        default=CoachingCategory.LEADERSHIP,
    )
    session_date = models.DateField(_("Session date"), default=timezone.localdate)
    objectives = models.TextField(_("Objectives"), blank=True)
    topics_discussed = models.TextField(_("Topics discussed"), blank=True)
    agreed_actions = models.TextField(_("Agreed actions"), blank=True)
    follow_up_date = models.DateField(_("Follow-up date"), null=True, blank=True)
    outcomes = models.TextField(_("Outcomes"), blank=True)
    is_confidential = models.BooleanField(
        _("Confidential"), default=True, help_text=_("Restricted to authorized users.")
    )

    class Meta:
        verbose_name = _("Coaching Record")
        verbose_name_plural = _("Coaching Records")
        ordering = ("-session_date", "-created_at")

    def __str__(self) -> str:
        return f"Coaching: {self.coach} -> {self.leader} ({self.session_date})"


class MentorshipRecord(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """A structured mentorship relationship for succession and development."""

    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leadership_mentorships",
        verbose_name=_("Mentor"),
    )
    mentee = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="mentorship_records",
        verbose_name=_("Mentee"),
    )
    start_date = models.DateField(_("Start date"), default=timezone.localdate)
    end_date = models.DateField(_("End date"), null=True, blank=True)
    development_objectives = models.TextField(_("Development objectives"), blank=True)
    progress_notes = models.TextField(_("Progress notes"), blank=True)
    outcomes = models.TextField(_("Outcomes"), blank=True)
    evaluation = models.TextField(_("Evaluation"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=MentorshipStatus.choices,
        default=MentorshipStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Mentorship Record")
        verbose_name_plural = _("Mentorship Records")
        ordering = ("-start_date", "-created_at")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["mentor", "mentee"],
                condition=models.Q(status=MentorshipStatus.ACTIVE),
                name="unique_active_mentorship_pair",
            ),
        ]

    def __str__(self) -> str:
        return f"Mentorship: {self.mentor} -> {self.mentee}"

    def clean(self) -> None:
        super().clean()
        from .validators import validate_date_order

        validate_date_order(self.start_date, self.end_date, "Mentorship")
        if self.mentor_id and self.mentee_id and self.mentor_id == self.mentee.user_id:
            raise ValidationError(
                _("A leader cannot mentor themselves."),
                code="invalid_mentor",
            )


class PerformanceReview(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """A structured leadership performance evaluation."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="performance_reviews",
        verbose_name=_("Leader"),
    )
    review_cycle = models.CharField(
        _("Review cycle"),
        max_length=20,
        choices=ReviewCycle.choices,
        default=ReviewCycle.ANNUAL,
    )
    period_start = models.DateField(_("Review period start"))
    period_end = models.DateField(_("Review period end"))
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_reviews_given",
        verbose_name=_("Reviewer"),
    )
    performance_ratings = models.JSONField(
        _("Performance ratings"),
        default=dict,
        blank=True,
        help_text=_("Map of dimension to 1-5 rating."),
    )
    achievements = models.TextField(_("Achievements"), blank=True)
    challenges = models.TextField(_("Challenges"), blank=True)
    recommendations = models.TextField(_("Recommendations"), blank=True)
    improvement_plan = models.TextField(_("Improvement plan"), blank=True)
    overall_assessment = models.TextField(_("Overall assessment"), blank=True)
    overall_rating = models.PositiveSmallIntegerField(
        _("Overall rating"), choices=RatingScale.choices, null=True, blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.DRAFT,
        db_index=True,
    )
    reviewed_at = models.DateTimeField(_("Reviewed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Performance Review")
        verbose_name_plural = _("Performance Reviews")
        ordering = ("-period_end", "-created_at")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["profile", "period_start", "period_end"],
                name="unique_leadership_review_per_period",
            ),
        ]

    def __str__(self) -> str:
        return f"Review {self.profile} ({self.period_start} to {self.period_end})"

    def clean(self) -> None:
        super().clean()
        from .validators import validate_date_order

        validate_date_order(self.period_start, self.period_end, "Review period")


class RecognitionRecord(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Recognition or award granted to a leader."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="recognition_records",
        verbose_name=_("Leader"),
    )
    award_name = models.CharField(_("Award name"), max_length=200)
    category = models.CharField(
        _("Category"),
        max_length=30,
        choices=RecognitionCategory.choices,
        default=RecognitionCategory.LEADERSHIP,
    )
    date_awarded = models.DateField(_("Date awarded"), default=timezone.localdate)
    awarding_authority = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_awards_given",
        verbose_name=_("Awarding authority"),
    )
    citation = models.TextField(_("Citation"), blank=True)
    supporting_document = models.FileField(
        _("Supporting document"),
        upload_to="leadership/recognition/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Recognition Record")
        verbose_name_plural = _("Recognition Records")
        ordering = ("-date_awarded", "-created_at")

    def __str__(self) -> str:
        return f"{self.award_name} - {self.profile}"


class DisciplinaryRecord(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """A securely maintained disciplinary record for a leader."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="disciplinary_records",
        verbose_name=_("Leader"),
    )
    record_type = models.CharField(
        _("Record type"),
        max_length=40,
        choices=DisciplinaryType.choices,
        db_index=True,
    )
    description = models.TextField(_("Description"), blank=True)
    incident_date = models.DateField(_("Incident date"), default=timezone.localdate)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DisciplinaryStatus.choices,
        default=DisciplinaryStatus.OPEN,
        db_index=True,
    )
    resolution = models.TextField(_("Resolution / decision"), blank=True)
    supporting_document = models.FileField(
        _("Supporting document"),
        upload_to="leadership/disciplinary/",
        null=True,
        blank=True,
    )
    is_confidential = models.BooleanField(
        _("Confidential"),
        default=True,
        help_text=_("Restricted to authorized personnel."),
    )

    class Meta:
        verbose_name = _("Disciplinary Record")
        verbose_name_plural = _("Disciplinary Records")
        ordering = ("-incident_date", "-created_at")

    def __str__(self) -> str:
        return f"{self.get_record_type_display()} - {self.profile}"


class SuccessionPlan(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """A structured succession plan for a critical leadership position."""

    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="succession_plans",
        verbose_name=_("Critical position"),
    )
    current_holder = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="succession_plans_holding",
        verbose_name=_("Current office holder"),
    )
    potential_successors = models.ManyToManyField(
        LeadershipProfile,
        related_name="succession_candidates",
        verbose_name=_("Potential successors"),
        blank=True,
    )
    readiness_level = models.CharField(
        _("Readiness level"),
        max_length=20,
        choices=SuccessionReadiness.choices,
        default=SuccessionReadiness.DEVELOPING,
    )
    required_competencies = models.TextField(_("Required competencies"), blank=True)
    development_activities = models.TextField(_("Development activities"), blank=True)
    target_readiness_date = models.DateField(
        _("Target readiness date"), null=True, blank=True
    )
    risk = models.CharField(
        _("Risk assessment"),
        max_length=20,
        choices=SuccessionRisk.choices,
        default=SuccessionRisk.MEDIUM,
    )
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Succession Plan")
        verbose_name_plural = _("Succession Plans")
        ordering = ("-created_at",)
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["position"],
                condition=models.Q(is_active=True),
                name="unique_active_succession_plan_per_position",
            ),
        ]

    def __str__(self) -> str:
        return f"Succession plan: {self.position.title}"


class LeadershipDocument(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """A versioned, confidentiality-controlled document for a leader."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Leader"),
    )
    category = models.CharField(
        _("Category"),
        max_length=40,
        choices=DocumentCategory.choices,
        default=DocumentCategory.OTHER,
        db_index=True,
    )
    title = models.CharField(_("Title"), max_length=200)
    file = models.FileField(_("File"), upload_to="leadership/documents/")
    version = models.CharField(_("Version"), max_length=20, default="1.0")
    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )

    class Meta:
        verbose_name = _("Leadership Document")
        verbose_name_plural = _("Leadership Documents")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} (v{self.version}) - {self.profile}"


class LeadershipScorecard(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """A configurable performance scorecard for a leader."""

    profile = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.CASCADE,
        related_name="scorecards",
        verbose_name=_("Leader"),
    )
    period_start = models.DateField(_("Period start"))
    period_end = models.DateField(_("Period end"))
    attendance_score = models.DecimalField(
        _("Attendance score"), max_digits=5, decimal_places=2, default=0
    )
    report_submission_score = models.DecimalField(
        _("Report submission score"), max_digits=5, decimal_places=2, default=0
    )
    goal_achievement_score = models.DecimalField(
        _("Goal achievement score"), max_digits=5, decimal_places=2, default=0
    )
    kpi_performance_score = models.DecimalField(
        _("KPI performance score"), max_digits=5, decimal_places=2, default=0
    )
    team_supervision_score = models.DecimalField(
        _("Team supervision score"), max_digits=5, decimal_places=2, default=0
    )
    program_oversight_score = models.DecimalField(
        _("Program oversight score"), max_digits=5, decimal_places=2, default=0
    )
    community_engagement_score = models.DecimalField(
        _("Community engagement score"), max_digits=5, decimal_places=2, default=0
    )
    stakeholder_engagement_score = models.DecimalField(
        _("Stakeholder engagement score"), max_digits=5, decimal_places=2, default=0
    )
    training_participation_score = models.DecimalField(
        _("Training participation score"), max_digits=5, decimal_places=2, default=0
    )
    overall_rating = models.DecimalField(
        _("Overall rating"), max_digits=5, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ScorecardStatus.choices,
        default=ScorecardStatus.DRAFT,
        db_index=True,
    )

    SCORE_FIELDS: ClassVar[tuple[str, ...]] = (
        "attendance_score",
        "report_submission_score",
        "goal_achievement_score",
        "kpi_performance_score",
        "team_supervision_score",
        "program_oversight_score",
        "community_engagement_score",
        "stakeholder_engagement_score",
        "training_participation_score",
    )

    class Meta:
        verbose_name = _("Leadership Scorecard")
        verbose_name_plural = _("Leadership Scorecards")
        ordering = ("-period_end", "-created_at")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["profile", "period_start", "period_end"],
                name="unique_leadership_scorecard_per_period",
            ),
        ]

    def __str__(self) -> str:
        return f"Scorecard {self.profile} ({self.period_start} to {self.period_end})"

    def clean(self) -> None:
        super().clean()
        from .validators import validate_date_order, validate_score_range

        validate_date_order(self.period_start, self.period_end, "Scorecard period")
        for field in self.SCORE_FIELDS:
            validate_score_range(getattr(self, field))

    def calculate_overall_rating(self) -> None:
        """Set the overall rating as the average of the component scores."""
        scores = [float(getattr(self, field) or 0) for field in self.SCORE_FIELDS]
        self.overall_rating = round(sum(scores) / len(scores), 2) if scores else 0


class LeadershipAuditRecord(UUIDModel, TimeStampedModel):
    """Immutable audit trail of every leadership change."""

    entity_type = models.CharField(_("Entity type"), max_length=60, db_index=True)
    entity_id = models.CharField(_("Entity ID"), max_length=60, db_index=True)
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=LeadershipAuditAction.choices,
        db_index=True,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leadership_audit_records",
        verbose_name=_("Changed by"),
    )
    from_data = models.JSONField(_("From data"), default=dict, blank=True)
    to_data = models.JSONField(_("To data"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Leadership Audit Record")
        verbose_name_plural = _("Leadership Audit Records")
        ordering = ("-created_at",)
        indexes: ClassVar[list] = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type} {self.entity_id} - {self.get_action_display()}"

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(
                IMMUTABLE_LEADERSHIP_RECORD_MESSAGE,
                code="immutable_leadership_audit",
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_LEADERSHIP_RECORD_MESSAGE,
            code="immutable_leadership_audit",
        )
