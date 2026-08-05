"""
Central authorization engine for the SITADC Youth Hub.

All permission and scope decisions should be made through these helpers so
that views, templates, services and middleware apply identical rules.
"""

from __future__ import annotations

from typing import Any

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from .constants import AssignmentStatus
from .models import AccessScope, Role, UserRoleAssignment
from .seed_data import ALL_PERMISSION_CODES


def get_active_role_assignments(user: Any) -> QuerySet[UserRoleAssignment]:
    """Return the currently active role assignments for a user."""
    now = timezone.now()
    return (
        UserRoleAssignment.objects.filter(
            user=user,
            status=AssignmentStatus.ACTIVE,
            effective_from__lte=now,
        )
        .filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now))
        .select_related("role", "access_scope")
    )


def get_effective_permission_codes(user: Any) -> frozenset[str]:
    """
    Return the union of permission codes granted by the user's active roles
    plus any direct permissions assigned to the user.
    """
    if not user or not user.is_authenticated:
        return frozenset()
    cached = getattr(user, "_rbac_permission_codes", None)
    if cached is not None:
        return cached

    codes: set[str] = set()
    for assignment in get_active_role_assignments(user):
        codes.update(
            assignment.role.permissions.all().values_list("codename", flat=True)
        )
    codes.update(user.user_permissions.values_list("codename", flat=True))

    result = frozenset(codes)
    user._rbac_permission_codes = result
    return result


def clear_permission_cache(user) -> None:
    """
    Invalidate the per-instance permission cache for a user.

    Called by signals whenever assignments or permissions change so that
    subsequent authorization checks reflect the latest state.
    """
    if hasattr(user, "_rbac_permission_codes"):
        del user._rbac_permission_codes


def user_has_permission(user: Any, permission_code: str) -> bool:
    """Whether the user holds the given ``module.action`` permission."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if permission_code not in ALL_PERMISSION_CODES:
        return False
    return permission_code in get_effective_permission_codes(user)


def user_has_all_permissions(user: Any, permission_codes: list[str]) -> bool:
    """Whether the user holds every listed permission (AND semantics)."""
    return all(user_has_permission(user, code) for code in permission_codes)


def user_has_any_permission(user: Any, permission_codes: list[str]) -> bool:
    """Whether the user holds at least one of the listed permissions."""
    return any(user_has_permission(user, code) for code in permission_codes)


def get_roles_for_user(user: Any) -> QuerySet[Role]:
    """Return the distinct roles currently assigned to the user."""
    role_ids = (
        get_active_role_assignments(user).values_list("role_id", flat=True).distinct()
    )
    return Role.objects.filter(id__in=role_ids)


def user_has_role(user: Any, role_slug: str) -> bool:
    """Whether the user currently holds the role identified by ``role_slug``."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return get_active_role_assignments(user).filter(role__slug=role_slug).exists()


def get_effective_scopes_for_user(user: Any) -> list[AccessScope]:
    """
    Return the access scopes granted through the user's active assignments.

    When no scope is explicitly assigned, the user is treated as having the
    default (National) scope.  Phase 08 will refine this behaviour by
    attaching concrete organizational units to each scope.
    """
    if not user or not user.is_authenticated:
        return []
    scopes = list(
        AccessScope.objects.filter(
            role_assignments__user=user,
            role_assignments__status=AssignmentStatus.ACTIVE,
            role_assignments__effective_from__lte=timezone.now(),
        )
        .exclude(role_assignments__expires_at__lte=timezone.now())
        .order_by("level")
        .distinct()
    )
    return scopes or list(
        AccessScope.objects.filter(is_active=True).order_by("level")[:1]
    )


def user_has_scope(user: Any, scope_code: str) -> bool:
    """
    Whether the user's granted scopes cover ``scope_code``.

    A broader scope (lower level) automatically covers every narrower scope.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        required_level = AccessScope.objects.get(code=scope_code).level
    except AccessScope.DoesNotExist:
        return False
    granted_levels = [scope.level for scope in get_effective_scopes_for_user(user)]
    return any(level <= required_level for level in granted_levels)


def can_manage_role(user: Any, role: Role) -> bool:
    """Whether the user may administer the given role."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if role.is_system and not user_has_permission(user, "administration.manage"):
        return False
    return user_has_permission(user, "administration.manage")
