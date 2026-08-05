import pytest
from django.db import IntegrityError

from apps.accounts.models import User

from ..models import OrganizationLevel, PositionClassification


@pytest.fixture
def actor(db):
    user = User.objects.create_user(
        email="org-models-actor@example.com",
        username="orgmodelsactor",
        password="TestPassword123!",
    )
    user.is_superuser = True
    user.save()
    return user


@pytest.mark.django_db
def test_organization_level_created(actor):
    level = OrganizationLevel.objects.create(
        name="National",
        code="national",
        sort_order=10,
        created_by=actor,
        updated_by=actor,
    )
    assert level.pk
    assert level.code == "national"


@pytest.mark.django_db
def test_organization_level_code_is_unique(actor):
    OrganizationLevel.objects.create(
        name="National", code="national", created_by=actor, updated_by=actor
    )
    with pytest.raises(IntegrityError):
        OrganizationLevel.objects.create(
            name="National 2", code="national", created_by=actor, updated_by=actor
        )


@pytest.mark.django_db
def test_position_classification_created(actor):
    classification = PositionClassification.objects.create(
        name="Senior Management",
        code="senior-management",
        sort_order=20,
        created_by=actor,
        updated_by=actor,
    )
    assert classification.pk
    assert classification.name == "Senior Management"
