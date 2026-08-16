"""Forms for the Calendar & Meetings module.

Every form includes server-side validation and accessible markup rendered by
the shared ``includes/form_fields.html`` template.
"""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .constants import ConfidentialityLevel, QuorumType
from .models import (
    AgendaItem,
    Calendar,
    CalendarEvent,
    CalendarShare,
    Meeting,
    MeetingActionItem,
    MeetingAgenda,
    MeetingDecision,
    MeetingDocument,
    MeetingMinutes,
    MeetingParticipant,
    MeetingTemplate,
    MeetingVenue,
)
from .selectors import access_scope_queryset, organization_unit_queryset, user_queryset
from .validators import validate_recurrence_rule, validate_time_range

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


def _field_choices(model, field_name: str) -> list:
    choices = model._meta.get_field(field_name).choices
    return list(choices) if choices is not None else []


def _confidentiality_widget(form) -> None:
    if form.instance.is_confidential:
        form.fields["confidentiality_level"].initial = ConfidentialityLevel.CONFIDENTIAL


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = [
            "name",
            "calendar_type",
            "description",
            "visibility",
            "organization_unit",
            "access_scope",
            "default_timezone",
            "color",
            "is_default",
            "is_confidential",
            "confidentiality_level",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_widget()),
            "calendar_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "visibility": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "organization_unit": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "access_scope": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "default_timezone": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "color": forms.TextInput(attrs=_widget({"type": "color"})),
            "is_default": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "is_confidential": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "confidentiality_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "is_active": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            _set_queryset(self, "organization_unit", organization_unit_queryset(user))
            _set_queryset(self, "access_scope", access_scope_queryset(user))
        _confidentiality_widget(self)
        for field_name in (
            "organization_unit",
            "access_scope",
            "default_timezone",
            "color",
            "is_default",
            "is_confidential",
            "confidentiality_level",
            "is_active",
        ):
            self.fields[field_name].required = False


class CalendarShareForm(forms.ModelForm):
    class Meta:
        model = CalendarShare
        fields = [
            "user",
            "organization_unit",
            "access_scope",
            "permission_level",
            "expires_at",
        ]
        widgets = {
            "user": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "organization_unit": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "access_scope": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "permission_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "expires_at": forms.DateTimeInput(
                attrs=_widget({"type": "datetime-local"})
            ),
        }

    def __init__(self, *args, calendar=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.calendar = calendar
        if user is not None:
            _set_queryset(self, "user", user_queryset(user))
            _set_queryset(self, "organization_unit", organization_unit_queryset(user))
        for field_name in ("organization_unit", "access_scope"):
            self.fields[field_name].required = False

    def clean(self) -> None:
        cleaned = super().clean()
        if not any(
            (
                cleaned.get("user"),
                cleaned.get("organization_unit"),
                cleaned.get("access_scope"),
            )
        ):
            raise ValidationError(
                _("Choose a user, unit, or access scope to share with.")
            )
        return cleaned


class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = [
            "calendar",
            "event_type",
            "title",
            "description",
            "start_at",
            "end_at",
            "all_day",
            "timezone",
            "venue",
            "online_meeting_link",
            "location_details",
            "host",
            "organizer",
            "program",
            "project",
            "organization_unit",
            "access_scope",
            "priority",
            "is_confidential",
            "confidentiality_level",
            "recurrence_rule",
            "is_recurring",
            "maximum_attendance",
            "registration_required",
            "approval_required",
        ]
        widgets = {
            "calendar": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "event_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "title": forms.TextInput(attrs=_widget()),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "start_at": forms.DateTimeInput(attrs=_widget({"type": "datetime-local"})),
            "end_at": forms.DateTimeInput(attrs=_widget({"type": "datetime-local"})),
            "all_day": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "timezone": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "venue": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "online_meeting_link": forms.URLInput(attrs=_widget()),
            "location_details": forms.TextInput(attrs=_widget()),
            "host": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "organizer": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "program": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "project": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "organization_unit": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "access_scope": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "priority": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "is_confidential": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "confidentiality_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "recurrence_rule": forms.Textarea(
                attrs=_widget(
                    {
                        "rows": 3,
                        "placeholder": (
                            '{"frequency": "weekly", "weekdays": ["MO", "WE"]}'
                        ),
                    }
                )
            ),
            "is_recurring": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "maximum_attendance": forms.NumberInput(attrs=_widget()),
            "registration_required": forms.CheckboxInput(
                attrs={"class": BOOTSTRAP_CHECK}
            ),
            "approval_required": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            from .selectors import (
                calendar_queryset,
                program_queryset,
                project_queryset,
                user_queryset,
                venue_queryset,
            )

            _set_queryset(self, "calendar", calendar_queryset(user))
            _set_queryset(self, "venue", venue_queryset(user))
            _set_queryset(self, "host", user_queryset(user))
            _set_queryset(self, "organizer", user_queryset(user))
            _set_queryset(self, "program", program_queryset(user))
            _set_queryset(self, "project", project_queryset(user))
            _confidentiality_widget(self)
        for field_name in (
            "calendar",
            "timezone",
            "priority",
            "confidentiality_level",
            "host",
            "organizer",
            "program",
            "project",
            "venue",
            "organization_unit",
            "access_scope",
        ):
            self.fields[field_name].required = False

    def clean(self) -> None:
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")
        if start_at and end_at:
            try:
                validate_time_range(start_at, end_at)
            except ValidationError as exc:
                self.add_error("end_at", exc)
        rule = cleaned.get("recurrence_rule")
        if rule:
            validate_recurrence_rule(rule)
        return cleaned


class MeetingVenueForm(forms.ModelForm):
    accessibility_features = forms.CharField(
        required=False,
        label=_("Accessibility features"),
        widget=forms.TextInput(
            attrs=_widget({"placeholder": _("Comma-separated list")})
        ),
    )
    equipment = forms.CharField(
        required=False,
        label=_("Equipment"),
        widget=forms.TextInput(
            attrs=_widget({"placeholder": _("Comma-separated list")})
        ),
    )

    class Meta:
        model = MeetingVenue
        fields = [
            "name",
            "venue_type",
            "description",
            "address",
            "location_details",
            "capacity",
            "accessibility_features",
            "equipment",
            "contact_person",
            "contact_phone",
            "contact_email",
            "organization_unit",
            "access_scope",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_widget()),
            "venue_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "address": forms.TextInput(attrs=_widget()),
            "location_details": forms.TextInput(attrs=_widget()),
            "capacity": forms.NumberInput(attrs=_widget()),
            "contact_person": forms.TextInput(attrs=_widget()),
            "contact_phone": forms.TextInput(attrs=_widget()),
            "contact_email": forms.EmailInput(attrs=_widget()),
            "organization_unit": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "access_scope": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "is_active": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            _set_queryset(self, "organization_unit", organization_unit_queryset(user))
            _set_queryset(self, "access_scope", access_scope_queryset(user))

    def clean_accessibility_features(self):
        return self._split_list(self.cleaned_data.get("accessibility_features"))

    def clean_equipment(self):
        return self._split_list(self.cleaned_data.get("equipment"))

    @staticmethod
    def _split_list(value):
        if not value:
            return []
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]


class MeetingTemplateForm(forms.ModelForm):
    class Meta:
        model = MeetingTemplate
        fields = [
            "name",
            "code",
            "description",
            "meeting_type",
            "default_title",
            "default_purpose",
            "default_objectives",
            "standard_duration_minutes",
            "default_confidentiality",
            "default_quorum_type",
            "default_quorum_value",
            "quorum_required_roles",
            "default_participant_roles",
            "agenda_template",
            "minutes_template",
            "decision_requirements",
            "action_requirements",
            "recurrence_defaults",
            "approval_required",
            "default_reminders",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_widget()),
            "code": forms.TextInput(attrs=_widget()),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "meeting_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "default_title": forms.TextInput(attrs=_widget()),
            "default_purpose": forms.Textarea(attrs=_widget({"rows": 3})),
            "default_objectives": forms.Textarea(
                attrs=_widget({"rows": 3, "placeholder": _("JSON array")})
            ),
            "standard_duration_minutes": forms.NumberInput(attrs=_widget()),
            "default_confidentiality": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "default_quorum_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "default_quorum_value": forms.NumberInput(attrs=_widget()),
            "quorum_required_roles": forms.Textarea(
                attrs=_widget({"rows": 2, "placeholder": _("JSON array")})
            ),
            "default_participant_roles": forms.Textarea(
                attrs=_widget({"rows": 2, "placeholder": _("JSON array")})
            ),
            "agenda_template": forms.Textarea(
                attrs=_widget({"rows": 4, "placeholder": _("JSON array")})
            ),
            "minutes_template": forms.Textarea(
                attrs=_widget({"rows": 4, "placeholder": _("JSON array")})
            ),
            "decision_requirements": forms.Textarea(
                attrs=_widget({"rows": 2, "placeholder": _("JSON object")})
            ),
            "action_requirements": forms.Textarea(
                attrs=_widget({"rows": 2, "placeholder": _("JSON object")})
            ),
            "recurrence_defaults": forms.Textarea(
                attrs=_widget({"rows": 2, "placeholder": _("JSON object")})
            ),
            "approval_required": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "default_reminders": forms.Textarea(
                attrs=_widget({"rows": 2, "placeholder": _("JSON array")})
            ),
            "is_active": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }

    def clean_default_quorum_value(self):
        value = self.cleaned_data.get("default_quorum_value")
        if (
            self.cleaned_data.get("default_quorum_type") == QuorumType.FIXED_NUMBER
            and value is None
        ):
            raise ValidationError(_("A fixed quorum value is required."))
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in (
            "default_confidentiality",
            "default_quorum_type",
            "standard_duration_minutes",
        ):
            self.fields[field_name].required = False


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = [
            "meeting_type",
            "template",
            "title",
            "purpose",
            "objectives",
            "start_at",
            "end_at",
            "timezone",
            "mode",
            "venue",
            "venue_reservation_status",
            "virtual_provider",
            "online_meeting_link",
            "meeting_id",
            "meeting_passcode",
            "virtual_consent_required",
            "recording_allowed",
            "organizer",
            "chairperson",
            "secretary",
            "minute_taker",
            "facilitator",
            "program",
            "project",
            "organization_unit",
            "access_scope",
            "confidentiality_level",
            "is_confidential",
            "publication_status",
            "expected_attendees",
            "required_attendees",
            "quorum_type",
            "quorum_value",
            "quorum_required_roles",
            "notes",
        ]
        widgets = {
            "meeting_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "template": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "title": forms.TextInput(attrs=_widget()),
            "purpose": forms.Textarea(attrs=_widget({"rows": 3})),
            "objectives": forms.Textarea(
                attrs=_widget({"rows": 2, "placeholder": _("JSON array")})
            ),
            "start_at": forms.DateTimeInput(attrs=_widget({"type": "datetime-local"})),
            "end_at": forms.DateTimeInput(attrs=_widget({"type": "datetime-local"})),
            "timezone": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "mode": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "venue": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "venue_reservation_status": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "virtual_provider": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "online_meeting_link": forms.URLInput(attrs=_widget()),
            "meeting_id": forms.TextInput(attrs=_widget()),
            "meeting_passcode": forms.TextInput(attrs=_widget()),
            "virtual_consent_required": forms.CheckboxInput(
                attrs={"class": BOOTSTRAP_CHECK}
            ),
            "recording_allowed": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "organizer": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "chairperson": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "secretary": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "minute_taker": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "facilitator": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "program": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "project": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "organization_unit": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "access_scope": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "confidentiality_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "is_confidential": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "publication_status": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "expected_attendees": forms.NumberInput(attrs=_widget()),
            "required_attendees": forms.NumberInput(attrs=_widget()),
            "quorum_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "quorum_value": forms.NumberInput(attrs=_widget()),
            "quorum_required_roles": forms.Textarea(
                attrs=_widget({"rows": 2, "placeholder": _("JSON array")})
            ),
            "notes": forms.Textarea(attrs=_widget({"rows": 3})),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            from .selectors import (
                program_queryset,
                project_queryset,
                template_queryset,
                user_queryset,
                venue_queryset,
            )

            _set_queryset(self, "venue", venue_queryset(user))
            _set_queryset(self, "template", template_queryset(user))
            _set_queryset(self, "organizer", user_queryset(user))
            _set_queryset(self, "chairperson", user_queryset(user))
            _set_queryset(self, "secretary", user_queryset(user))
            _set_queryset(self, "minute_taker", user_queryset(user))
            _set_queryset(self, "facilitator", user_queryset(user))
            _set_queryset(self, "program", program_queryset(user))
            _set_queryset(self, "project", project_queryset(user))
            _confidentiality_widget(self)
        for field_name in (
            "template",
            "venue",
            "organizer",
            "chairperson",
            "secretary",
            "minute_taker",
            "facilitator",
            "program",
            "project",
            "organization_unit",
            "access_scope",
            "quorum_value",
            "timezone",
            "mode",
            "venue_reservation_status",
            "confidentiality_level",
            "publication_status",
            "expected_attendees",
            "required_attendees",
            "quorum_type",
        ):
            self.fields[field_name].required = False

    def clean(self) -> None:
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")
        if start_at and end_at:
            try:
                validate_time_range(start_at, end_at)
            except ValidationError as exc:
                self.add_error("end_at", exc)
        return cleaned


class MeetingParticipantForm(forms.ModelForm):
    class Meta:
        model = MeetingParticipant
        fields = [
            "participant_type",
            "user",
            "name_snapshot",
            "email_snapshot",
            "phone_snapshot",
            "organization",
            "role_in_meeting",
            "is_required",
            "special_requirements",
            "accessibility_accommodation",
        ]
        widgets = {
            "participant_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "user": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "name_snapshot": forms.TextInput(attrs=_widget()),
            "email_snapshot": forms.EmailInput(attrs=_widget()),
            "phone_snapshot": forms.TextInput(attrs=_widget()),
            "organization": forms.TextInput(attrs=_widget()),
            "role_in_meeting": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "is_required": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "special_requirements": forms.Textarea(attrs=_widget({"rows": 2})),
            "accessibility_accommodation": forms.Textarea(attrs=_widget({"rows": 2})),
        }

    def __init__(self, *args, user=None, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting = meeting
        if user is not None:
            from .selectors import user_queryset

            _set_queryset(self, "user", user_queryset(user))

    def clean(self) -> None:
        cleaned = super().clean()
        if not any(
            (
                cleaned.get("user"),
                cleaned.get("name_snapshot"),
                cleaned.get("email_snapshot"),
            )
        ):
            raise ValidationError(
                _("Provide a user, name, or email address for the participant.")
            )
        return cleaned


class MeetingAgendaForm(forms.ModelForm):
    class Meta:
        model = MeetingAgenda
        fields = ["title", "confidentiality_level", "change_summary"]
        widgets = {
            "title": forms.TextInput(attrs=_widget()),
            "confidentiality_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "change_summary": forms.Textarea(attrs=_widget({"rows": 2})),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user


class AgendaItemForm(forms.ModelForm):
    class Meta:
        model = AgendaItem
        fields = [
            "item_number",
            "display_order",
            "title",
            "description",
            "item_type",
            "presenter",
            "time_allocation_minutes",
            "start_time",
            "end_time",
            "confidentiality_level",
            "decision_required",
            "discussion_required",
            "information_only",
            "related_document",
        ]
        widgets = {
            "item_number": forms.NumberInput(attrs=_widget()),
            "display_order": forms.NumberInput(attrs=_widget()),
            "title": forms.TextInput(attrs=_widget()),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "item_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "presenter": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "time_allocation_minutes": forms.NumberInput(attrs=_widget()),
            "start_time": forms.TimeInput(attrs=_widget({"type": "time"})),
            "end_time": forms.TimeInput(attrs=_widget({"type": "time"})),
            "confidentiality_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "decision_required": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "discussion_required": forms.CheckboxInput(
                attrs={"class": BOOTSTRAP_CHECK}
            ),
            "information_only": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "related_document": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
        }

    def __init__(self, *args, user=None, agenda=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.agenda = agenda
        if user is not None:
            from .selectors import presenter_queryset, related_document_queryset

            _set_queryset(self, "presenter", presenter_queryset(user))
            _set_queryset(self, "related_document", related_document_queryset(user))
        for field_name in (
            "presenter",
            "related_document",
            "start_time",
            "end_time",
            "confidentiality_level",
        ):
            self.fields[field_name].required = False

    def clean(self) -> None:
        cleaned = super().clean()
        start_time = cleaned.get("start_time")
        end_time = cleaned.get("end_time")
        if start_time and end_time and end_time <= start_time:
            raise ValidationError(_("End time must be after start time."))
        return cleaned


class MeetingMinutesForm(forms.ModelForm):
    class Meta:
        model = MeetingMinutes
        fields = [
            "title",
            "summary",
            "opening",
            "closing",
            "quorum_status",
            "publication_status",
            "confidentiality_level",
            "change_summary",
        ]
        widgets = {
            "title": forms.TextInput(attrs=_widget()),
            "summary": forms.Textarea(attrs=_widget({"rows": 3})),
            "opening": forms.Textarea(attrs=_widget({"rows": 3})),
            "closing": forms.Textarea(attrs=_widget({"rows": 3})),
            "quorum_status": forms.TextInput(attrs=_widget()),
            "publication_status": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "confidentiality_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "change_summary": forms.Textarea(attrs=_widget({"rows": 2})),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        for field_name in ("publication_status", "confidentiality_level"):
            self.fields[field_name].required = False


class MeetingDecisionForm(forms.ModelForm):
    class Meta:
        model = MeetingDecision
        fields = [
            "agenda_item",
            "decision_text",
            "decision_type",
            "decision_date",
            "proposed_by",
            "seconded_by",
            "voting_method",
            "responsible_officer",
            "effective_date",
            "review_date",
            "is_confidential",
            "confidentiality_level",
            "supporting_document",
        ]
        widgets = {
            "agenda_item": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "decision_text": forms.Textarea(attrs=_widget({"rows": 4})),
            "decision_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "decision_date": forms.DateInput(attrs=_widget({"type": "date"})),
            "proposed_by": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "seconded_by": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "voting_method": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "responsible_officer": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "effective_date": forms.DateInput(attrs=_widget({"type": "date"})),
            "review_date": forms.DateInput(attrs=_widget({"type": "date"})),
            "is_confidential": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "confidentiality_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "supporting_document": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
        }

    def __init__(self, *args, meeting=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting = meeting
        if user is not None:
            from .selectors import (
                agenda_queryset_for_meeting,
                related_document_queryset,
                user_queryset,
            )

            _set_queryset(
                self, "agenda_item", agenda_queryset_for_meeting(user, meeting)
            )
            _set_queryset(self, "proposed_by", user_queryset(user))
            _set_queryset(self, "seconded_by", user_queryset(user))
            _set_queryset(self, "responsible_officer", user_queryset(user))
            _set_queryset(self, "supporting_document", related_document_queryset(user))
            _confidentiality_widget(self)
        for field_name in (
            "agenda_item",
            "proposed_by",
            "seconded_by",
            "responsible_officer",
            "effective_date",
            "review_date",
            "supporting_document",
            "voting_method",
            "confidentiality_level",
        ):
            self.fields[field_name].required = False


class MeetingActionItemForm(forms.ModelForm):
    supporting_team = forms.CharField(
        required=False,
        label=_("Supporting team"),
        widget=forms.TextInput(
            attrs=_widget({"placeholder": _("Comma-separated emails")})
        ),
    )

    class Meta:
        model = MeetingActionItem
        fields = [
            "agenda_item",
            "decision",
            "description",
            "owner",
            "supporting_team",
            "start_date",
            "due_date",
            "priority",
            "progress_percentage",
            "evidence",
        ]
        widgets = {
            "agenda_item": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "decision": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "description": forms.Textarea(attrs=_widget({"rows": 3})),
            "owner": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "start_date": forms.DateInput(attrs=_widget({"type": "date"})),
            "due_date": forms.DateInput(attrs=_widget({"type": "date"})),
            "priority": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "progress_percentage": forms.NumberInput(attrs=_widget()),
            "evidence": forms.Textarea(attrs=_widget({"rows": 2})),
        }

    def __init__(self, *args, meeting=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting = meeting
        if user is not None:
            from .selectors import (
                agenda_queryset_for_meeting,
                decision_queryset_for_meeting,
                user_queryset,
            )

            _set_queryset(
                self, "agenda_item", agenda_queryset_for_meeting(user, meeting)
            )
            _set_queryset(
                self, "decision", decision_queryset_for_meeting(user, meeting)
            )
            _set_queryset(self, "owner", user_queryset(user))
        for field_name in (
            "agenda_item",
            "decision",
            "owner",
            "start_date",
            "due_date",
            "priority",
            "progress_percentage",
        ):
            self.fields[field_name].required = False

    def clean_progress_percentage(self):
        value = self.cleaned_data.get("progress_percentage")
        if value is not None and not 0 <= value <= 100:
            raise ValidationError(_("Progress must be between 0 and 100."))
        return value

    def clean_supporting_team(self):
        value = self.cleaned_data.get("supporting_team")
        if not value:
            return []
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]


class MeetingDocumentForm(forms.ModelForm):
    class Meta:
        model = MeetingDocument
        fields = ["document", "document_type", "is_public_to_participants", "notes"]
        widgets = {
            "document": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "document_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "is_public_to_participants": forms.CheckboxInput(
                attrs={"class": BOOTSTRAP_CHECK}
            ),
            "notes": forms.Textarea(attrs=_widget({"rows": 2})),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            from .selectors import document_queryset

            _set_queryset(self, "document", document_queryset(user))


class MeetingSearchForm(forms.Form):
    """Combined search and filter form for meetings."""

    q = forms.CharField(
        required=False,
        label=_("Search"),
        widget=forms.TextInput(
            attrs=_widget({"placeholder": _("Title, reference, or keyword")})
        ),
    )
    meeting_type = forms.ChoiceField(
        required=False,
        label=_("Meeting type"),
        choices=[("", _("All types")), *_field_choices(Meeting, "meeting_type")],
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )
    status = forms.ChoiceField(
        required=False,
        label=_("Status"),
        choices=[("", _("All statuses")), *_field_choices(Meeting, "status")],
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )
    confidentiality = forms.ChoiceField(
        required=False,
        label=_("Confidentiality"),
        choices=[
            ("", _("All levels")),
            *_field_choices(Meeting, "confidentiality_level"),
        ],
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )
    start_after = forms.DateField(
        required=False,
        label=_("Start after"),
        widget=forms.DateInput(attrs=_widget({"type": "date"})),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def apply_filters(self, queryset):
        data = self.cleaned_data
        if data.get("q"):
            queryset = queryset.filter(
                Q(title__icontains=data["q"]) | Q(reference__icontains=data["q"])
            )
        if data.get("meeting_type"):
            queryset = queryset.filter(meeting_type=data["meeting_type"])
        if data.get("status"):
            queryset = queryset.filter(status=data["status"])
        if data.get("confidentiality"):
            queryset = queryset.filter(confidentiality_level=data["confidentiality"])
        if data.get("start_after"):
            queryset = queryset.filter(start_at__date__gte=data["start_after"])
        return queryset
