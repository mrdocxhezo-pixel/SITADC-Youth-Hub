"""Forms for the Enterprise Search module."""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import DEFAULT_RESULTS_PER_TYPE, ENTITY_TYPE_KEYS
from .exceptions import SearchValidationError
from .selectors import available_entity_type_choices
from .validators import coerce_entity_type_keys, validate_query


class GlobalSearchForm(forms.Form):
    """Search box + optional entity type refinements."""

    q = forms.CharField(
        label=_("Search"),
        required=False,
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": _(
                    "Search leadership, members, programmes, reports, documents..."
                ),
                "aria-label": _("Search SITADC Youth Hub"),
                "autofocus": True,
            }
        ),
    )
    types = forms.MultipleChoiceField(
        label=_("Entity types"),
        required=False,
        choices=ENTITY_TYPE_KEYS,
        widget=forms.CheckboxSelectMultiple,
    )
    per_type = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=25,
        widget=forms.HiddenInput,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            choices = available_entity_type_choices(user)
            self.fields["types"].choices = choices
            self.available_keys = [key for key, _label in choices]
        else:
            self.available_keys = list(ENTITY_TYPE_KEYS)

    def clean_q(self):
        raw = self.cleaned_data.get("q", "")
        if not raw:
            return ""
        try:
            return validate_query(raw)
        except SearchValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc

    def clean_types(self):
        raw = self.cleaned_data.get("types")
        return coerce_entity_type_keys(raw)

    def clean(self):
        cleaned = super().clean()
        keys = cleaned.get("types")
        if keys is None:
            cleaned["types"] = []
        per_type = cleaned.get("per_type")
        cleaned["per_type"] = int(per_type) if per_type else DEFAULT_RESULTS_PER_TYPE
        return cleaned


class SavedSearchForm(forms.Form):
    """Name a search to persist for quick reuse."""

    name = forms.CharField(
        label=_("Saved search name"),
        required=False,
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("e.g. OVC beneficiaries - Lusaka"),
            }
        ),
    )
    query = forms.CharField(widget=forms.HiddenInput, required=False)
    types = forms.CharField(widget=forms.HiddenInput, required=False)
