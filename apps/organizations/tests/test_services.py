from datetime import date

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.constants import AccountStatus
from apps.accounts.models import User
from apps.rbac.models import AccessScope

from ..models import OrganizationLevel, PositionAssignment
from ..permissions import ORGANIZATIONS_ASSIGN, ORGANIZATIONS_MANAGE, ORGANIZATIONS_VIEW
from ..services import (
    ActingAppointmentService,
    AppointmentService,
    ApproveTransferService,
    CompleteTransferService,
    EndAppointmentService,
    OrganizationUnitService,
    PositionService,
    SetOrganizationUnitStatusService,
    SetReportingLineService,
    TransferService,
    VacancyService,
)


def _grant(user, code):
    permission = Permission.objects.get(codename=code)
    user.user_permissions.add(permission)


@pytest.fixture
def base(db):
    level = OrganizationLevel.objects.create(name="National", code="national")
    return {"level": level}


@pytest.fixture
def manager(db, base):
    user = User.objects.create_user(
        email="org-manager@example.com",
        username="orgmanager",
        password="TestPassword123!",
    )
    user.status = AccountStatus.ACTIVE
    user.save()
    _grant(user, ORGANIZATIONS_MANAGE)
    _grant(user, ORGANIZATIONS_VIEW)
    return user


@pytest.fixture
def assigner(db, base):
    user = User.objects.create_user(
        email="org-assigner@example.com",
        username="orgassigner",
        password="TestPassword123!",
    )
    user.status = AccountStatus.ACTIVE
    user.save()
    _grant(user, ORGANIZATIONS_ASSIGN)
    _grant(user, ORGANIZATIONS_VIEW)
    return user


@pytest.fixture
def viewer(db, base):
    user = User.objects.create_user(
        email="org-viewer@example.com",
        username="orgviewer",
        password="TestPassword123!",
    )
    user.status = AccountStatus.ACTIVE
    user.save()
    _grant(user, ORGANIZATIONS_VIEW)
    return user


@pytest.fixture
def no_perm_user(db, base):
    return User.objects.create_user(
        email="org-noperm@example.com",
        username="orgnoperm",
        password="TestPassword123!",
    )


@pytest.fixture
def unit(db, manager, base):
    return OrganizationUnitService(user=manager).execute(
        identifier="ORG-NAT",
        name="SITADC Youth Organization",
        unit_type="NATIONAL_ORGANIZATION",
        level=base["level"],
        status="ACTIVE",
    )


@pytest.fixture
def position(db, manager, unit):
    return PositionService(user=manager).execute(
        title="Executive Director",
        organizational_unit=unit,
        appointment_type="PERMANENT",
    )


@pytest.fixture
def staff_person(db):
    return User.objects.create_user(
        email="staff@example.com",
        username="staff",
        password="TestPassword123!",
        status=AccountStatus.ACTIVE,
    )


def test_unit_creation_requires_manage(no_perm_user, base):
    with pytest.raises(PermissionDenied):
        OrganizationUnitService(user=no_perm_user).execute(
            identifier="ORG-DENIED",
            name="Denied",
            unit_type="DEPARTMENT",
            level=base["level"],
        )


def test_unit_creation_records_audit(manager, base):
    unit = OrganizationUnitService(user=manager).execute(
        identifier="ORG-AUDIT",
        name="Audited Unit",
        unit_type="DIRECTORATE",
        level=base["level"],
    )
    from ..models import OrganizationAuditRecord

    assert OrganizationAuditRecord.objects.filter(
        entity_type="OrganizationUnit", entity_id=str(unit.pk)
    ).exists()


def test_position_creation_requires_manage(viewer, unit):
    with pytest.raises(PermissionDenied):
        PositionService(user=viewer).execute(
            title="Denied Position", organizational_unit=unit
        )


def test_position_duplicate_slug_rejected(manager, unit):
    PositionService(user=manager).execute(
        title="Duplicate Position", organizational_unit=unit
    )
    with pytest.raises(ValidationError):
        PositionService(user=manager).execute(
            title="Duplicate Position", organizational_unit=unit
        )


def test_appointment_flow(assigner, manager, position, staff_person, unit):
    assignment = AppointmentService(user=assigner).execute(
        person=staff_person,
        position=position,
        organizational_unit=unit,
        appointment_type="PERMANENT",
    )
    assert assignment.status == "ACTIVE"
    assert (
        PositionAssignment.objects.filter(person=staff_person, status="ACTIVE").count()
        == 1
    )
    assert position.is_vacant is False


def test_appointment_requires_assign(manager, position, staff_person, unit):
    with pytest.raises(PermissionDenied):
        AppointmentService(user=manager).execute(
            person=staff_person,
            position=position,
            organizational_unit=unit,
        )


def test_single_active_appointment_enforced(
    assigner, manager, position, staff_person, unit
):
    AppointmentService(user=assigner).execute(
        person=staff_person, position=position, organizational_unit=unit
    )
    second_person = User.objects.create_user(
        email="staff2@example.com",
        username="staff2",
        password="TestPassword123!",
        status=AccountStatus.ACTIVE,
    )
    with pytest.raises(ValidationError):
        AppointmentService(user=assigner).execute(
            person=second_person, position=position, organizational_unit=unit
        )


def test_end_appointment(assigner, position, staff_person, unit):
    assignment = AppointmentService(user=assigner).execute(
        person=staff_person, position=position, organizational_unit=unit
    )
    EndAppointmentService(user=assigner).execute(assignment=assignment)
    assignment.refresh_from_db()
    assert assignment.status == "ENDED"
    assert position.is_vacant is True


def test_reporting_line_and_cycle_prevention(manager, unit):
    top = PositionService(user=manager).execute(
        title="Top Leader", organizational_unit=unit
    )
    mid = PositionService(user=manager).execute(
        title="Middle Leader", organizational_unit=unit
    )
    low = PositionService(user=manager).execute(
        title="Low Officer", organizational_unit=unit
    )
    SetReportingLineService(user=manager).execute(position=mid, supervisor=top)
    SetReportingLineService(user=manager).execute(position=low, supervisor=mid)
    with pytest.raises(ValidationError):
        SetReportingLineService(user=manager).execute(position=top, supervisor=low)


def test_unit_status_change(manager, unit):
    SetOrganizationUnitStatusService(user=manager).execute(unit=unit, status="INACTIVE")
    unit.refresh_from_db()
    assert unit.status == "INACTIVE"


def test_vacancy_and_transfer_flow(assigner, manager, position, staff_person, unit):
    assignment = AppointmentService(user=assigner).execute(
        person=staff_person, position=position, organizational_unit=unit
    )
    EndAppointmentService(user=assigner).execute(assignment=assignment)

    vacancy = VacancyService(user=manager).execute(
        position=position, organizational_unit=unit, vacancy_reason="Staff departure"
    )
    assert vacancy.recruitment_status == "OPEN"

    new_position = PositionService(user=manager).execute(
        title="New Position", organizational_unit=unit
    )
    transfer = TransferService(user=assigner).execute(
        person=staff_person,
        previous_organizational_unit=unit,
        new_organizational_unit=unit,
        previous_position=position,
        new_position=new_position,
        effective_date=date.today(),
    )
    assert transfer.status == "PENDING"

    ApproveTransferService(user=assigner).execute(transfer=transfer)
    transfer.refresh_from_db()
    assert transfer.status == "APPROVED"

    CompleteTransferService(user=assigner).execute(transfer=transfer)
    transfer.refresh_from_db()
    assert transfer.status == "COMPLETED"
    assert PositionAssignment.objects.filter(
        person=staff_person, position=new_position, status="ACTIVE"
    ).exists()


def test_acting_appointment_flow(assigner, manager, position, staff_person):
    appointment = ActingAppointmentService(user=assigner).execute(
        acting_officer=staff_person,
        position=position,
        effective_from="2026-08-01",
        end_date="2026-09-01",
        reason="Coverage while recruiting.",
    )
    assert appointment.status == "ACTIVE"


def test_acting_overlap_rejected(assigner, manager, position, staff_person):
    second_person = User.objects.create_user(
        email="staff3@example.com",
        username="staff3",
        password="TestPassword123!",
        status=AccountStatus.ACTIVE,
    )
    ActingAppointmentService(user=assigner).execute(
        acting_officer=staff_person,
        position=position,
        effective_from="2026-08-01",
        end_date="2026-09-01",
    )
    with pytest.raises(ValidationError):
        ActingAppointmentService(user=assigner).execute(
            acting_officer=second_person,
            position=position,
            effective_from="2026-08-15",
            end_date="2026-10-01",
        )


def test_appointment_immutable(assigner, position, staff_person, unit):
    assignment = AppointmentService(user=assigner).execute(
        person=staff_person, position=position, organizational_unit=unit
    )
    with pytest.raises(ValidationError):
        assignment.delete()


def test_access_scope_seeded(db):
    scope = AccessScope.objects.get(code="national")
    assert scope.pk
