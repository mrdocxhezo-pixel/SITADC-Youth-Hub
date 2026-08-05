"""Accessible, service-facing forms for stakeholder management."""

# ruff: noqa: RUF012 - Django form Meta options are declarative attributes.

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.selectors import get_active_users
from apps.leadership.models import LeadershipProfile
from apps.organizations.selectors import get_active_units

from .constants import (
    ActionStatus,
    AgreementStatus,
    CommitmentStatus,
    ContributionStatus,
    DueDiligenceStatus,
    ReferenceDataKind,
    RenewalStatus,
    StakeholderStatus,
)
from .models import (
    Stakeholder,
    StakeholderActionItem,
    StakeholderAgreement,
    StakeholderAssessment,
    StakeholderCommitment,
    StakeholderCommunication,
    StakeholderConflictOfInterest,
    StakeholderContact,
    StakeholderContribution,
    StakeholderDocument,
    StakeholderDueDiligence,
    StakeholderEngagement,
    StakeholderEngagementPlan,
    StakeholderNote,
    StakeholderPerformanceDimension,
    StakeholderReferenceData,
    StakeholderRisk,
)
from .services import AGREEMENT_TRANSITIONS, STAKEHOLDER_TRANSITIONS

ASSESSMENT_SCORE_FIELDS = (
    "influence_score",
    "interest_score",
    "power_score",
    "impact_score",
    "strategic_importance_score",
    "strategic_relevance_score",
    "relationship_potential_score",
    "resource_capacity_score",
    "technical_capacity_score",
    "geographic_relevance_score",
    "reputation_score",
    "compliance_score",
    "safeguarding_readiness_score",
    "financial_risk_score",
    "operational_risk_score",
)


def _model_choice(form: forms.BaseForm, name: str) -> forms.ModelChoiceField:
    """Return a model-choice field with its concrete Django type."""
    return cast(forms.ModelChoiceField, form.fields[name])


def _choice(form: forms.BaseForm, name: str) -> forms.ChoiceField:
    """Return a choice field with its concrete Django type."""
    return cast(forms.ChoiceField, form.fields[name])


class StakeholderFormMixin:
    """Apply Bootstrap controls and accessible error/help associations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():  # type: ignore[attr-defined]
            widget = field.widget
            if isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(
                    attrs=widget.attrs,
                    format="%Y-%m-%dT%H:%M",
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
    return StakeholderReferenceData.objects.filter(kind=kind, active=True).order_by(
        "order", "name"
    )


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


class StakeholderForm(StakeholderFormMixin, forms.ModelForm):
    """Create or update an authoritative stakeholder profile."""

    class Meta:
        model = Stakeholder
        fields = [
            "entity_type",
            "legal_name",
            "trading_name",
            "display_name",
            "acronym",
            "former_names",
            "logo",
            "description",
            "vision",
            "mission",
            "core_objectives",
            "areas_of_expertise",
            "primary_areas_of_work",
            "areas_of_interest",
            "potential_collaboration_areas",
            "categories",
            "relationship_type",
            "classification",
            "ownership_type",
            "priority",
            "relationship_level",
            "sectors",
            "focus_areas",
            "sdgs",
            "registration_number",
            "registration_authority",
            "date_established",
            "country_of_registration",
            "physical_address",
            "postal_address",
            "country",
            "province_or_region",
            "district",
            "community",
            "geographic_coverage",
            "gps_coordinates",
            "website",
            "general_email",
            "general_phone",
            "alternative_phone",
            "identification_source",
            "referred_by",
            "program_references",
            "project_references",
            "responsibilities",
            "relationship_start_date",
            "relationship_end_date",
            "next_engagement_date",
            "key_achievements",
            "relationship_challenges",
            "organization_unit",
            "responsible_directorate",
            "primary_responsible_officer",
            "responsible_leadership",
            "confidentiality",
            "consent_recorded",
            "retention_until",
            "specialization_data",
        ]
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in (
                "former_names",
                "description",
                "vision",
                "mission",
                "core_objectives",
                "areas_of_expertise",
                "primary_areas_of_work",
                "areas_of_interest",
                "potential_collaboration_areas",
                "physical_address",
                "postal_address",
                "geographic_coverage",
                "program_references",
                "project_references",
                "responsibilities",
                "key_achievements",
                "relationship_challenges",
                "specialization_data",
            )
        }

    REFERENCE_FIELDS = {
        "categories": ReferenceDataKind.CATEGORY,
        "relationship_type": ReferenceDataKind.TYPE,
        "classification": ReferenceDataKind.CLASSIFICATION,
        "ownership_type": ReferenceDataKind.OWNERSHIP_TYPE,
        "priority": ReferenceDataKind.PRIORITY,
        "relationship_level": ReferenceDataKind.RELATIONSHIP_LEVEL,
        "sectors": ReferenceDataKind.SECTOR,
        "focus_areas": ReferenceDataKind.FOCUS_AREA,
        "sdgs": ReferenceDataKind.SDG,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, kind in self.REFERENCE_FIELDS.items():
            _model_choice(self, field_name).queryset = _active_reference_data(kind)
        _model_choice(self, "primary_responsible_officer").queryset = (
            get_active_users().order_by("first_name", "last_name", "email")
        )
        active_units = get_active_units().order_by("name")
        _model_choice(self, "organization_unit").queryset = active_units
        _model_choice(self, "responsible_directorate").queryset = active_units
        _model_choice(self, "responsible_leadership").queryset = (
            LeadershipProfile.objects.active().select_related("user")
        )

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(
            cleaned_data, "relationship_start_date", "relationship_end_date"
        )
        established = cleaned_data.get("date_established")
        if established and established > timezone.localdate():
            self.add_error(
                "date_established", _("Date established cannot be in the future.")
            )
        return cleaned_data


class StakeholderArchiveForm(StakeholderFormMixin, forms.Form):
    reason = forms.CharField(
        label=_("Reason"),
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("The reason is preserved in status history."),
    )


class StakeholderStatusTransitionForm(StakeholderFormMixin, forms.Form):
    new_status = forms.ChoiceField(label=_("New status"))
    reason = forms.CharField(
        label=_("Reason"),
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("This reason is retained in the status history."),
    )

    def __init__(self, *args, stakeholder: Stakeholder, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = STAKEHOLDER_TRANSITIONS.get(stakeholder.status, set())
        _choice(self, "new_status").choices = [
            (value, label)
            for value, label in StakeholderStatus.choices
            if value in allowed
        ]


class StakeholderContactForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderContact
        fields = [
            "full_name",
            "title",
            "designation",
            "department",
            "email",
            "phone_primary",
            "phone_secondary",
            "whatsapp_number",
            "preferred_communication",
            "availability",
            "is_primary",
            "is_decision_maker",
            "is_technical_contact",
            "is_finance_contact",
            "is_safeguarding_contact",
            "is_active",
            "valid_from",
            "valid_to",
            "consent_recorded",
            "communication_consent",
            "private_notes",
        ]
        widgets = {"private_notes": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "valid_from", "valid_to")
        if not any(
            cleaned_data.get(name)
            for name in ("email", "phone_primary", "phone_secondary")
        ):
            raise ValidationError(_("Provide an email address or phone number."))
        if cleaned_data.get("is_primary") and not cleaned_data.get("is_active"):
            self.add_error("is_primary", _("A primary contact must be active."))
        return cleaned_data


class StakeholderAssessmentForm(StakeholderFormMixin, forms.ModelForm):
    SCORE_FIELDS = ASSESSMENT_SCORE_FIELDS

    class Meta:
        model = StakeholderAssessment
        fields = [
            "assessment_date",
            *ASSESSMENT_SCORE_FIELDS,
            "evidence_summary",
            "recommendation",
            "review_date",
            "assessment_status",
            "approval_status",
        ]
        widgets = {
            "evidence_summary": forms.Textarea(attrs={"rows": 3}),
            "recommendation": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.SCORE_FIELDS:
            self.fields[name].help_text = _("Optional score from 1 to 5.")
            self.fields[name].widget.attrs.update({"min": 1, "max": 5})
        self.fields["influence_score"].help_text = _(
            "Optional score from 1 to 5; used with interest for matrix placement."
        )
        self.fields["interest_score"].help_text = _(
            "Optional score from 1 to 5; used with influence for matrix placement."
        )

    def clean_assessment_date(self):
        value = self.cleaned_data["assessment_date"]
        if value > timezone.localdate():
            raise ValidationError(_("Assessment date cannot be in the future."))
        return value


class StakeholderEngagementPlanForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderEngagementPlan
        fields = [
            "title",
            "purpose",
            "objectives",
            "strategy",
            "communication_method",
            "key_messages",
            "risks",
            "engagement_level",
            "responsible_officer",
            "planned_activities",
            "communication_frequency",
            "expected_outcomes",
            "success_indicators",
            "escalation_procedure",
            "start_date",
            "end_date",
            "next_review_date",
            "status",
        ]
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in (
                "purpose",
                "objectives",
                "strategy",
                "key_messages",
                "risks",
                "planned_activities",
                "expected_outcomes",
                "success_indicators",
                "escalation_procedure",
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "engagement_level").queryset = _active_reference_data(
            ReferenceDataKind.ENGAGEMENT_LEVEL
        )
        _model_choice(self, "responsible_officer").queryset = (
            get_active_users().order_by("first_name", "last_name", "email")
        )

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "start_date", "end_date")
        return cleaned_data


class StakeholderEngagementForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderEngagement
        fields = [
            "plan",
            "engagement_type",
            "title",
            "scheduled_at",
            "venue_or_link",
            "purpose",
            "responsible_officer",
            "internal_participants",
            "external_participants",
            "agenda",
            "follow_up_date",
            "is_confidential",
        ]
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in (
                "purpose",
                "internal_participants",
                "external_participants",
                "agenda",
            )
        }

    def __init__(self, *args, stakeholder: Stakeholder, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "plan").queryset = stakeholder.engagement_plans.all()
        _model_choice(self, "responsible_officer").queryset = (
            get_active_users().order_by("first_name", "last_name", "email")
        )


class EngagementCompletionForm(StakeholderFormMixin, forms.Form):
    minutes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    decisions = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    outcomes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    follow_up_date = forms.DateField(required=False)


class StakeholderCommunicationForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderCommunication
        fields = [
            "contact",
            "engagement",
            "channel",
            "direction",
            "subject",
            "summary",
            "occurred_at",
            "sender",
            "recipients",
            "outcome",
            "responsible_officer",
            "attachment",
            "requires_follow_up",
            "follow_up_due_date",
            "is_confidential",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "recipients": forms.Textarea(attrs={"rows": 2}),
            "outcome": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(
        self,
        *args,
        stakeholder: Stakeholder,
        can_view_private_contacts: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        _model_choice(self, "contact").queryset = (
            stakeholder.contacts.filter(is_active=True)
            if can_view_private_contacts
            else StakeholderContact.objects.none()
        )
        _model_choice(self, "engagement").queryset = stakeholder.engagements.all()
        _model_choice(self, "responsible_officer").queryset = (
            get_active_users().order_by("first_name", "last_name", "email")
        )

    def clean(self):
        cleaned_data = super().clean() or {}
        if cleaned_data.get("requires_follow_up") and not cleaned_data.get(
            "follow_up_due_date"
        ):
            self.add_error("follow_up_due_date", _("A follow-up date is required."))
        return cleaned_data


class StakeholderCommitmentForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderCommitment
        fields = [
            "title",
            "commitment_type",
            "description",
            "responsible_party",
            "responsible_officer",
            "due_date",
            "commitment_date",
            "status",
            "progress_percentage",
            "progress_notes",
            "expected_value",
            "actual_value",
            "currency",
            "in_kind_details",
            "follow_up_owner",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "progress_notes": forms.Textarea(attrs={"rows": 3}),
            "in_kind_details": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_users = get_active_users().order_by("first_name", "last_name", "email")
        _model_choice(self, "responsible_officer").queryset = active_users
        _model_choice(self, "follow_up_owner").queryset = active_users
        _choice(self, "status").choices = [
            choice
            for choice in CommitmentStatus.choices
            if choice[0] != CommitmentStatus.COMPLETED
        ]


class CommitmentProgressForm(StakeholderFormMixin, forms.Form):
    progress_percentage = forms.DecimalField(
        min_value=Decimal("0"), max_value=Decimal("100"), decimal_places=2
    )
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    complete = forms.BooleanField(
        required=False,
        label=_("Mark completed"),
        help_text=_("Completion records today's date."),
    )


class StakeholderContributionForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderContribution
        fields = [
            "contribution_type",
            "description",
            "contribution_date",
            "amount",
            "estimated_value",
            "currency",
            "quantity",
            "unit",
            "program_reference",
            "project_reference",
            "status",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "contribution_type").queryset = _active_reference_data(
            ReferenceDataKind.CONTRIBUTION_TYPE
        )
        _choice(self, "status").choices = [
            choice
            for choice in ContributionStatus.choices
            if choice[0] != ContributionStatus.VERIFIED
        ]

    def clean(self):
        cleaned_data = super().clean() or {}
        if not any(
            cleaned_data.get(name) is not None
            for name in ("amount", "estimated_value", "quantity")
        ):
            raise ValidationError(_("Record an amount, estimated value, or quantity."))
        return cleaned_data


class StakeholderAgreementForm(StakeholderFormMixin, forms.ModelForm):
    file = forms.FileField(
        required=False,
        label=_("Agreement file"),
        help_text=_("Optional first version of the agreement."),
    )
    change_summary = forms.CharField(
        required=False,
        initial=_("Initial agreement version."),
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    class Meta:
        model = StakeholderAgreement
        fields = [
            "agreement_type",
            "title",
            "purpose",
            "description",
            "responsibilities",
            "deliverables",
            "obligations",
            "reporting_requirements",
            "confidentiality_terms",
            "termination_terms",
            "program_references",
            "project_references",
            "effective_date",
            "expiry_date",
            "notice_period_days",
            "signing_date",
            "renewal_date",
            "sitadc_signatory",
            "stakeholder_signatory",
            "financial_value",
            "in_kind_value",
            "currency",
            "relationship_owner",
        ]
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in (
                "purpose",
                "description",
                "responsibilities",
                "deliverables",
                "obligations",
                "reporting_requirements",
                "confidentiality_terms",
                "termination_terms",
                "program_references",
                "project_references",
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "agreement_type").queryset = _active_reference_data(
            ReferenceDataKind.AGREEMENT_TYPE
        )
        _model_choice(self, "relationship_owner").queryset = (
            get_active_users().order_by("first_name", "last_name", "email")
        )

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "effective_date", "expiry_date")
        return cleaned_data


class AgreementTransitionForm(StakeholderFormMixin, forms.Form):
    new_status = forms.ChoiceField(label=_("New agreement status"))
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Required when terminating an agreement."),
    )

    def __init__(self, *args, agreement: StakeholderAgreement, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = AGREEMENT_TRANSITIONS.get(agreement.status, set())
        _choice(self, "new_status").choices = [
            (value, label)
            for value, label in AgreementStatus.choices
            if value in allowed
        ]

    def clean(self):
        cleaned_data = super().clean() or {}
        if (
            cleaned_data.get("new_status") == AgreementStatus.TERMINATED
            and not str(cleaned_data.get("reason", "")).strip()
        ):
            self.add_error("reason", _("A termination reason is required."))
        return cleaned_data


class AgreementVersionForm(StakeholderFormMixin, forms.Form):
    title = forms.CharField(max_length=255)
    purpose = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    responsibilities = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    deliverables = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    effective_date = forms.DateField(required=False)
    expiry_date = forms.DateField(required=False)
    program_references = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2})
    )
    project_references = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2})
    )
    file = forms.FileField(required=False)
    change_summary = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, agreement: StakeholderAgreement, **kwargs):
        kwargs.setdefault(
            "initial",
            {
                "title": agreement.title,
                "purpose": agreement.purpose,
                "responsibilities": agreement.responsibilities,
                "deliverables": agreement.deliverables,
                "effective_date": agreement.effective_date,
                "expiry_date": agreement.expiry_date,
                "program_references": agreement.program_references,
                "project_references": agreement.project_references,
            },
        )
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "effective_date", "expiry_date")
        return cleaned_data


class AgreementRenewalRequestForm(StakeholderFormMixin, forms.Form):
    proposed_effective_date = forms.DateField()
    proposed_expiry_date = forms.DateField(required=False)
    rationale = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(
            cleaned_data, "proposed_effective_date", "proposed_expiry_date"
        )
        return cleaned_data


class AgreementRenewalDecisionForm(StakeholderFormMixin, forms.Form):
    decision = forms.ChoiceField(
        choices=(("approve", _("Approve")), ("reject", _("Reject")))
    )
    decision_notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))


class StakeholderDueDiligenceForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderDueDiligence
        fields = [
            "review_date",
            "expiry_date",
            "status",
            "checks",
            "missing_information",
            "findings",
            "conditions",
            "recommendation",
        ]
        widgets = {
            "checks": forms.Textarea(attrs={"rows": 5}),
            "missing_information": forms.Textarea(attrs={"rows": 3}),
            "findings": forms.Textarea(attrs={"rows": 3}),
            "conditions": forms.Textarea(attrs={"rows": 3}),
            "recommendation": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "checks": _("Enter a JSON object of named checks, results, and evidence."),
            "missing_information": _("Enter a JSON list of missing information."),
        }

    def __init__(self, *args, reviewer=None, **kwargs):
        self.reviewer = reviewer
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "review_date", "expiry_date")
        if self.reviewer and cleaned_data.get("status") in {
            DueDiligenceStatus.PASSED,
            DueDiligenceStatus.CONDITIONAL,
            DueDiligenceStatus.FAILED,
        }:
            self.instance.reviewed_by = self.reviewer
            self.instance.completed_at = timezone.now()
        return cleaned_data


class StakeholderConflictForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderConflictOfInterest
        fields = ["nature", "affected_decisions", "mitigation", "status"]
        widgets = {
            "nature": forms.Textarea(attrs={"rows": 3}),
            "affected_decisions": forms.Textarea(attrs={"rows": 3}),
            "mitigation": forms.Textarea(attrs={"rows": 3}),
        }


class StakeholderRiskForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderRisk
        fields = [
            "category",
            "title",
            "description",
            "likelihood",
            "impact",
            "mitigation_strategy",
            "responsible_officer",
            "next_review_date",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "mitigation_strategy": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "category").queryset = _active_reference_data(
            ReferenceDataKind.RISK_CATEGORY
        )
        _model_choice(self, "responsible_officer").queryset = (
            get_active_users().order_by("first_name", "last_name", "email")
        )


class StakeholderPerformanceForm(StakeholderFormMixin, forms.Form):
    review_period = forms.CharField(
        max_length=80,
        help_text=_("Use a clear unique period, for example 2026 Q3."),
    )
    review_date = forms.DateField(initial=timezone.localdate)
    strengths = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    improvement_areas = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    recommendations = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dimensions = list(
            StakeholderPerformanceDimension.objects.filter(active=True).order_by(
                "order", "name"
            )
        )
        for dimension in self.dimensions:
            self.fields[f"score_{dimension.pk}"] = forms.DecimalField(
                required=False,
                min_value=dimension.minimum_score,
                max_value=dimension.maximum_score,
                decimal_places=2,
                label=_("%(name)s (weight %(weight)s)")
                % {"name": dimension.name, "weight": dimension.weight},
                help_text=_("Allowed range: %(minimum)s to %(maximum)s.")
                % {
                    "minimum": dimension.minimum_score,
                    "maximum": dimension.maximum_score,
                },
            )
        self._apply_dynamic_bootstrap()

    def _apply_dynamic_bootstrap(self):
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"
            if field.help_text:
                widget.attrs["aria-describedby"] = f"id_{name}_help"

    def clean_review_date(self):
        value = self.cleaned_data["review_date"]
        if value > timezone.localdate():
            raise ValidationError(_("Review date cannot be in the future."))
        return value

    def clean(self):
        cleaned_data = super().clean() or {}
        if self.dimensions and not any(
            cleaned_data.get(f"score_{dimension.pk}") is not None
            for dimension in self.dimensions
        ):
            raise ValidationError(_("Provide at least one performance score."))
        return cleaned_data

    @property
    def scores(self) -> dict[str, Decimal]:
        return {
            str(dimension.pk): self.cleaned_data[f"score_{dimension.pk}"]
            for dimension in self.dimensions
            if self.cleaned_data.get(f"score_{dimension.pk}") is not None
        }


class StakeholderActionForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderActionItem
        fields = [
            "engagement",
            "commitment",
            "agreement",
            "title",
            "description",
            "assigned_to",
            "due_date",
            "priority",
            "status",
            "progress_notes",
            "assigned_date",
            "evidence_reference",
            "escalation_status",
            "comments",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "progress_notes": forms.Textarea(attrs={"rows": 3}),
            "comments": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, stakeholder: Stakeholder, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "engagement").queryset = stakeholder.engagements.all()
        _model_choice(self, "commitment").queryset = stakeholder.commitments.all()
        _model_choice(self, "agreement").queryset = stakeholder.agreements.all()
        _model_choice(self, "assigned_to").queryset = get_active_users().order_by(
            "first_name", "last_name", "email"
        )
        _choice(self, "status").choices = [
            choice
            for choice in ActionStatus.choices
            if choice[0] != ActionStatus.COMPLETED
        ]


class ActionStatusForm(StakeholderFormMixin, forms.Form):
    status = forms.ChoiceField(choices=ActionStatus.choices)
    progress_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )


class StakeholderNoteForm(StakeholderFormMixin, forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}))

    class Meta:
        model = StakeholderNote
        fields = ["title", "category", "owner", "confidentiality"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "owner").queryset = get_active_users().order_by(
            "first_name", "last_name", "email"
        )


class NoteVersionForm(StakeholderFormMixin, forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={"rows": 7}))
    change_summary = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2})
    )


class StakeholderDocumentForm(StakeholderFormMixin, forms.ModelForm):
    class Meta:
        model = StakeholderDocument
        fields = [
            "document_key",
            "title",
            "document_type",
            "file",
            "status",
            "confidentiality",
            "is_protected",
            "effective_date",
            "expiry_date",
            "retention_until",
        ]

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "effective_date", "expiry_date")
        return cleaned_data


class EmptyConfirmationForm(StakeholderFormMixin, forms.Form):
    confirm = forms.BooleanField(
        label=_("I confirm this action"),
        help_text=_("This workflow action is recorded with your user account."),
    )


class AgreementRenewalStatusForm(StakeholderFormMixin, forms.Form):
    status = forms.ChoiceField(choices=RenewalStatus.choices)
