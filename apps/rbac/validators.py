"""
Reusable validation helpers for the RBAC framework.

These validators are shared by forms, services and management commands so
that authorization invariants are enforced consistently everywhere.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .constants import AssignmentStatus
from .models import Role, UserRoleAssignment
from .seed_data import ALL_PERMISSION_CODES


def validate_role_name_available(name: str, exclude_pk=None) -> None:
    """Raise if another non-deleted role already uses this name."""
    queryset = Role.objects.filter(name__iexact=name)
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.exists():
        raise ValidationError(
            _("A role with this name already exists."), code="duplicate_role_name"
        )


def validate_role_slug_available(slug: str, exclude_pk=None) -> None:
    """Raise if another non-deleted role already uses this slug."""
    queryset = Role.objects.filter(slug__iexact=slug)
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.exists():
        raise ValidationError(
            _("A role with this slug already exists."), code="duplicate_role_slug"
        )


def validate_permission_codes(codes: list[str]) -> None:
    """Raise if any requested permission code is not part of the catalogue."""
    invalid = [code for code in codes if code not in ALL_PERMISSION_CODES]
    if invalid:
        raise ValidationError(
            _("Unknown permission(s): %(codes)s")
            % {"codes": ", ".join(sorted(invalid))},
            code="invalid_permission_codes",
        )


def validate_role_usable(role: Role) -> None:
    """Raise if the role cannot currently be assigned (archived or inactive)."""
    if role.is_archived or role.status != "ACTIVE":
        raise ValidationError(
            _("The role %(role)s is not active and cannot be used.")
            % {"role": role.name},
            code="role_not_active",
        )


def validate_assignment_dates(effective_from, expires_at) -> None:
    """Raise if the assignment date range is invalid."""
    if effective_from and expires_at and expires_at <= effective_from:
        raise ValidationError(
            _("The expiry date must be after the effective date."),
            code="invalid_assignment_dates",
        )


def validate_no_active_assignment(user, role, access_scope=None) -> None:
    """Raise if the user already holds the same active assignment."""
    if UserRoleAssignment.objects.filter(
        user=user,
        role=role,
        access_scope=access_scope,
        status=AssignmentStatus.ACTIVE,
    ).exists():
        raise ValidationError(
            _("This role is already assigned to the user in the selected scope."),
            code="duplicate_active_assignment",
        )
