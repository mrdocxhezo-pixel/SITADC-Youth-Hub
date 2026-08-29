"""
Data models for the volunteer management module.
"""

# ruff: noqa: RUF012 - Django model Meta options are declarative attributes.

from __future__ import annotations

from typing import ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
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
from apps.organizations.models import OrganizationUnit

from .constants import (
    ActivityCategory,
    ApplicationStatus,
    AttendanceCategory,
    AttendanceStatus,
    AvailabilityType,
    CommunicationChannel,
    DisciplinaryDecision,
    DisciplinaryStatus,
    ExitReason,
    ExitStatus,
    LeaveStatus,
    LeaveType,
    RecognitionCategory,
    RecruitmentStatus,
    SkillProficiency,
    VolunteerAuditAction,
    VolunteerDocumentStatus,
    VolunteerStatus,
    WelfareCategory,
)
from .managers import ImmutableVolunteerManager, VolunteerProfileManager
from .storage import private_volunteer_storage
from .validators import (
    validate_date_range,
    validate_volunteer_document,
    validate_volunteer_image,
)

IMMUTABLE_VOLUNTEER_RECORD_MESSAGE = _(
    "Volunteer audit records and status history are immutable and cannot be modified."
)


class VolunteerCategory(UUIDModel, TimeStampedModel, CreatedByModel):
    """Configurable volunteer category taxonomy."""

    code = models.CharField(_("Code"), max_length=40, unique=True, db_index=True)
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    eligibility_requirements = models.TextField(
        _("Eligibility Requirements"), blank=True
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Volunteer Category")
        verbose_name_plural = _("Volunteer Categories")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        self.code = self.code.strip().upper()
        if not self.code:
            raise ValidationError({"code": _("Code is required.")})


class VolunteerType(UUIDModel, TimeStampedModel, CreatedByModel):
    """Configurable volunteer type taxonomy."""

    code = models.CharField(_("Code"), max_length=40, unique=True, db_index=True)
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Volunteer Type")
        verbose_name_plural = _("Volunteer Types")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        self.code = self.code.strip().upper()
        if not self.code:
            raise ValidationError({"code": _("Code is required.")})


class VolunteerLevel(UUIDModel, TimeStampedModel, CreatedByModel):
    """Configurable volunteer level taxonomy."""

    code = models.CharField(_("Code"), max_length=40, unique=True, db_index=True)
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Volunteer Level")
        verbose_name_plural = _("Volunteer Levels")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        self.code = self.code.strip().upper()
        if not self.code:
            raise ValidationError({"code": _("Code is required.")})


class VolunteerProfile(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    ArchivableModel,
    NotesModel,
):
    """
    Core profile linked to an account and the centralized reference service.
    """

    reference_number = models.CharField(
        _("Volunteer reference number"),
        max_length=60,
        unique=True,
        db_index=True,
        help_text=_(
            "Immutable reference number issued by the centralized numbering service."
        ),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="volunteer_profile",
        verbose_name=_("Linked user account"),
    )
    membership_number = models.CharField(
        _("Membership number"),
        max_length=60,
        blank=True,
        help_text=_("Optional Phase 12 membership number link."),
    )
    national_id = models.CharField(
        _("National ID / Passport"), max_length=60, blank=True
    )
    profile_photo = models.ImageField(
        _("Profile photograph"),
        upload_to="volunteers/profiles/",
        null=True,
        blank=True,
        validators=[validate_volunteer_image],
    )
    date_of_birth = models.DateField(_("Date of birth"), null=True, blank=True)
    gender = models.CharField(_("Gender"), max_length=20, blank=True)
    nationality = models.CharField(_("Nationality"), max_length=60, default="Zambian")
    phone_number = models.CharField(_("Phone number"), max_length=30, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    residential_address = models.TextField(_("Residential address"), blank=True)

    region = models.CharField(_("Region / Province"), max_length=100, blank=True)
    district = models.CharField(_("District"), max_length=100, blank=True)
    community = models.CharField(_("Community"), max_length=100, blank=True)

    province_location = models.ForeignKey(
        "locations.Province",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volunteer_profiles",
        verbose_name=_("Province"),
    )
    district_location = models.ForeignKey(
        "locations.District",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volunteer_profiles",
        verbose_name=_("District"),
    )
    constituency_location = models.ForeignKey(
        "locations.Constituency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volunteer_profiles",
        verbose_name=_("Constituency"),
    )
    ward_location = models.ForeignKey(
        "locations.Ward",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volunteer_profiles",
        verbose_name=_("Ward / Community"),
    )

    emergency_contact_name = models.CharField(
        _("Emergency contact name"), max_length=150, blank=True
    )
    emergency_contact_relationship = models.CharField(
        _("Emergency contact relationship"), max_length=60, blank=True
    )
    emergency_contact_phone = models.CharField(
        _("Emergency contact phone"), max_length=30, blank=True
    )

    education_level = models.CharField(
        _("Highest level of education"), max_length=100, blank=True
    )
    occupation = models.CharField(
        _("Occupation / Profession"), max_length=100, blank=True
    )
    languages = models.CharField(
        _("Languages spoken"),
        max_length=255,
        blank=True,
        help_text=_("Comma separated languages."),
    )

    category = models.ForeignKey(
        VolunteerCategory,
        on_delete=models.PROTECT,
        related_name="profiles",
        verbose_name=_("Volunteer category"),
        null=True,
        blank=True,
        db_index=True,
    )
    volunteer_type = models.ForeignKey(
        VolunteerType,
        on_delete=models.PROTECT,
        related_name="profiles",
        verbose_name=_("Volunteer type"),
        null=True,
        blank=True,
        db_index=True,
    )
    volunteer_level = models.ForeignKey(
        VolunteerLevel,
        on_delete=models.PROTECT,
        related_name="profiles",
        verbose_name=_("Volunteer level"),
        null=True,
        blank=True,
        db_index=True,
    )
    availability = models.CharField(
        _("Availability type"),
        max_length=40,
        choices=AvailabilityType.choices,
        default=AvailabilityType.PART_TIME,
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=VolunteerStatus.choices,
        default=VolunteerStatus.APPLICANT,
        db_index=True,
    )

    team = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volunteer_team_members",
        verbose_name=_("Assigned organizational team / unit"),
    )
    supervisor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_volunteers",
        verbose_name=_("Assigned supervisor"),
    )

    start_date = models.DateField(_("Volunteer start date"), null=True, blank=True)
    end_date = models.DateField(_("Expected end date"), null=True, blank=True)
    exit_date = models.DateField(_("Exit date"), null=True, blank=True)
    exit_reason = models.CharField(
        _("Exit reason"), max_length=50, choices=ExitReason.choices, blank=True
    )

    biography = models.TextField(_("Biography / Summary"), blank=True)

    objects = VolunteerProfileManager()  # type: ignore[misc]

    class Meta:
        verbose_name = _("Volunteer Profile")
        verbose_name_plural = _("Volunteer Profiles")
        ordering = ["-created_at"]
        indexes: ClassVar[list] = [
            models.Index(fields=["status", "category"]),
            models.Index(fields=["team", "status"]),
            models.Index(fields=["region", "district"]),
            models.Index(fields=["province_location", "district_location"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.full_name} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date)
        if self.date_of_birth and self.date_of_birth > timezone.localdate():
            raise ValidationError(
                {"date_of_birth": _("Date of birth cannot be in the future.")}
            )
        if self.supervisor_id and self.supervisor_id == self.pk:
            raise ValidationError(
                {"supervisor": _("A volunteer cannot supervise themselves.")}
            )


class VolunteerRecruitment(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    NotesModel,
):
    """Recruitment campaign for sourcing volunteers."""

    title = models.CharField(_("Recruitment title"), max_length=200)
    reference_number = models.CharField(
        _("Campaign reference"), max_length=60, unique=True, db_index=True
    )
    category = models.ForeignKey(
        VolunteerCategory,
        on_delete=models.PROTECT,
        related_name="recruitment_campaigns",
        verbose_name=_("Volunteer category"),
    )
    volunteer_type = models.ForeignKey(
        VolunteerType,
        on_delete=models.PROTECT,
        related_name="recruitment_campaigns",
        verbose_name=_("Volunteer type"),
    )
    vacancies = models.PositiveIntegerField(_("Number of vacancies"), default=1)
    location = models.CharField(_("Location / Region"), max_length=150, blank=True)
    required_skills = models.TextField(
        _("Required skills & qualifications"), blank=True
    )
    application_deadline = models.DateField(_("Application deadline"))
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=RecruitmentStatus.choices,
        default=RecruitmentStatus.OPEN,
        db_index=True,
    )
    supervisor = models.ForeignKey(
        VolunteerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recruitment_campaigns",
    )

    class Meta:
        verbose_name = _("Volunteer Recruitment Campaign")
        verbose_name_plural = _("Volunteer Recruitment Campaigns")
        ordering = ["-created_at"]

    def clean(self) -> None:
        super().clean()
        if self.vacancies < 1:
            raise ValidationError(
                {"vacancies": _("A campaign must have at least one vacancy.")}
            )
        if (
            self.status == RecruitmentStatus.OPEN
            and self.application_deadline < timezone.localdate()
        ):
            raise ValidationError(
                {"application_deadline": _("An open campaign deadline cannot be past.")}
            )

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class VolunteerApplication(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    NotesModel,
):
    """Application submitted by an individual to become a volunteer."""

    recruitment = models.ForeignKey(
        VolunteerRecruitment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    reference_number = models.CharField(
        _("Application reference"), max_length=60, unique=True, db_index=True
    )
    applicant_name = models.CharField(_("Full name"), max_length=150)
    email = models.EmailField(_("Email address"))
    phone_number = models.CharField(_("Phone number"), max_length=30)
    gender = models.CharField(_("Gender"), max_length=20, blank=True)
    date_of_birth = models.DateField(_("Date of birth"), null=True, blank=True)
    address = models.TextField(_("Residential address"), blank=True)
    category = models.ForeignKey(
        VolunteerCategory,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name=_("Preferred category"),
    )
    volunteer_type = models.ForeignKey(
        VolunteerType,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name=_("Preferred type"),
    )
    skills = models.TextField(_("Skills & experience"), blank=True)
    motivation = models.TextField(_("Motivation statement"), blank=True)
    cv_file = models.FileField(
        _("Curriculum Vitae (CV)"),
        upload_to="volunteers/applications/cv/",
        null=True,
        blank=True,
        storage=private_volunteer_storage,
        validators=[validate_volunteer_document],
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED,
        db_index=True,
    )
    consent_confirmed = models.BooleanField(
        _("Privacy notice and application consent confirmed"), default=False
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_volunteer_applications",
    )
    reviewed_at = models.DateTimeField(_("Reviewed at"), null=True, blank=True)
    decision_notes = models.TextField(_("Decision notes"), blank=True)

    class Meta:
        verbose_name = _("Volunteer Application")
        verbose_name_plural = _("Volunteer Applications")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.applicant_name} - {self.reference_number}"

    def clean(self) -> None:
        super().clean()
        if self.date_of_birth and self.date_of_birth > timezone.localdate():
            raise ValidationError(
                {"date_of_birth": _("Date of birth cannot be in the future.")}
            )
        recruitment = self.recruitment if self.recruitment_id else None
        if recruitment and (
            recruitment.status != RecruitmentStatus.OPEN
            or recruitment.application_deadline < timezone.localdate()
        ):
            raise ValidationError(
                {"recruitment": _("Applications are closed for this campaign.")}
            )


class VolunteerScreening(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Screening verification for a volunteer application."""

    application = models.OneToOneField(
        VolunteerApplication, on_delete=models.CASCADE, related_name="screening"
    )
    identity_verified = models.BooleanField(_("Identity verified"), default=False)
    references_checked = models.BooleanField(_("References checked"), default=False)
    qualifications_verified = models.BooleanField(
        _("Qualifications verified"), default=False
    )
    safeguarding_cleared = models.BooleanField(
        _("Safeguarding assessment cleared"), default=False
    )
    passed = models.BooleanField(_("Screening passed"), default=False)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    review_date = models.DateField(_("Screening date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Volunteer Screening")
        verbose_name_plural = _("Volunteer Screenings")

    def clean(self) -> None:
        super().clean()
        checks = (
            self.identity_verified,
            self.references_checked,
            self.qualifications_verified,
            self.safeguarding_cleared,
        )
        if self.passed and not all(checks):
            raise ValidationError(
                _("All screening checks must pass before approval."),
                code="incomplete_screening",
            )


class VolunteerInterview(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Interview record for a volunteer candidate."""

    application = models.ForeignKey(
        VolunteerApplication, on_delete=models.CASCADE, related_name="interviews"
    )
    scheduled_datetime = models.DateTimeField(_("Scheduled date and time"))
    venue_or_link = models.CharField(
        _("Venue / Online Link"), max_length=255, blank=True
    )
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    score = models.PositiveSmallIntegerField(
        _("Interview score (0-100)"),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    recommendation = models.TextField(_("Recommendation & Notes"), blank=True)
    passed = models.BooleanField(_("Interview passed"), default=False)
    completed = models.BooleanField(_("Completed"), default=False)

    class Meta:
        verbose_name = _("Volunteer Interview")
        verbose_name_plural = _("Volunteer Interviews")

    def clean(self) -> None:
        super().clean()
        if self.passed and not self.completed:
            raise ValidationError(
                {"passed": _("An incomplete interview cannot be marked as passed.")}
            )


class VolunteerOnboarding(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Onboarding and orientation sign-offs."""

    profile = models.OneToOneField(
        VolunteerProfile, on_delete=models.CASCADE, related_name="onboarding"
    )
    orientation_completed = models.BooleanField(
        _("Orientation completed"), default=False
    )
    code_of_conduct_signed = models.BooleanField(
        _("Code of conduct signed"), default=False
    )
    safeguarding_agreed = models.BooleanField(
        _("Safeguarding policy agreed"), default=False
    )
    confidentiality_signed = models.BooleanField(
        _("Confidentiality agreement signed"), default=False
    )
    welcome_pack_issued = models.BooleanField(_("Welcome pack issued"), default=False)
    id_card_issued = models.BooleanField(_("ID Card issued"), default=False)
    completed = models.BooleanField(_("Onboarding complete"), default=False)
    completion_date = models.DateField(_("Completion date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Volunteer Onboarding")
        verbose_name_plural = _("Volunteer Onboardings")

    def clean(self) -> None:
        super().clean()
        required = (
            self.orientation_completed,
            self.code_of_conduct_signed,
            self.safeguarding_agreed,
            self.confidentiality_signed,
        )
        if self.completed and not all(required):
            raise ValidationError(
                _("All required onboarding acknowledgements must be complete."),
                code="incomplete_onboarding",
            )
        if self.completed and not self.completion_date:
            raise ValidationError(
                {"completion_date": _("Completion date is required.")}
            )


class VolunteerSkill(UUIDModel, TimeStampedModel, CreatedByModel):
    """Skills possessed by a volunteer."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="skills"
    )
    name = models.CharField(_("Skill name"), max_length=100)
    category = models.CharField(_("Category"), max_length=50, default="Technical")
    proficiency = models.CharField(
        _("Proficiency level"),
        max_length=20,
        choices=SkillProficiency.choices,
        default=SkillProficiency.INTERMEDIATE,
    )

    class Meta:
        verbose_name = _("Volunteer Skill")
        verbose_name_plural = _("Volunteer Skills")
        unique_together = ("profile", "name")

    def __str__(self) -> str:
        return f"{self.profile} - {self.name} ({self.proficiency})"


class VolunteerInterest(UUIDModel, TimeStampedModel, CreatedByModel):
    """Interest areas of a volunteer."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="interests"
    )
    area_name = models.CharField(_("Interest area"), max_length=100)

    class Meta:
        verbose_name = _("Volunteer Interest")
        verbose_name_plural = _("Volunteer Interests")
        unique_together = ("profile", "area_name")

    def __str__(self) -> str:
        return f"{self.profile} - {self.area_name}"


class VolunteerAssignment(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    NotesModel,
):
    """Deployment or role assignment of a volunteer to a program/project/unit."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="assignments"
    )
    title = models.CharField(_("Assignment / Role Title"), max_length=200)
    program_name = models.CharField(_("Program Name"), max_length=150, blank=True)
    project_name = models.CharField(_("Project Name"), max_length=150, blank=True)
    team = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volunteer_assignments",
    )
    supervisor = models.ForeignKey(
        VolunteerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_assignments",
    )
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"), null=True, blank=True)
    objectives = models.TextField(_("Key Objectives & Deliverables"), blank=True)
    is_active = models.BooleanField(
        _("Is active assignment"), default=True, db_index=True
    )

    class Meta:
        verbose_name = _("Volunteer Assignment")
        verbose_name_plural = _("Volunteer Assignments")
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.profile} - {self.title}"

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date)
        if self.supervisor_id and self.supervisor_id == self.profile_id:
            raise ValidationError(
                {"supervisor": _("A volunteer cannot supervise their own assignment.")}
            )


class VolunteerDeploymentHistory(
    UUIDModel, TimeStampedModel, CreatedByModel, NotesModel
):
    """Immutable log of historical deployments."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="deployment_history"
    )
    assignment_title = models.CharField(_("Assignment Title"), max_length=200)
    program_or_project = models.CharField(_("Program / Project"), max_length=200)
    community_served = models.CharField(
        _("Community Served"), max_length=150, blank=True
    )
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    supervisor_name = models.CharField(_("Supervisor Name"), max_length=150, blank=True)
    outcomes_summary = models.TextField(_("Outcomes & Impact Summary"), blank=True)

    class Meta:
        verbose_name = _("Volunteer Deployment History")
        verbose_name_plural = _("Volunteer Deployment Histories")
        ordering = ["-end_date"]

    objects = ImmutableVolunteerManager()

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(
                IMMUTABLE_VOLUNTEER_RECORD_MESSAGE,
                code="immutable_volunteer_record",
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_VOLUNTEER_RECORD_MESSAGE,
            code="immutable_volunteer_record",
        )


class VolunteerAttendance(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Attendance log for volunteer service."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField(_("Date of Service"), db_index=True)
    activity_name = models.CharField(_("Activity / Event Name"), max_length=200)
    category = models.CharField(
        _("Category"),
        max_length=40,
        choices=AttendanceCategory.choices,
        default=AttendanceCategory.DAILY,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )
    hours_served = models.DecimalField(
        _("Hours served"),
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )
    location = models.CharField(_("Location"), max_length=150, blank=True)

    class Meta:
        verbose_name = _("Volunteer Attendance")
        verbose_name_plural = _("Volunteer Attendance Logs")
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "date", "activity_name"],
                name="unique_volunteer_attendance_activity",
            )
        ]

    def __str__(self) -> str:
        return f"{self.profile} - {self.date} ({self.status})"

    def clean(self) -> None:
        super().clean()
        if self.date > timezone.localdate():
            raise ValidationError(
                {"date": _("Attendance cannot be recorded in the future.")}
            )
        if (
            self.status in {AttendanceStatus.ABSENT, AttendanceStatus.EXCUSED}
            and self.hours_served
        ):
            raise ValidationError(
                {
                    "hours_served": _(
                        "Absent or excused attendance cannot record service hours."
                    )
                }
            )


class VolunteerTraining(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Training and capacity building record."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="trainings"
    )
    title = models.CharField(_("Training Title"), max_length=200)
    provider = models.CharField(
        _("Training Provider / Facilitator"), max_length=150, blank=True
    )
    start_date = models.DateField(_("Start Date"))
    completion_date = models.DateField(_("Completion Date"), null=True, blank=True)
    certificate_issued = models.BooleanField(_("Certificate Issued"), default=False)
    certificate_file = models.FileField(
        _("Certificate File"),
        upload_to="volunteers/certificates/",
        null=True,
        blank=True,
        storage=private_volunteer_storage,
        validators=[validate_volunteer_document],
    )
    competencies_acquired = models.TextField(_("Competencies Acquired"), blank=True)

    class Meta:
        verbose_name = _("Volunteer Training")
        verbose_name_plural = _("Volunteer Trainings")
        ordering = ["-start_date"]

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.completion_date)
        if self.certificate_issued and not self.completion_date:
            raise ValidationError(
                {
                    "certificate_issued": _(
                        "Training must be completed before issuing a certificate."
                    )
                }
            )


class VolunteerPerformance(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Performance evaluation record for a volunteer."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="performance_reviews"
    )
    review_period = models.CharField(_("Review Period (e.g. 2026 Q1)"), max_length=60)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    overall_score = models.PositiveSmallIntegerField(
        _("Overall Score (1-100)"),
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    kpis_met = models.TextField(_("KPIs & Targets Achieved"), blank=True)
    strengths = models.TextField(_("Key Strengths"), blank=True)
    areas_for_growth = models.TextField(_("Areas for Growth & Coaching"), blank=True)
    community_feedback = models.TextField(
        _("Community / Beneficiary Feedback"), blank=True
    )
    review_date = models.DateField(_("Review Date"), default=timezone.now)

    class Meta:
        verbose_name = _("Volunteer Performance Review")
        verbose_name_plural = _("Volunteer Performance Reviews")
        ordering = ["-review_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "review_period"],
                name="unique_volunteer_review_period",
            )
        ]


class VolunteerRecognition(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Recognition, awards, and appreciation badges."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="recognitions"
    )
    title = models.CharField(_("Award / Recognition Title"), max_length=200)
    category = models.CharField(
        _("Category"),
        max_length=40,
        choices=RecognitionCategory.choices,
        default=RecognitionCategory.CERTIFICATE,
    )
    award_date = models.DateField(_("Award Date"), default=timezone.now)
    citation = models.TextField(_("Citation / Reason for Award"), blank=True)

    class Meta:
        verbose_name = _("Volunteer Recognition")
        verbose_name_plural = _("Volunteer Recognitions")
        ordering = ["-award_date"]


class VolunteerWelfare(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Welfare support request and resolution record."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="welfare_records"
    )
    category = models.CharField(
        _("Support Category"),
        max_length=40,
        choices=WelfareCategory.choices,
        default=WelfareCategory.WELFARE_REQUEST,
    )
    description = models.TextField(_("Details of Request / Referral"))
    action_taken = models.TextField(_("Action Taken / Resolution"), blank=True)
    resolved = models.BooleanField(_("Is Resolved"), default=False)

    class Meta:
        verbose_name = _("Volunteer Welfare Record")
        verbose_name_plural = _("Volunteer Welfare Records")
        ordering = ["-created_at"]


class VolunteerLeave(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """Leave application and tracking for volunteers."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="leaves"
    )
    leave_type = models.CharField(
        _("Leave Type"),
        max_length=30,
        choices=LeaveType.choices,
        default=LeaveType.ANNUAL,
    )
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    reason = models.TextField(_("Reason for Leave"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=LeaveStatus.choices,
        default=LeaveStatus.SUBMITTED,
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_volunteer_leaves",
    )
    approval_notes = models.TextField(_("Approval / Rejection Notes"), blank=True)

    class Meta:
        verbose_name = _("Volunteer Leave Application")
        verbose_name_plural = _("Volunteer Leave Applications")
        ordering = ["-start_date"]

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date)


class VolunteerExit(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """Exit process record for departing volunteers."""

    profile = models.OneToOneField(
        VolunteerProfile, on_delete=models.CASCADE, related_name="exit_record"
    )
    reason = models.CharField(
        _("Exit Reason"), max_length=50, choices=ExitReason.choices
    )
    effective_date = models.DateField(_("Effective Exit Date"))
    exit_interview_notes = models.TextField(_("Exit Interview Notes"), blank=True)
    assets_returned = models.BooleanField(_("Assets & Badges Returned"), default=False)
    documents_returned = models.BooleanField(
        _("Documents & Files Returned"), default=False
    )
    clearance_approved = models.BooleanField(
        _("Supervisor Clearance Approved"), default=False
    )
    transition_to_alumni = models.BooleanField(
        _("Transfer to Volunteer Alumni Network"), default=True
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=ExitStatus.choices,
        default=ExitStatus.INITIATED,
    )

    class Meta:
        verbose_name = _("Volunteer Exit Record")
        verbose_name_plural = _("Volunteer Exit Records")

    def clean(self) -> None:
        super().clean()
        if self.profile.start_date and self.effective_date < self.profile.start_date:
            raise ValidationError(
                {
                    "effective_date": _(
                        "Exit date cannot precede the volunteer start date."
                    )
                }
            )


class VolunteerActivityLog(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """Service activity log for a volunteer."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="activity_logs"
    )
    activity_title = models.CharField(_("Activity Title"), max_length=200)
    category = models.CharField(
        _("Category"),
        max_length=40,
        choices=ActivityCategory.choices,
        default=ActivityCategory.OTHER,
    )
    activity_date = models.DateField(_("Activity Date"), db_index=True)
    program_name = models.CharField(
        _("Program / Project Name"), max_length=200, blank=True
    )
    location = models.CharField(_("Location"), max_length=150, blank=True)
    hours_served = models.DecimalField(
        _("Hours served"),
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )
    beneficiaries_reached = models.PositiveIntegerField(
        _("Beneficiaries reached"), default=0
    )
    supervisor_comments = models.TextField(_("Supervisor Comments"), blank=True)
    supporting_evidence = models.FileField(
        _("Supporting Evidence"),
        upload_to="volunteers/activity_evidence/",
        null=True,
        blank=True,
        storage=private_volunteer_storage,
        validators=[validate_volunteer_document],
    )

    class Meta:
        verbose_name = _("Volunteer Activity Log")
        verbose_name_plural = _("Volunteer Activity Logs")
        ordering = ["-activity_date"]
        indexes: ClassVar[list] = [
            models.Index(fields=["profile", "activity_date"]),
            models.Index(fields=["activity_date", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.profile} - {self.activity_title} ({self.activity_date})"

    def clean(self) -> None:
        super().clean()
        if self.activity_date > timezone.localdate():
            raise ValidationError(
                {"activity_date": _("Activity date cannot be in the future.")}
            )
        if self.hours_served and self.hours_served > 24:
            raise ValidationError(
                {"hours_served": _("Hours served cannot exceed 24 in one activity.")}
            )


class VolunteerDisciplinaryRecord(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """Disciplinary concern and resolution record for a volunteer."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="disciplinary_records"
    )
    reference_number = models.CharField(
        _("Disciplinary reference"), max_length=60, unique=True, db_index=True
    )
    incident_date = models.DateField(_("Incident Date"), db_index=True)
    nature_of_concern = models.TextField(_("Nature of Concern / Incident"))
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=DisciplinaryStatus.choices,
        default=DisciplinaryStatus.PENDING,
        db_index=True,
    )
    decision = models.CharField(
        _("Decision"),
        max_length=30,
        choices=DisciplinaryDecision.choices,
        blank=True,
    )
    investigation_summary = models.TextField(_("Investigation Summary"), blank=True)
    corrective_action = models.TextField(_("Corrective Action / Outcome"), blank=True)
    supporting_documents = models.FileField(
        _("Supporting Documents"),
        upload_to="volunteers/disciplinary/",
        null=True,
        blank=True,
        storage=private_volunteer_storage,
        validators=[validate_volunteer_document],
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_volunteer_disciplinary_records",
    )
    decided_at = models.DateTimeField(_("Decided At"), null=True, blank=True)
    effective_date = models.DateField(_("Effective Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Volunteer Disciplinary Record")
        verbose_name_plural = _("Volunteer Disciplinary Records")
        ordering = ["-incident_date"]
        indexes: ClassVar[list] = [models.Index(fields=["profile", "status"])]

    def __str__(self) -> str:
        return f"{self.profile} - {self.reference_number}"

    def clean(self) -> None:
        super().clean()
        if self.incident_date > timezone.localdate():
            raise ValidationError(
                {"incident_date": _("Incident date cannot be in the future.")}
            )
        if self.status == DisciplinaryStatus.RESOLVED and not self.decision:
            raise ValidationError(
                {
                    "decision": _(
                        "A decision is required to close a disciplinary record."
                    )
                }
            )
        if (
            self.effective_date
            and self.incident_date
            and self.effective_date < self.incident_date
        ):
            raise ValidationError(
                {
                    "effective_date": _(
                        "Effective date cannot precede the incident date."
                    )
                }
            )


class VolunteerCommunication(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """Record of communications sent to a volunteer."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="communications"
    )
    channel = models.CharField(
        _("Channel"), max_length=20, choices=CommunicationChannel.choices
    )
    subject = models.CharField(_("Subject"), max_length=200)
    body = models.TextField(_("Message Body"), blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_volunteer_communications",
    )
    sent_at = models.DateTimeField(_("Sent At"), default=timezone.now, db_index=True)
    attachment = models.FileField(
        _("Attachment"),
        upload_to="volunteers/communications/",
        null=True,
        blank=True,
        storage=private_volunteer_storage,
        validators=[validate_volunteer_document],
    )

    class Meta:
        verbose_name = _("Volunteer Communication")
        verbose_name_plural = _("Volunteer Communications")
        ordering = ["-sent_at"]

    def __str__(self) -> str:
        return f"{self.profile} - {self.subject} ({self.sent_at})"


class VolunteerDocument(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """Uploaded files and documents for a volunteer profile."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="documents"
    )
    title = models.CharField(_("Document Title"), max_length=200)
    document_type = models.CharField(
        _("Document Type"), max_length=100, default="General"
    )
    file = models.FileField(
        _("File"),
        upload_to="volunteers/documents/",
        storage=private_volunteer_storage,
        validators=[validate_volunteer_document],
    )
    is_confidential = models.BooleanField(_("Confidential"), default=True)
    uploaded_at = models.DateTimeField(_("Uploaded At"), auto_now_add=True)
    version = models.PositiveIntegerField(_("Version"), default=1, db_index=True)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=VolunteerDocumentStatus.choices,
        default=VolunteerDocumentStatus.PENDING_APPROVAL,
        db_index=True,
    )
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseding_versions",
        verbose_name=_("Supersedes version"),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_volunteer_documents",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)
    retention_until = models.DateField(_("Retention Until"), null=True, blank=True)

    class Meta:
        verbose_name = _("Volunteer Document")
        verbose_name_plural = _("Volunteer Documents")
        ordering = ["-version"]
        indexes: ClassVar[list] = [
            models.Index(fields=["profile", "status"]),
            models.Index(fields=["profile", "version"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} v{self.version} ({self.profile})"

    def clean(self) -> None:
        super().clean()
        if self.status == VolunteerDocumentStatus.APPROVED and not self.approved_at:
            raise ValidationError(
                {
                    "approved_at": _(
                        "Approval timestamp is required for approved documents."
                    )
                }
            )


class VolunteerStatusHistory(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """Immutable audit trail for profile status transitions."""

    profile = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="status_history"
    )
    from_status = models.CharField(_("From status"), max_length=40)
    to_status = models.CharField(_("To status"), max_length=40)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Volunteer Status History")
        verbose_name_plural = _("Volunteer Status Histories")
        ordering = ["-created_at"]
        indexes: ClassVar[list] = [models.Index(fields=["profile", "created_at"])]

    objects = ImmutableVolunteerManager()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(IMMUTABLE_VOLUNTEER_RECORD_MESSAGE)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_VOLUNTEER_RECORD_MESSAGE,
            code="immutable_volunteer_record",
        )


class VolunteerAuditRecord(UUIDModel, TimeStampedModel):
    """Immutable audit trail for all volunteer module events."""

    entity_type = models.CharField(_("Entity type"), max_length=100, db_index=True)
    entity_id = models.CharField(_("Entity ID"), max_length=64, db_index=True)
    action = models.CharField(
        _("Action"), max_length=50, choices=VolunteerAuditAction.choices, db_index=True
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    from_data = models.JSONField(_("Data before change"), default=dict, blank=True)
    to_data = models.JSONField(_("Data after change"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Volunteer Audit Record")
        verbose_name_plural = _("Volunteer Audit Records")
        ordering = ["-created_at"]
        indexes: ClassVar[list] = [models.Index(fields=["entity_type", "entity_id"])]

    objects = ImmutableVolunteerManager()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(IMMUTABLE_VOLUNTEER_RECORD_MESSAGE)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_VOLUNTEER_RECORD_MESSAGE,
            code="immutable_volunteer_record",
        )
