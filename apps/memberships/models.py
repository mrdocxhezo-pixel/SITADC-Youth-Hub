"""
Data models for the membership management module.

Implements the official membership registry for the SITADC Youth Organization:
member profiles, applications, approvals, renewals, upgrades, transfers,
suspensions, terminations, exit & alumni, attendance, participation,
committees, fees, payments, documents, cards, communications, status history
and the immutable membership audit log.

Membership categories, types, levels and statuses are configuration-driven
(DB-backed) so they can be managed without modifying application code.
"""

from __future__ import annotations

from decimal import Decimal
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

from .constants import (
    AdjustmentStatus,
    ApplicationStatus,
    AttendanceStatus,
    AttendanceType,
    BenefitStatus,
    CardStatus,
    CommunicationStatus,
    CommunicationType,
    ComplaintStatus,
    ComplaintType,
    DisciplinaryStatus,
    DisciplinaryType,
    DocumentCategory,
    DocumentStatus,
    EducationLevel,
    ExitStatus,
    ExitType,
    FeeAdjustmentType,
    Gender,
    LeaveStatus,
    LeaveType,
    MembershipAuditAction,
    ParticipationStatus,
    ParticipationType,
    PaymentMethod,
    PaymentStatus,
    RecognitionType,
    RenewalStatus,
    TerminationReason,
    TransferStatus,
    UpgradeStatus,
)

IMMUTABLE_MEMBERSHIP_RECORD_MESSAGE = _(
    "Membership audit and history records are immutable and cannot be modified."
)


# ---------------------------------------------------------------------------
# Configuration models (DB-backed, manageable without code changes)
# ---------------------------------------------------------------------------


class MembershipCategory(UUIDModel, TimeStampedModel, ArchivableModel, NotesModel):
    """Configurable membership category (Founding, Ordinary, Student, ...)."""

    code = models.SlugField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    rights = models.TextField(_("Membership Rights"), blank=True)
    responsibilities = models.TextField(_("Membership Responsibilities"), blank=True)
    eligibility_criteria = models.TextField(_("Eligibility Criteria"), blank=True)
    leadership_eligible = models.BooleanField(_("Leadership Eligible"), default=False)
    voting_rights = models.BooleanField(_("Voting Rights"), default=True)
    default_fee_amount = models.DecimalField(
        _("Default Fee Amount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    renewal_fee_amount = models.DecimalField(
        _("Renewal Fee Amount"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency = models.CharField(_("Currency"), max_length=10, default="ZMW")
    billing_frequency_months = models.PositiveIntegerField(
        _("Billing Frequency (months)"), default=12
    )
    renewal_period_months = models.PositiveIntegerField(
        _("Renewal Period (months)"), default=12
    )
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0)

    class Meta:
        verbose_name = _("Membership Category")
        verbose_name_plural = _("Membership Categories")
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["is_active"], name="member_cat_active_idx"),
            models.Index(fields=["code"], name="member_cat_code_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class MembershipType(UUIDModel, TimeStampedModel, ArchivableModel, NotesModel):
    """Configurable membership type (Individual, Institutional, Community, ...)."""

    code = models.SlugField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0)

    class Meta:
        verbose_name = _("Membership Type")
        verbose_name_plural = _("Membership Types")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class MembershipLevel(UUIDModel, TimeStampedModel, ArchivableModel, NotesModel):
    """Configurable membership level (National, Regional, District, Community, Team)."""

    code = models.SlugField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0)

    class Meta:
        verbose_name = _("Membership Level")
        verbose_name_plural = _("Membership Levels")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class MembershipStatus(UUIDModel, TimeStampedModel, ArchivableModel, NotesModel):
    """Configurable membership lifecycle status (Pending, Active, Suspended, ...)."""

    code = models.SlugField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0)

    class Meta:
        verbose_name = _("Membership Status")
        verbose_name_plural = _("Membership Statuses")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class MembershipBenefit(UUIDModel, TimeStampedModel, ArchivableModel, NotesModel):
    """Configurable benefit offered to members."""

    code = models.SlugField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0)

    class Meta:
        verbose_name = _("Membership Benefit")
        verbose_name_plural = _("Membership Benefits")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class RenewalRule(UUIDModel, TimeStampedModel):
    """Singleton configuration governing membership renewal behaviour."""

    name = models.CharField(_("Name"), max_length=100, default="Default Renewal Rule")
    is_active = models.BooleanField(_("Is Active"), default=True)
    notice_period_days = models.PositiveIntegerField(
        _("Notice Period (days before expiry)"), default=30
    )
    grace_period_days = models.PositiveIntegerField(
        _("Grace Period (days after expiry)"), default=30
    )
    renewal_period_months = models.PositiveIntegerField(
        _("Default Renewal Period (months)"), default=12
    )
    requires_profile_update = models.BooleanField(
        _("Requires Profile Update"), default=True
    )
    requires_fee_payment = models.BooleanField(_("Requires Fee Payment"), default=True)
    requires_policy_acceptance = models.BooleanField(
        _("Requires Policy Acceptance"), default=True
    )
    auto_expire_lapsed_members = models.BooleanField(
        _("Auto-Expire Lapsed Members"), default=False
    )

    class Meta:
        verbose_name = _("Renewal Rule")
        verbose_name_plural = _("Renewal Rules")

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Member Profile
# ---------------------------------------------------------------------------


class MemberProfile(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    ArchivableModel,
    NotesModel,
):
    """
    The primary membership record for a SITADC member.

    Each profile is linked to a system user account and captures the
    complete personal, contact, and membership information.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="member_profile",
        verbose_name=_("User Account"),
    )
    membership_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("Membership ID"),
        help_text=_("Auto-generated unique membership identifier."),
    )
    photo = models.ImageField(
        upload_to="memberships/photos/",
        blank=True,
        null=True,
        verbose_name=_("Profile Photo"),
    )

    # Personal information
    gender = models.CharField(
        max_length=30,
        choices=Gender.choices,
        blank=True,
        verbose_name=_("Gender"),
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Birth"),
    )
    nationality = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Nationality"),
    )
    national_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("National ID / Passport"),
    )
    education_level = models.CharField(
        max_length=30,
        choices=EducationLevel.choices,
        blank=True,
        verbose_name=_("Education Level"),
    )
    occupation = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("Occupation"),
    )

    # Contact information
    phone_primary = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_("Primary Phone"),
    )
    phone_secondary = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_("Secondary Phone"),
    )
    email_personal = models.EmailField(
        blank=True,
        verbose_name=_("Personal Email"),
    )
    physical_address = models.TextField(
        blank=True,
        verbose_name=_("Physical Address"),
    )
    province = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Province"),
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("District"),
    )
    community = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Community"),
    )

    # Emergency contact
    emergency_contact_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("Emergency Contact Name"),
    )
    emergency_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_("Emergency Contact Phone"),
    )
    emergency_contact_relationship = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_("Relationship"),
    )

    # Membership details (configuration-driven)
    category = models.ForeignKey(
        MembershipCategory,
        on_delete=models.PROTECT,
        related_name="member_profiles",
        null=True,
        blank=True,
        verbose_name=_("Membership Category"),
    )
    membership_type = models.ForeignKey(
        MembershipType,
        on_delete=models.PROTECT,
        related_name="member_profiles",
        null=True,
        blank=True,
        verbose_name=_("Membership Type"),
    )
    level = models.ForeignKey(
        MembershipLevel,
        on_delete=models.PROTECT,
        related_name="member_profiles",
        null=True,
        blank=True,
        verbose_name=_("Membership Level"),
    )
    status = models.ForeignKey(
        MembershipStatus,
        on_delete=models.PROTECT,
        related_name="member_profiles",
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Status"),
    )
    date_joined = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date Joined"),
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Membership Expiry Date"),
    )

    # Engagement and privacy
    profile_visibility = models.CharField(
        _("Profile Visibility"),
        max_length=20,
        choices=[
            ("PUBLIC", _("Public")),
            ("MEMBERS_ONLY", _("Members Only")),
            ("PRIVATE", _("Private")),
        ],
        default="MEMBERS_ONLY",
    )
    preferred_communication = models.CharField(
        _("Preferred Communication"),
        max_length=20,
        choices=CommunicationType.choices,
        default=CommunicationType.EMAIL,
    )
    referral_source = models.CharField(
        _("Referral Source"),
        max_length=200,
        blank=True,
    )
    responsibilities_acknowledged = models.BooleanField(
        _("Responsibilities Acknowledged"),
        default=False,
        help_text=_("Member has acknowledged organizational responsibilities."),
    )
    consent_to_communications = models.BooleanField(
        _("Consent to Communications"), default=True
    )

    # Skills and interests stored as comma-separated text; replaced by
    # MemberSkill / MemberInterest models for structured tracking.
    skills_summary = models.TextField(
        blank=True,
        verbose_name=_("Skills Summary"),
    )
    interests_summary = models.TextField(
        blank=True,
        verbose_name=_("Interests Summary"),
    )

    class Meta:
        verbose_name = _("Member Profile")
        verbose_name_plural = _("Member Profiles")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="member_status_idx"),
            models.Index(fields=["category"], name="member_category_idx"),
            models.Index(fields=["level"], name="member_level_idx"),
            models.Index(fields=["membership_id"], name="member_id_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user.full_name} [{self.membership_id or 'PENDING'}]"

    @property
    def is_active(self) -> bool:
        return self.status is not None and self.status.code == "ACTIVE"

    @property
    def is_suspended(self) -> bool:
        return self.status is not None and self.status.code == "SUSPENDED"

    @property
    def is_terminated(self) -> bool:
        return self.status is not None and self.status.code == "TERMINATED"

    @property
    def is_expired(self) -> bool:
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def status_display(self) -> str:
        return str(self.status.name if self.status else _("Unassigned"))

    @property
    def category_display(self) -> str:
        return str(self.category.name if self.category else _("Unassigned"))

    @property
    def membership_type_display(self) -> str:
        return str(
            self.membership_type.name if self.membership_type else _("Unassigned")
        )


# ---------------------------------------------------------------------------
# Membership Application
# ---------------------------------------------------------------------------


class MembershipApplication(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """
    A formal membership application submitted by a prospective member.

    Applications are reviewed, approved/rejected, and on approval a
    MemberProfile is created automatically.
    """

    reference_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("Reference Number"),
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="membership_applications",
        verbose_name=_("Applicant"),
    )

    # Personal information captured at application time
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(max_length=30, blank=True, verbose_name=_("Phone"))
    gender = models.CharField(
        max_length=30, choices=Gender.choices, blank=True, verbose_name=_("Gender")
    )
    date_of_birth = models.DateField(
        null=True, blank=True, verbose_name=_("Date of Birth")
    )
    nationality = models.CharField(
        max_length=100, blank=True, verbose_name=_("Nationality")
    )
    national_id = models.CharField(
        max_length=50, blank=True, verbose_name=_("National ID / Passport")
    )
    occupation = models.CharField(
        max_length=150, blank=True, verbose_name=_("Occupation")
    )
    education_level = models.CharField(
        max_length=30,
        choices=EducationLevel.choices,
        blank=True,
        verbose_name=_("Education Level"),
    )
    province = models.CharField(max_length=100, blank=True, verbose_name=_("Province"))
    district = models.CharField(max_length=100, blank=True, verbose_name=_("District"))
    community = models.CharField(
        max_length=100, blank=True, verbose_name=_("Community")
    )

    # Membership preferences (configuration-driven)
    category = models.ForeignKey(
        MembershipCategory,
        on_delete=models.PROTECT,
        related_name="applications",
        null=True,
        blank=True,
        verbose_name=_("Requested Category"),
    )
    membership_type = models.ForeignKey(
        MembershipType,
        on_delete=models.PROTECT,
        related_name="applications",
        null=True,
        blank=True,
        verbose_name=_("Membership Type"),
    )
    level = models.ForeignKey(
        MembershipLevel,
        on_delete=models.PROTECT,
        related_name="applications",
        null=True,
        blank=True,
        verbose_name=_("Membership Level"),
    )
    skills = models.TextField(blank=True, verbose_name=_("Skills"))
    interests = models.TextField(blank=True, verbose_name=_("Interests"))
    referral_source = models.CharField(
        max_length=200, blank=True, verbose_name=_("Referral Source")
    )
    declaration_agreed = models.BooleanField(
        default=False, verbose_name=_("Declaration Agreed")
    )
    responsibilities_acknowledged = models.BooleanField(
        default=False, verbose_name=_("Responsibilities Acknowledged")
    )

    # Workflow
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        db_index=True,
        verbose_name=_("Status"),
    )
    submitted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Submitted At")
    )
    verification_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Verification Status"),
        help_text=_("Outcome of the initial verification step."),
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_membership_applications",
        verbose_name=_("Reviewed By"),
    )
    reviewed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Reviewed At")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_membership_applications",
        verbose_name=_("Approved By"),
    )
    approved_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Approved At")
    )
    decision_notes = models.TextField(blank=True, verbose_name=_("Decision Notes"))

    # Link to created profile (set on approval)
    member_profile = models.OneToOneField(
        MemberProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application",
        verbose_name=_("Member Profile"),
    )

    class Meta:
        verbose_name = _("Membership Application")
        verbose_name_plural = _("Membership Applications")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"Application {self.reference_number} — {self.first_name} {self.last_name}"
        )


# ---------------------------------------------------------------------------
# Membership Renewal
# ---------------------------------------------------------------------------


class MembershipRenewal(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records a membership renewal request and its outcome."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="renewals",
        verbose_name=_("Member"),
    )
    previous_expiry = models.DateField(verbose_name=_("Previous Expiry Date"))
    new_expiry = models.DateField(
        null=True, blank=True, verbose_name=_("New Expiry Date")
    )
    renewal_period_months = models.PositiveIntegerField(
        default=12, verbose_name=_("Renewal Period (months)")
    )
    fee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Renewal Fee"),
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_("Payment Status"),
    )
    status = models.CharField(
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.PENDING,
        db_index=True,
        verbose_name=_("Renewal Status"),
    )
    policy_accepted = models.BooleanField(
        default=False, verbose_name=_("Policy Accepted")
    )
    profile_details_confirmed = models.BooleanField(
        default=False, verbose_name=_("Profile Details Confirmed")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_renewals",
        verbose_name=_("Approved By"),
    )
    approved_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Approved At")
    )

    class Meta:
        verbose_name = _("Membership Renewal")
        verbose_name_plural = _("Membership Renewals")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Renewal — {self.member} [{self.status}]"


# ---------------------------------------------------------------------------
# Membership Upgrade
# ---------------------------------------------------------------------------


class MembershipUpgrade(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records a category/level upgrade for an existing member."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="upgrades",
        verbose_name=_("Member"),
    )
    from_category = models.ForeignKey(
        MembershipCategory,
        on_delete=models.PROTECT,
        related_name="upgrades_from",
        verbose_name=_("From Category"),
    )
    to_category = models.ForeignKey(
        MembershipCategory,
        on_delete=models.PROTECT,
        related_name="upgrades_to",
        verbose_name=_("To Category"),
    )
    effective_date = models.DateField(verbose_name=_("Effective Date"))
    reason = models.TextField(blank=True, verbose_name=_("Reason"))
    status = models.CharField(
        max_length=20,
        choices=UpgradeStatus.choices,
        default=UpgradeStatus.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_upgrades",
        verbose_name=_("Approved By"),
    )

    class Meta:
        verbose_name = _("Membership Upgrade")
        verbose_name_plural = _("Membership Upgrades")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Upgrade — {self.member} ({self.from_category} → {self.to_category})"


# ---------------------------------------------------------------------------
# Membership Transfer
# ---------------------------------------------------------------------------


class MembershipTransfer(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records an administrative transfer of a member between regions/districts."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="transfers",
        verbose_name=_("Member"),
    )
    from_province = models.CharField(
        max_length=100, blank=True, verbose_name=_("From Province")
    )
    from_district = models.CharField(
        max_length=100, blank=True, verbose_name=_("From District")
    )
    from_community = models.CharField(
        max_length=100, blank=True, verbose_name=_("From Community")
    )
    to_province = models.CharField(
        max_length=100, blank=True, verbose_name=_("To Province")
    )
    to_district = models.CharField(
        max_length=100, blank=True, verbose_name=_("To District")
    )
    to_community = models.CharField(
        max_length=100, blank=True, verbose_name=_("To Community")
    )
    effective_date = models.DateField(verbose_name=_("Effective Date"))
    reason = models.TextField(blank=True, verbose_name=_("Reason"))
    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_transfers",
        verbose_name=_("Authorized By"),
    )

    class Meta:
        verbose_name = _("Membership Transfer")
        verbose_name_plural = _("Membership Transfers")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Transfer — {self.member} ({self.from_district} → {self.to_district})"


# ---------------------------------------------------------------------------
# Membership Suspension
# ---------------------------------------------------------------------------


class MembershipSuspension(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records a membership suspension and any subsequent reinstatement."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="suspensions",
        verbose_name=_("Member"),
    )
    reason = models.TextField(verbose_name=_("Suspension Reason"))
    effective_date = models.DateField(verbose_name=_("Effective Date"))
    review_date = models.DateField(null=True, blank=True, verbose_name=_("Review Date"))
    supporting_document = models.FileField(
        upload_to="memberships/suspensions/",
        blank=True,
        null=True,
        verbose_name=_("Supporting Document"),
    )
    lifted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Lifted At"))
    lifted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lifted_suspensions",
        verbose_name=_("Lifted By"),
    )
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_suspensions",
        verbose_name=_("Authorized By"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Currently Active"))

    class Meta:
        verbose_name = _("Membership Suspension")
        verbose_name_plural = _("Membership Suspensions")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Suspension — {self.member} ({self.effective_date})"


# ---------------------------------------------------------------------------
# Membership Termination
# ---------------------------------------------------------------------------


class MembershipTermination(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    NotesModel,
):
    """Records permanent termination of a membership. Immutable once created."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="terminations",
        verbose_name=_("Member"),
    )
    reason = models.CharField(
        max_length=40,
        choices=TerminationReason.choices,
        verbose_name=_("Reason"),
    )
    reason_detail = models.TextField(blank=True, verbose_name=_("Reason Detail"))
    effective_date = models.DateField(verbose_name=_("Effective Date"))
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_terminations",
        verbose_name=_("Authorized By"),
    )

    _is_new: ClassVar[bool] = True

    class Meta:
        verbose_name = _("Membership Termination")
        verbose_name_plural = _("Membership Terminations")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(IMMUTABLE_MEMBERSHIP_RECORD_MESSAGE)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(IMMUTABLE_MEMBERSHIP_RECORD_MESSAGE)

    def __str__(self) -> str:
        return f"Termination — {self.member} ({self.effective_date})"


# ---------------------------------------------------------------------------
# Membership Exit & Alumni
# ---------------------------------------------------------------------------


class MembershipExit(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records an exit from active membership and the transition to alumni."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="exits",
        verbose_name=_("Member"),
    )
    exit_type = models.CharField(
        max_length=40,
        choices=ExitType.choices,
        verbose_name=_("Exit Type"),
    )
    reason = models.TextField(blank=True, verbose_name=_("Reason"))
    effective_date = models.DateField(verbose_name=_("Effective Date"))
    status = models.CharField(
        max_length=30,
        choices=ExitStatus.choices,
        default=ExitStatus.INITIATED,
        db_index=True,
        verbose_name=_("Status"),
    )
    exit_interview_notes = models.TextField(
        blank=True, verbose_name=_("Exit Interview Notes")
    )
    assets_returned = models.BooleanField(
        default=False, verbose_name=_("Assets Returned")
    )
    documents_returned = models.BooleanField(
        default=False, verbose_name=_("Documents Returned")
    )
    outstanding_fees = models.BooleanField(
        default=False, verbose_name=_("Outstanding Fees")
    )
    clearances_completed = models.BooleanField(
        default=False, verbose_name=_("Clearances Completed")
    )
    transition_to_alumni = models.BooleanField(
        default=True, verbose_name=_("Transition to Alumni")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_membership_exits",
        verbose_name=_("Approved By"),
    )

    class Meta:
        verbose_name = _("Membership Exit")
        verbose_name_plural = _("Membership Exits")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Exit — {self.member} ({self.effective_date}) [{self.status}]"


class AlumniRecord(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    NotesModel,
):
    """Permanent alumni record for former members."""

    member = models.OneToOneField(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="alumni_record",
        verbose_name=_("Former Member"),
    )
    alumni_since = models.DateField(verbose_name=_("Alumni Since"))
    previous_category = models.ForeignKey(
        MembershipCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alumni_records",
        verbose_name=_("Previous Category"),
    )
    previous_level = models.CharField(
        max_length=100, blank=True, verbose_name=_("Previous Level")
    )
    previous_district = models.CharField(
        max_length=100, blank=True, verbose_name=_("Previous District")
    )
    contribution_summary = models.TextField(
        blank=True, verbose_name=_("Contribution Summary")
    )
    communication_consent = models.BooleanField(
        default=True, verbose_name=_("Communication Consent")
    )
    alumni_engagement = models.BooleanField(
        default=True, verbose_name=_("Eligible for Alumni Engagement")
    )
    rejoining_eligible = models.BooleanField(
        default=True, verbose_name=_("Rejoining Eligible")
    )
    exit_record = models.ForeignKey(
        MembershipExit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alumni_record",
        verbose_name=_("Exit Record"),
    )

    class Meta:
        verbose_name = _("Alumni Record")
        verbose_name_plural = _("Alumni Records")
        ordering = ["-alumni_since"]

    def __str__(self) -> str:
        return f"Alumni — {self.member} (since {self.alumni_since})"


# ---------------------------------------------------------------------------
# Membership Attendance
# ---------------------------------------------------------------------------


class MembershipAttendance(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records a member's attendance at an organizational activity."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="attendance_records",
        verbose_name=_("Member"),
    )
    activity_type = models.CharField(
        max_length=30,
        choices=AttendanceType.choices,
        verbose_name=_("Activity Type"),
    )
    activity_name = models.CharField(max_length=200, verbose_name=_("Activity Name"))
    activity_date = models.DateField(verbose_name=_("Activity Date"))
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
        verbose_name=_("Attendance Status"),
    )
    excuse_reason = models.TextField(blank=True, verbose_name=_("Excuse Reason"))

    class Meta:
        verbose_name = _("Membership Attendance")
        verbose_name_plural = _("Membership Attendances")
        ordering = ["-activity_date"]
        unique_together = [["member", "activity_type", "activity_date"]]

    def __str__(self) -> str:
        return f"{self.member} — {self.activity_name} [{self.status}]"


# ---------------------------------------------------------------------------
# Member Participation
# ---------------------------------------------------------------------------


class MemberParticipation(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records a member's participation in programs, projects and activities."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="participation_records",
        verbose_name=_("Member"),
    )
    participation_type = models.CharField(
        max_length=30,
        choices=ParticipationType.choices,
        verbose_name=_("Participation Type"),
    )
    activity_name = models.CharField(
        max_length=200, verbose_name=_("Activity / Programme Name")
    )
    role = models.CharField(max_length=150, blank=True, verbose_name=_("Role"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(null=True, blank=True, verbose_name=_("End Date"))
    status = models.CharField(
        max_length=20,
        choices=ParticipationStatus.choices,
        default=ParticipationStatus.ENROLLED,
        db_index=True,
        verbose_name=_("Status"),
    )
    outcomes = models.TextField(blank=True, verbose_name=_("Outcomes / Notes"))

    class Meta:
        verbose_name = _("Member Participation")
        verbose_name_plural = _("Member Participations")
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.member} — {self.activity_name} [{self.status}]"


# ---------------------------------------------------------------------------
# Member Committees
# ---------------------------------------------------------------------------


class MemberCommittee(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """A committee or working group a member may serve on."""

    name = models.CharField(_("Committee Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Member Committee")
        verbose_name_plural = _("Member Committees")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class MemberCommitteeAssignment(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Membership of a member on a committee."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="committee_assignments",
        verbose_name=_("Member"),
    )
    committee = models.ForeignKey(
        MemberCommittee,
        on_delete=models.PROTECT,
        related_name="assignments",
        verbose_name=_("Committee"),
    )
    position = models.CharField(
        max_length=150, blank=True, verbose_name=_("Position Held")
    )
    appointment_date = models.DateField(verbose_name=_("Appointment Date"))
    end_date = models.DateField(null=True, blank=True, verbose_name=_("End Date"))
    responsibilities = models.TextField(blank=True, verbose_name=_("Responsibilities"))
    status = models.CharField(
        max_length=20,
        choices=ParticipationStatus.choices,
        default=ParticipationStatus.ACTIVE,
        db_index=True,
        verbose_name=_("Status"),
    )

    class Meta:
        verbose_name = _("Committee Assignment")
        verbose_name_plural = _("Committee Assignments")
        ordering = ["-appointment_date"]

    def __str__(self) -> str:
        return f"{self.member} — {self.committee} ({self.position or _('Member')})"


# ---------------------------------------------------------------------------
# Membership Fee
# ---------------------------------------------------------------------------


class MembershipFee(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Configurable membership fee structure per category."""

    category = models.ForeignKey(
        MembershipCategory,
        on_delete=models.PROTECT,
        related_name="fees",
        verbose_name=_("Membership Category"),
    )
    fee_name = models.CharField(
        _("Fee Name"), max_length=150, default=_("Membership Fee")
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Amount")
    )
    currency = models.CharField(
        max_length=10, default="ZMW", verbose_name=_("Currency")
    )
    billing_frequency_months = models.PositiveIntegerField(
        default=12, verbose_name=_("Billing Frequency (months)")
    )
    effective_from = models.DateField(verbose_name=_("Effective From"))
    effective_to = models.DateField(
        null=True, blank=True, verbose_name=_("Effective To")
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_("Is Active"), db_index=True
    )

    class Meta:
        verbose_name = _("Membership Fee")
        verbose_name_plural = _("Membership Fees")
        ordering = ["-effective_from"]

    def __str__(self) -> str:
        return f"{self.category} — {self.currency} {self.amount}"


# ---------------------------------------------------------------------------
# Membership Payment
# ---------------------------------------------------------------------------


class MembershipPayment(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records a payment made for membership fees."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name=_("Member"),
    )
    fee = models.ForeignKey(
        MembershipFee,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
        verbose_name=_("Fee Structure"),
    )
    receipt_number = models.CharField(
        max_length=50, unique=True, blank=True, verbose_name=_("Receipt Number")
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Amount")
    )
    currency = models.CharField(
        max_length=10, default="ZMW", verbose_name=_("Currency")
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        verbose_name=_("Payment Method"),
    )
    payment_date = models.DateField(verbose_name=_("Payment Date"))
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    transaction_reference = models.CharField(
        max_length=100, blank=True, verbose_name=_("Transaction Reference")
    )
    period_from = models.DateField(null=True, blank=True, verbose_name=_("Period From"))
    period_to = models.DateField(null=True, blank=True, verbose_name=_("Period To"))
    receipt_file = models.FileField(
        upload_to="memberships/receipts/",
        blank=True,
        null=True,
        verbose_name=_("Receipt File"),
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_membership_payments",
        verbose_name=_("Verified By"),
    )
    verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Verified At")
    )

    class Meta:
        verbose_name = _("Membership Payment")
        verbose_name_plural = _("Membership Payments")
        ordering = ["-payment_date"]

    def __str__(self) -> str:
        return f"Payment {self.receipt_number} — {self.member}"


class MembershipFeeAdjustment(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records a discount, waiver or adjustment applied to a member's fees."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="fee_adjustments",
        verbose_name=_("Member"),
    )
    adjustment_type = models.CharField(
        max_length=20,
        choices=FeeAdjustmentType.choices,
        verbose_name=_("Adjustment Type"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Amount"),
        help_text=_("Absolute amount for the adjustment."),
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Percentage"),
        help_text=_("Percentage discount/waiver where applicable."),
    )
    reason = models.TextField(verbose_name=_("Reason"))
    effective_from = models.DateField(verbose_name=_("Effective From"))
    effective_to = models.DateField(
        null=True, blank=True, verbose_name=_("Effective To")
    )
    status = models.CharField(
        max_length=20,
        choices=AdjustmentStatus.choices,
        default=AdjustmentStatus.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_fee_adjustments",
        verbose_name=_("Approved By"),
    )

    class Meta:
        verbose_name = _("Membership Fee Adjustment")
        verbose_name_plural = _("Membership Fee Adjustments")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.adjustment_type} — {self.member}"


# ---------------------------------------------------------------------------
# Member Interest
# ---------------------------------------------------------------------------


class MemberInterest(UUIDModel, TimeStampedModel):
    """A tagged interest for a member profile."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="interests",
        verbose_name=_("Member"),
    )
    name = models.CharField(max_length=100, verbose_name=_("Interest"))

    class Meta:
        verbose_name = _("Member Interest")
        verbose_name_plural = _("Member Interests")
        unique_together = [["member", "name"]]

    def __str__(self) -> str:
        return f"{self.member} — {self.name}"


# ---------------------------------------------------------------------------
# Member Skill
# ---------------------------------------------------------------------------


class MemberSkill(UUIDModel, TimeStampedModel):
    """A skill entry for a member profile."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="skills",
        verbose_name=_("Member"),
    )
    name = models.CharField(max_length=100, verbose_name=_("Skill"))
    proficiency = models.CharField(
        max_length=50, blank=True, verbose_name=_("Proficiency Level")
    )

    class Meta:
        verbose_name = _("Member Skill")
        verbose_name_plural = _("Member Skills")
        unique_together = [["member", "name"]]

    def __str__(self) -> str:
        return f"{self.member} — {self.name}"


# ---------------------------------------------------------------------------
# Member Training Record
# ---------------------------------------------------------------------------


class MemberTrainingRecord(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    NotesModel,
):
    """Records training completed by a member."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="training_records",
        verbose_name=_("Member"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Training Title"))
    provider = models.CharField(max_length=200, blank=True, verbose_name=_("Provider"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    completion_date = models.DateField(
        null=True, blank=True, verbose_name=_("Completion Date")
    )
    certificate_issued = models.BooleanField(
        default=False, verbose_name=_("Certificate Issued")
    )
    competencies = models.TextField(blank=True, verbose_name=_("Competencies Acquired"))
    certificate_file = models.FileField(
        upload_to="memberships/certificates/",
        blank=True,
        null=True,
        verbose_name=_("Certificate File"),
    )

    class Meta:
        verbose_name = _("Member Training Record")
        verbose_name_plural = _("Member Training Records")
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.member} — {self.title}"


# ---------------------------------------------------------------------------
# Member Recognition
# ---------------------------------------------------------------------------


class MemberRecognition(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records recognition or an award granted to a member."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="recognitions",
        verbose_name=_("Member"),
    )
    recognition_type = models.CharField(
        max_length=30,
        choices=RecognitionType.choices,
        verbose_name=_("Recognition Type"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Recognition Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    award_date = models.DateField(verbose_name=_("Award Date"))
    issuing_authority = models.CharField(
        max_length=200, blank=True, verbose_name=_("Issuing Authority")
    )
    evidence_file = models.FileField(
        upload_to="memberships/recognitions/",
        blank=True,
        null=True,
        verbose_name=_("Evidence File"),
    )
    publication_permission = models.BooleanField(
        default=False, verbose_name=_("Permission to Publish")
    )

    class Meta:
        verbose_name = _("Member Recognition")
        verbose_name_plural = _("Member Recognitions")
        ordering = ["-award_date"]

    def __str__(self) -> str:
        return f"{self.member} — {self.title}"


# ---------------------------------------------------------------------------
# Member Leave
# ---------------------------------------------------------------------------


class MemberLeave(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Records a leave application for a member."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="leaves",
        verbose_name=_("Member"),
    )
    leave_type = models.CharField(
        max_length=20, choices=LeaveType.choices, verbose_name=_("Leave Type")
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    reason = models.TextField(blank=True, verbose_name=_("Reason"))
    status = models.CharField(
        max_length=20,
        choices=LeaveStatus.choices,
        default=LeaveStatus.SUBMITTED,
        db_index=True,
        verbose_name=_("Status"),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_member_leaves",
        verbose_name=_("Approved By"),
    )
    approval_notes = models.TextField(blank=True, verbose_name=_("Approval Notes"))

    class Meta:
        verbose_name = _("Member Leave")
        verbose_name_plural = _("Member Leaves")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.member} — {self.leave_type} [{self.status}]"


# ---------------------------------------------------------------------------
# Member Complaint (confidential)
# ---------------------------------------------------------------------------


class MemberComplaint(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Confidential complaint record (restricted access)."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="complaints",
        verbose_name=_("Member"),
    )
    complaint_type = models.CharField(
        max_length=30,
        choices=ComplaintType.choices,
        verbose_name=_("Complaint Type"),
    )
    description = models.TextField(verbose_name=_("Description"))
    status = models.CharField(
        max_length=30,
        choices=ComplaintStatus.choices,
        default=ComplaintStatus.RECEIVED,
        db_index=True,
        verbose_name=_("Status"),
    )
    resolution_notes = models.TextField(blank=True, verbose_name=_("Resolution Notes"))
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_member_complaints",
        verbose_name=_("Resolved By"),
    )
    resolved_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Resolved At")
    )

    class Meta:
        verbose_name = _("Member Complaint")
        verbose_name_plural = _("Member Complaints")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Complaint — {self.member} [{self.status}]"


# ---------------------------------------------------------------------------
# Member Disciplinary Record
# ---------------------------------------------------------------------------


class MemberDisciplinaryRecord(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Disciplinary record for a member."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="disciplinary_records",
        verbose_name=_("Member"),
    )
    disciplinary_type = models.CharField(
        max_length=30,
        choices=DisciplinaryType.choices,
        verbose_name=_("Disciplinary Type"),
    )
    description = models.TextField(verbose_name=_("Description"))
    incident_date = models.DateField(verbose_name=_("Incident Date"))
    status = models.CharField(
        max_length=30,
        choices=DisciplinaryStatus.choices,
        default=DisciplinaryStatus.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    resolution = models.TextField(blank=True, verbose_name=_("Resolution"))
    evidence_file = models.FileField(
        upload_to="memberships/disciplinary/",
        blank=True,
        null=True,
        verbose_name=_("Evidence File"),
    )
    is_confidential = models.BooleanField(default=True, verbose_name=_("Confidential"))

    class Meta:
        verbose_name = _("Member Disciplinary Record")
        verbose_name_plural = _("Member Disciplinary Records")
        ordering = ["-incident_date"]

    def __str__(self) -> str:
        return f"Disciplinary — {self.member} [{self.status}]"


# ---------------------------------------------------------------------------
# Membership Document
# ---------------------------------------------------------------------------


class MembershipDocument(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """A document attached to a membership profile."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name=_("Member"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    category = models.CharField(
        max_length=30,
        choices=DocumentCategory.choices,
        verbose_name=_("Category"),
    )
    file = models.FileField(
        upload_to="memberships/documents/",
        verbose_name=_("File"),
    )
    status = models.CharField(
        max_length=30,
        choices=DocumentStatus.choices,
        default=DocumentStatus.APPROVED,
        db_index=True,
        verbose_name=_("Status"),
    )
    version = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    confidentiality = models.CharField(
        max_length=20,
        choices=[
            ("PUBLIC", _("Public")),
            ("INTERNAL", _("Internal")),
            ("CONFIDENTIAL", _("Confidential")),
            ("RESTRICTED", _("Restricted")),
        ],
        default="INTERNAL",
        verbose_name=_("Confidentiality Level"),
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_membership_documents",
        verbose_name=_("Uploaded By"),
    )

    class Meta:
        verbose_name = _("Membership Document")
        verbose_name_plural = _("Membership Documents")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.member} — {self.title} (v{self.version})"


# ---------------------------------------------------------------------------
# Membership Card
# ---------------------------------------------------------------------------


class MembershipCard(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Digital / printable membership identification card."""

    member = models.OneToOneField(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="membership_card",
        verbose_name=_("Member"),
    )
    card_number = models.CharField(
        max_length=50, unique=True, verbose_name=_("Card Number")
    )
    verification_code = models.CharField(
        max_length=32, unique=True, verbose_name=_("Verification Code")
    )
    issue_date = models.DateField(verbose_name=_("Issue Date"))
    expiry_date = models.DateField(null=True, blank=True, verbose_name=_("Expiry Date"))
    status = models.CharField(
        max_length=20,
        choices=CardStatus.choices,
        default=CardStatus.ACTIVE,
        db_index=True,
        verbose_name=_("Status"),
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_membership_cards",
        verbose_name=_("Issued By"),
    )
    revoked_reason = models.TextField(blank=True, verbose_name=_("Revoked Reason"))

    class Meta:
        verbose_name = _("Membership Card")
        verbose_name_plural = _("Membership Cards")
        ordering = ["-issue_date"]

    def __str__(self) -> str:
        return f"Card {self.card_number} — {self.member}"


# ---------------------------------------------------------------------------
# Member Benefit Assignment
# ---------------------------------------------------------------------------


class MemberBenefitAssignment(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Assignment of a configured benefit to a member."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="benefit_assignments",
        verbose_name=_("Member"),
    )
    benefit = models.ForeignKey(
        MembershipBenefit,
        on_delete=models.PROTECT,
        related_name="assignments",
        verbose_name=_("Benefit"),
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_member_benefits",
        verbose_name=_("Granted By"),
    )
    granted_at = models.DateField(verbose_name=_("Granted At"))
    expires_at = models.DateField(null=True, blank=True, verbose_name=_("Expires At"))
    status = models.CharField(
        max_length=20,
        choices=BenefitStatus.choices,
        default=BenefitStatus.ACTIVE,
        db_index=True,
        verbose_name=_("Status"),
    )

    class Meta:
        verbose_name = _("Member Benefit Assignment")
        verbose_name_plural = _("Member Benefit Assignments")
        ordering = ["-granted_at"]

    def __str__(self) -> str:
        return f"{self.member} — {self.benefit}"


# ---------------------------------------------------------------------------
# Member Organization Assignment
# ---------------------------------------------------------------------------


class MemberOrganizationAssignment(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """Assignment of a member to an organizational unit."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="organization_assignments",
        verbose_name=_("Member"),
    )
    organizational_unit = models.ForeignKey(
        "organizations.OrganizationUnit",
        on_delete=models.PROTECT,
        related_name="member_assignments",
        null=True,
        blank=True,
        verbose_name=_("Organizational Unit"),
    )
    assignment_type = models.CharField(
        max_length=50, blank=True, verbose_name=_("Assignment Type")
    )
    effective_from = models.DateField(verbose_name=_("Effective From"))
    effective_to = models.DateField(
        null=True, blank=True, verbose_name=_("Effective To")
    )
    is_primary = models.BooleanField(
        default=False, verbose_name=_("Primary Assignment")
    )
    status = models.CharField(
        max_length=20,
        choices=ParticipationStatus.choices,
        default=ParticipationStatus.ACTIVE,
        db_index=True,
        verbose_name=_("Status"),
    )

    class Meta:
        verbose_name = _("Member Organization Assignment")
        verbose_name_plural = _("Member Organization Assignments")
        ordering = ["-effective_from"]

    def __str__(self) -> str:
        return f"{self.member} — {self.organizational_unit or _('Unit')}"


# ---------------------------------------------------------------------------
# Membership Communication
# ---------------------------------------------------------------------------


class MembershipCommunication(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    NotesModel,
):
    """A communication sent to members (in-app, email, SMS, ...)."""

    communication_type = models.CharField(
        max_length=30,
        choices=CommunicationType.choices,
        verbose_name=_("Communication Type"),
    )
    subject = models.CharField(max_length=200, verbose_name=_("Subject"))
    body = models.TextField(verbose_name=_("Body"))
    recipients = models.ManyToManyField(
        MemberProfile,
        related_name="communications",
        blank=True,
        verbose_name=_("Recipients"),
    )
    sent_to_all = models.BooleanField(
        default=False, verbose_name=_("Send to All Active Members")
    )
    status = models.CharField(
        max_length=20,
        choices=CommunicationStatus.choices,
        default=CommunicationStatus.DRAFT,
        db_index=True,
        verbose_name=_("Status"),
    )
    scheduled_for = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Scheduled For")
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Sent At"))
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_membership_communications",
        verbose_name=_("Sent By"),
    )

    class Meta:
        verbose_name = _("Membership Communication")
        verbose_name_plural = _("Membership Communications")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.subject} [{self.status}]"


# ---------------------------------------------------------------------------
# Membership Status History (immutable)
# ---------------------------------------------------------------------------


class MembershipStatusHistory(UUIDModel, TimeStampedModel):
    """Immutable record of every status change for a member profile."""

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.PROTECT,
        related_name="status_history",
        verbose_name=_("Member"),
    )
    from_status = models.ForeignKey(
        MembershipStatus,
        on_delete=models.PROTECT,
        related_name="status_history_from",
        null=True,
        blank=True,
        verbose_name=_("From Status"),
    )
    to_status = models.ForeignKey(
        MembershipStatus,
        on_delete=models.PROTECT,
        related_name="status_history_to",
        verbose_name=_("To Status"),
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Changed By"),
    )
    reason = models.TextField(blank=True, verbose_name=_("Reason"))

    class Meta:
        verbose_name = _("Membership Status History")
        verbose_name_plural = _("Membership Status Histories")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(IMMUTABLE_MEMBERSHIP_RECORD_MESSAGE)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(IMMUTABLE_MEMBERSHIP_RECORD_MESSAGE)

    def __str__(self) -> str:
        return f"{self.member}: {self.from_status} → {self.to_status}"


# ---------------------------------------------------------------------------
# Membership Audit Log (immutable)
# ---------------------------------------------------------------------------


class MembershipAuditRecord(UUIDModel, TimeStampedModel):
    """
    Immutable audit trail for all membership management events.

    Cannot be modified or deleted after creation.
    """

    entity_type = models.CharField(
        max_length=100, verbose_name=_("Entity Type"), db_index=True
    )
    entity_id = models.CharField(
        max_length=100, verbose_name=_("Entity ID"), db_index=True
    )
    action = models.CharField(
        max_length=40,
        choices=MembershipAuditAction.choices,
        verbose_name=_("Action"),
        db_index=True,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Changed By"),
    )
    from_data = models.JSONField(default=dict, verbose_name=_("From Data"))
    to_data = models.JSONField(default=dict, verbose_name=_("To Data"))
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name=_("IP Address")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Membership Audit Record")
        verbose_name_plural = _("Membership Audit Records")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["entity_type", "entity_id"],
                name="member_audit_entity_idx",
            ),
            models.Index(fields=["action"], name="member_audit_action_idx"),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(IMMUTABLE_MEMBERSHIP_RECORD_MESSAGE)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(IMMUTABLE_MEMBERSHIP_RECORD_MESSAGE)

    def __str__(self) -> str:
        return f"[{self.action}] {self.entity_type}/{self.entity_id}"
