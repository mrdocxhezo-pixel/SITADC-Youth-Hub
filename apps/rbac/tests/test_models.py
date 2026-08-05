from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User
from apps.rbac.models import AccessScope, Role, RoleHistory, UserRoleAssignment


@pytest.mark.django_db
def test_create_role():
    """Verify Role creation with a linked Django group."""
    group = Group.objects.create(name="Test Role")
    role = Role.objects.create(
        name="Test Role",
        slug="test-role",
        group=group,
        priority=50,
        is_system=False,
    )
    assert role.name == "Test Role"
    assert role.status == "ACTIVE"
    assert role.priority == 50
    assert role.is_archived is False
    assert role.group == group
    assert str(role) == "Test Role"


@pytest.mark.django_db
def test_role_archive_and_restore():
    """Verify archive() deactivates and restore() reactivates."""
    role = Role.objects.create(name="Temp Role", slug="temp-role")
    assert role.is_archived is False

    role.archive(archived_by=None)
    assert role.is_archived is True
    assert role.status == "INACTIVE"

    role.restore()
    assert role.is_archived is False
    assert role.status == "ACTIVE"


@pytest.mark.django_db
def test_role_history_is_immutable():
    """Verify RoleHistory cannot be updated or deleted."""
    role = Role.objects.create(name="Audit Role", slug="audit-role")
    history = RoleHistory.objects.create(
        role=role,
        action="CREATED",
        changed_by=None,
        notes="Created.",
    )
    assert history.pk is not None

    with pytest.raises(ValidationError):
        history.notes = "Mutated"
        history.save()

    with pytest.raises(ValidationError):
        history.delete()

    assert RoleHistory.objects.count() == 1


@pytest.mark.django_db
def test_assignment_is_active_now():
    """Verify is_active_now handles dates and expiry."""
    user = User.objects.create_user(
        email="assign@example.com",
        username="assignuser",
        first_name="Assign",
        last_name="User",
    )
    role = Role.objects.create(name="Worker Role", slug="worker-role")
    assignment = UserRoleAssignment.objects.create(
        user=user,
        role=role,
        status="ACTIVE",
        effective_from=timezone.now() - timedelta(days=1),
        expires_at=timezone.now() + timedelta(days=30),
    )
    assert assignment.is_active_now() is True
    assert assignment.is_expired() is False

    assignment.expires_at = timezone.now() - timedelta(days=1)
    assignment.save()
    assert assignment.is_active_now() is False
    assert assignment.is_expired() is True


@pytest.mark.django_db
def test_unique_active_assignment_constraint():
    """Verify a duplicate active assignment is rejected at the DB level."""
    from django.db import IntegrityError

    user = User.objects.create_user(
        email="dup@example.com",
        username="dupuser",
        first_name="Dup",
        last_name="User",
    )
    role = Role.objects.create(name="Dup Role", slug="dup-role")
    scope = AccessScope.objects.create(code="test-scope", name="Test Scope", level=999)
    UserRoleAssignment.objects.create(
        user=user, role=role, access_scope=scope, status="ACTIVE"
    )
    with pytest.raises(IntegrityError):
        UserRoleAssignment.objects.create(
            user=user, role=role, access_scope=scope, status="ACTIVE"
        )


@pytest.mark.django_db
def test_permission_catalogue_linked_to_role():
    """Verify the seeded permission catalogue can be linked to roles."""
    role = Role.objects.create(name="Catalogue Role", slug="catalogue-role")
    permission = Permission.objects.filter(codename__contains=".").first()
    assert permission is not None
    role.permissions.add(permission)
    assert role.permissions.count() == 1


@pytest.mark.django_db
def test_access_scope_model():
    """Verify AccessScope stores its hierarchy level."""
    scope = AccessScope.objects.create(
        code="district-test",
        name="District Test",
        level=31,
        description="Test scope.",
    )
    assert scope.code == "district-test"
    assert scope.level == 31
    assert scope.is_active is True
    assert str(scope) == "District Test"
