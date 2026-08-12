"""Forms for the Organizational Registers module.

Every form includes server-side validation and accessible markup rendered by
the shared ``includes/form_fields.html`` template.
"""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Register,
    RegisterAttachment,
    RegisterCategory,
    RegisterEntry,
    RegisterTemplate,
)

BOOTSTRAP_TEXT = "form-control"
BOOTSTRAP_SELECT = "form-select"
BOOTSTRAP_CHECK = "form-check-input"


def _widget(attrs: dict | None = None) -> dict:
    return {"class": BOOTSTRAP_TEXT, **(attrs or {})}


def _set_queryset(form, name: str, queryset) -> None:
    """Narrow the declared field type and scope its queryset."""
    field = form.fields[name]
    assert isinstance(field, forms.ModelChoiceField)
    field.queryset = queryset


def _field_choices(entry, field_name: str) -> list:
    """Return a copy of a model field's choices, defaulting to empty."""
    choices = entry._meta.get_field(field_name).choices
    return list(choices) if choices is not None else []


def _reference_query(q: str):
    from django.db.models import Q

    return (
        Q(reference_number__icontains=q)
        | Q(title__icontains=q)
        | Q(keywords__icontains=q)
    )


class RegisterSearchForm(forms.Form):
    """Combined search and filter form for register entries."""

    q = forms.CharField(
        required=False,
        label=_("Search"),
        widget=forms.TextInput(
            attrs=_widget({"placeholder": _("Reference number or title")})
        ),
    )
    register = forms.ModelChoiceField(
        queryset=Register.objects.none(),
        required=False,
        label=_("Register"),
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )
    category = forms.ModelChoiceField(
        queryset=RegisterCategory.objects.none(),
        required=False,
        label=_("Category"),
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )
    approval_status = forms.ChoiceField(
        required=False,
        label=_("Approval status"),
        choices=[
            ("", _("All statuses")),
            *_field_choices(RegisterEntry, "approval_status"),
        ],
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )
    confidentiality = forms.ChoiceField(
        required=False,
        label=_("Confidentiality"),
        choices=[
            ("", _("All levels")),
            *_field_choices(RegisterEntry, "confidentiality"),
        ],
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            from .selectors import category_queryset, register_queryset

            _set_queryset(self, "register", register_queryset(user))
            _set_queryset(self, "category", category_queryset(user))

    def apply_filters(self, queryset):
        data = self.cleaned_data
        if data.get("q"):
            queryset = queryset.filter(_reference_query(data["q"]))
        if data.get("register"):
            queryset = queryset.filter(register=data["register"])
        if data.get("category"):
            queryset = queryset.filter(register__category=data["category"])
        if data.get("approval_status"):
            queryset = queryset.filter(approval_status=data["approval_status"])
        if data.get("confidentiality"):
            queryset = queryset.filter(confidentiality=data["confidentiality"])
        return queryset


class RegisterCategoryForm(forms.ModelForm):
    class Meta:
        model = RegisterCategory
        fields = [
            "name",
            "code",
            "number_prefix",
            "description",
            "default_confidentiality",
            "retention_policy",
            "retention_years",
            "sort_order",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_widget()),
            "code": forms.TextInput(attrs=_widget()),
            "number_prefix": forms.TextInput(attrs=_widget()),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "default_confidentiality": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "retention_policy": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "retention_years": forms.NumberInput(attrs=_widget()),
            "sort_order": forms.NumberInput(attrs=_widget()),
            "is_active": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Register
        fields = [
            "name",
            "code",
            "category",
            "description",
            "owner",
            "responsible_department",
            "numbering_scheme",
            "confidentiality",
            "approval_required",
            "retention_policy",
            "retention_years",
            "status",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_widget()),
            "code": forms.TextInput(attrs=_widget()),
            "category": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "owner": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "responsible_department": forms.TextInput(attrs=_widget()),
            "numbering_scheme": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "confidentiality": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "approval_required": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "retention_policy": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "retention_years": forms.NumberInput(attrs=_widget()),
            "status": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "is_active": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            from .selectors import category_queryset

            _set_queryset(self, "category", category_queryset(user))


class RegisterTemplateForm(forms.ModelForm):
    class Meta:
        model = RegisterTemplate
        fields = [
            "name",
            "code",
            "register",
            "description",
            "fields",
            "validation_rules",
            "default_confidentiality",
            "is_default",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_widget()),
            "code": forms.TextInput(attrs=_widget()),
            "register": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "fields": forms.Textarea(
                attrs={
                    **_widget({"rows": 6}),
                    "placeholder": (
                        '[{"key": "code", "label": "Code", '
                        '"type": "TEXT", "required": true}]'
                    ),
                }
            ),
            "validation_rules": forms.Textarea(
                attrs={
                    **_widget({"rows": 3}),
                    "placeholder": (
                        '[{"code": "code_required", "field": "code", '
                        '"rule": "required"}]'
                    ),
                }
            ),
            "default_confidentiality": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "is_default": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "is_active": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }


class RegisterEntryForm(forms.ModelForm):
    class Meta:
        model = RegisterEntry
        fields = [
            "register",
            "template",
            "title",
            "description",
            "owner",
            "directorate",
            "program",
            "project",
            "reporting_period_start",
            "reporting_period_end",
            "confidentiality",
            "field_data",
            "tags",
            "keywords",
        ]
        widgets = {
            "register": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "template": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "title": forms.TextInput(attrs=_widget()),
            "description": forms.Textarea(attrs=_widget({"rows": 4})),
            "owner": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "directorate": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "program": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "project": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "reporting_period_start": forms.DateInput(attrs=_widget({"type": "date"})),
            "reporting_period_end": forms.DateInput(attrs=_widget({"type": "date"})),
            "confidentiality": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "field_data": forms.Textarea(
                attrs={
                    **_widget({"rows": 6}),
                    "placeholder": '{"custom_field": "value"}',
                }
            ),
            "tags": forms.TextInput(
                attrs=_widget({"placeholder": _("Comma-separated tags")})
            ),
            "keywords": forms.TextInput(attrs=_widget()),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            from apps.programs.models import Program, Project

            from .selectors import register_queryset, template_queryset

            _set_queryset(self, "register", register_queryset(user))
            _set_queryset(self, "template", template_queryset(user))
            _set_queryset(self, "program", Program.objects.filter(is_deleted=False))
            _set_queryset(self, "project", Project.objects.filter(is_deleted=False))
            owner_field = self.fields["owner"]
            assert isinstance(owner_field, forms.ModelChoiceField)
            if owner_field.queryset is not None:
                owner_field.queryset = owner_field.queryset.filter(is_active=True)

    def clean_tags(self):
        raw = self.cleaned_data.get("tags") or ""
        if isinstance(raw, str):
            return [tag.strip() for tag in raw.split(",") if tag.strip()]
        return raw or []


class RegisterEntryTransitionForm(forms.Form):
    """Comment-only form used for entry workflow transitions."""

    comment = forms.CharField(
        required=False,
        label=_("Comment"),
        widget=forms.Textarea(attrs=_widget({"rows": 3})),
    )


class RegisterAttachmentForm(forms.ModelForm):
    class Meta:
        model = RegisterAttachment
        fields = ["file", "description"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs=_widget()),
        }
