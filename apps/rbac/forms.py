"""Forms for the RBAC framework (role and assignment management)."""

from __future__ import annotations

from typing import ClassVar

from django import forms
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _

from apps.accounts.constants import AccountStatus
from apps.accounts.models import User

from .constants import RoleStatus
from .models import AccessScope, Role, UserRoleAssignment
from .seed_data import PERMISSION_CATEGORIES


def permission_choices() -> list[tuple[str, str]]:
    """Build grouped ``module.action`` permission choices from the catalogue."""
    choices: list[tuple[str, str]] = []
    for category in sorted(PERMISSION_CATEGORIES):
        label, actions = PERMISSION_CATEGORIES[category]
        choices.append((category, f"{label}"))
        for action in actions:
            choices.append(
                (f"{category}.{action}", f"    {action.replace('_', ' ').title()}")
            )
    return choices


def grouped_permission_choices() -> list[tuple[str, list[tuple[str, str]]]]:
    """Build optgroup choices suitable for a grouped select widget."""
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    for category in sorted(PERMISSION_CATEGORIES):
        label, actions = PERMISSION_CATEGORIES[category]
        groups.append(
            (
                label,
                [
                    (f"{category}.{action}", f"{action.replace('_', ' ').title()}")
                    for action in actions
                ],
            )
        )
    return groups


class RoleForm(forms.ModelForm):
    """Create/update a role, including its permission set."""

    permission_codes = forms.MultipleChoiceField(
        choices=grouped_permission_choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Permissions"),
        help_text=_("Select the permission codes granted by this role."),
    )

    grouped_permission_choices: ClassVar[list[tuple[str, list[tuple[str, str]]]]] = (
        grouped_permission_choices()
    )

    class Meta:
        model = Role
        fields = ("name", "description", "priority", "status")
        widgets: ClassVar[dict] = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "priority": forms.NumberInput(attrs={"min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance._state.adding:
            self.fields["permission_codes"].initial = list(
                self.instance.permissions.values_list("codename", flat=True)
            )
        else:
            self.fields["status"].required = False
            self.fields["status"].widget = forms.HiddenInput()
        if self.instance and self.instance.is_system:
            self.fields["status"].disabled = True
            self.fields["status"].help_text = _(
                "System role status is managed through activate/deactivate actions."
            )
        self.fields["name"].label = _("Role name")
        self.fields["priority"].help_text = _("Lower values indicate higher authority.")

    def save(self, commit: bool = True) -> Role:
        role = super().save(commit=False)
        selected = self.cleaned_data.get("permission_codes") or []
        if commit:
            role.save()
            role.permissions.set(Permission.objects.filter(codename__in=selected))
        return role


class RolePermissionForm(forms.Form):
    """Replace the permission set of an existing role."""

    permission_codes = forms.MultipleChoiceField(
        choices=grouped_permission_choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Permissions"),
    )


class RoleCloneForm(forms.Form):
    """Clone an existing role under a new name."""

    new_name = forms.CharField(
        max_length=150,
        label=_("New role name"),
        help_text=_("The cloned role inherits the source role's permissions."),
    )


class UserRoleAssignmentForm(forms.ModelForm):
    """Assign a role (with optional scope and dates) to a user."""

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(
            status=AccountStatus.ACTIVE, is_active=True
        ).order_by("email"),
        label=_("User"),
        empty_label=_("Select a user..."),
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(
            status=RoleStatus.ACTIVE, is_archived=False
        ).order_by("priority", "name"),
        label=_("Role"),
        empty_label=_("Select a role..."),
    )
    access_scope = forms.ModelChoiceField(
        queryset=AccessScope.objects.filter(is_active=True).order_by("level"),
        required=False,
        label=_("Access scope"),
        help_text=_("Leave blank to grant the default (National) scope."),
    )
    is_primary = forms.BooleanField(
        required=False,
        label=_("Primary role"),
        help_text=_("Each user may designate at most one primary active role."),
    )
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label=_("Expires at"),
        help_text=_("Optional expiry date; the assignment auto-expires."),
    )
    effective_from = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label=_("Effective from"),
        help_text=_("Leave blank to start immediately."),
    )

    class Meta:
        model = UserRoleAssignment
        fields = (
            "user",
            "role",
            "access_scope",
            "is_primary",
            "effective_from",
            "expires_at",
            "notes",
        )
        widgets: ClassVar[dict] = {"notes": forms.Textarea(attrs={"rows": 2})}
