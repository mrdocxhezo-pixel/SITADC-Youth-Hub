"""Normalized data model for the Phase 17 Beneficiary Management module.

The module owns the unified beneficiary profile and its lifecycle, while the
Phase 15/16 program and project modules reference beneficiaries by their
central references.  Every sensitive area (consent, safeguarding, outcomes,
exits) is modelled as a first-class, permission-gated entity with an
append-only history where immutability is required.
"""

# ruff: noqa: RUF012 - Django Meta options are declarative class attributes.

from __future__ import annotations

import hashlib
import logging
from typing import ClassVar, NoReturn, cast

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)
from apps.organizations.models import OrganizationUnit

from .constants import (
    DEFAULT_CURRENCY,
    AssessmentStatus,
    AttendanceStatus,
    BeneficiaryStatus,
    CaseNoteStatus,
    CommunicationChannel,
    CommunicationDirection,
    ConfidentialityLevel,
    ConsentStatus,
    ConsentType,
    DocumentStatus,
    DuplicateReviewStatus,
    EnrollmentStatus,
    ExitStatus,
    FeedbackStatus,
    FollowUpStatus,
    GroupStatus,
    GuardianRole,
    HouseholdStatus,
    OutcomeStatus,
    ParticipationStatus,
    PlanStatus,
    ReferenceDataKind,
    ReferralStatus,
    RiskLevel,
    SafeguardingStatus,
    ServiceDeliveryStatus,
    TransferStatus,
)
from .managers import IMMUTABLE_HISTORY_MESSAGE, ImmutableHistoryManager
from .storage import private_beneficiary_storage
from .validators import (
    is_minor,
    validate_beneficiary_document,
    validate_date_not_future,
    validate_date_of_birth,
    validate_date_range,
    validate_national_identifier,
    validate_percentage,
    validate_phone_number,
)

logger = logging.getLogger(__name__)


class BeneficiaryRecord(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
):
    """Common actor and timestamp metadata for beneficiary domain rows."""

    class Meta:
        abstract = True


class ImmutableHistoricalRecord:
    """Model-method protection for append-only historical rows.

    Rows are immutable after creation except for an explicit whitelist of
    lifecycle fields (for example consent status transitions).  Update saves
    must pass ``update_fields`` limited to that whitelist; everything else is
    rejected.
    """

    ALLOWED_UPDATE_FIELDS: ClassVar[set[str]] = set()

    def save(self, *args, **kwargs) -> None:
        model = cast(models.Model, self)
        if not model._state.adding:
            update_fields = kwargs.get("update_fields")
            if update_fields is not None and set(update_fields).issubset(
                self.ALLOWED_UPDATE_FIELDS
            ):
                models.Model.save(model, *args, **kwargs)
                return
            raise ValidationError(IMMUTABLE_HISTORY_MESSAGE, code="immutable_history")
        models.Model.save(model, *args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(IMMUTABLE_HISTORY_MESSAGE, code="immutable_history")


class BeneficiaryReferenceData(BeneficiaryRecord):
    """Configurable taxonomy shared by beneficiary profile and service fields."""

    kind = models.CharField(
        _("Kind"), max_length=40, choices=ReferenceDataKind.choices, db_index=True
    )
    code = models.SlugField(_("Code"), max_length=80)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    active = models.BooleanField(_("Active"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Beneficiary Reference Data")
        verbose_name_plural = _("Beneficiary Reference Data")
        ordering = ("kind", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "code"], name="beneficiary_ref_kind_code_uniq"
            )
        ]
        indexes = [models.Index(fields=["kind", "active", "order"])]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.name}"


class Beneficiary(
    BeneficiaryRecord,
    SoftDeleteModel,
    ArchivableModel,
):
    """Authoritative, consent-governed profile for a service beneficiary."""

    reference_number = models.CharField(
        _("Beneficiary ID"), max_length=80, unique=True, db_index=True
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=BeneficiaryStatus.choices,
        default=BeneficiaryStatus.IDENTIFIED,
        db_index=True,
    )
    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.CONFIDENTIAL,
        db_index=True,
    )

    first_name = models.CharField(_("First name"), max_length=120)
    middle_name = models.CharField(_("Middle name"), max_length=120, blank=True)
    last_name = models.CharField(_("Last name"), max_length=120)
    date_of_birth = models.DateField(_("Date of birth"), null=True, blank=True)
    gender = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="gender_beneficiaries",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.GENDER},
    )
    marital_status = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="marital_status_beneficiaries",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.MARITAL_STATUS},
    )
    nationality = models.CharField(_("Nationality"), max_length=100, blank=True)
    is_minor = models.BooleanField(_("Is a minor"), default=False, db_index=True)

    category = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="category_beneficiaries",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.CATEGORY},
    )
    classification = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="classified_beneficiaries",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.CLASSIFICATION},
    )
    vulnerabilities = models.ManyToManyField(
        BeneficiaryReferenceData,
        related_name="vulnerable_beneficiaries",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.VULNERABILITY},
    )
    inclusion_barriers = models.ManyToManyField(
        BeneficiaryReferenceData,
        related_name="inclusion_barrier_beneficiaries",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.INCLUSION},
    )
    disabilities = models.ManyToManyField(
        BeneficiaryReferenceData,
        related_name="disability_beneficiaries",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.DISABILITY},
    )
    skills = models.ManyToManyField(
        BeneficiaryReferenceData,
        related_name="skilled_beneficiaries",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.SKILL},
    )
    interests = models.ManyToManyField(
        BeneficiaryReferenceData,
        related_name="interested_beneficiaries",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.INTEREST},
    )
    needs = models.ManyToManyField(
        BeneficiaryReferenceData,
        related_name="needed_beneficiaries",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.NEED_TYPE},
    )

    education_level = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="education_beneficiaries",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.EDUCATION_LEVEL},
    )
    school_name = models.CharField(
        _("School or institution"), max_length=220, blank=True
    )
    current_grade = models.CharField(
        _("Current grade or level"), max_length=120, blank=True
    )
    is_in_school = models.BooleanField(_("Currently in school"), default=False)

    occupation = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="occupation_beneficiaries",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.OCCUPATION},
    )
    employment_status = models.CharField(
        _("Employment status"), max_length=80, blank=True
    )
    workplace = models.CharField(
        _("Workplace or enterprise"), max_length=220, blank=True
    )

    phone_primary = models.CharField(
        _("Primary phone"),
        max_length=40,
        blank=True,
        validators=[validate_phone_number],
    )
    phone_secondary = models.CharField(
        _("Secondary phone"),
        max_length=40,
        blank=True,
        validators=[validate_phone_number],
    )
    whatsapp_number = models.CharField(
        _("WhatsApp number"),
        max_length=40,
        blank=True,
        validators=[validate_phone_number],
    )
    email = models.EmailField(_("Email"), blank=True)
    physical_address = models.TextField(_("Physical address"), blank=True)
    country = models.CharField(_("Country"), max_length=100, blank=True)
    province_or_region = models.CharField(
        _("Province or region"), max_length=120, blank=True, db_index=True
    )
    district = models.CharField(
        _("District"), max_length=120, blank=True, db_index=True
    )
    community = models.CharField(
        _("Community"), max_length=120, blank=True, db_index=True
    )
    ward = models.CharField(_("Ward"), max_length=120, blank=True)
    village = models.CharField(_("Village"), max_length=120, blank=True)
    gps_coordinates = models.CharField(
        _("GPS coordinates"),
        max_length=80,
        blank=True,
        help_text=_("Record only where operationally necessary and authorized."),
    )

    national_id_number = models.CharField(
        _("National ID number"),
        max_length=60,
        blank=True,
        validators=[validate_national_identifier],
    )
    birth_certificate_number = models.CharField(
        _("Birth certificate number"),
        max_length=60,
        blank=True,
        validators=[validate_national_identifier],
    )
    passport_number = models.CharField(
        _("Passport number"),
        max_length=60,
        blank=True,
        validators=[validate_national_identifier],
    )
    other_identifier = models.CharField(
        _("Other identifier"), max_length=120, blank=True
    )

    household = models.ForeignKey(
        "BeneficiaryHousehold",
        on_delete=models.SET_NULL,
        related_name="members",
        null=True,
        blank=True,
    )
    is_household_head = models.BooleanField(_("Is household head"), default=False)

    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        related_name="beneficiaries",
        null=True,
        blank=True,
    )
    primary_responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="primary_beneficiary_responsibilities",
        null=True,
        blank=True,
    )
    case_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_beneficiaries",
        null=True,
        blank=True,
    )

    referral_source = models.CharField(_("Referral source"), max_length=180, blank=True)
    registration_date = models.DateField(
        _("Registration date"), default=timezone.localdate, db_index=True
    )
    verification_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="verified_beneficiaries",
        null=True,
        blank=True,
    )
    eligibility_notes = models.TextField(_("Eligibility notes"), blank=True)
    enrolled_at = models.DateField(null=True, blank=True)
    graduated_at = models.DateField(null=True, blank=True)
    exited_at = models.DateField(null=True, blank=True)

    consent_status = models.CharField(
        _("Consent status"),
        max_length=20,
        choices=ConsentStatus.choices,
        default=ConsentStatus.DENIED,
        db_index=True,
    )
    consent_recorded_at = models.DateTimeField(null=True, blank=True)
    consent_expiry_date = models.DateField(null=True, blank=True)
    consent_version = models.CharField(
        _("Consent form version"), max_length=60, blank=True
    )
    assent_recorded = models.BooleanField(_("Child assent recorded"), default=False)
    assent_recorded_at = models.DateTimeField(null=True, blank=True)
    assent_version = models.CharField(
        _("Assent form version"), max_length=60, blank=True
    )

    safeguarding_concerns = models.BooleanField(
        _("Safeguarding concerns recorded"), default=False, db_index=True
    )
    safeguarding_notes = models.TextField(_("Safeguarding notes"), blank=True)

    duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="possible_duplicates",
        null=True,
        blank=True,
    )
    duplicate_review_status = models.CharField(
        _("Duplicate review status"),
        max_length=20,
        choices=DuplicateReviewStatus.choices,
        default=DuplicateReviewStatus.PENDING,
        db_index=True,
    )

    notes = models.TextField(_("Notes"), blank=True)

    objects: ClassVar[models.Manager[Beneficiary]] = models.Manager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Beneficiary")
        verbose_name_plural = _("Beneficiaries")
        ordering = ("last_name", "first_name")
        indexes = [
            models.Index(fields=["status", "confidentiality"]),
            models.Index(fields=["province_or_region", "district"]),
            models.Index(fields=["primary_responsible_officer", "status"]),
            models.Index(fields=["case_manager", "status"]),
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["is_minor", "consent_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.reference_number})"

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(part for part in parts if part)

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.registration_date)
        if self.date_of_birth:
            validate_date_of_birth(self.date_of_birth)
            self.is_minor = is_minor(self.date_of_birth)
        if self.verification_date and self.verification_date < self.registration_date:
            raise ValidationError(
                {"verification_date": _("Verification cannot precede registration.")}
            )
        validate_date_range(
            self.registration_date, self.enrolled_at, end_field="enrolled_at"
        )
        validate_date_range(
            self.registration_date, self.graduated_at, end_field="graduated_at"
        )
        validate_date_range(
            self.registration_date, self.exited_at, end_field="exited_at"
        )
        for field_name, expected_kind in (
            ("gender", ReferenceDataKind.GENDER),
            ("marital_status", ReferenceDataKind.MARITAL_STATUS),
            ("category", ReferenceDataKind.CATEGORY),
            ("classification", ReferenceDataKind.CLASSIFICATION),
            ("education_level", ReferenceDataKind.EDUCATION_LEVEL),
            ("occupation", ReferenceDataKind.OCCUPATION),
        ):
            value = getattr(self, field_name, None)
            if value and value.kind != expected_kind:
                raise ValidationError(
                    {field_name: _("Selected reference data has the wrong kind.")}
                )
        if (
            self.is_minor
            and self.consent_status
            in {
                ConsentStatus.GRANTED,
                ConsentStatus.WITHDRAWN,
            }
            and not self.assent_recorded
        ):
            raise ValidationError(
                {
                    "assent_recorded": _(
                        "Assent must be recorded for a consenting minor."
                    )
                }
            )
        if self.status == BeneficiaryStatus.VERIFIED and not (
            self.verification_date and self.verified_by_id
        ):
            raise ValidationError(
                {"status": _("Verified beneficiaries require verification metadata.")}
            )


class BeneficiaryStatusHistory(ImmutableHistoricalRecord, BeneficiaryRecord):
    """Append-only beneficiary lifecycle history."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="status_history"
    )
    from_status = models.CharField(max_length=30, choices=BeneficiaryStatus.choices)
    to_status = models.CharField(max_length=30, choices=BeneficiaryStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="beneficiary_status_changes",
        null=True,
        blank=True,
    )
    reason = models.TextField(blank=True)
    effective_date = models.DateTimeField(default=timezone.now, db_index=True)
    context = models.JSONField(default=dict, blank=True)

    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("-effective_date",)
        indexes = [models.Index(fields=["beneficiary", "effective_date"])]

    def __str__(self) -> str:
        return f"{self.beneficiary}: {self.from_status} to {self.to_status}"


class GuardianRecord(BeneficiaryRecord):
    """A recorded guardian or care-giver for a beneficiary (often a minor)."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="guardians"
    )
    full_name = models.CharField(max_length=180)
    relationship = models.CharField(
        max_length=20, choices=GuardianRole.choices, default=GuardianRole.PARENT
    )
    relationship_other = models.CharField(max_length=120, blank=True)
    phone_primary = models.CharField(
        _("Primary phone"),
        max_length=40,
        blank=True,
        validators=[validate_phone_number],
    )
    phone_secondary = models.CharField(
        _("Secondary phone"),
        max_length=40,
        blank=True,
        validators=[validate_phone_number],
    )
    email = models.EmailField(blank=True)
    national_id_number = models.CharField(
        _("National ID number"), max_length=60, blank=True
    )
    physical_address = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    consent_recorded = models.BooleanField(_("Consent recorded"), default=False)
    consent_recorded_at = models.DateTimeField(null=True, blank=True)
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-is_primary", "full_name")
        constraints = [
            models.UniqueConstraint(
                fields=["beneficiary"],
                condition=models.Q(is_primary=True, is_active=True),
                name="beneficiary_one_active_primary_guardian",
            )
        ]
        indexes = [models.Index(fields=["beneficiary", "is_active", "is_primary"])]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.beneficiary}"

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.valid_from, self.valid_to, end_field="valid_to")
        if not (self.phone_primary or self.phone_secondary or self.email):
            raise ValidationError(_("A guardian requires contact details."))
        if self.is_primary and not self.is_active:
            raise ValidationError(
                {"is_primary": _("A primary guardian must be active.")}
            )


class BeneficiaryHousehold(BeneficiaryRecord):
    """A shared living and economic unit for one or more beneficiaries."""

    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    household_name = models.CharField(_("Household name"), max_length=220)
    household_type = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="households",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.HOUSEHOLD_TYPE},
    )
    head = models.ForeignKey(
        Beneficiary,
        on_delete=models.SET_NULL,
        related_name="headed_households",
        null=True,
        blank=True,
    )
    physical_address = models.TextField(_("Physical address"), blank=True)
    country = models.CharField(_("Country"), max_length=100, blank=True)
    province_or_region = models.CharField(
        _("Province or region"), max_length=120, blank=True, db_index=True
    )
    district = models.CharField(
        _("District"), max_length=120, blank=True, db_index=True
    )
    community = models.CharField(_("Community"), max_length=120, blank=True)
    village = models.CharField(_("Village"), max_length=120, blank=True)
    number_of_members = models.PositiveIntegerField(default=0)
    number_of_dependents = models.PositiveIntegerField(default=0)
    primary_income_source = models.CharField(max_length=160, blank=True)
    monthly_income = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    status = models.CharField(
        max_length=20,
        choices=HouseholdStatus.choices,
        default=HouseholdStatus.PROSPECTIVE,
        db_index=True,
    )
    formed_on = models.DateField(default=timezone.localdate)
    closed_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Beneficiary Household")
        verbose_name_plural = _("Beneficiary Households")
        ordering = ("household_name",)
        indexes = [models.Index(fields=["status", "province_or_region"])]

    def __str__(self) -> str:
        return f"{self.household_name} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.formed_on)
        validate_date_range(self.formed_on, self.closed_on, end_field="closed_on")
        head = self.head
        if (
            head is not None
            and head.household_id is not None
            and head.household_id != self.pk
        ):
            raise ValidationError(
                {"head": _("The household head belongs to another household.")}
            )

    def recalculate_member_count(self) -> None:
        count = self.memberships.filter(is_active=True).count()
        type(self).objects.filter(pk=self.pk).update(number_of_members=count)


class HouseholdMember(BeneficiaryRecord):
    """Membership of a beneficiary within a household."""

    household = models.ForeignKey(
        BeneficiaryHousehold, on_delete=models.PROTECT, related_name="memberships"
    )
    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="household_memberships"
    )
    relationship_to_head = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="household_members",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.RELATIONSHIP},
    )
    is_head = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    joined_on = models.DateField(default=timezone.localdate)
    left_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("-is_head", "beneficiary__last_name")
        constraints = [
            models.UniqueConstraint(
                fields=["household", "beneficiary"],
                name="household_member_household_beneficiary_uniq",
            )
        ]
        indexes = [models.Index(fields=["household", "is_active"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} in {self.household}"

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.joined_on, self.left_on, end_field="left_on")


class BeneficiaryGroup(BeneficiaryRecord):
    """A cohort or self-help group of beneficiaries with shared objectives."""

    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    group_name = models.CharField(_("Group name"), max_length=220)
    group_type = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="groups",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.GROUP_TYPE},
    )
    description = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    formation_date = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=20,
        choices=GroupStatus.choices,
        default=GroupStatus.FORMING,
        db_index=True,
    )
    province_or_region = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    community = models.CharField(max_length=120, blank=True)
    meeting_schedule = models.CharField(max_length=160, blank=True)
    group_leader = models.ForeignKey(
        Beneficiary,
        on_delete=models.SET_NULL,
        related_name="led_groups",
        null=True,
        blank=True,
    )
    member_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Beneficiary Group")
        verbose_name_plural = _("Beneficiary Groups")
        ordering = ("group_name",)
        indexes = [models.Index(fields=["status", "district"])]

    def __str__(self) -> str:
        return f"{self.group_name} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.formation_date)
        group_type = self.group_type
        if group_type is not None and group_type.kind != ReferenceDataKind.GROUP_TYPE:
            raise ValidationError({"group_type": _("Invalid group type kind.")})

    def recalculate_member_count(self) -> None:
        count = self.memberships.filter(is_active=True).count()
        type(self).objects.filter(pk=self.pk).update(member_count=count)


class GroupMembership(BeneficiaryRecord):
    """Membership of a beneficiary within a beneficiary group."""

    group = models.ForeignKey(
        BeneficiaryGroup, on_delete=models.PROTECT, related_name="memberships"
    )
    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="group_memberships"
    )
    role = models.CharField(_("Role"), max_length=120, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    joined_on = models.DateField(default=timezone.localdate)
    left_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("-joined_on",)
        constraints = [
            models.UniqueConstraint(
                fields=["group", "beneficiary"],
                name="beneficiary_group_member_uniq",
            )
        ]
        indexes = [models.Index(fields=["group", "is_active"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} in {self.group}"

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.joined_on, self.left_on, end_field="left_on")


class BeneficiaryEnrollment(BeneficiaryRecord):
    """Enrollment of a beneficiary in a program, project, or intervention."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="enrollments"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    enrollment_type = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="enrollments",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.ENROLLMENT_TYPE},
    )
    program_reference = models.CharField(
        _("Program reference"), max_length=180, blank=True
    )
    project_reference = models.CharField(
        _("Project reference"), max_length=180, blank=True
    )
    activity_title = models.CharField(
        _("Activity or intervention title"), max_length=220
    )
    description = models.TextField(blank=True)
    source = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="enrollment_sources",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.ENROLLMENT_SOURCE},
    )
    enrollment_date = models.DateField(default=timezone.localdate, db_index=True)
    exit_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.PENDING,
        db_index=True,
    )
    objectives = models.TextField(blank=True)
    needs_addressed = models.TextField(blank=True)
    expected_outcome_date = models.DateField(null=True, blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_beneficiary_enrollments",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-enrollment_date",)
        indexes = [models.Index(fields=["beneficiary", "status", "enrollment_date"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.activity_title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.enrollment_date)
        validate_date_range(self.enrollment_date, self.exit_date, end_field="exit_date")
        validate_date_range(
            self.enrollment_date,
            self.expected_outcome_date,
            end_field="expected_outcome_date",
        )
        enrollment_type = self.enrollment_type
        if (
            enrollment_type is not None
            and enrollment_type.kind != ReferenceDataKind.ENROLLMENT_TYPE
        ):
            raise ValidationError(
                {"enrollment_type": _("Invalid enrollment type kind.")}
            )
        source = self.source
        if source is not None and source.kind != ReferenceDataKind.ENROLLMENT_SOURCE:
            raise ValidationError({"source": _("Invalid enrollment source kind.")})


class BeneficiaryParticipation(BeneficiaryRecord):
    """Recorded participation of a beneficiary in a program or project activity."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="participations"
    )
    enrollment = models.ForeignKey(
        BeneficiaryEnrollment,
        on_delete=models.SET_NULL,
        related_name="participations",
        null=True,
        blank=True,
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    activity_title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    activity_date = models.DateField(db_index=True)
    duration_hours = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    location = models.CharField(max_length=220, blank=True)
    facilitator = models.CharField(max_length=180, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ParticipationStatus.choices,
        default=ParticipationStatus.CONFIRMED,
        db_index=True,
    )
    services_received = models.TextField(blank=True)
    outcomes_observed = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-activity_date",)
        indexes = [models.Index(fields=["beneficiary", "activity_date"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.activity_title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.activity_date)
        enrollment = self.enrollment
        if (
            self.enrollment_id
            and enrollment is not None
            and enrollment.beneficiary_id != self.beneficiary_id
        ):
            raise ValidationError(
                {"enrollment": _("Enrollment belongs to a different beneficiary.")}
            )


class AttendanceRecord(BeneficiaryRecord):
    """Attendance of a beneficiary at a scheduled session or event."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="attendance_records"
    )
    participation = models.ForeignKey(
        BeneficiaryParticipation,
        on_delete=models.SET_NULL,
        related_name="attendance",
        null=True,
        blank=True,
    )
    session_title = models.CharField(max_length=220)
    session_date = models.DateField(db_index=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
        db_index=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_beneficiary_attendance",
        null=True,
        blank=True,
    )
    reason = models.CharField(_("Absence reason"), max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-session_date",)
        indexes = [models.Index(fields=["beneficiary", "session_date"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.session_title} ({self.status})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.session_date)
        participation = self.participation
        if (
            self.participation_id
            and participation is not None
            and participation.beneficiary_id != self.beneficiary_id
        ):
            raise ValidationError(
                {
                    "participation": _(
                        "Participation belongs to a different beneficiary."
                    )
                }
            )


class ServiceDeliveryRecord(BeneficiaryRecord):
    """Delivery of a service to a beneficiary, with outcome and verification."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="services_received"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    service_type = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="service_deliveries",
        limit_choices_to={"kind": ReferenceDataKind.SERVICE_TYPE},
    )
    service_name = models.CharField(_("Service name"), max_length=220)
    description = models.TextField(blank=True)
    service_date = models.DateField(db_index=True)
    quantity = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    unit = models.CharField(_("Unit"), max_length=60, blank=True)
    provider = models.CharField(_("Provider"), max_length=180, blank=True)
    provider_reference = models.CharField(max_length=180, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ServiceDeliveryStatus.choices,
        default=ServiceDeliveryStatus.PLANNED,
        db_index=True,
    )
    delivered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="delivered_beneficiary_services",
        null=True,
        blank=True,
    )
    delivered_at = models.DateTimeField(null=True, blank=True)
    outcome_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-service_date",)
        indexes = [models.Index(fields=["beneficiary", "service_date", "status"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.service_name} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.service_date)
        if (
            self.service_type_id
            and self.service_type.kind != ReferenceDataKind.SERVICE_TYPE
        ):
            raise ValidationError({"service_type": _("Invalid service type kind.")})
        if self.status == ServiceDeliveryStatus.DELIVERED and not self.delivered_at:
            raise ValidationError(
                {"delivered_at": _("Delivered services require a delivery time.")}
            )


class Referral(BeneficiaryRecord):
    """Internal or external referral made on behalf of a beneficiary."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="referrals"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    referral_type = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="referrals",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.REFERRAL_TYPE},
    )
    referral_date = models.DateField(default=timezone.localdate, db_index=True)
    referred_from = models.CharField(max_length=180, blank=True)
    referred_to = models.CharField(max_length=180)
    reason = models.TextField()
    priority = models.PositiveSmallIntegerField(
        choices=RiskLevel.choices,
        default=RiskLevel.MODERATE,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    expected_response_date = models.DateField(null=True, blank=True)
    response_received = models.BooleanField(default=False)
    response_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ReferralStatus.choices,
        default=ReferralStatus.OPEN,
        db_index=True,
    )
    closed_on = models.DateField(null=True, blank=True)
    follow_up_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="beneficiary_referral_followups",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-referral_date",)
        indexes = [models.Index(fields=["beneficiary", "status", "referral_date"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} -> {self.referred_to} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.referral_date)
        validate_date_range(
            self.referral_date,
            self.expected_response_date,
            end_field="expected_response_date",
        )
        validate_date_range(self.referral_date, self.closed_on, end_field="closed_on")
        referral_type = self.referral_type
        if (
            referral_type is not None
            and referral_type.kind != ReferenceDataKind.REFERRAL_TYPE
        ):
            raise ValidationError({"referral_type": _("Invalid referral type kind.")})


class CaseNote(BeneficiaryRecord):
    """A structured case-management note with confidentiality control."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="case_notes"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    note_type = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="case_notes",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.CASE_NOTE_TYPE},
    )
    title = models.CharField(max_length=220)
    content = models.TextField()
    occurred_on = models.DateField(default=timezone.localdate, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=CaseNoteStatus.choices,
        default=CaseNoteStatus.FINALIZED,
        db_index=True,
    )
    is_confidential = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="authored_beneficiary_case_notes",
        null=True,
        blank=True,
    )
    related_referral = models.ForeignKey(
        Referral,
        on_delete=models.SET_NULL,
        related_name="case_notes",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-occurred_on", "-created_at")
        indexes = [models.Index(fields=["beneficiary", "occurred_on"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.title}"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.occurred_on)
        note_type = self.note_type
        if note_type is not None and note_type.kind != ReferenceDataKind.CASE_NOTE_TYPE:
            raise ValidationError({"note_type": _("Invalid case note type kind.")})
        referral = self.related_referral
        if (
            self.related_referral_id
            and referral is not None
            and referral.beneficiary_id != self.beneficiary_id
        ):
            raise ValidationError(
                {"related_referral": _("Referral belongs to a different beneficiary.")}
            )


class FollowUpVisit(BeneficiaryRecord):
    """A scheduled or completed follow-up visit or contact."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="follow_ups"
    )
    purpose = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="follow_ups",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.FOLLOW_UP_PURPOSE},
    )
    scheduled_on = models.DateField(db_index=True)
    completed_on = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=FollowUpStatus.choices,
        default=FollowUpStatus.PLANNED,
        db_index=True,
    )
    method = models.CharField(max_length=80, default="HOME_VISIT")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_beneficiary_follow_ups",
        null=True,
        blank=True,
    )
    summary = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    action_items = models.TextField(blank=True)
    next_follow_up_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("-scheduled_on",)
        indexes = [models.Index(fields=["beneficiary", "status", "scheduled_on"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.scheduled_on} ({self.status})"

    @property
    def is_overdue(self) -> bool:
        return (
            self.status == FollowUpStatus.PLANNED
            and self.scheduled_on < timezone.localdate()
        )

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.scheduled_on)
        validate_date_range(
            self.scheduled_on, self.completed_on, end_field="completed_on"
        )
        purpose = self.purpose
        if purpose is not None and purpose.kind != ReferenceDataKind.FOLLOW_UP_PURPOSE:
            raise ValidationError({"purpose": _("Invalid follow-up purpose kind.")})
        if self.status == FollowUpStatus.COMPLETED and not self.completed_on:
            raise ValidationError(
                {"completed_on": _("Completed follow-ups require a completion date.")}
            )


class BeneficiaryAssessment(BeneficiaryRecord):
    """A structured needs or eligibility assessment with reproducible output."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="assessments"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    assessment_type = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="assessments",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.ASSESSMENT_TYPE},
    )
    assessment_date = models.DateField(default=timezone.localdate, db_index=True)
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="beneficiary_assessments_completed",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.DRAFT,
        db_index=True,
    )
    scores = models.JSONField(
        _("Dimension scores"),
        default=dict,
        blank=True,
        help_text=_("Named assessment dimensions with numeric scores and rationale."),
    )
    summary = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    priority_needs = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    next_review_date = models.DateField(null=True, blank=True, db_index=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="submitted_beneficiary_assessments",
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_beneficiary_assessments",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-assessment_date", "-created_at")
        indexes = [models.Index(fields=["beneficiary", "assessment_date"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.assessment_date} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.assessment_date)
        assessment_type = self.assessment_type
        if (
            assessment_type is not None
            and assessment_type.kind != ReferenceDataKind.ASSESSMENT_TYPE
        ):
            raise ValidationError(
                {"assessment_type": _("Invalid assessment type kind.")}
            )


class SupportPlan(BeneficiaryRecord):
    """A time-bound plan of interventions derived from an assessment."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="support_plans"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    title = models.CharField(max_length=220)
    assessment = models.ForeignKey(
        BeneficiaryAssessment,
        on_delete=models.SET_NULL,
        related_name="support_plans",
        null=True,
        blank=True,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PlanStatus.choices,
        default=PlanStatus.DRAFT,
        db_index=True,
    )
    goals = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    interventions = models.TextField(blank=True)
    support_coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="coordinated_beneficiary_support_plans",
        null=True,
        blank=True,
    )
    next_review_date = models.DateField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-start_date",)
        indexes = [models.Index(fields=["beneficiary", "status"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date, end_field="end_date")
        assessment = self.assessment
        if (
            self.assessment_id
            and assessment is not None
            and assessment.beneficiary_id != self.beneficiary_id
        ):
            raise ValidationError(
                {"assessment": _("Assessment belongs to a different beneficiary.")}
            )


class ConsentRecord(ImmutableHistoricalRecord, BeneficiaryRecord):
    """Immutable, versioned record of consent or assent for a beneficiary."""

    ALLOWED_UPDATE_FIELDS = {"status", "withdrawal_reason", "updated_by"}

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="consent_records"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    consent_type = models.CharField(
        max_length=20, choices=ConsentType.choices, default=ConsentType.DATA_PROCESSING
    )
    status = models.CharField(
        max_length=20, choices=ConsentStatus.choices, default=ConsentStatus.GRANTED
    )
    is_assent = models.BooleanField(_("Is child assent"), default=False)
    provided_by = models.CharField(_("Provided by"), max_length=180)
    relationship = models.CharField(
        max_length=20, choices=GuardianRole.choices, blank=True
    )
    recorded_on = models.DateField(default=timezone.localdate)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_beneficiary_consent",
        null=True,
        blank=True,
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    form_version = models.CharField(max_length=60, blank=True)
    details = models.TextField(blank=True)
    witness_name = models.CharField(max_length=180, blank=True)
    document = models.FileField(
        upload_to="beneficiaries/consent/",
        storage=private_beneficiary_storage,
        validators=[validate_beneficiary_document],
        null=True,
        blank=True,
    )
    withdrawal_reason = models.TextField(blank=True)

    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("-recorded_on", "-created_at")
        indexes = [models.Index(fields=["beneficiary", "consent_type"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.get_consent_type_display()} ({self.status})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.recorded_on)
        validate_date_range(self.valid_from, self.valid_to, end_field="valid_to")
        if self.is_assent and not self.beneficiary.is_minor:
            raise ValidationError(
                {"is_assent": _("Assent applies only to minor beneficiaries.")}
            )


class SafeguardingRecord(ImmutableHistoricalRecord, BeneficiaryRecord):
    """Immutable safeguarding concern, action, and closure record."""

    ALLOWED_UPDATE_FIELDS = {
        "status",
        "investigation_notes",
        "resolved_on",
        "outcome",
        "updated_by",
    }

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="safeguarding_records"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    category = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="safeguarding_records",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.SAFEGUARDING_CATEGORY},
    )
    reported_on = models.DateField(default=timezone.localdate, db_index=True)
    reported_by = models.CharField(_("Reported by"), max_length=180)
    reporter_role = models.CharField(max_length=120, blank=True)
    confidentiality = models.CharField(
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.RESTRICTED,
    )
    description = models.TextField()
    immediate_action = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=SafeguardingStatus.choices,
        default=SafeguardingStatus.OPEN,
        db_index=True,
    )
    risk_level = models.PositiveSmallIntegerField(
        choices=RiskLevel.choices,
        default=RiskLevel.HIGH,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    investigation_notes = models.TextField(blank=True)
    actions_taken = models.TextField(blank=True)
    external_reference = models.CharField(max_length=180, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_beneficiary_safeguarding",
        null=True,
        blank=True,
    )
    resolved_on = models.DateField(null=True, blank=True)
    outcome = models.TextField(blank=True)

    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("-reported_on", "-created_at")
        indexes = [models.Index(fields=["beneficiary", "status"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - safeguarding ({self.status})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.reported_on)
        validate_date_range(self.reported_on, self.resolved_on, end_field="resolved_on")
        category = self.category
        if (
            category is not None
            and category.kind != ReferenceDataKind.SAFEGUARDING_CATEGORY
        ):
            raise ValidationError(
                {"category": _("Invalid safeguarding category kind.")}
            )


class OutcomeRecord(BeneficiaryRecord):
    """Outcome and result evidence for a beneficiary against an indicator."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="outcomes"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    indicator = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="outcomes",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.OUTCOME_INDICATOR},
    )
    indicator_name = models.CharField(max_length=220)
    measurement_date = models.DateField(db_index=True)
    baseline_value = models.CharField(max_length=120, blank=True)
    current_value = models.CharField(max_length=120)
    target_value = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=OutcomeStatus.choices,
        default=OutcomeStatus.PARTIAL,
        db_index=True,
    )
    evidence_summary = models.TextField(blank=True)
    evidence_document = models.FileField(
        upload_to="beneficiaries/outcomes/",
        storage=private_beneficiary_storage,
        validators=[validate_beneficiary_document],
        null=True,
        blank=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_beneficiary_outcomes",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-measurement_date",)
        indexes = [models.Index(fields=["beneficiary", "measurement_date"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.indicator_name} ({self.current_value})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.measurement_date)
        indicator = self.indicator
        if (
            indicator is not None
            and indicator.kind != ReferenceDataKind.OUTCOME_INDICATOR
        ):
            raise ValidationError({"indicator": _("Invalid outcome indicator kind.")})


class ExitRecord(BeneficiaryRecord):
    """The exit, graduation, or discontinuation record for a beneficiary."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="exit_records"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    exit_date = models.DateField(default=timezone.localdate, db_index=True)
    exit_status = models.CharField(
        max_length=20, choices=ExitStatus.choices, default=ExitStatus.GRADUATED
    )
    exit_reason = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="exit_records",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.EXIT_REASON},
    )
    reason = models.TextField()
    exit_summary = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    outcomes_achieved = models.TextField(blank=True)
    handover_notes = models.TextField(blank=True)
    re_eligibility = models.BooleanField(_("Re-eligible in future"), default=True)
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="conducted_beneficiary_exits",
        null=True,
        blank=True,
    )
    approval_reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-exit_date",)
        indexes = [models.Index(fields=["beneficiary", "exit_status"])]

    def __str__(self) -> str:
        return (
            f"{self.beneficiary} - {self.get_exit_status_display()}"
            f" ({self.reference_number})"
        )

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.exit_date)
        exit_reason = self.exit_reason
        if (
            exit_reason is not None
            and exit_reason.kind != ReferenceDataKind.EXIT_REASON
        ):
            raise ValidationError({"exit_reason": _("Invalid exit reason kind.")})


class TransferRecord(BeneficiaryRecord):
    """Transfer of a beneficiary between programs, projects, or sites."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="transfers"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    transfer_date = models.DateField(default=timezone.localdate, db_index=True)
    from_program_reference = models.CharField(max_length=180, blank=True)
    to_program_reference = models.CharField(max_length=180, blank=True)
    from_site = models.CharField(max_length=180, blank=True)
    to_site = models.CharField(max_length=180, blank=True)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING,
        db_index=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_beneficiary_transfers",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_on = models.DateField(null=True, blank=True)
    handover_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-transfer_date",)
        indexes = [models.Index(fields=["beneficiary", "status"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} transfer ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.transfer_date)
        validate_date_range(
            self.transfer_date, self.completed_on, end_field="completed_on"
        )


class BeneficiaryDocument(BeneficiaryRecord):
    """A consent-gated, version-tracked document attached to a beneficiary."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="documents"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    document_type = models.ForeignKey(
        BeneficiaryReferenceData,
        on_delete=models.PROTECT,
        related_name="documents",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.DOCUMENT_TYPE},
    )
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to="beneficiaries/documents/",
        storage=private_beneficiary_storage,
        validators=[validate_beneficiary_document],
    )
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=128, blank=True)
    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.CURRENT,
        db_index=True,
    )
    confidentiality = models.CharField(
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.CONFIDENTIAL,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="uploaded_beneficiary_documents",
        null=True,
        blank=True,
    )
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-uploaded_at",)
        indexes = [models.Index(fields=["beneficiary", "status"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.title} ({self.reference_number})"

    def save(self, *args, **kwargs) -> None:
        if self.file:
            self.file_name = self.file.name.rsplit("/", 1)[-1]
            if self.file_size is None and self.file.size is not None:
                self.file_size = self.file.size
        super().save(*args, **kwargs)

    def compute_checksum(self) -> str:
        if not self.file:
            return ""
        digest = hashlib.sha256()
        self.file.open("rb")
        for chunk in self.file.chunks():
            digest.update(chunk)
        self.file.close()
        return digest.hexdigest()


class BeneficiaryCommunication(BeneficiaryRecord):
    """Retained communication history for a beneficiary."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="communications"
    )
    channel = models.CharField(max_length=20, choices=CommunicationChannel.choices)
    direction = models.CharField(max_length=20, choices=CommunicationDirection.choices)
    subject = models.CharField(max_length=255)
    summary = models.TextField()
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    sender = models.CharField(max_length=180, blank=True)
    recipients = models.TextField(blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_beneficiary_communications",
        null=True,
        blank=True,
    )
    requires_follow_up = models.BooleanField(default=False)
    follow_up_due_date = models.DateField(null=True, blank=True, db_index=True)
    is_confidential = models.BooleanField(default=False)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [models.Index(fields=["beneficiary", "channel", "occurred_at"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - {self.subject}"


class FeedbackRecord(BeneficiaryRecord):
    """Beneficiary feedback and complaints, including safeguarding hotline use."""

    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.PROTECT, related_name="feedback_records"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    feedback_date = models.DateField(default=timezone.localdate, db_index=True)
    channel = models.CharField(
        max_length=20,
        choices=CommunicationChannel.choices,
        default=CommunicationChannel.OTHER,
    )
    feedback_type = models.CharField(max_length=80, blank=True)
    is_complaint = models.BooleanField(default=False)
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="received_beneficiary_feedback",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.RECEIVED,
        db_index=True,
    )
    response = models.TextField(blank=True)
    resolved_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-feedback_date",)
        indexes = [models.Index(fields=["beneficiary", "status"])]

    def __str__(self) -> str:
        return f"{self.beneficiary} - feedback ({self.status})"

    def clean(self) -> None:
        super().clean()
        validate_date_not_future(self.feedback_date)
        validate_date_range(
            self.feedback_date, self.resolved_on, end_field="resolved_on"
        )


class DuplicateReviewRecord(BeneficiaryRecord):
    """Review of a possible duplicate beneficiary pair."""

    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.PROTECT,
        related_name="duplicate_reviews",
    )
    duplicate_candidate = models.ForeignKey(
        Beneficiary,
        on_delete=models.PROTECT,
        related_name="as_duplicate_candidate",
    )
    match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[validate_percentage],
    )
    matching_fields = models.JSONField(default=list, blank=True)
    review_status = models.CharField(
        max_length=20,
        choices=DuplicateReviewStatus.choices,
        default=DuplicateReviewStatus.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_beneficiary_duplicates",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)
    merged_into = models.ForeignKey(
        Beneficiary,
        on_delete=models.SET_NULL,
        related_name="merged_records",
        null=True,
        blank=True,
    )
    merged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-match_score",)
        constraints = [
            models.UniqueConstraint(
                fields=["beneficiary", "duplicate_candidate"],
                name="beneficiary_duplicate_pair_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.beneficiary} ~ {self.duplicate_candidate} ({self.match_score}%)"


class BeneficiaryAuditRecord(models.Model):
    """Immutable structured audit trail for significant beneficiary events.

    This lightweight, app-local table mirrors the central audit contract until
    the Phase 8 audit module is integrated.
    """

    entity_type = models.CharField(max_length=80, db_index=True)
    entity_id = models.CharField(max_length=80, db_index=True)
    action = models.CharField(max_length=60, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="beneficiary_audit_records",
        null=True,
        blank=True,
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    from_data = models.JSONField(default=dict, blank=True)
    to_data = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Beneficiary Audit Record")
        verbose_name_plural = _("Beneficiary Audit Records")
        ordering = ("-changed_at",)
        indexes = [models.Index(fields=["entity_type", "entity_id", "changed_at"])]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}:{self.entity_id}"

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(IMMUTABLE_HISTORY_MESSAGE, code="immutable_history")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(IMMUTABLE_HISTORY_MESSAGE, code="immutable_history")
