"""Accessible, service-facing forms for beneficiary management."""

# ruff: noqa: RUF012 - Django form Meta options are declarative attributes.

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.selectors import get_active_users
from apps.locations.forms import GeographicFieldsMixin
from apps.organizations.selectors import get_active_units

from .constants import BeneficiaryStatus, ReferenceDataKind
from .models import (
    AttendanceRecord,
    Beneficiary,
    BeneficiaryAssessment,
    BeneficiaryCommunication,
    BeneficiaryDocument,
    BeneficiaryEnrollment,
    BeneficiaryGroup,
    BeneficiaryHousehold,
    BeneficiaryParticipation,
    BeneficiaryReferenceData,
    CaseNote,
    ConsentRecord,
    DuplicateReviewRecord,
    ExitRecord,
    FeedbackRecord,
    FollowUpVisit,
    GuardianRecord,
    OutcomeRecord,
    Referral,
    SafeguardingRecord,
    ServiceDeliveryRecord,
    SupportPlan,
    TransferRecord,
)
from .services import BENEFICIARY_TRANSITIONS

BENEFICIARY_FORM_FIELDS = [
    "first_name",
    "middle_name",
    "last_name",
    "date_of_birth",
    "gender",
    "marital_status",
    "nationality",
    "category",
    "classification",
    "vulnerabilities",
    "inclusion_barriers",
    "disabilities",
    "skills",
    "interests",
    "needs",
    "education_level",
    "school_name",
    "current_grade",
    "is_in_school",
    "occupation",
    "employment_status",
    "workplace",
    "phone_primary",
    "phone_secondary",
    "whatsapp_number",
    "email",
    "physical_address",
    "country",
    "province_or_region",
    "district",
    "community",
    "ward",
    "village",
    "province_location",
    "district_location",
    "constituency_location",
    "ward_location",
    "gps_coordinates",
    "national_id_number",
    "birth_certificate_number",
    "passport_number",
    "other_identifier",
    "household",
    "organization_unit",
    "primary_responsible_officer",
    "case_manager",
    "referral_source",
    "registration_date",
    "eligibility_notes",
    "notes",
]


def _model_choice(form: forms.BaseForm, name: str) -> forms.ModelChoiceField:
    """Return a model-choice field with its concrete Django type."""
    return cast(forms.ModelChoiceField, form.fields[name])


def _choice(form: forms.BaseForm, name: str) -> forms.ChoiceField:
    """Return a choice field with its concrete Django type."""
    return cast(forms.ChoiceField, form.fields[name])


class BeneficiaryFormMixin:
    """Apply Bootstrap controls and accessible error/help associations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():  # type: ignore[attr-defined]
            widget = field.widget
            if isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(
                    attrs=widget.attrs, format="%Y-%m-%dT%H:%M"
                )
                field.widget.attrs["type"] = "datetime-local"
                field.input_formats = ["%Y-%m-%dT%H:%M"]
                widget = field.widget
            elif isinstance(field, forms.DateField):
                field.widget = forms.DateInput(attrs=widget.attrs, format="%Y-%m-%d")
                field.widget.attrs["type"] = "date"
                widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select | forms.SelectMultiple):
                css_class = "form-select"
            else:
                css_class = "form-control"
            widget.attrs["class"] = " ".join(
                value for value in (widget.attrs.get("class", ""), css_class) if value
            )
            if field.help_text:
                widget.attrs["aria-describedby"] = f"id_{name}_help"

    def full_clean(self):
        super().full_clean()  # type: ignore[misc]
        for name in self.errors:  # type: ignore[attr-defined]
            field = self.fields.get(name)  # type: ignore[attr-defined]
            if field is None:
                continue
            css_classes = field.widget.attrs.get("class", "").split()
            if "is-invalid" not in css_classes:
                css_classes.append("is-invalid")
            field.widget.attrs["class"] = " ".join(css_classes)
            field.widget.attrs["aria-invalid"] = "true"


def _active_reference_data(kind: str):
    return BeneficiaryReferenceData.objects.filter(kind=kind, active=True).order_by(
        "order", "name"
    )


def _reference_choices(kind: str):
    return _active_reference_data(kind)


def _validate_date_order(
    cleaned_data: dict[str, Any],
    start_name: str,
    end_name: str,
    *,
    message: str | None = None,
) -> None:
    start = cleaned_data.get(start_name)
    end = cleaned_data.get(end_name)
    if start and end and end < start:
        raise ValidationError(
            {end_name: message or _("The end date cannot precede the start date.")}
        )


class BeneficiaryForm(BeneficiaryFormMixin, GeographicFieldsMixin, forms.ModelForm):
    """Create or update an authoritative beneficiary profile."""

    geo_fields = {
        "province": {"field": "province_location", "required": False},
        "district": {"field": "district_location", "required": False},
        "constituency": {"field": "constituency_location", "required": False},
        "ward": {"field": "ward_location", "required": False},
    }
    geo_text_fields = {
        "province": "province_or_region",
        "district": "district",
        "ward": "community",
    }

    class Meta:
        model = Beneficiary
        fields = BENEFICIARY_FORM_FIELDS
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in (
                "physical_address",
                "eligibility_notes",
                "notes",
            )
        }

    REFERENCE_FIELDS = {
        "gender": ReferenceDataKind.GENDER,
        "marital_status": ReferenceDataKind.MARITAL_STATUS,
        "category": ReferenceDataKind.CATEGORY,
        "classification": ReferenceDataKind.CLASSIFICATION,
        "vulnerabilities": ReferenceDataKind.VULNERABILITY,
        "inclusion_barriers": ReferenceDataKind.INCLUSION,
        "disabilities": ReferenceDataKind.DISABILITY,
        "skills": ReferenceDataKind.SKILL,
        "interests": ReferenceDataKind.INTEREST,
        "needs": ReferenceDataKind.NEED_TYPE,
        "education_level": ReferenceDataKind.EDUCATION_LEVEL,
        "occupation": ReferenceDataKind.OCCUPATION,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_users = get_active_users().order_by("first_name", "last_name", "email")
        for field_name, kind in self.REFERENCE_FIELDS.items():
            _model_choice(self, field_name).queryset = _reference_choices(kind)
        _model_choice(self, "primary_responsible_officer").queryset = active_users
        _model_choice(self, "case_manager").queryset = active_users
        _model_choice(self, "organization_unit").queryset = get_active_units().order_by(
            "name"
        )
        _model_choice(self, "household").queryset = BeneficiaryHousehold.objects.filter(
            status__in=("PROSPECTIVE", "ACTIVE")
        ).order_by("household_name")

    def clean(self):
        cleaned_data = super().clean() or {}
        if not any(
            cleaned_data.get(name)
            for name in ("email", "phone_primary", "phone_secondary")
        ):
            raise ValidationError(_("Provide an email address or phone number."))
        return cleaned_data


class BeneficiaryUpdateForm(BeneficiaryForm):
    """Update form that also allows consent bookkeeping fields."""

    class Meta(BeneficiaryForm.Meta):
        fields = [
            *BENEFICIARY_FORM_FIELDS,
            "consent_status",
            "consent_expiry_date",
            "consent_version",
            "assent_recorded",
        ]


class BeneficiaryArchiveForm(BeneficiaryFormMixin, forms.Form):
    reason = forms.CharField(
        label=_("Reason"),
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("The reason is preserved in status history."),
    )


class BeneficiaryStatusTransitionForm(BeneficiaryFormMixin, forms.Form):
    new_status = forms.ChoiceField(label=_("New status"))
    reason = forms.CharField(
        label=_("Reason"),
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("This reason is retained in the status history."),
    )

    def __init__(self, *args, beneficiary: Beneficiary, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = BENEFICIARY_TRANSITIONS.get(beneficiary.status, set())
        _choice(self, "new_status").choices = [
            (value, label)
            for value, label in BeneficiaryStatus.choices
            if value in allowed
        ]


class GuardianForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = GuardianRecord
        fields = [
            "full_name",
            "relationship",
            "relationship_other",
            "phone_primary",
            "phone_secondary",
            "email",
            "national_id_number",
            "physical_address",
            "is_primary",
            "is_active",
            "consent_recorded",
            "consent_recorded_at",
            "valid_from",
            "valid_to",
            "notes",
        ]
        widgets = {
            "physical_address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "valid_from", "valid_to")
        if not any(
            cleaned_data.get(name)
            for name in ("email", "phone_primary", "phone_secondary")
        ):
            raise ValidationError(_("A guardian requires contact details."))
        return cleaned_data


class HouseholdForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = BeneficiaryHousehold
        fields = [
            "household_name",
            "household_type",
            "physical_address",
            "country",
            "province_or_region",
            "district",
            "community",
            "village",
            "number_of_dependents",
            "primary_income_source",
            "monthly_income",
            "currency",
            "formed_on",
            "status",
            "notes",
        ]
        widgets = {
            "physical_address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "household_type").queryset = _reference_choices(
            ReferenceDataKind.HOUSEHOLD_TYPE
        )


class HouseholdMemberForm(BeneficiaryFormMixin, forms.Form):
    beneficiary = forms.ModelChoiceField(
        queryset=Beneficiary.objects.none(), label=_("Beneficiary")
    )
    relationship_to_head: forms.ModelChoiceField = forms.ModelChoiceField(
        queryset=_reference_choices(ReferenceDataKind.RELATIONSHIP),
        required=False,
        label=_("Relationship to head"),
    )
    is_head = forms.BooleanField(required=False, label=_("Household head"))

    def __init__(self, *args, beneficiaries=None, **kwargs):
        super().__init__(*args, **kwargs)
        if beneficiaries is not None:
            _model_choice(self, "beneficiary").queryset = beneficiaries


class GroupForm(BeneficiaryFormMixin, GeographicFieldsMixin, forms.ModelForm):
    geo_fields = {
        "province": {"field": "province_location", "required": False},
        "district": {"field": "district_location", "required": False},
        "ward": {"field": "ward_location", "required": False},
    }
    geo_text_fields = {
        "province": "province_or_region",
        "district": "district",
        "ward": "community",
    }

    class Meta:
        model = BeneficiaryGroup
        fields = [
            "group_name",
            "group_type",
            "description",
            "objectives",
            "formation_date",
            "province_or_region",
            "district",
            "community",
            "province_location",
            "district_location",
            "ward_location",
            "meeting_schedule",
            "group_leader",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "objectives": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, beneficiaries=None, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "group_type").queryset = _reference_choices(
            ReferenceDataKind.GROUP_TYPE
        )
        if beneficiaries is not None:
            _model_choice(self, "group_leader").queryset = beneficiaries


class GroupMemberForm(BeneficiaryFormMixin, forms.Form):
    beneficiary = forms.ModelChoiceField(
        queryset=Beneficiary.objects.none(), label=_("Beneficiary")
    )
    role = forms.CharField(max_length=120, required=False, label=_("Role"))

    def __init__(self, *args, beneficiaries=None, **kwargs):
        super().__init__(*args, **kwargs)
        if beneficiaries is not None:
            _model_choice(self, "beneficiary").queryset = beneficiaries


class EnrollmentForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = BeneficiaryEnrollment
        fields = [
            "enrollment_type",
            "program_reference",
            "project_reference",
            "activity_title",
            "description",
            "source",
            "enrollment_date",
            "objectives",
            "needs_addressed",
            "expected_outcome_date",
            "responsible_officer",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "objectives": forms.Textarea(attrs={"rows": 3}),
            "needs_addressed": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "enrollment_type").queryset = _reference_choices(
            ReferenceDataKind.ENROLLMENT_TYPE
        )
        _model_choice(self, "source").queryset = _reference_choices(
            ReferenceDataKind.ENROLLMENT_SOURCE
        )
        _model_choice(self, "responsible_officer").queryset = (
            get_active_users().order_by("first_name", "last_name", "email")
        )


class EnrollmentStatusForm(BeneficiaryFormMixin, forms.Form):
    status = forms.ChoiceField(
        choices=list(BeneficiaryEnrollment._meta.get_field("status").choices or []),
        label=_("Enrollment status"),
    )
    reason = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class ParticipationForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = BeneficiaryParticipation
        fields = [
            "enrollment",
            "activity_title",
            "description",
            "activity_date",
            "duration_hours",
            "location",
            "facilitator",
            "status",
            "services_received",
            "outcomes_observed",
            "feedback",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "services_received": forms.Textarea(attrs={"rows": 3}),
            "outcomes_observed": forms.Textarea(attrs={"rows": 3}),
            "feedback": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, beneficiary: Beneficiary, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "enrollment").queryset = beneficiary.enrollments.all()


class AttendanceForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = [
            "participation",
            "session_title",
            "session_date",
            "check_in_time",
            "status",
            "reason",
            "notes",
        ]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, beneficiary: Beneficiary, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "participation").queryset = beneficiary.participations.all()


class ServiceDeliveryForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = ServiceDeliveryRecord
        fields = [
            "service_type",
            "service_name",
            "description",
            "service_date",
            "quantity",
            "unit",
            "provider",
            "provider_reference",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "service_type").queryset = _reference_choices(
            ReferenceDataKind.SERVICE_TYPE
        )


class ServiceDeliveryCompleteForm(BeneficiaryFormMixin, forms.Form):
    outcome_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 4})
    )


class ReferralForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = Referral
        fields = [
            "referral_type",
            "referral_date",
            "referred_from",
            "referred_to",
            "reason",
            "priority",
            "expected_response_date",
            "follow_up_owner",
            "notes",
        ]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "referral_type").queryset = _reference_choices(
            ReferenceDataKind.REFERRAL_TYPE
        )
        _model_choice(self, "follow_up_owner").queryset = get_active_users().order_by(
            "first_name", "last_name", "email"
        )


class ReferralStatusForm(BeneficiaryFormMixin, forms.Form):
    status = forms.ChoiceField(
        choices=list(Referral._meta.get_field("status").choices or []),
        label=_("Referral status"),
    )
    response_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )


class CaseNoteForm(BeneficiaryFormMixin, forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}))

    class Meta:
        model = CaseNote
        fields = ["note_type", "title", "content", "occurred_on", "is_confidential"]

    def __init__(self, *args, beneficiary: Beneficiary, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "note_type").queryset = _reference_choices(
            ReferenceDataKind.CASE_NOTE_TYPE
        )


class FollowUpForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = FollowUpVisit
        fields = ["purpose", "scheduled_on", "method", "assigned_to"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "purpose").queryset = _reference_choices(
            ReferenceDataKind.FOLLOW_UP_PURPOSE
        )
        _model_choice(self, "assigned_to").queryset = get_active_users().order_by(
            "first_name", "last_name", "email"
        )


class FollowUpCompleteForm(BeneficiaryFormMixin, forms.Form):
    summary = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    findings = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    action_items = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    next_follow_up_date = forms.DateField(required=False)


class AssessmentForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = BeneficiaryAssessment
        fields = [
            "assessment_type",
            "assessment_date",
            "scores",
            "summary",
            "strengths",
            "challenges",
            "priority_needs",
            "recommendation",
            "next_review_date",
            "notes",
        ]
        widgets = {
            "scores": forms.Textarea(attrs={"rows": 3}),
            "summary": forms.Textarea(attrs={"rows": 3}),
            "strengths": forms.Textarea(attrs={"rows": 3}),
            "challenges": forms.Textarea(attrs={"rows": 3}),
            "priority_needs": forms.Textarea(attrs={"rows": 3}),
            "recommendation": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "scores": _(
                "Enter a JSON object of named dimensions, scores, and rationale."
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "assessment_type").queryset = _reference_choices(
            ReferenceDataKind.ASSESSMENT_TYPE
        )


class SupportPlanForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = SupportPlan
        fields = [
            "title",
            "assessment",
            "start_date",
            "end_date",
            "goals",
            "objectives",
            "interventions",
            "support_coordinator",
            "next_review_date",
            "notes",
        ]
        widgets = {
            "goals": forms.Textarea(attrs={"rows": 3}),
            "objectives": forms.Textarea(attrs={"rows": 3}),
            "interventions": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, beneficiary: Beneficiary, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "assessment").queryset = beneficiary.assessments.all()
        _model_choice(self, "support_coordinator").queryset = (
            get_active_users().order_by("first_name", "last_name", "email")
        )


class ConsentForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = ConsentRecord
        fields = [
            "consent_type",
            "is_assent",
            "provided_by",
            "relationship",
            "recorded_on",
            "valid_from",
            "valid_to",
            "form_version",
            "details",
            "witness_name",
            "document",
        ]
        widgets = {
            "details": forms.Textarea(attrs={"rows": 3}),
        }


class ConsentWithdrawForm(BeneficiaryFormMixin, forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))


class SafeguardingForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = SafeguardingRecord
        fields = [
            "category",
            "reported_on",
            "reported_by",
            "reporter_role",
            "confidentiality",
            "description",
            "immediate_action",
            "risk_level",
            "actions_taken",
            "external_reference",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "immediate_action": forms.Textarea(attrs={"rows": 3}),
            "actions_taken": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "category").queryset = _reference_choices(
            ReferenceDataKind.SAFEGUARDING_CATEGORY
        )


class SafeguardingStatusForm(BeneficiaryFormMixin, forms.Form):
    status = forms.ChoiceField(
        choices=list(SafeguardingRecord._meta.get_field("status").choices or []),
        label=_("Safeguarding status"),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class OutcomeForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = OutcomeRecord
        fields = [
            "indicator",
            "indicator_name",
            "measurement_date",
            "baseline_value",
            "current_value",
            "target_value",
            "status",
            "evidence_summary",
            "evidence_document",
            "notes",
        ]
        widgets = {
            "evidence_summary": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "indicator").queryset = _reference_choices(
            ReferenceDataKind.OUTCOME_INDICATOR
        )


class ExitForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = ExitRecord
        fields = [
            "exit_date",
            "exit_status",
            "exit_reason",
            "reason",
            "exit_summary",
            "achievements",
            "outcomes_achieved",
            "handover_notes",
            "re_eligibility",
            "approval_reference",
            "notes",
        ]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 3}),
            "exit_summary": forms.Textarea(attrs={"rows": 3}),
            "achievements": forms.Textarea(attrs={"rows": 3}),
            "outcomes_achieved": forms.Textarea(attrs={"rows": 3}),
            "handover_notes": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "exit_reason").queryset = _reference_choices(
            ReferenceDataKind.EXIT_REASON
        )


class TransferForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = TransferRecord
        fields = [
            "transfer_date",
            "from_program_reference",
            "to_program_reference",
            "from_site",
            "to_site",
            "reason",
            "notes",
        ]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class TransferCompleteForm(BeneficiaryFormMixin, forms.Form):
    handover_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 4})
    )


class DocumentForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = BeneficiaryDocument
        fields = ["document_type", "title", "description", "file", "confidentiality"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "document_type").queryset = _reference_choices(
            ReferenceDataKind.DOCUMENT_TYPE
        )


class CommunicationForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = BeneficiaryCommunication
        fields = [
            "channel",
            "direction",
            "subject",
            "summary",
            "occurred_at",
            "sender",
            "recipients",
            "requires_follow_up",
            "follow_up_due_date",
            "is_confidential",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "recipients": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean() or {}
        if cleaned_data.get("requires_follow_up") and not cleaned_data.get(
            "follow_up_due_date"
        ):
            self.add_error("follow_up_due_date", _("A follow-up date is required."))
        return cleaned_data


class FeedbackForm(BeneficiaryFormMixin, forms.ModelForm):
    class Meta:
        model = FeedbackRecord
        fields = [
            "feedback_date",
            "channel",
            "feedback_type",
            "is_complaint",
            "content",
            "is_anonymous",
            "notes",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class FeedbackResponseForm(BeneficiaryFormMixin, forms.Form):
    response = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
    close = forms.BooleanField(
        required=False,
        label=_("Close this feedback"),
        help_text=_("Closing records today's resolution date."),
    )


class DuplicateReviewForm(BeneficiaryFormMixin, forms.Form):
    candidate = forms.ModelChoiceField(
        queryset=Beneficiary.objects.none(), label=_("Duplicate candidate")
    )
    review_status = forms.ChoiceField(
        choices=list(
            DuplicateReviewRecord._meta.get_field("review_status").choices or []
        ),
        label=_("Review status"),
    )
    match_score = forms.DecimalField(
        initial=Decimal("0.00"),
        min_value=Decimal("0"),
        max_value=Decimal("100"),
        decimal_places=2,
        label=_("Match score (%)"),
    )
    matching_fields = forms.CharField(
        required=False,
        label=_("Matching fields"),
        help_text=_("Comma-separated field names that matched."),
    )
    decision_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, candidates=None, **kwargs):
        super().__init__(*args, **kwargs)
        if candidates is not None:
            _model_choice(self, "candidate").queryset = candidates

    def clean_matching_fields(self):
        value = self.cleaned_data["matching_fields"]
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]


class EmptyConfirmationForm(BeneficiaryFormMixin, forms.Form):
    confirm = forms.BooleanField(
        label=_("I confirm this action"),
        help_text=_("This workflow action is recorded with your user account."),
    )
