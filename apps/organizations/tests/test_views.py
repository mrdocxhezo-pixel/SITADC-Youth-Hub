import pytest
from django.urls import reverse

from apps.accounts.models import User

from ..models import OrganizationLevel, OrganizationUnit, Position


@pytest.fixture
def admin(db):
    user = User.objects.create_user(
        email="org-admin@example.com",
        username="orgadmin",
        password="TestPassword123!",
    )
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture
def plain_user(db):
    return User.objects.create_user(
        email="org-plain@example.com",
        username="orgplain",
        password="TestPassword123!",
    )


@pytest.fixture
def level(db):
    return OrganizationLevel.objects.create(name="National", code="national")


@pytest.mark.django_db
def test_organization_pages_require_login(client, db):
    """Unauthenticated users must be redirected away."""
    for url_name in [
        "organizations_index",
        "unit_list",
        "position_list",
        "vacancy_list",
        "transfer_list",
        "organization_audit",
        "catalogue_list",
    ]:
        response = client.get(reverse(f"core:{url_name}"))
        assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_organization_index_renders(client, admin):
    client.force_login(admin)
    response = client.get(reverse("core:organizations_index"))
    assert response.status_code == 200
    assert b"Organization" in response.content


@pytest.mark.django_db
def test_unit_list_renders(client, admin, level):
    client.force_login(admin)
    response = client.get(reverse("core:unit_list"))
    assert response.status_code == 200
    assert b"Units" in response.content


@pytest.mark.django_db
def test_position_list_renders(client, admin, level):
    client.force_login(admin)
    response = client.get(reverse("core:position_list"))
    assert response.status_code == 200
    assert b"Positions" in response.content


@pytest.mark.django_db
def test_catalogue_list_renders(client, admin, level):
    client.force_login(admin)
    response = client.get(reverse("core:catalogue_list"))
    assert response.status_code == 200
    assert b"Organizational Levels" in response.content


@pytest.mark.django_db
def test_unauthorized_user_gets_403(client, plain_user):
    client.force_login(plain_user)
    response = client.get(reverse("core:unit_list"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_unit_create_flow(client, admin, level):
    client.force_login(admin)
    response = client.post(
        reverse("core:unit_create"),
        {
            "identifier": "ORG-HEAD",
            "name": "National Headquarters",
            "short_name": "NHQ",
            "unit_type": "EXECUTIVE_MANAGEMENT",
            "level": str(level.pk),
            "status": "ACTIVE",
            "description": "Central executive management unit.",
        },
    )
    assert response.status_code == 302
    assert OrganizationUnit.objects.filter(identifier="ORG-HEAD").exists()


@pytest.mark.django_db
def test_position_create_flow(client, admin, level):
    client.force_login(admin)
    unit = OrganizationUnit.objects.create(
        identifier="ORG-HQ", name="HQ", level=level, unit_type="EXECUTIVE_MANAGEMENT"
    )
    response = client.post(
        reverse("core:position_create"),
        {
            "title": "Programme Manager",
            "organizational_unit": str(unit.pk),
            "appointment_type": "PERMANENT",
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 302
    assert Position.objects.filter(slug="programme-manager").exists()


@pytest.mark.django_db
def test_vacancy_create_flow(client, admin, level):
    client.force_login(admin)
    unit = OrganizationUnit.objects.create(
        identifier="ORG-HQ", name="HQ", level=level, unit_type="EXECUTIVE_MANAGEMENT"
    )
    position = Position.objects.create(
        title="Vacant Role", slug="vacant-role", organizational_unit=unit
    )
    response = client.post(
        reverse("core:vacancy_create"),
        {
            "position": str(position.pk),
            "organizational_unit": str(unit.pk),
            "recruitment_status": "OPEN",
            "vacancy_reason": "Role vacated.",
        },
    )
    assert response.status_code == 302
    assert position.vacancy is not None


@pytest.mark.django_db
def test_audit_page_renders(client, admin):
    client.force_login(admin)
    response = client.get(reverse("core:organization_audit"))
    assert response.status_code == 200
