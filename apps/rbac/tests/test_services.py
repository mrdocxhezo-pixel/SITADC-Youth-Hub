import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.rbac.models import Role, RoleHistory
from apps.rbac.services import (
    ActivateRoleService,
    ArchiveRoleService,
    AssignRoleService,
    CloneRoleService,
    CreateRoleService,
    DeactivateRoleService,
    DeleteRoleService,
    RestoreRoleService,
    RevokeRoleService,
    SetRolePermissionsService,
    UpdateRoleService,
)


@pytest.fixture
def admin(db):
    admin = User.objects.create_user(
        email="admin-rbac@example.com",
        username="adminrbac",
        first_name="Admin",
        last_name="RBAC",
        password="TestPassword123!",
    )
    admin.is_superuser = True
    admin.save()
    return admin


def _permission(code: str) -> Permission:
    return Permission.objects.get(codename=code)


@pytest.mark.django_db
def test_create_role_service(admin):
    """Verify CreateRoleService creates a role, group, permissions and history."""
    role = CreateRoleService(user=admin).execute(
        name="Data Analyst",
        description="Analyses program data.",
        priority=30,
        permissions=["reports.view", "meal.view"],
    )
    assert role.slug == "data-analyst"
    assert role.group is not None
    assert set(role.permissions.values_list("codename", flat=True)) == {
        "reports.view",
        "meal.view",
    }
    assert RoleHistory.objects.filter(role=role, action="CREATED").exists()


@pytest.mark.django_db
def test_create_role_service_rejects_duplicate_name(admin):
    """Verify duplicate role names are rejected."""
    CreateRoleService(user=admin).execute(name="Data Analyst")
    with pytest.raises(ValidationError):
        CreateRoleService(user=admin).execute(name="Data Analyst")


@pytest.mark.django_db
def test_update_role_service(admin):
    """Verify UpdateRoleService changes metadata and the group name."""
    role = CreateRoleService(user=admin).execute(name="Analyst")
    updated = UpdateRoleService(user=admin).execute(
        role=role, name="Senior Analyst", description="Senior analyst.", priority=20
    )
    assert updated.name == "Senior Analyst"
    assert updated.slug == "senior-analyst"
    assert updated.group.name == "Senior Analyst"
    assert RoleHistory.objects.filter(role=role, action="UPDATED").exists()


@pytest.mark.django_db
def test_set_role_permissions_service(admin):
    """Verify permission replacement and history."""
    role = CreateRoleService(user=admin).execute(
        name="Permissions Role", permissions=["reports.view"]
    )
    SetRolePermissionsService(user=admin).execute(
        role=role, permissions=["meal.view", "meal.manage"]
    )
    assert set(role.permissions.values_list("codename", flat=True)) == {
        "meal.view",
        "meal.manage",
    }
    # The Django group stays in sync.
    assert set(role.group.permissions.values_list("codename", flat=True)) == {
        "meal.view",
        "meal.manage",
    }
    assert RoleHistory.objects.filter(role=role, action="PERMISSIONS_CHANGED").exists()


@pytest.mark.django_db
def test_archive_restore_services(admin):
    """Verify archive and restore lifecycle."""
    role = CreateRoleService(user=admin).execute(name="Archivable Role")
    ArchiveRoleService(user=admin).execute(role=role)
    assert role.is_archived is True
    assert role.status == "INACTIVE"

    RestoreRoleService(user=admin).execute(role=role)
    role.refresh_from_db()
    assert role.is_archived is False
    assert role.status == "ACTIVE"


@pytest.mark.django_db
def test_system_role_cannot_be_archived(admin):
    """Verify system roles cannot be archived."""
    role = CreateRoleService(user=admin).execute(name="System-ish")
    role.is_system = True
    role.save()
    with pytest.raises(ValidationError):
        ArchiveRoleService(user=admin).execute(role=role)


@pytest.mark.django_db
def test_super_admin_role_cannot_be_deactivated(admin):
    """Verify the Super Administrator role is protected from deactivation."""
    role = Role.objects.get(slug="super-administrator")
    with pytest.raises(ValidationError):
        DeactivateRoleService(user=admin).execute(role=role)


@pytest.mark.django_db
def test_activate_deactivate_services(admin):
    """Verify activate/deactivate lifecycle."""
    role = CreateRoleService(user=admin).execute(name="Toggle Role")
    DeactivateRoleService(user=admin).execute(role=role)
    role.refresh_from_db()
    assert role.status == "INACTIVE"
    ActivateRoleService(user=admin).execute(role=role)
    role.refresh_from_db()
    assert role.status == "ACTIVE"


@pytest.mark.django_db
def test_clone_role_service(admin):
    """Verify CloneRoleService copies metadata and permissions."""
    source = CreateRoleService(user=admin).execute(
        name="Clone Source", permissions=["reports.view"]
    )
    cloned = CloneRoleService(user=admin).execute(
        source_role=source, new_name="Clone Target"
    )
    assert cloned.name == "Clone Target"
    assert cloned.is_system is False
    assert set(cloned.permissions.values_list("codename", flat=True)) == {
        "reports.view"
    }
    assert RoleHistory.objects.filter(role=cloned, action="CLONED").exists()


@pytest.mark.django_db
def test_delete_role_service(admin):
    """Verify soft-delete removes the role and its group."""
    role = CreateRoleService(user=admin).execute(name="Disposable Role")
    role_id = role.pk
    DeleteRoleService(user=admin).execute(role=role)
    assert Role.objects.filter(pk=role_id).count() == 0
    assert Role.objects.deleted().filter(pk=role_id).count() == 1


@pytest.mark.django_db
def test_delete_role_service_blocks_system_roles(admin):
    """Verify system roles cannot be deleted."""
    role = Role.objects.get(slug="super-administrator")
    with pytest.raises(ValidationError):
        DeleteRoleService(user=admin).execute(role=role)


@pytest.mark.django_db
def test_assign_and_revoke_services(admin):
    """Verify assignment and revocation with audit records."""
    user = User.objects.create_user(
        email="target@example.com",
        username="target",
        first_name="Target",
        last_name="User",
    )
    role = CreateRoleService(user=admin).execute(name="Assignee Role")
    assignment = AssignRoleService(user=admin).execute(
        user=user, role=role, is_primary=True, notes="Assigned for testing."
    )
    assert assignment.is_primary is True
    assert assignment.status == "ACTIVE"
    assert RoleHistory.objects.filter(role=role, action="ROLE_ASSIGNED").exists()

    revoked = RevokeRoleService(user=admin).execute(assignment=assignment)
    assert revoked.status == "REVOKED"
    assert RoleHistory.objects.filter(role=role, action="ROLE_REVOKED").exists()


@pytest.mark.django_db
def test_assign_primary_clears_others(admin):
    """Verify only one primary assignment exists per user."""
    user = User.objects.create_user(
        email="primary@example.com",
        username="primary",
        first_name="Primary",
        last_name="User",
    )
    role_a = CreateRoleService(user=admin).execute(name="Role A")
    role_b = CreateRoleService(user=admin).execute(name="Role B")
    first = AssignRoleService(user=admin).execute(
        user=user, role=role_a, is_primary=True
    )
    second = AssignRoleService(user=admin).execute(
        user=user, role=role_b, is_primary=True
    )
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.is_primary is False
    assert second.is_primary is True
