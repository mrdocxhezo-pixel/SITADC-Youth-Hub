"""
Model tests for the reference numbering module.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.accounts.constants import AccountStatus
from apps.accounts.models import User

from ..constants import ReferenceModules, ReferenceNumberStatus
from ..models import GeneratedReferenceNumber, ReferenceNumberScheme, ReferenceSequence
from ..permissions import REFERENCE_NUMBERS_VIEW


@pytest.fixture
def admin(db):
    user = User.objects.create_user(
        email="ref-admin@example.com",
        username="refadmin",
        password="TestPassword123!",
    )
    user.is_superuser = True
    user.status = AccountStatus.ACTIVE
    user.save()
    return user


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
def test_scheme_requires_valid_prefix(db):
    with pytest.raises(ValidationError):
        ReferenceNumberScheme.objects.create(
            name="Bad",
            code="bad",
            module=ReferenceModules.PROJECTS,
            prefix="123",
        )


@pytest.mark.django_db
def test_scheme_requires_prefix_and_sequence_tokens(db):
    with pytest.raises(ValidationError):
        ReferenceNumberScheme.objects.create(
            name="Missing",
            code="missing",
            module=ReferenceModules.PROJECTS,
            prefix="PRJ",
            pattern="{YEAR}-{SEQUENCE}",
        )


@pytest.mark.django_db
def test_scheme_rejects_unknown_tokens(db):
    with pytest.raises(ValidationError):
        ReferenceNumberScheme.objects.create(
            name="Unknown",
            code="unknown",
            module=ReferenceModules.PROJECTS,
            prefix="PRJ",
            pattern="{PREFIX}-{UNKNOWN}",
        )


@pytest.mark.django_db
def test_scheme_activate_deactivate(scheme):
    assert scheme.is_usable
    scheme.deactivate()
    scheme.refresh_from_db()
    assert not scheme.is_active
    assert not scheme.is_usable
    scheme.activate()
    scheme.refresh_from_db()
    assert scheme.is_usable


@pytest.mark.django_db
def test_sequence_unique_per_scheme_period(scheme):
    ReferenceSequence.objects.create(
        scheme=scheme, period_key="2026", start_value=1, current_value=0, next_value=1
    )
    with pytest.raises(IntegrityError):
        ReferenceSequence.objects.create(
            scheme=scheme,
            period_key="2026",
            start_value=1,
            current_value=0,
            next_value=1,
        )


@pytest.mark.django_db
def test_generated_reference_is_immutable(scheme, admin):
    reference = GeneratedReferenceNumber.objects.create(
        scheme=scheme,
        reference_number="PRJ-SITADC-2026-000001",
        module=ReferenceModules.PROJECTS,
        record_type="project",
        sequence_value=1,
        period_key="always",
        created_by=admin,
    )
    reference.reference_number = "CHANGED"
    with pytest.raises(ValidationError):
        reference.save()
    with pytest.raises(ValidationError):
        reference.delete()


@pytest.mark.django_db
def test_generated_reference_transition_updates_status(scheme, admin):
    reference = GeneratedReferenceNumber.objects.create(
        scheme=scheme,
        reference_number="PRJ-SITADC-2026-000001",
        module=ReferenceModules.PROJECTS,
        record_type="project",
        sequence_value=1,
        period_key="always",
        created_by=admin,
    )
    reference.transition(status=ReferenceNumberStatus.ASSIGNED)
    reference.refresh_from_db()
    assert reference.status == ReferenceNumberStatus.ASSIGNED
    assert reference.reference_number == "PRJ-SITADC-2026-000001"


@pytest.mark.django_db
def test_reference_number_is_unique(scheme, admin):
    GeneratedReferenceNumber.objects.create(
        scheme=scheme,
        reference_number="PRJ-SITADC-2026-000001",
        module=ReferenceModules.PROJECTS,
        record_type="project",
        sequence_value=1,
        period_key="always",
        created_by=admin,
    )
    with pytest.raises(IntegrityError):
        GeneratedReferenceNumber.objects.create(
            scheme=scheme,
            reference_number="PRJ-SITADC-2026-000001",
            module=ReferenceModules.PROJECTS,
            record_type="project",
            sequence_value=2,
            period_key="always",
            created_by=admin,
        )


@pytest.mark.django_db
def test_sequence_value_unique_per_scheme_period(scheme, admin):
    GeneratedReferenceNumber.objects.create(
        scheme=scheme,
        reference_number="PRJ-SITADC-2026-000001",
        module=ReferenceModules.PROJECTS,
        record_type="project",
        sequence_value=1,
        period_key="always",
        created_by=admin,
    )
    with pytest.raises(IntegrityError):
        GeneratedReferenceNumber.objects.create(
            scheme=scheme,
            reference_number="PRJ-SITADC-2026-000002",
            module=ReferenceModules.PROJECTS,
            record_type="project",
            sequence_value=1,
            period_key="always",
            created_by=admin,
        )


@pytest.mark.django_db
def test_new_permission_code_registered(db):
    from apps.rbac.seed_data import ALL_PERMISSION_CODES

    assert REFERENCE_NUMBERS_VIEW in ALL_PERMISSION_CODES
