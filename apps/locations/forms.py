"""
Reusable form helpers for geographic dropdowns.

Provides a mixin that adds database-driven Province / District / Constituency /
Ward ModelChoiceFields to any Django (Model)Form, plus server-side validation of
the hierarchy chain (a child must belong to its selected parent).

The geographic fields are rendered as hidden inputs on the form and are meant to
be displayed through the ``locations/partials/geographic_dropdowns.html``
partial, whose ``<select>`` elements submit under the same field names. The
hidden widgets keep them out of generic ``{% for field in form %}`` loops.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .resolvers import resolve_location
from .services import (
    get_constituencies,
    get_districts,
    get_provinces,
    get_wards,
)

MISSING = object()


class GeographicHiddenInput(forms.HiddenInput):
    """Marker widget so template field loops can skip geographic fields."""


class GeographicFieldsMixin(forms.BaseForm):
    """
    Adds hidden, validated geographic FK fields to a form.

    Configure via ``geo_fields`` mapping each level to its model field, e.g.::

        geo_fields = {
            "province": {"field": "province_location", "required": False},
            "district": {"field": "district_location", "required": False},
            "constituency": {"field": "constituency_location", "required": False},
            "ward": {"field": "ward_location", "required": False},
        }

    Level selection also updates the legacy free-text fields in ``save()`` for
    backward compatibility.
    """

    geo_fields: dict = {}
    #: Mapping level -> the legacy text field kept in sync (optional).
    geo_text_fields: dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = dict(getattr(self, "initial", {}) or {})
        base_fields = self.fields

        for level, spec in self.geo_fields.items():
            field_name = spec.get("field", level)
            required = spec.get("required", False)
            label = spec.get("label", self._default_label(level))
            queryset = self._queryset_for(level)

            if level == "province":
                field = forms.ModelChoiceField(
                    queryset=get_provinces(active_only=True)
                    if queryset is MISSING
                    else queryset,
                    required=required,
                    label=label,
                    widget=GeographicHiddenInput(),
                )
            elif level == "district":
                field = forms.ModelChoiceField(
                    queryset=get_districts(active_only=True)
                    if queryset is MISSING
                    else queryset,
                    required=required,
                    label=label,
                    widget=GeographicHiddenInput(),
                )
            elif level == "constituency":
                field = forms.ModelChoiceField(
                    queryset=get_constituencies(active_only=True)
                    if queryset is MISSING
                    else queryset,
                    required=required,
                    label=label,
                    widget=GeographicHiddenInput(),
                )
            elif level == "ward":
                field = forms.ModelChoiceField(
                    queryset=get_wards(active_only=True)
                    if queryset is MISSING
                    else queryset,
                    required=required,
                    label=label,
                    widget=GeographicHiddenInput(),
                )
            else:
                continue

            existing = base_fields.get(field_name)
            if existing is not None:
                # Preserve any current value already bound to the model.
                field.initial = existing.initial
            if self.instance and getattr(self, "instance", None) is not None:
                value = getattr(self.instance, field_name, None)
                if value is not None:
                    field.initial = value
                    initial[field_name] = value

            base_fields[field_name] = field
            # Ensure the value is carried through on re-validation (POST).
            if field_name not in self.initial:
                self.initial[field_name] = field.initial

        self.geo_initial = initial

    def _default_label(self, level):
        labels = {
            "province": _("Province / Region"),
            "district": _("District"),
            "constituency": _("Constituency"),
            "ward": _("Ward"),
        }
        return labels.get(level, level)

    def _queryset_for(self, level):
        return MISSING

    def clean(self):
        cleaned = super().clean()
        # Validate that selected children belong to their selected parent.
        province = cleaned.get(
            self.geo_fields.get("province", {}).get("field", "province")
        )
        district = cleaned.get(
            self.geo_fields.get("district", {}).get("field", "district")
        )
        constituency = cleaned.get(
            self.geo_fields.get("constituency", {}).get("field", "constituency")
        )
        ward = cleaned.get(self.geo_fields.get("ward", {}).get("field", "ward"))
        try:
            resolve_location(
                province=province,
                district=district,
                constituency=constituency,
                ward=ward,
            )
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        return cleaned

    def save(self, commit=True):
        """Persist geo FK fields and sync the legacy free-text fields."""
        if isinstance(self, forms.ModelForm):
            instance = super().save(commit=False)
            self.save_geography(instance)
            if commit:
                instance.save()
            return instance
        return super().save(commit=commit)

    def save_geography(self, instance):
        """Copy cleaned geographic FK values onto the instance and sync text."""
        for level, spec in self.geo_fields.items():
            field_name = spec.get("field", level)
            value = self.cleaned_data.get(field_name)
            setattr(instance, field_name, value)
            text_field = self.geo_text_fields.get(level)
            if text_field and value is not None:
                setattr(instance, text_field, getattr(value, "name", str(value)))
        return instance
