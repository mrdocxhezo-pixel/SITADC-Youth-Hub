"""Dynamic form rendering for report data entry.

Reads the template schema (sections, field groups, dynamic fields) and
generates Django form fields at runtime so users can enter report data
against any published template.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from django import forms
from django.core.files.uploadedfile import UploadedFile

from apps.reports.models import DynamicField, TemplateSection


def _to_json_safe(value: Any) -> Any:
    """Convert cleaned form values into JSON-serializable primitives.

    Dynamic field responses are stored in ``JSONField`` columns, so rich
    Python types produced by form cleaning (dates, decimals, ...) must be
    reduced to strings before persistence.
    """
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    return value

# ---------------------------------------------------------------------------
# Field-type to form-field mapping
# ---------------------------------------------------------------------------

_FIELD_MAP: dict[str, type[forms.Field]] = {
    "TEXT": forms.CharField,
    "MULTILINE_TEXT": forms.CharField,
    "RICH_TEXT": forms.CharField,
    "INTEGER": forms.IntegerField,
    "DECIMAL": forms.DecimalField,
    "CURRENCY": forms.DecimalField,
    "PERCENTAGE": forms.DecimalField,
    "DATE": forms.DateField,
    "TIME": forms.TimeField,
    "DATETIME": forms.DateTimeField,
    "DROPDOWN": forms.ChoiceField,
    "MULTI_SELECT": forms.MultipleChoiceField,
    "RADIO": forms.RadioSelect,
    "CHECKBOX": forms.CheckboxInput,
    "TOGGLE": forms.CheckboxInput,
    "IMAGE": forms.FileField,
    "VIDEO": forms.FileField,
    "AUDIO": forms.FileField,
    "DOCUMENT": forms.FileField,
    "SIGNATURE": forms.CharField,
    "GPS_COORDINATES": forms.CharField,
    "USER_SELECTOR": forms.IntegerField,
    "PROGRAM_SELECTOR": forms.IntegerField,
    "PROJECT_SELECTOR": forms.IntegerField,
}


def _widget_for_field(field: DynamicField) -> forms.Widget | None:
    """Return an appropriate widget for the given dynamic field."""
    ft = field.field_type
    if ft in ("MULTILINE_TEXT", "RICH_TEXT"):
        return forms.Textarea(attrs={"rows": 4})
    if ft == "CHECKBOX" or ft == "TOGGLE":
        return forms.CheckboxInput(attrs={"class": "form-check-input"})
    if ft == "RADIO":
        return forms.RadioSelect()
    if ft in ("IMAGE", "VIDEO", "AUDIO", "DOCUMENT"):
        return forms.FileInput(attrs={"class": "form-control"})
    if ft == "DATE":
        return forms.DateInput(attrs={"type": "date", "class": "form-control"})
    if ft == "TIME":
        return forms.TimeInput(attrs={"type": "time", "class": "form-control"})
    if ft == "DATETIME":
        return forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        )
    if ft in ("INTEGER", "DECIMAL", "CURRENCY", "PERCENTAGE"):
        return forms.NumberInput(attrs={"class": "form-control"})
    if ft == "GPS_COORDINATES":
        return forms.TextInput(
            attrs={"class": "form-control", "placeholder": "lat, lng"}
        )
    return forms.TextInput(attrs={"class": "form-control"})


def _choices_for_field(field: DynamicField) -> list[tuple[str, str]]:
    """Return choice tuples for selection-type fields."""
    return [
        (opt.value, opt.label) for opt in field.options.order_by("sort_order", "value")
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class DynamicReportForm(forms.Form):
    """A dynamically-generated form representing all fields across all
    sections of a report template.

    Field names follow the pattern ``section_{section_pk}_field_{field_pk}``
    so the view layer can map responses back to the correct section/field.
    """

    def __init__(self, *args: Any, template_id: str | None = None, **kwargs: Any):
        self.template_id = template_id
        super().__init__(*args, **kwargs)
        if template_id is None:
            return

        sections = TemplateSection.objects.filter(template_id=template_id).order_by(
            "sort_order", "name"
        )
        for section in sections:
            groups = section.groups.order_by("sort_order", "name")
            for group in groups:
                fields = group.fields.order_by("sort_order", "label")
                for field in fields:
                    self._add_dynamic_field(section, field)

    def _add_dynamic_field(self, section: TemplateSection, field: DynamicField) -> None:
        """Add a single dynamic field to the form."""
        field_name = f"section_{section.pk}_field_{field.pk}"

        kwargs: dict[str, Any] = {
            "label": field.label,
            "required": field.required,
            "help_text": field.help_text or field.placeholder or "",
        }

        widget = _widget_for_field(field)
        if widget is not None:
            kwargs["widget"] = widget

        # Choice fields
        if field.field_type in ("DROPDOWN", "MULTI_SELECT", "RADIO"):
            choices = _choices_for_field(field)
            if not choices:
                choices = [("", "---------")]
            kwargs["choices"] = choices
            if field.field_type == "MULTI_SELECT":
                kwargs["widget"] = forms.SelectMultiple(attrs={"class": "form-select"})
            elif field.field_type == "RADIO":
                kwargs["widget"] = forms.RadioSelect()

        # Numeric fields
        if field.field_type in ("DECIMAL", "CURRENCY", "PERCENTAGE"):
            kwargs["max_digits"] = 12
            kwargs["decimal_places"] = 2

        # File fields
        if field.field_type in ("IMAGE", "VIDEO", "AUDIO", "DOCUMENT"):
            kwargs["widget"] = forms.FileInput(attrs={"class": "form-control"})

        # Boolean fields
        if field.field_type in ("CHECKBOX", "TOGGLE"):
            kwargs["required"] = False
            kwargs["widget"] = forms.CheckboxInput(attrs={"class": "form-check-input"})

        form_field_class = _FIELD_MAP.get(field.field_type, forms.CharField)
        try:
            self.fields[field_name] = form_field_class(**kwargs)
        except Exception:
            # Fallback to CharField if the specific type fails
            self.fields[field_name] = forms.CharField(
                label=field.label,
                required=field.required,
                help_text=field.help_text or "",
            )

    # ------------------------------------------------------------------
    # Helpers for extracting cleaned data by section
    # ------------------------------------------------------------------

    def section_data(self, section_pk: str) -> dict[str, Any]:
        """Return JSON-safe cleaned data for a specific section as a dict.

        Uploaded files are excluded; the view layer persists them through
        ``store_dynamic_field_upload`` and records the storage path as the
        field response value.
        """
        prefix = f"section_{section_pk}_field_"
        data: dict[str, Any] = {}
        for name, value in self.cleaned_data.items():
            if not name.startswith(prefix) or isinstance(value, UploadedFile):
                continue
            data[name[len(prefix) :]] = _to_json_safe(value)
        return data

    def all_section_data(self) -> dict[str, dict[str, Any]]:
        """Return a mapping of section_pk -> {field_pk: value}.

        Uploaded files are excluded; the view layer persists them through
        ``store_dynamic_field_upload``.
        """
        result: dict[str, dict[str, Any]] = {}
        for name, value in self.cleaned_data.items():
            if name.startswith("section_") and "_field_" in name:
                if isinstance(value, UploadedFile):
                    continue
                parts = name.split("_")
                # section_{pk}_field_{pk}
                section_pk = parts[1]
                field_pk = parts[3]
                result.setdefault(section_pk, {})[field_pk] = _to_json_safe(value)
        return result
