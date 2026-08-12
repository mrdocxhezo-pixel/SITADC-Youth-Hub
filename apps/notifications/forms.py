"""Forms for the Notifications & Announcements module.

Every form includes server-side validation and accessible markup rendered by
the shared ``includes/form_fields.html`` template.
"""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.organizations.models import OrganizationUnit
from apps.rbac.selectors import get_active_roles

from .constants import (
    AnnouncementAudience,
    DeliveryChannel,
    NotificationCategory,
    NotificationPriority,
)
from .models import (
    NotificationPreference,
    NotificationRule,
    NotificationTemplate,
    SystemAnnouncement,
)
from .selectors import template_queryset
from .validators import (
    validate_channels,
    validate_quiet_hours,
    validate_reminder_offsets,
)

BOOTSTRAP_TEXT = "form-control"
BOOTSTRAP_SELECT = "form-select"
BOOTSTRAP_CHECK = "form-check-input"


def _widget(attrs: dict | None = None) -> dict:
    return {"class": BOOTSTRAP_TEXT, **(attrs or {})}


class NotificationTemplateForm(forms.ModelForm):
    """Create or update a notification template."""

    class Meta:
        model = NotificationTemplate
        fields = [
            "code",
            "name",
            "description",
            "category",
            "event_type",
            "channel",
            "subject_template",
            "title_template",
            "message_template",
            "short_message_template",
            "action_label",
            "priority",
            "required_variables",
            "is_active",
            "organization_unit",
        ]
        widgets = {
            "code": forms.TextInput(attrs=_widget()),
            "name": forms.TextInput(attrs=_widget()),
            "description": forms.Textarea(attrs=_widget({"rows": 2})),
            "category": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "event_type": forms.TextInput(attrs=_widget()),
            "channel": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "subject_template": forms.TextInput(attrs=_widget()),
            "title_template": forms.TextInput(attrs=_widget()),
            "message_template": forms.Textarea(attrs=_widget({"rows": 4})),
            "short_message_template": forms.TextInput(attrs=_widget()),
            "action_label": forms.TextInput(attrs=_widget()),
            "priority": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "required_variables": forms.Textarea(attrs=_widget({"rows": 2})),
            "is_active": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "organization_unit": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if "organization_unit" in self.fields:
            self.fields["organization_unit"].queryset = (
                OrganizationUnit.objects.active()
            )
        self.fields["required_variables"].help_text = _(
            "Comma-separated variable names expected by the template."
        )

    def clean_required_variables(self):
        value = self.cleaned_data.get("required_variables")
        if isinstance(value, str):
            value = [v.strip() for v in value.split(",") if v.strip()]
        return value or []


class NotificationRuleForm(forms.ModelForm):
    """Create or update a notification rule."""

    channels = forms.MultipleChoiceField(
        required=False,
        choices=DeliveryChannel.choices,
        widget=forms.CheckboxSelectMultiple(attrs={"class": BOOTSTRAP_CHECK}),
    )

    class Meta:
        model = NotificationRule
        fields = [
            "name",
            "event_type",
            "category",
            "notification_type",
            "priority",
            "template",
            "channels",
            "recipient_user",
            "recipient_role",
            "recipient_type",
            "delay_minutes",
            "reminder_enabled",
            "reminder_offsets",
            "escalation_enabled",
            "escalation_level",
            "escalation_after_hours",
            "digest_eligible",
            "is_active",
            "organization_unit",
            "sort_order",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_widget()),
            "event_type": forms.TextInput(attrs=_widget()),
            "category": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "notification_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "priority": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "template": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "channels": forms.CheckboxSelectMultiple(),
            "recipient_user": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "recipient_role": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "recipient_type": forms.TextInput(attrs=_widget()),
            "delay_minutes": forms.NumberInput(attrs=_widget()),
            "reminder_enabled": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "reminder_offsets": forms.TextInput(attrs=_widget()),
            "escalation_enabled": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "escalation_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "escalation_after_hours": forms.NumberInput(attrs=_widget()),
            "digest_eligible": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "is_active": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "organization_unit": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "sort_order": forms.NumberInput(attrs=_widget()),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if "template" in self.fields:
            self.fields["template"].queryset = template_queryset(user)
            self.fields["template"].required = False
        if "recipient_role" in self.fields:
            self.fields["recipient_role"].queryset = get_active_roles()
            self.fields["recipient_role"].required = False
        if "recipient_user" in self.fields:
            self.fields["recipient_user"].required = False
        if "organization_unit" in self.fields:
            self.fields["organization_unit"].queryset = (
                OrganizationUnit.objects.active()
            )
            self.fields["organization_unit"].required = False
        if "channels" in self.fields:
            self.fields["channels"].queryset = None
            self.fields["channels"].choices = DeliveryChannel.choices
        for name in ("delay_minutes", "escalation_after_hours", "sort_order"):
            self.fields[name].required = False

    def clean_channels(self):
        channels = self.cleaned_data.get("channels")
        validate_channels(channels or [])
        return channels or [DeliveryChannel.IN_APP]

    def clean_delay_minutes(self):
        value = self.cleaned_data.get("delay_minutes")
        return 0 if value is None else value

    def clean_escalation_after_hours(self):
        value = self.cleaned_data.get("escalation_after_hours")
        return 24 if value is None else value

    def clean_sort_order(self):
        value = self.cleaned_data.get("sort_order")
        return 0 if value is None else value

    def clean_reminder_offsets(self):
        value = self.cleaned_data.get("reminder_offsets")
        if isinstance(value, str):
            try:
                value = [int(v.strip()) for v in value.split(",") if v.strip()]
            except ValueError as exc:
                raise ValidationError(
                    _("Reminder offsets must be integers (hours).")
                ) from exc
        validate_reminder_offsets(value or [])
        return value or []


class AnnouncementForm(forms.ModelForm):
    """Create or update an announcement."""

    publish_now = forms.BooleanField(
        label=_("Publish immediately"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
    )

    class Meta:
        model = SystemAnnouncement
        fields = [
            "title",
            "message",
            "announcement_type",
            "audience_type",
            "audience_roles",
            "audience_units",
            "priority",
            "category",
            "publish_at",
            "expires_at",
            "is_dismissible",
            "acknowledgement_required",
            "deep_link",
            "organization_unit",
        ]
        widgets = {
            "title": forms.TextInput(attrs=_widget()),
            "message": forms.Textarea(attrs=_widget({"rows": 4})),
            "announcement_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "audience_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "audience_roles": forms.SelectMultiple(attrs={"class": BOOTSTRAP_SELECT}),
            "audience_units": forms.SelectMultiple(attrs={"class": BOOTSTRAP_SELECT}),
            "priority": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "category": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "publish_at": forms.DateTimeInput(
                attrs=_widget({"type": "datetime-local"}), format="%Y-%m-%dT%H:%M"
            ),
            "expires_at": forms.DateTimeInput(
                attrs=_widget({"type": "datetime-local"}), format="%Y-%m-%dT%H:%M"
            ),
            "is_dismissible": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "acknowledgement_required": forms.CheckboxInput(
                attrs={"class": BOOTSTRAP_CHECK}
            ),
            "deep_link": forms.TextInput(attrs=_widget()),
            "organization_unit": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "publish_at" in self.fields:
            self.fields["publish_at"].required = False
        if "audience_roles" in self.fields:
            self.fields["audience_roles"].queryset = get_active_roles()
            self.fields["audience_roles"].required = False
        if "audience_units" in self.fields:
            self.fields["audience_units"].queryset = OrganizationUnit.objects.active()
            self.fields["audience_units"].required = False
        if "organization_unit" in self.fields:
            self.fields["organization_unit"].queryset = (
                OrganizationUnit.objects.active()
            )
            self.fields["organization_unit"].required = False

    def clean(self):
        cleaned = super().clean()
        audience_type = cleaned.get("audience_type")
        if audience_type in (
            AnnouncementAudience.SPECIFIC_ROLES,
            AnnouncementAudience.DIRECTORATES,
        ) and not cleaned.get("audience_roles"):
            self.add_error("audience_roles", _("Select at least one audience role."))
        if audience_type in (
            AnnouncementAudience.ORGANIZATION_UNITS,
            AnnouncementAudience.REGIONS,
            AnnouncementAudience.DISTRICTS,
        ) and not cleaned.get("audience_units"):
            self.add_error(
                "audience_units", _("Select at least one organization unit.")
            )
        return cleaned


class NotificationPreferenceForm(forms.ModelForm):
    """Per-user notification channel, digest and quiet-hours preferences."""

    class Meta:
        model = NotificationPreference
        fields = [
            "in_app_enabled",
            "email_enabled",
            "sms_enabled",
            "push_enabled",
            "digest_frequency",
            "digest_timezone",
            "digest_channels",
            "quiet_hours_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
            "quiet_hours_policy",
            "timezone",
            "reminder_frequency",
            "marketing_enabled",
        ]
        widgets = {
            "in_app_enabled": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "email_enabled": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "sms_enabled": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "push_enabled": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "digest_frequency": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "digest_timezone": forms.TextInput(attrs=_widget()),
            "digest_channels": forms.CheckboxSelectMultiple(),
            "quiet_hours_enabled": forms.CheckboxInput(
                attrs={"class": BOOTSTRAP_CHECK}
            ),
            "quiet_hours_start": forms.TextInput(
                attrs=_widget({"placeholder": "22:00"})
            ),
            "quiet_hours_end": forms.TextInput(attrs=_widget({"placeholder": "07:00"})),
            "quiet_hours_policy": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "timezone": forms.TextInput(attrs=_widget()),
            "reminder_frequency": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "marketing_enabled": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "digest_channels" in self.fields:
            self.fields["digest_channels"].choices = [
                (DeliveryChannel.EMAIL, "Email"),
                (DeliveryChannel.PUSH, "Push"),
            ]

    def clean_digest_channels(self):
        value = self.cleaned_data.get("digest_channels")
        return value or []

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("quiet_hours_start") or ""
        end = cleaned.get("quiet_hours_end") or ""
        validate_quiet_hours(start, end)
        return cleaned


class NotificationSearchForm(forms.Form):
    """Search and filter notifications in the inbox."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs=_widget({"placeholder": _("Search title, message or source")})
        ),
    )
    category = forms.ChoiceField(
        required=False,
        choices=[("", _("All categories")), *list(NotificationCategory.choices)],
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[("", _("All priorities")), *list(NotificationPriority.choices)],
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )
    read_status = forms.ChoiceField(
        required=False,
        choices=[
            ("", _("All read states")),
            ("UNREAD", _("Unread")),
            ("READ", _("Read")),
        ],
        widget=forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
    )

    def filter(self, queryset):
        q = self.cleaned_data.get("q")
        category = self.cleaned_data.get("category")
        priority = self.cleaned_data.get("priority")
        read_status = self.cleaned_data.get("read_status")
        if q:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(message__icontains=q)
                | Q(source_app__icontains=q)
                | Q(source_object_reference__icontains=q)
            )
        if category:
            queryset = queryset.filter(category=category)
        if priority:
            queryset = queryset.filter(priority=priority)
        if read_status:
            queryset = queryset.filter(read_status=read_status)
        return queryset
