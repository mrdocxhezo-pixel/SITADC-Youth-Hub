"""Forms for the Export Engine (Phase 27).

Server-side validation always wins here; the forms only present choices the
actor is permitted to use (source/format choices are filtered by the caller).
"""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import ExportFormat, ExportSourceType


class ExportRequestForm(forms.Form):
    """Create an export request for a chosen source and format."""

    source_type = forms.ChoiceField(
        label=_("Data source"),
        choices=[],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    format = forms.ChoiceField(
        label=_("Format"),
        choices=[],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    include_sensitive = forms.BooleanField(
        label=_("Include sensitive/confidential fields"),
        required=False,
        help_text=_(
            "Only tick this if the dataset contains personal or confidential "
            "information and you hold the sensitive-export permission."
        ),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    confirmed = forms.BooleanField(
        label=_(
            "I confirm I am authorized to export this data and will handle it securely."
        ),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, source_choices=None, format_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if source_choices:
            self.fields["source_type"].choices = source_choices
        if format_choices:
            self.fields["format"].choices = format_choices
        if not self.fields["source_type"].choices:
            self.fields["source_type"].choices = []
        if not self.fields["format"].choices:
            self.fields["format"].choices = []

    def clean_source_type(self):
        source_type = self.cleaned_data.get("source_type")
        allowed = [key for key, _label in self.fields["source_type"].choices]
        if source_type not in allowed:
            raise forms.ValidationError(
                _("The selected data source is not available to you.")
            )
        return source_type

    def clean_format(self):
        format_code = self.cleaned_data.get("format")
        allowed = [key for key, _label in self.fields["format"].choices]
        if format_code not in allowed:
            raise forms.ValidationError(
                _("The selected format is not available to you.")
            )
        return format_code

    def clean_confirmed(self):
        confirmed = self.cleaned_data.get("confirmed")
        if not confirmed:
            raise forms.ValidationError(
                _("Please confirm you are authorized to export this data.")
            )
        return confirmed


class ExportFiltersForm(forms.Form):
    """Lightweight filter form; only safe exact-match fields are offered."""

    status = forms.CharField(
        label=_("Status"),
        required=False,
        max_length=60,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("e.g. ACTIVE")}
        ),
    )


class ExportConfigurationForm(forms.Form):
    """Edit the singleton engine configuration (admin/settings view)."""

    organization_name = forms.CharField(
        label=_("Organization name"), max_length=300, required=False
    )
    short_name = forms.CharField(
        label=_("Short name"), max_length=120, required=False
    )
    contact_email = forms.EmailField(label=_("Contact email"), required=False)
    website = forms.URLField(label=_("Website"), required=False)

    default_format = forms.ChoiceField(
        label=_("Default format"), choices=ExportFormat.choices
    )
    default_page_size = forms.ChoiceField(
        label=_("Default page size"),
        choices=[("A4", "A4"), ("LETTER", "Letter")],
        required=False,
    )
    default_orientation = forms.ChoiceField(
        label=_("Default orientation"),
        choices=[("PORTRAIT", "Portrait"), ("LANDSCAPE", "Landscape")],
        required=False,
    )

    max_sync_rows = forms.IntegerField(
        label=_("Maximum synchronous rows"), min_value=1, required=False
    )
    max_bulk_rows = forms.IntegerField(
        label=_("Maximum bulk rows"), min_value=1, required=False
    )
    max_file_size_mb = forms.IntegerField(
        label=_("Maximum file size (MB)"), min_value=1, required=False
    )
    max_columns = forms.IntegerField(
        label=_("Maximum columns"), min_value=1, required=False
    )
    standard_retention_hours = forms.IntegerField(
        label=_("Standard retention (hours)"), min_value=1, required=False
    )
    sensitive_retention_hours = forms.IntegerField(
        label=_("Sensitive retention (hours)"), min_value=1, required=False
    )
    download_expiry_hours = forms.IntegerField(
        label=_("Download expiry (hours)"), min_value=1, required=False
    )


class ExportTemplateForm(forms.Form):
    """Create/update an export template (admin view)."""

    code = forms.CharField(label=_("Code"), max_length=60)
    name = forms.CharField(label=_("Name"), max_length=150)
    description = forms.CharField(
        label=_("Description"), widget=forms.Textarea, required=False
    )
    source_type = forms.ChoiceField(
        label=_("Source type"), choices=ExportSourceType.choices
    )
    page_size = forms.ChoiceField(
        label=_("Page size"),
        choices=[("A4", "A4"), ("LETTER", "Letter")],
        required=False,
    )
    orientation = forms.ChoiceField(
        label=_("Orientation"),
        choices=[("PORTRAIT", "Portrait"), ("LANDSCAPE", "Landscape")],
        required=False,
    )
    watermark_text = forms.CharField(
        label=_("Watermark text"), max_length=80, required=False
    )
    is_active = forms.BooleanField(
        label=_("Active"), required=False, initial=True
    )
