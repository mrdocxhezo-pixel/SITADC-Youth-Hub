"""Forms for the reference numbering module."""

from __future__ import annotations

from typing import ClassVar

from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import ReferenceModules
from .models import ReferenceNumberScheme

CONTROL_CLASS = "form-control"
SELECT_CLASS = "form-select"
CHECK_CLASS = "form-check-input"


def _control(attrs: dict | None = None) -> dict:
    return {"class": CONTROL_CLASS, **(attrs or {})}


def _select(attrs: dict | None = None) -> dict:
    return {"class": SELECT_CLASS, **(attrs or {})}


def _check(attrs: dict | None = None) -> dict:
    return {"class": CHECK_CLASS, **(attrs or {})}


class ReferenceNumberSchemeForm(forms.ModelForm):
    """Create or update a reference number scheme."""

    class Meta:
        model = ReferenceNumberScheme
        fields = (
            "name",
            "code",
            "module",
            "record_type",
            "prefix",
            "pattern",
            "organization_code",
            "sequence_length",
            "start_value",
            "reset_period",
            "fiscal_start_month",
            "custom_reset_interval_days",
            "is_default_for_module",
            "is_default_for_record_type",
            "is_fallback",
            "description",
            "notes",
        )
        widgets: ClassVar[dict] = {
            "name": forms.TextInput(attrs=_control()),
            "code": forms.TextInput(attrs=_control()),
            "module": forms.Select(attrs=_select()),
            "record_type": forms.TextInput(attrs=_control()),
            "prefix": forms.TextInput(attrs=_control()),
            "pattern": forms.TextInput(attrs=_control()),
            "organization_code": forms.TextInput(attrs=_control()),
            "sequence_length": forms.NumberInput(attrs=_control()),
            "start_value": forms.NumberInput(attrs=_control()),
            "reset_period": forms.Select(attrs=_select()),
            "fiscal_start_month": forms.NumberInput(attrs=_control()),
            "custom_reset_interval_days": forms.NumberInput(attrs=_control()),
            "is_default_for_module": forms.CheckboxInput(attrs=_check()),
            "is_default_for_record_type": forms.CheckboxInput(attrs=_check()),
            "is_fallback": forms.CheckboxInput(attrs=_check()),
            "description": forms.Textarea(attrs=_control({"rows": 3})),
            "notes": forms.Textarea(attrs=_control({"rows": 2})),
        }


class ReferencePreviewForm(forms.Form):
    """Preview the next reference number for a context without consuming it."""

    module = forms.ChoiceField(
        choices=ReferenceModules.choices,
        label=_("Module"),
        widget=forms.Select(attrs=_select()),
    )
    record_type = forms.CharField(
        label=_("Record type"),
        required=False,
        help_text=_("Optional narrower type within the module."),
        widget=forms.TextInput(attrs=_control()),
    )
    scheme = forms.ModelChoiceField(
        queryset=ReferenceNumberScheme.objects.filter(is_active=True),
        required=False,
        label=_("Scheme"),
        help_text=_("Leave blank to resolve the scheme automatically."),
        widget=forms.Select(attrs=_select()),
    )
    year = forms.IntegerField(
        label=_("Year"),
        required=False,
        help_text=_("Leave blank to use the current year."),
        widget=forms.NumberInput(attrs=_control()),
    )
    organization_code = forms.CharField(
        label=_("Organization code"),
        required=False,
        help_text=_("Leave blank to use the scheme's organization code."),
        widget=forms.TextInput(attrs=_control()),
    )


class SequenceResetForm(forms.Form):
    """Reset a scheme's sequence to a new starting value."""

    start_value = forms.IntegerField(
        label=_("Start value"),
        min_value=1,
        help_text=_(
            "The sequence never goes backwards; it resumes one past the "
            "highest value already issued."
        ),
        widget=forms.NumberInput(attrs=_control()),
    )
    notes = forms.CharField(
        label=_("Reason"),
        required=False,
        widget=forms.Textarea(attrs=_control({"rows": 2})),
    )
