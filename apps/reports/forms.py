"""Accessible, service-facing forms for the Dynamic Report Builder module.

Forms follow the MEAL convention: Bootstrap 5 controls, accessible labels and
help associations, ``%Y-%m-%d`` date inputs.  Writes are delegated to the
service layer which performs the server-side permission and status checks.
"""

# ruff: noqa: RUF012 - Django form Meta options are declarative attributes.

from __future__ import annotations

import json

from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import ConfidentialityLevel, ReportingFrequency
from .models import (
    DynamicField,
    FieldGroup,
    ReportCategory,
    ReportTemplate,
    ReportTemplateSettings,
    TemplateSection,
)


class ReportFormMixin:
    """Apply Bootstrap controls and accessible error/help associations."""

    fields: dict[str, forms.Field]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            widget = field.widget
            if isinstance(field, forms.DateField):
                field.widget = forms.DateInput(attrs=widget.attrs, format="%Y-%m-%d")
                field.widget.attrs["type"] = "date"
                field.input_formats = ["%Y-%m-%d"]
                widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select | forms.SelectMultiple):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class ReportCategoryForm(ReportFormMixin, forms.ModelForm):
    class Meta:
        model = ReportCategory
        fields = ["code", "name", "description", "color", "icon", "sort_order"]


class ReportTemplateForm(ReportFormMixin, forms.ModelForm):
    class Meta:
        model = ReportTemplate
        fields = [
            "code",
            "title",
            "category",
            "reporting_frequency",
            "description",
            "department",
            "owner",
            "confidentiality",
            "effective_from",
            "expires_on",
            "retention_period_days",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = ReportCategory.objects.all()
        self.fields["confidentiality"] = forms.ChoiceField(
            choices=ConfidentialityLevel.choices,
            label=_("Confidentiality"),
        )
        self.fields["reporting_frequency"] = forms.ChoiceField(
            choices=ReportingFrequency.choices,
            label=_("Reporting frequency"),
        )


class TemplatePublishForm(ReportFormMixin, forms.Form):
    notes = forms.CharField(
        label=_("Publication notes"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text=_("Optional notes recorded in the audit trail."),
    )


class TemplateCloneForm(ReportFormMixin, forms.Form):
    new_code = forms.SlugField(
        label=_("New template code"),
        max_length=100,
        help_text=_("Unique code for the cloned template."),
    )
    new_title = forms.CharField(label=_("New title"), max_length=255, required=False)
    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class TemplateImportForm(ReportFormMixin, forms.Form):
    category = forms.ModelChoiceField(
        queryset=ReportCategory.objects.all(),
        label=_("Report category"),
    )
    code = forms.SlugField(
        label=_("Template code"),
        max_length=100,
        required=False,
        help_text=_("Leave blank to use the code from the payload."),
    )
    title = forms.CharField(label=_("Title"), max_length=255, required=False)
    payload = forms.CharField(
        label=_("JSON payload"),
        widget=forms.Textarea(attrs={"rows": 14, "spellcheck": "false"}),
        help_text=_("Paste a previously exported template JSON payload."),
    )
    dry_run = forms.BooleanField(
        label=_("Validate only (dry run)"),
        required=False,
        help_text=_("Check the payload without importing."),
    )

    def clean_payload(self):
        raw = self.cleaned_data["payload"]
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(
                _("Invalid JSON: %(message)s") % {"message": exc.msg}
            ) from exc
        if not isinstance(payload, dict):
            raise forms.ValidationError(_("The payload must be a JSON object."))
        return payload


class SchemaEditorForm(ReportFormMixin, forms.Form):
    """Persist a full template schema from its JSON representation.

    The payload is validated by the service layer (structure, formulas,
    conditional logic and dependency graphs) before any record is written.
    """

    schema = forms.CharField(
        label=_("Schema JSON"),
        widget=forms.Textarea(attrs={"rows": 24, "spellcheck": "false"}),
        help_text=_(
            "Full schema object with sections, field groups, fields, "
            "conditional rules and components."
        ),
    )
    change_summary = forms.CharField(
        label=_("Change summary"),
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={"placeholder": "What changed in this draft?"}),
    )

    def clean_schema(self):
        raw = self.cleaned_data["schema"]
        try:
            schema = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(
                _("Invalid JSON: %(message)s") % {"message": exc.msg}
            ) from exc
        if not isinstance(schema, dict) or "sections" not in schema:
            raise forms.ValidationError(_("The schema must contain a sections list."))
        return schema


class ReportTemplateSettingsForm(ReportFormMixin, forms.ModelForm):
    class Meta:
        model = ReportTemplateSettings
        fields = [
            "template_numbering_scheme_code",
            "default_reporting_frequency",
            "default_page_layout",
            "default_export_settings",
            "auto_save_interval_seconds",
            "retention_default_days",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["default_reporting_frequency"] = forms.ChoiceField(
            choices=[("", _("Use template default")), *ReportingFrequency.choices],
            label=_("Default reporting frequency"),
            required=False,
        )
        self.fields["default_page_layout"] = forms.CharField(
            label=_("Default page layout"),
            required=False,
            widget=forms.Textarea(
                attrs={
                    "rows": 3,
                    "spellcheck": "false",
                    "placeholder": '{"key": "value"}',
                }
            ),
            help_text=_("Optional JSON configuration."),
        )
        self.fields["default_export_settings"] = forms.CharField(
            label=_("Default export settings"),
            required=False,
            widget=forms.Textarea(
                attrs={
                    "rows": 3,
                    "spellcheck": "false",
                    "placeholder": '{"key": "value"}',
                }
            ),
            help_text=_("Optional JSON configuration."),
        )


class SectionDesignerForm(ReportFormMixin, forms.ModelForm):
    class Meta:
        model = TemplateSection
        fields = [
            "parent",
            "name",
            "code",
            "description",
            "instructions",
            "sort_order",
            "is_repeatable",
            "is_collapsible",
            "is_locked",
            "visibility_mode",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = TemplateSection.objects.filter(
            template_id=self.instance.template_id
        )


class FieldGroupDesignerForm(ReportFormMixin, forms.ModelForm):
    class Meta:
        model = FieldGroup
        fields = ["name", "code", "description", "sort_order"]


class DynamicFieldDesignerForm(ReportFormMixin, forms.ModelForm):
    class Meta:
        model = DynamicField
        fields = [
            "label",
            "code",
            "field_type",
            "data_type",
            "required",
            "read_only",
            "hidden",
            "is_repeatable",
            "is_calculated",
            "formula",
            "default_value",
            "placeholder",
            "help_text",
            "tooltip",
            "sort_order",
        ]
        widgets = {
            "formula": forms.TextInput(
                attrs={"spellcheck": "false", "placeholder": "sum([a, b]) * 1.1"}
            ),
            "help_text": forms.Textarea(attrs={"rows": 2}),
            "default_value": forms.Textarea(
                attrs={"rows": 2, "spellcheck": "false", "placeholder": '{"value": 1}'}
            ),
        }

    def clean_default_value(self):
        raw = self.cleaned_data.get("default_value")
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(_("Default value must be valid JSON.")) from exc

    def clean_formula(self):
        formula = self.cleaned_data.get("formula", "")
        is_calculated = self.cleaned_data.get("is_calculated", False)
        if is_calculated and not formula:
            raise forms.ValidationError(_("Calculated fields require a formula."))
        return formula


class VersionRestoreForm(ReportFormMixin, forms.Form):
    change_summary = forms.CharField(
        label=_("Change summary"),
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={"placeholder": "Restored from version ..."}),
    )
