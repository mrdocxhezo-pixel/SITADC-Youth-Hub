"""
Service tests for the reference numbering module.
"""

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.constants import AccountStatus
from apps.accounts.models import User

from ..constants import ReferenceAuditAction, ReferenceModules, ReferenceNumberStatus
from ..models import ReferenceNumberAuditRecord, ReferenceNumberScheme
from ..permissions import (
    REFERENCE_NUMBERS_CREATE,
    REFERENCE_NUMBERS_RESET,
    REFERENCE_NUMBERS_UPDATE,
    REFERENCE_NUMBERS_VIEW,
)
from ..services import (
    ActivateReferenceNumberSchemeService,
    CancelReferenceReservationService,
    ConfirmReferenceAssignmentService,
    CreateReferenceNumberSchemeService,
    DeactivateReferenceNumberSchemeService,
    ManualReferenceCorrectionService,
    ReferenceNumberService,
    ResetReferenceSequenceService,
    UpdateReferenceNumberSchemeService,
    VoidReferenceService,
)


def _grant(user, code):
    permission = Permission.objects.get(codename=code)
    user.user_permissions.add(permission)


@pytest.fixture
def base(db):
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


@pytest.fixture
def admin(db):
    user = User.objects.create_user(
        email="ref-manager@example.com",
        username="refmanager",
        password="TestPassword123!",
    )
    user.is_superuser = True
    user.status = AccountStatus.ACTIVE
    user.save()
    return user


@pytest.fixture
def viewer(db):
    user = User.objects.create_user(
        email="ref-viewer@example.com",
        username="refviewer",
        password="TestPassword123!",
    )
    user.status = AccountStatus.ACTIVE
    user.save()
    _grant(user, REFERENCE_NUMBERS_VIEW)
    return user


@pytest.fixture
def manager(db):
    user = User.objects.create_user(
        email="ref-manager@example.com",
        username="refmanager2",
        password="TestPassword123!",
    )
    user.status = AccountStatus.ACTIVE
    user.save()
    _grant(user, REFERENCE_NUMBERS_CREATE)
    _grant(user, REFERENCE_NUMBERS_UPDATE)
    _grant(user, REFERENCE_NUMBERS_RESET)
    _grant(user, REFERENCE_NUMBERS_VIEW)
    return user


def test_create_scheme_requires_permission(db, viewer):
    with pytest.raises(PermissionDenied):
        CreateReferenceNumberSchemeService(user=viewer).execute(
            name="Report", code="report", module=ReferenceModules.REPORTS, prefix="RPT"
        )


def test_create_scheme(db, admin):
    scheme = CreateReferenceNumberSchemeService(user=admin).execute(
        name="Report",
        code="report",
        module=ReferenceModules.REPORTS,
        record_type="report",
        prefix="RPT",
        is_default_for_record_type=True,
    )
    assert scheme.prefix == "RPT"
    assert scheme.is_active


def test_update_scheme(db, admin, base):
    updated = UpdateReferenceNumberSchemeService(user=admin).execute(
        scheme=base,
        name="Project (Renamed)",
        description="Renamed project scheme.",
        sequence_length=8,
    )
    updated.refresh_from_db()
    assert updated.name == "Project (Renamed)"
    assert updated.sequence_length == 8


def test_activate_deactivate(db, admin, base):
    DeactivateReferenceNumberSchemeService(user=admin).execute(scheme=base)
    base.refresh_from_db()
    assert not base.is_active
    ActivateReferenceNumberSchemeService(user=admin).execute(scheme=base)
    base.refresh_from_db()
    assert base.is_active


def test_generate_reference(db, admin, base):
    reference = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    assert reference.reference_number == "PRJ-SITADC-2026-000001"
    assert reference.status == ReferenceNumberStatus.RESERVED


def test_sequential_generation(db, admin, base):
    first = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    second = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    assert second.sequence_value == first.sequence_value + 1
    assert second.reference_number != first.reference_number


def test_generate_with_custom_context(db, admin, base):
    reference = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS,
        record_type="project",
        context={"org": "REG", "year": 2025},
    )
    assert reference.reference_number == "PRJ-REG-2025-000001"


def test_confirm_assignment(db, admin, base):
    reference = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    ConfirmReferenceAssignmentService(user=admin).execute(
        reference=reference, record_id="00000000-0000-0000-0000-000000000007"
    )
    reference.refresh_from_db()
    assert reference.status == ReferenceNumberStatus.ASSIGNED


def test_cancel_reservation(db, admin, base):
    reference = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    CancelReferenceReservationService(user=admin).execute(reference=reference)
    reference.refresh_from_db()
    assert reference.status == ReferenceNumberStatus.CANCELLED


def test_void_assigned(db, admin, base):
    reference = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    ConfirmReferenceAssignmentService(user=admin).execute(
        reference=reference, record_id="00000000-0000-0000-0000-000000000008"
    )
    VoidReferenceService(user=admin).execute(reference=reference)
    reference.refresh_from_db()
    assert reference.status == ReferenceNumberStatus.VOIDED


def test_manual_correction(db, admin, base):
    original = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    ConfirmReferenceAssignmentService(user=admin).execute(
        reference=original, record_id="00000000-0000-0000-0000-000000000009"
    )
    replacement = ManualReferenceCorrectionService(user=admin).execute(
        generated=original, reason="Wrong project linked"
    )
    original.refresh_from_db()
    replacement.refresh_from_db()
    assert original.status == ReferenceNumberStatus.VOIDED
    assert replacement.status == ReferenceNumberStatus.ASSIGNED
    assert replacement.reference_number != original.reference_number
    assert replacement.record_id == original.record_id


def test_manual_correction_requires_reason(db, admin, base):
    original = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    with pytest.raises(ValidationError):
        ManualReferenceCorrectionService(user=admin).execute(
            generated=original, reason=""
        )


def test_reset_requires_permission(db, viewer, base):
    with pytest.raises(PermissionDenied):
        ResetReferenceSequenceService(user=viewer).execute(scheme=base, start_value=1)


def test_reset_sequence(db, manager, base):
    ReferenceNumberService(user=manager).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    ReferenceNumberService(user=manager).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    sequence = ResetReferenceSequenceService(user=manager).execute(
        scheme=base, start_value=1, notes="Clean restart"
    )
    assert sequence.next_value > 2  # never goes backwards


def test_sequence_never_goes_backwards(db, admin, base):
    for _ in range(5):
        ReferenceNumberService(user=admin).execute(
            module=ReferenceModules.PROJECTS, record_type="project"
        )
    sequence = ResetReferenceSequenceService(user=admin).execute(
        scheme=base, start_value=1, notes="Try to go back"
    )
    assert sequence.next_value == 6


def test_generate_records_audit(db, admin, base):
    reference = ReferenceNumberService(user=admin).execute(
        module=ReferenceModules.PROJECTS, record_type="project"
    )
    assert ReferenceNumberAuditRecord.objects.filter(
        entity_type="GeneratedReferenceNumber",
        entity_id=str(reference.pk),
        action=ReferenceAuditAction.RESERVED,
    ).exists()
