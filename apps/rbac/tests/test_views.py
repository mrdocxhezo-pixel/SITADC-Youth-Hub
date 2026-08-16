import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from apps.accounts.models import User
from apps.rbac.models import Role, UserRoleAssignment


@pytest.fixture
def admin(db):
    admin = User.objects.create_user(
        email="admin-views@example.com",
        username="adminviews",
        first_name="Admin",
        last_name="Views",
        password="TestPassword123!",
    )
    admin.is_superuser = True
    admin.save()
    return admin


@pytest.fixture
def plain_user(db):
    user = User.objects.create_user(
        email="plain@example.com",
        username="plain",
        first_name="Plain",
        last_name="User",
        password="TestPassword123!",
    )
    return user


def _permission(code: str) -> Permission:
    return Permission.objects.get(codename=code)


@pytest.mark.django_db
def test_rbac_pages_require_login(client, db):
    """Verify unauthenticated users are redirected to login."""
    for url_name in ["rbac_index", "role_list", "permission_list", "access_scope_list"]:
        response = client.get(reverse(f"rbac:{url_name}"))
        assert response.status_code in (302, 403)
        if response.status_code == 302:
            assert "/accounts/login" in response.url


@pytest.mark.django_db
def test_role_list_renders_for_admin(client, admin):
    """Verify the role list page renders for an admin."""
    client.force_login(admin)
    response = client.get(reverse("rbac:role_list"))
    assert response.status_code == 200
    assert b"Roles" in response.content


@pytest.mark.django_db
def test_role_create_flow(client, admin):
    """Verify a full create-role POST flow."""
    client.force_login(admin)
    response = client.post(
        reverse("rbac:role_create"),
        {
            "name": "Field Officer",
            "description": "Runs field activities.",
            "priority": 60,
            "permission_codes": ["programmes.view", "projects.view"],
        },
    )
    assert response.status_code == 302
    role = Role.objects.get(slug="field-officer")
    assert role.name == "Field Officer"
    assert set(role.permissions.values_list("codename", flat=True)) == {
        "programmes.view",
        "projects.view",
    }


@pytest.mark.django_db
def test_role_detail_renders(client, admin):
    """Verify the role detail page renders seeded role data."""
    client.force_login(admin)
    role = Role.objects.get(slug="super-administrator")
    response = client.get(reverse("rbac:role_detail", kwargs={"slug": role.slug}))
    assert response.status_code == 200
    assert role.name.encode() in response.content


@pytest.mark.django_db
def test_permission_page_renders(client, admin):
    """Verify the permission catalogue page renders."""
    client.force_login(admin)
    response = client.get(reverse("rbac:permission_list"))
    assert response.status_code == 200
    assert b"Permission Catalogue" in response.content


@pytest.mark.django_db
def test_access_scope_page_renders(client, admin):
    """Verify the access scopes page renders."""
    client.force_login(admin)
    response = client.get(reverse("rbac:access_scope_list"))
    assert response.status_code == 200
    assert b"Access Scopes" in response.content


@pytest.mark.django_db
def test_access_denied_page_status(client, admin):
    """Verify the access-denied page returns 403."""
    client.force_login(admin)
    response = client.get(reverse("rbac:access_denied"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthorized_user_gets_403(client, plain_user):
    """Verify a user without permission receives 403 (not the page)."""
    client.force_login(plain_user)
    response = client.get(reverse("rbac:role_list"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_assign_role_flow(client, admin):
    """Verify the role-assignment POST flow works."""
    from apps.accounts.constants import AccountStatus

    client.force_login(admin)
    user = User.objects.create_user(
        email="assignee@example.com",
        username="assignee",
        first_name="Assignee",
        last_name="User",
    )
    user.status = AccountStatus.ACTIVE
    user.save()
    role = Role.objects.create(name="Assistant", slug="assistant")
    response = client.post(
        reverse("rbac:role_assignment_create", kwargs={"slug": role.slug}),
        {"user": str(user.pk), "role": str(role.pk), "is_primary": "on"},
    )
    assert response.status_code == 302
    assert UserRoleAssignment.objects.filter(user=user, role=role).exists()


@pytest.mark.django_db
def test_revoke_assignment_flow(client, admin):
    """Verify the revoke-assignment POST flow works."""
    client.force_login(admin)
    user = User.objects.create_user(
        email="revokee@example.com",
        username="revokee",
        first_name="Revokee",
        last_name="User",
    )
    role = Role.objects.create(name="Temporary", slug="temporary")
    assignment = UserRoleAssignment.objects.create(
        user=user, role=role, status="ACTIVE"
    )
    response = client.post(
        reverse("rbac:role_assignment_revoke", kwargs={"assignment_id": assignment.pk})
    )
    assert response.status_code == 302
    assignment.refresh_from_db()
    assert assignment.status == "REVOKED"


@pytest.mark.django_db
def test_role_archive_post(client, admin):
    """Verify the archive POST action redirects and archives."""
    client.force_login(admin)
    role = Role.objects.create(name="Expendable", slug="expendable")
    response = client.post(reverse("rbac:role_archive", kwargs={"slug": role.slug}))
    assert response.status_code == 302
    role.refresh_from_db()
    assert role.is_archived is True


@pytest.mark.django_db
def test_role_history_page_renders(client, admin):
    """Verify the role history page renders."""
    client.force_login(admin)
    role = Role.objects.get(slug="super-administrator")
    response = client.get(reverse("rbac:role_history", kwargs={"slug": role.slug}))
    assert response.status_code == 200


@pytest.mark.django_db
def test_permission_matrix_renders(client, admin):
    """Verify the permission matrix page renders for an admin."""
    client.force_login(admin)
    response = client.get(reverse("rbac:permission_matrix"))
    assert response.status_code == 200
    assert b"Permission Matrix" in response.content


@pytest.mark.django_db
def test_permission_matrix_accepts_category_filter(client, admin):
    """Verify the matrix honours the category query parameter."""
    client.force_login(admin)
    response = client.get(reverse("rbac:permission_matrix"), {"category": "reports"})
    assert response.status_code == 200
    assert b"Reports" in response.content


@pytest.mark.django_db
def test_permission_search_filters_catalogue(client, admin):
    """Verify the permission catalogue supports keyword search."""
    client.force_login(admin)
    response = client.get(reverse("rbac:permission_list"), {"q": "reports.submit"})
    assert response.status_code == 200
    assert b"reports.submit" in response.content


@pytest.mark.django_db
def test_permission_search_empty_result(client, admin):
    """Verify a non-matching search returns no categories."""
    client.force_login(admin)
    response = client.get(reverse("rbac:permission_list"), {"q": "zzznomatch"})
    assert response.status_code == 200
    assert b"No permissions found" in response.content
