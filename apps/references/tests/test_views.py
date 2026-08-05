"""
View tests for the reference numbering module.
"""

import pytest
from django.urls import reverse

from apps.accounts.constants import AccountStatus
from apps.accounts.models import User

from ..constants import ReferenceModules
from ..models import ReferenceNumberScheme


@pytest.fixture
def admin(db):
    user = User.objects.create_user(
        email="ref-view-admin@example.com",
        username="refviewadmin",
        password="TestPassword123!",
    )
    user.is_superuser = True
    user.status = AccountStatus.ACTIVE
    user.save()
    return user


@pytest.fixture
def plain_user(db):
    return User.objects.create_user(
        email="ref-view-plain@example.com",
        username="refviewplain",
        password="TestPassword123!",
    )


@pytest.fixture
def scheme(db):
    return ReferenceNumberScheme.objects.create(
        name="Project",
        code="project",
        module=ReferenceModules.PROJECTS,
        record_type="project",
        prefix="PRJ",
        pattern="{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
        organization_code="SITADC",
        sequence_length=6,
        start_value=1,
        is_default_for_record_type=True,
        is_default_for_module=True,
    )


@pytest.mark.django_db
def test_reference_pages_require_login(client, db):
    for url_name in [
        "references_index",
        "scheme_list",
        "reference_registry",
        "sequence_list",
        "audit_list",
        "scheme_preview",
    ]:
        response = client.get(reverse(f"core:{url_name}"))
        assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_references_index_renders(client, admin):
    client.force_login(admin)
    response = client.get(reverse("core:references_index"))
    assert response.status_code == 200
    assert b"Reference Numbering" in response.content


@pytest.mark.django_db
def test_scheme_list_renders(client, admin, scheme):
    client.force_login(admin)
    response = client.get(reverse("core:scheme_list"))
    assert response.status_code == 200
    assert b"Schemes" in response.content


@pytest.mark.django_db
def test_scheme_detail_renders(client, admin, scheme):
    client.force_login(admin)
    response = client.get(reverse("core:scheme_detail", args=[scheme.pk]))
    assert response.status_code == 200
    assert b"Project" in response.content


@pytest.mark.django_db
def test_registry_renders(client, admin):
    client.force_login(admin)
    response = client.get(reverse("core:reference_registry"))
    assert response.status_code == 200
    assert b"Reference Registry" in response.content


@pytest.mark.django_db
def test_preview_renders(client, admin):
    client.force_login(admin)
    response = client.get(reverse("core:scheme_preview"))
    assert response.status_code == 200
    assert b"Preview" in response.content


@pytest.mark.django_db
def test_sequence_list_renders(client, admin):
    client.force_login(admin)
    response = client.get(reverse("core:sequence_list"))
    assert response.status_code == 200
    assert b"Sequences" in response.content


@pytest.mark.django_db
def test_audit_list_renders(client, admin):
    client.force_login(admin)
    response = client.get(reverse("core:audit_list"))
    assert response.status_code == 200
    assert b"Audit Trail" in response.content


@pytest.mark.django_db
def test_unauthorized_user_gets_403(client, plain_user):
    client.force_login(plain_user)
    response = client.get(reverse("core:scheme_list"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_preview_post_renders_result(client, admin, scheme):
    client.force_login(admin)
    response = client.post(
        reverse("core:scheme_preview"),
        {"module": ReferenceModules.PROJECTS, "record_type": "project"},
    )
    assert response.status_code == 200
    assert b"PRJ-SITADC" in response.content


@pytest.mark.django_db
def test_scheme_create_post(client, admin):
    client.force_login(admin)
    response = client.post(
        reverse("core:scheme_create"),
        {
            "name": "Report",
            "code": "report",
            "module": ReferenceModules.REPORTS,
            "record_type": "report",
            "prefix": "RPT",
            "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
            "organization_code": "SITADC",
            "sequence_length": 6,
            "start_value": 1,
            "reset_period": "NEVER",
            "fiscal_start_month": 1,
            "custom_reset_interval_days": "",
        },
    )
    assert response.status_code == 302
    assert ReferenceNumberScheme.objects.filter(code="report").exists()
