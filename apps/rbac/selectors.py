"""
Read-only retrieval helpers for the RBAC framework.

Selectors never modify data; they only fetch and shape it for views,
services and templates.
"""

from __future__ import annotations

from django.contrib.auth.models import Permission
from django.db.models import QuerySet

from apps.accounts.models import User

from .authorization import get_active_role_assignments, get_effective_permission_codes
from .constants import RoleStatus
from .models import (
    AccessScope,
    PermissionCategory,
    Role,
    RoleHistory,
    UserRoleAssignment,
)


def get_roles() -> QuerySet[Role]:
    """Return all non-deleted roles ordered by priority."""
    return Role.objects.select_related("group").order_by("priority", "name")


def get_active_roles() -> QuerySet[Role]:
    """Return active, non-archived, non-deleted roles."""
    return get_roles().filter(status=RoleStatus.ACTIVE, is_archived=False)


def get_role_by_slug(slug: str) -> Role:
    """Retrieve a single role by slug."""
    return Role.objects.get(slug=slug)


def get_role_by_id(role_id) -> Role:
    """Retrieve a single role by primary key."""
    return Role.objects.get(id=role_id)


def get_role_permissions(role: Role) -> QuerySet[Permission]:
    """Return the permissions assigned to a role."""
    return role.permissions.all().order_by("content_type_id", "codename")


def get_permission_by_code(code: str) -> Permission:
    """Retrieve a permission by its ``module.action`` codename."""
    return Permission.objects.get(codename=code)


def get_permission_categories() -> QuerySet[PermissionCategory]:
    """Return all permission categories ordered for display."""
    return PermissionCategory.objects.all().order_by("sort_order", "name")


def get_permissions_by_category(category: PermissionCategory) -> QuerySet[Permission]:
    """Return permissions whose codename belongs to a category."""
    prefix = f"{category.code}."
    return Permission.objects.filter(codename__startswith=prefix).order_by("codename")


def get_roles_for_user(user: User) -> QuerySet[Role]:
    """Return the roles currently active for a user."""
    role_ids = (
        get_active_role_assignments(user).values_list("role_id", flat=True).distinct()
    )
    return Role.objects.filter(id__in=role_ids)


def get_effective_permissions_for_user(user: User) -> list[str]:
    """Return the sorted effective permission codes for a user."""
    return sorted(get_effective_permission_codes(user))


def get_active_role_assignments_for_user(user: User) -> QuerySet[UserRoleAssignment]:
    """Return the active role assignments for a user."""
    return get_active_role_assignments(user)


def get_all_role_assignments_for_user(user: User) -> QuerySet[UserRoleAssignment]:
    """Return every role assignment (including expired/revoked) for a user."""
    return (
        UserRoleAssignment.objects.filter(user=user)
        .select_related("role", "access_scope", "assigned_by")
        .order_by("-created_at")
    )


def get_users_by_role(role: Role) -> QuerySet[User]:
    """Return the distinct active users assigned to a role."""
    user_ids = (
        UserRoleAssignment.objects.filter(role=role, status="ACTIVE")
        .values_list("user_id", flat=True)
        .distinct()
    )
    return User.objects.filter(id__in=user_ids, is_active=True)


def get_active_users() -> QuerySet[User]:
    """Return all active users ordered by email."""
    from apps.accounts.constants import AccountStatus

    return User.objects.filter(status=AccountStatus.ACTIVE, is_active=True).order_by(
        "email"
    )


def get_role_history(role: Role) -> QuerySet[RoleHistory]:
    """Return the audit history for a role, most recent first."""
    return (
        RoleHistory.objects.filter(role=role)
        .select_related("changed_by")
        .order_by("-created_at")
    )


def get_access_scopes() -> QuerySet[AccessScope]:
    """Return all access scopes ordered by hierarchy (broadest first)."""
    return AccessScope.objects.all().order_by("level", "name")


def get_active_access_scopes() -> QuerySet[AccessScope]:
    """Return active access scopes ordered by hierarchy."""
    return get_access_scopes().filter(is_active=True)


def get_scope_by_code(code: str) -> AccessScope:
    """Retrieve a single access scope by code."""
    return AccessScope.objects.get(code=code)


def get_role_assignment_counts() -> dict[str, int]:
    """Return a mapping of role slug to active assignment count."""
    from django.db.models import Count

    rows = (
        UserRoleAssignment.objects.filter(status="ACTIVE")
        .values("role__slug")
        .annotate(count=Count("id"))
    )
    return {row["role__slug"]: row["count"] for row in rows}
