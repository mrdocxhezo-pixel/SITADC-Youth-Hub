from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.utils import timezone

from apps.accounts.constants import AccountStatus
from apps.accounts.models import User
from apps.rbac.authorization import (
    can_manage_role,
    get_effective_permission_codes,
    user_has_permission,
    user_has_role,
    user_has_scope,
)
from apps.rbac.models import AccessScope, Role, UserRoleAssignment


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="rbac@example.com",
        username="rbacuser",
        first_name="RBAC",
        last_name="User",
        password="TestPassword123!",
    )


@pytest.fixture
def manager(db):
    manager = User.objects.create_user(
        email="manager@example.com",
        username="manager",
        first_name="Manager",
        last_name="User",
        password="TestPassword123!",
    )
    manager.status = AccountStatus.ACTIVE
    manager.save()
    return manager


def _permission(code: str) -> Permission:
    return Permission.objects.get(codename=code)


@pytest.mark.django_db
def test_user_has_permission_denies_unknown_codes(user):
    """Verify unknown permission codes always fail (deny by default)."""
    assert user_has_permission(user, "nonexistent.action") is False
    assert user_has_permission(user, "") is False


@pytest.mark.django_db
def test_superuser_short_circuit(user):
    """Verify superusers are granted every permission and role."""
    user.is_superuser = True
    user.save()
    assert user_has_permission(user, "administration.manage") is True
    assert user_has_role(user, "super-administrator") is True
    assert user_has_scope(user, "project") is True
    assert can_manage_role(user, Role()) is True


@pytest.mark.django_db
def test_effective_permissions_from_role(user):
    """Verify permission codes are inherited from an active role."""
    role = Role.objects.create(name="Reporter", slug="reporter")
    role.permissions.set([_permission("reports.view"), _permission("reports.submit")])
    UserRoleAssignment.objects.create(user=user, role=role, status="ACTIVE")

    codes = get_effective_permission_codes(user)
    assert "reports.view" in codes
    assert "reports.submit" in codes
    assert "reports.manage" not in codes
    assert user_has_permission(user, "reports.view") is True


@pytest.mark.django_db
def test_expired_assignment_revokes_permissions(user):
    """Verify an expired assignment no longer grants permissions."""
    role = Role.objects.create(name="Reporter", slug="reporter")
    role.permissions.set([_permission("reports.view")])
    UserRoleAssignment.objects.create(
        user=user,
        role=role,
        status="ACTIVE",
        effective_from=timezone.now() - timedelta(days=10),
        expires_at=timezone.now() - timedelta(days=1),
    )
    assert user_has_permission(user, "reports.view") is False


@pytest.mark.django_db
def test_revoked_assignment_removes_permissions(user):
    """Verify a revoked assignment no longer grants permissions."""
    role = Role.objects.create(name="Reporter", slug="reporter")
    role.permissions.set([_permission("reports.view")])
    assignment = UserRoleAssignment.objects.create(
        user=user, role=role, status="ACTIVE"
    )
    assert user_has_permission(user, "reports.view") is True
    assignment.status = "REVOKED"
    assignment.save()
    assert user_has_permission(user, "reports.view") is False


@pytest.mark.django_db
def test_user_has_role(user):
    """Verify user_has_role reflects active assignments."""
    role = Role.objects.create(name="Coordinator", slug="coordinator")
    assert user_has_role(user, "coordinator") is False
    UserRoleAssignment.objects.create(user=user, role=role, status="ACTIVE")
    assert user_has_role(user, "coordinator") is True


@pytest.mark.django_db
def test_scope_hierarchy(user):
    """Verify broader scopes cover narrower ones."""
    national = AccessScope.objects.get(code="national")
    district = AccessScope.objects.get(code="district")

    role = Role.objects.create(name="Scoped", slug="scoped")
    UserRoleAssignment.objects.create(
        user=user, role=role, status="ACTIVE", access_scope=national
    )
    # National (level 10) covers district (30) and project (70).
    assert user_has_scope(user, "district") is True
    assert user_has_scope(user, "project") is True
    # It cannot cover a hypothetical broader scope.
    assert user_has_scope(user, "national") is True

    user2 = User.objects.create_user(
        email="scoped@example.com",
        username="scopeduser",
        first_name="Scoped",
        last_name="User",
    )
    UserRoleAssignment.objects.create(
        user=user2, role=role, status="ACTIVE", access_scope=district
    )
    # District (30) covers project (70) but not national (10).
    assert user_has_scope(user2, "project") is True
    assert user_has_scope(user2, "national") is False


@pytest.mark.django_db
def test_anonymous_user_is_denied():
    """Verify unauthenticated users are denied everywhere."""
    from django.contrib.auth.models import AnonymousUser

    anonymous = AnonymousUser()
    assert user_has_permission(anonymous, "administration.manage") is False
    assert user_has_role(anonymous, "super-administrator") is False
    assert user_has_scope(anonymous, "national") is False
    assert get_effective_permission_codes(anonymous) == frozenset()


@pytest.mark.django_db
def test_can_manage_role_requires_admin_permission(manager):
    """Verify can_manage_role requires administration.manage for system roles."""
    system_role = Role.objects.create(
        name="System Role", slug="system-role", is_system=True
    )
    # Manager has no administration.manage permission -> cannot manage.
    assert can_manage_role(manager, system_role) is False

    manager.user_permissions.set([_permission("administration.manage")])
    manager.is_active = True
    manager.save()
    manager.refresh_from_db()
    assert can_manage_role(manager, system_role) is True
