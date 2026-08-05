"""Forms for the organizational structure module."""

from __future__ import annotations

from typing import ClassVar, cast

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.constants import AccountStatus
from apps.accounts.models import User

from .constants import ActingAppointmentStatus
from .models import (
    ActingAppointment,
    OrganizationLevel,
    OrganizationUnit,
    Position,
    PositionAssignment,
    PositionClassification,
    TransferRecord,
    Vacancy,
)

CONTROL_CLASS = "form-control"
SELECT_CLASS = "form-select"


def _model_choice(form: forms.BaseForm, name: str) -> forms.ModelChoiceField:
    """Return a model-choice field with its concrete Django type."""
    return cast(forms.ModelChoiceField, form.fields[name])


def _control(attrs: dict | None = None) -> dict:
    return {"class": CONTROL_CLASS, **(attrs or {})}


def _select(attrs: dict | None = None) -> dict:
    return {"class": SELECT_CLASS, **(attrs or {})}


class OrganizationLevelForm(forms.ModelForm):
    """Create or update an organizational level."""

    class Meta:
        model = OrganizationLevel
        fields = ("name", "code", "description", "sort_order", "is_active")
        widgets: ClassVar[dict] = {
            "name": forms.TextInput(attrs=_control()),
            "code": forms.TextInput(attrs=_control()),
            "description": forms.Textarea(attrs=_control({"rows": 3})),
            "sort_order": forms.NumberInput(attrs=_control()),
        }


class PositionClassificationForm(forms.ModelForm):
    """Create or update a position classification."""

    class Meta:
        model = PositionClassification
        fields = ("name", "code", "description", "sort_order", "is_active")
        widgets: ClassVar[dict] = {
            "name": forms.TextInput(attrs=_control()),
            "code": forms.TextInput(attrs=_control()),
            "description": forms.Textarea(attrs=_control({"rows": 3})),
            "sort_order": forms.NumberInput(attrs=_control()),
        }


class OrganizationUnitForm(forms.ModelForm):
    """Create or update an organizational unit."""

    class Meta:
        model = OrganizationUnit
        fields = (
            "identifier",
            "name",
            "short_name",
            "description",
            "level",
            "parent",
            "unit_type",
            "unit_head",
            "office_location",
            "contact_email",
            "contact_phone",
            "status",
            "effective_date",
            "established_date",
            "access_scope",
            "notes",
        )
        widgets: ClassVar[dict] = {
            "identifier": forms.TextInput(attrs=_control()),
            "name": forms.TextInput(attrs=_control()),
            "short_name": forms.TextInput(attrs=_control()),
            "description": forms.Textarea(attrs=_control({"rows": 3})),
            "level": forms.Select(attrs=_select()),
            "parent": forms.Select(attrs=_select()),
            "unit_type": forms.Select(attrs=_select()),
            "unit_head": forms.Select(attrs=_select()),
            "office_location": forms.TextInput(attrs=_control()),
            "contact_email": forms.EmailInput(attrs=_control()),
            "contact_phone": forms.TextInput(attrs=_control()),
            "status": forms.Select(attrs=_select()),
            "effective_date": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "established_date": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "access_scope": forms.Select(attrs=_select()),
            "notes": forms.Textarea(attrs=_control({"rows": 2})),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "parent").queryset = (
            OrganizationUnit.objects.with_parent().exclude(pk=self.instance.pk)
        )
        _model_choice(self, "unit_head").queryset = (
            Position.objects.active().select_related("organizational_unit")
        )


class PositionForm(forms.ModelForm):
    """Create or update a position."""

    class Meta:
        model = Position
        fields = (
            "title",
            "organizational_unit",
            "classification",
            "appointment_type",
            "responsibilities",
            "required_competencies",
            "effective_date",
            "is_protected",
            "status",
            "notes",
        )
        widgets: ClassVar[dict] = {
            "title": forms.TextInput(attrs=_control()),
            "organizational_unit": forms.Select(attrs=_select()),
            "classification": forms.Select(attrs=_select()),
            "appointment_type": forms.Select(attrs=_select()),
            "responsibilities": forms.Textarea(attrs=_control({"rows": 3})),
            "required_competencies": forms.Textarea(attrs=_control({"rows": 3})),
            "effective_date": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "status": forms.Select(attrs=_select()),
            "notes": forms.Textarea(attrs=_control({"rows": 2})),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "organizational_unit").queryset = (
            OrganizationUnit.objects.with_parent()
        )


class ReportingLineForm(forms.Form):
    """Set the primary reporting line for a position."""

    supervisor = forms.ModelChoiceField(
        queryset=Position.objects.none(),
        required=False,
        empty_label=_("No supervisor (top of reporting chain)"),
        label=_("Primary supervisor"),
        help_text=_("Select the position this position reports to directly."),
        widget=forms.Select(attrs=_select()),
    )

    def __init__(self, *args, position=None, **kwargs):
        super().__init__(*args, **kwargs)
        if position is not None:
            _model_choice(self, "supervisor").queryset = (
                Position.objects.active().exclude(pk=position.pk)
            )
            self.fields["supervisor"].initial = (
                position.primary_supervisor.pk if position.primary_supervisor else None
            )


class PositionAssignmentForm(forms.ModelForm):
    """Appoint a person to a position."""

    person = forms.ModelChoiceField(
        queryset=User.objects.filter(
            status=AccountStatus.ACTIVE, is_active=True
        ).order_by("email"),
        label=_("Person"),
        empty_label=_("Select a person..."),
        widget=forms.Select(attrs=_select()),
    )

    class Meta:
        model = PositionAssignment
        fields = (
            "person",
            "position",
            "organizational_unit",
            "appointment_date",
            "effective_date",
            "appointment_type",
            "term_start",
            "term_end",
            "renewal_eligible",
            "supporting_document",
            "notes",
        )
        widgets: ClassVar[dict] = {
            "position": forms.Select(attrs=_select()),
            "organizational_unit": forms.Select(attrs=_select()),
            "appointment_date": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "effective_date": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "appointment_type": forms.Select(attrs=_select()),
            "term_start": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "term_end": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "supporting_document": forms.ClearableFileInput(attrs=_control()),
            "notes": forms.Textarea(attrs=_control({"rows": 2})),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "position").queryset = (
            Position.objects.active().select_related("organizational_unit")
        )
        _model_choice(self, "organizational_unit").queryset = (
            OrganizationUnit.objects.with_parent()
        )


class ActingAppointmentForm(forms.ModelForm):
    """Create a temporary acting appointment."""

    class Meta:
        model = ActingAppointment
        fields = (
            "acting_officer",
            "position",
            "original_assignee",
            "effective_from",
            "end_date",
            "reason",
            "approval_authority",
            "supporting_document",
        )
        widgets: ClassVar[dict] = {
            "acting_officer": forms.Select(attrs=_select()),
            "position": forms.Select(attrs=_select()),
            "original_assignee": forms.Select(attrs=_select()),
            "effective_from": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "end_date": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "reason": forms.Textarea(attrs=_control({"rows": 3})),
            "approval_authority": forms.Select(attrs=_select()),
            "supporting_document": forms.ClearableFileInput(attrs=_control()),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "acting_officer").queryset = User.objects.filter(
            status=AccountStatus.ACTIVE, is_active=True
        ).order_by("email")
        _model_choice(self, "position").queryset = (
            Position.objects.active().select_related("organizational_unit")
        )
        _model_choice(self, "original_assignee").queryset = User.objects.filter(
            is_active=True
        ).order_by("email")
        _model_choice(self, "approval_authority").queryset = User.objects.filter(
            is_active=True
        ).order_by("email")
        self.fields["status"] = forms.ChoiceField(
            choices=ActingAppointmentStatus.choices,
            initial=ActingAppointmentStatus.ACTIVE,
            required=False,
            widget=forms.Select(attrs=_select()),
            label=_("Status"),
        )


class VacancyForm(forms.ModelForm):
    """Open or manage a vacancy for a position."""

    class Meta:
        model = Vacancy
        fields = (
            "position",
            "organizational_unit",
            "vacancy_reason",
            "date_vacant",
            "recruitment_status",
            "expected_appointment_date",
            "acting_appointment",
            "notes",
        )
        widgets: ClassVar[dict] = {
            "position": forms.Select(attrs=_select()),
            "organizational_unit": forms.Select(attrs=_select()),
            "vacancy_reason": forms.Textarea(attrs=_control({"rows": 3})),
            "date_vacant": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "recruitment_status": forms.Select(attrs=_select()),
            "expected_appointment_date": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "acting_appointment": forms.Select(attrs=_select()),
            "notes": forms.Textarea(attrs=_control({"rows": 2})),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "position").queryset = (
            Position.objects.active().select_related("organizational_unit")
        )
        _model_choice(self, "organizational_unit").queryset = (
            OrganizationUnit.objects.with_parent()
        )
        _model_choice(self, "acting_appointment").queryset = (
            ActingAppointment.objects.filter(
                status=ActingAppointmentStatus.ACTIVE
            ).select_related("position")
        )
        self.fields["date_vacant"].required = False


class TransferForm(forms.ModelForm):
    """Record a personnel transfer request."""

    class Meta:
        model = TransferRecord
        fields = (
            "person",
            "previous_organizational_unit",
            "previous_position",
            "new_organizational_unit",
            "new_position",
            "effective_date",
            "reason",
            "supporting_document",
        )
        widgets: ClassVar[dict] = {
            "person": forms.Select(attrs=_select()),
            "previous_organizational_unit": forms.Select(attrs=_select()),
            "previous_position": forms.Select(attrs=_select()),
            "new_organizational_unit": forms.Select(attrs=_select()),
            "new_position": forms.Select(attrs=_select()),
            "effective_date": forms.DateInput(
                attrs=_control({"type": "date"}), format="%Y-%m-%d"
            ),
            "reason": forms.Textarea(attrs=_control({"rows": 3})),
            "supporting_document": forms.ClearableFileInput(attrs=_control()),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "person").queryset = User.objects.filter(
            status=AccountStatus.ACTIVE, is_active=True
        ).order_by("email")
        _model_choice(self, "previous_position").queryset = Position.objects.active()
        _model_choice(self, "new_position").queryset = Position.objects.active()
        _model_choice(self, "previous_organizational_unit").queryset = (
            OrganizationUnit.objects.with_parent()
        )
        _model_choice(self, "new_organizational_unit").queryset = (
            OrganizationUnit.objects.with_parent()
        )
