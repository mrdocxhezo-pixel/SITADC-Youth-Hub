"""
Django Forms for the membership management module.
"""

from __future__ import annotations

from django import forms

from apps.locations.forms import GeographicFieldsMixin

from .models import (
    MemberCommitteeAssignment,
    MemberLeave,
    MemberParticipation,
    MemberProfile,
    MemberRecognition,
    MembershipApplication,
    MembershipExit,
    MembershipPayment,
    MembershipTransfer,
    MembershipUpgrade,
)


class MemberProfileForm(GeographicFieldsMixin, forms.ModelForm):
    """Form for editing a member profile."""

    geo_fields = {
        "province": {"field": "province_location", "required": False},
        "district": {"field": "district_location", "required": False},
        "ward": {"field": "ward_location", "required": False},
    }
    geo_text_fields = {
        "province": "province",
        "district": "district",
        "ward": "community",
    }

    class Meta:
        model = MemberProfile
        fields = [
            "photo",
            "gender",
            "date_of_birth",
            "nationality",
            "national_id",
            "education_level",
            "occupation",
            "phone_primary",
            "phone_secondary",
            "email_personal",
            "physical_address",
            "province",
            "district",
            "community",
            "province_location",
            "district_location",
            "ward_location",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "skills_summary",
            "interests_summary",
            "profile_visibility",
            "preferred_communication",
            "referral_source",
            "consent_to_communications",
        ]
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nationality": forms.TextInput(attrs={"class": "form-control"}),
            "national_id": forms.TextInput(attrs={"class": "form-control"}),
            "education_level": forms.Select(attrs={"class": "form-select"}),
            "occupation": forms.TextInput(attrs={"class": "form-control"}),
            "phone_primary": forms.TextInput(attrs={"class": "form-control"}),
            "phone_secondary": forms.TextInput(attrs={"class": "form-control"}),
            "email_personal": forms.EmailInput(attrs={"class": "form-control"}),
            "physical_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "province": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "district": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "community": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "emergency_contact_name": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact_phone": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact_relationship": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "skills_summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "interests_summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "profile_visibility": forms.Select(attrs={"class": "form-select"}),
            "preferred_communication": forms.Select(attrs={"class": "form-select"}),
            "referral_source": forms.TextInput(attrs={"class": "form-control"}),
            "consent_to_communications": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class MembershipApplicationForm(GeographicFieldsMixin, forms.ModelForm):
    """Public form for submitting a membership application."""

    geo_fields = {
        "province": {"field": "province_location", "required": False},
        "district": {"field": "district_location", "required": False},
        "ward": {"field": "ward_location", "required": False},
    }
    geo_text_fields = {
        "province": "province",
        "district": "district",
        "ward": "community",
    }

    class Meta:
        model = MembershipApplication
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "gender",
            "date_of_birth",
            "nationality",
            "national_id",
            "occupation",
            "education_level",
            "province",
            "district",
            "community",
            "province_location",
            "district_location",
            "ward_location",
            "category",
            "membership_type",
            "level",
            "skills",
            "interests",
            "referral_source",
            "declaration_agreed",
            "responsibilities_acknowledged",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nationality": forms.TextInput(attrs={"class": "form-control"}),
            "national_id": forms.TextInput(attrs={"class": "form-control"}),
            "occupation": forms.TextInput(attrs={"class": "form-control"}),
            "education_level": forms.Select(attrs={"class": "form-select"}),
            "province": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "district": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "community": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "membership_type": forms.Select(attrs={"class": "form-select"}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "interests": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "referral_source": forms.TextInput(attrs={"class": "form-control"}),
            "declaration_agreed": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "responsibilities_acknowledged": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class MembershipPaymentForm(forms.ModelForm):
    """Form for recording a membership payment."""

    class Meta:
        model = MembershipPayment
        fields = [
            "member",
            "fee",
            "amount",
            "currency",
            "payment_method",
            "payment_date",
            "transaction_reference",
            "period_from",
            "period_to",
            "receipt_file",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "fee": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "currency": forms.TextInput(attrs={"class": "form-control"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "payment_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "transaction_reference": forms.TextInput(attrs={"class": "form-control"}),
            "period_from": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "period_to": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "receipt_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class MembershipTransferForm(GeographicFieldsMixin, forms.ModelForm):
    """Form for requesting a membership transfer."""

    geo_fields = {
        "province": {"field": "to_province_location", "required": False},
        "district": {"field": "to_district_location", "required": False},
    }
    geo_text_fields = {
        "province": "to_province",
        "district": "to_district",
    }

    class Meta:
        model = MembershipTransfer
        fields = [
            "member",
            "to_province",
            "to_district",
            "to_community",
            "to_province_location",
            "to_district_location",
            "effective_date",
            "reason",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "to_province": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "to_district": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "to_community": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "effective_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MembershipUpgradeForm(forms.ModelForm):
    """Form for requesting a membership upgrade."""

    class Meta:
        model = MembershipUpgrade
        fields = ["member", "to_category", "effective_date", "reason"]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "to_category": forms.Select(attrs={"class": "form-select"}),
            "effective_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MembershipExitForm(forms.ModelForm):
    """Form for initiating a membership exit."""

    class Meta:
        model = MembershipExit
        fields = [
            "member",
            "exit_type",
            "reason",
            "effective_date",
            "exit_interview_notes",
            "assets_returned",
            "documents_returned",
            "transition_to_alumni",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "exit_type": forms.Select(attrs={"class": "form-select"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "effective_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "exit_interview_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "assets_returned": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "documents_returned": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "transition_to_alumni": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class MemberLeaveForm(forms.ModelForm):
    """Form for applying for member leave."""

    class Meta:
        model = MemberLeave
        fields = ["member", "leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "leave_type": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MemberParticipationForm(forms.ModelForm):
    """Form for recording member participation."""

    class Meta:
        model = MemberParticipation
        fields = [
            "member",
            "participation_type",
            "activity_name",
            "role",
            "start_date",
            "end_date",
            "outcomes",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "participation_type": forms.Select(attrs={"class": "form-select"}),
            "activity_name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "outcomes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MemberRecognitionForm(forms.ModelForm):
    """Form for recording member recognition."""

    class Meta:
        model = MemberRecognition
        fields = [
            "member",
            "recognition_type",
            "title",
            "description",
            "award_date",
            "issuing_authority",
            "evidence_file",
            "publication_permission",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "recognition_type": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "award_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "issuing_authority": forms.TextInput(attrs={"class": "form-control"}),
            "evidence_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "publication_permission": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class CommitteeAssignmentForm(forms.ModelForm):
    """Form for assigning a member to a committee."""

    class Meta:
        model = MemberCommitteeAssignment
        fields = [
            "member",
            "committee",
            "position",
            "appointment_date",
            "end_date",
            "responsibilities",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "committee": forms.Select(attrs={"class": "form-select"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "appointment_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "responsibilities": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }
