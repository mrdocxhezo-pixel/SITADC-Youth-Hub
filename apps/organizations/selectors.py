"""
Read-only retrieval helpers for the organizational structure module.

Selectors never modify data; they only fetch and shape organizational
information for views, services and templates.
"""

from __future__ import annotations

from django.db.models import Count, Q, QuerySet

from apps.accounts.models import User

from .constants import (
    ActingAppointmentStatus,
    AppointmentStatus,
    PositionStatus,
    UnitStatus,
    UnitType,
    VacancyStatus,
)
from .models import (
    ActingAppointment,
    OrganizationAuditRecord,
    OrganizationLevel,
    OrganizationUnit,
    Position,
    PositionAssignment,
    PositionClassification,
    ReportingRelationship,
    TransferRecord,
    Vacancy,
)


def get_organization_units(unit_type: str | None = None) -> QuerySet[OrganizationUnit]:
    """Return organizational units, optionally filtered by unit type."""
    qs = OrganizationUnit.objects.with_parent()
    if unit_type:
        qs = qs.of_type(unit_type)
    return qs


def get_active_units() -> QuerySet[OrganizationUnit]:
    """Return only active organizational units."""
    return get_organization_units().filter(status=UnitStatus.ACTIVE)


def get_directorates() -> QuerySet[OrganizationUnit]:
    return get_organization_units(UnitType.DIRECTORATE)


def get_departments() -> QuerySet[OrganizationUnit]:
    return get_organization_units(UnitType.DEPARTMENT)


def get_regions() -> QuerySet[OrganizationUnit]:
    return get_organization_units(UnitType.REGION)


def get_districts() -> QuerySet[OrganizationUnit]:
    return get_organization_units(UnitType.DISTRICT)


def get_communities() -> QuerySet[OrganizationUnit]:
    return get_organization_units(UnitType.COMMUNITY)


def get_teams() -> QuerySet[OrganizationUnit]:
    return get_organization_units(UnitType.TEAM)


def get_unit_by_identifier(identifier: str) -> OrganizationUnit:
    return OrganizationUnit.objects.get(identifier=identifier)


def get_unit_by_id(unit_id) -> OrganizationUnit:
    return OrganizationUnit.objects.get(id=unit_id)


def get_organization_tree() -> list[OrganizationUnit]:
    """
    Return the full organizational tree as a flat list ordered depth-first,
    starting from root units.
    """
    units = list(OrganizationUnit.objects.with_parent().order_by("name"))
    by_parent: dict = {}
    for unit in units:
        by_parent.setdefault(unit.parent_id, []).append(unit)
    roots = by_parent.get(None, [])
    ordered: list[OrganizationUnit] = []
    for root in roots:
        ordered.append(root)
        for child in by_parent.get(root.pk, []):
            ordered.append(child)
            ordered.extend(by_parent.get(child.pk, []))
    return ordered


def get_levels() -> QuerySet[OrganizationLevel]:
    """Return organizational levels ordered for hierarchy display."""
    return OrganizationLevel.objects.all().order_by("sort_order", "name")


def get_active_levels() -> QuerySet[OrganizationLevel]:
    return get_levels().filter(is_active=True)


def get_classifications() -> QuerySet[PositionClassification]:
    """Return position classifications ordered for display."""
    return PositionClassification.objects.all().order_by("sort_order", "name")


def get_active_classifications() -> QuerySet[PositionClassification]:
    return get_classifications().filter(is_active=True)


def get_positions(unit_id=None, include_vacant=None) -> QuerySet[Position]:
    """Return positions, optionally filtered by unit and occupancy."""
    qs = Position.objects.with_unit()
    if unit_id:
        qs = qs.filter(organizational_unit_id=unit_id)
    if include_vacant is True:
        occupied = PositionAssignment.objects.filter(
            status=AppointmentStatus.ACTIVE
        ).values_list("position_id", flat=True)
        qs = qs.exclude(pk__in=occupied)
    elif include_vacant is False:
        occupied = PositionAssignment.objects.filter(
            status=AppointmentStatus.ACTIVE
        ).values_list("position_id", flat=True)
        qs = qs.filter(pk__in=occupied)
    return qs


def get_active_positions() -> QuerySet[Position]:
    return get_positions().filter(status=PositionStatus.ACTIVE)


def get_position_by_slug(slug: str) -> Position:
    return Position.objects.get(slug=slug)


def get_position_by_id(position_id) -> Position:
    return Position.objects.get(id=position_id)


def get_reporting_chain(position: Position) -> list[Position]:
    """Return the reporting chain from the position up to the root."""
    return position.get_reporting_chain()


def get_reporting_relationships(
    position: Position,
) -> QuerySet[ReportingRelationship]:
    """Return the reporting relationships for a position."""
    return position.reporting_relationships.select_related("supervisor").order_by(
        "-is_primary", "-is_active", "effective_from"
    )


def get_direct_subordinates(position: Position) -> QuerySet[Position]:
    """Return the positions that report directly to the given position."""
    return Position.objects.with_unit().filter(
        reporting_relationships__supervisor=position,
        reporting_relationships__is_active=True,
    )


def get_unit_members(unit: OrganizationUnit) -> QuerySet[User]:
    """Return the distinct people currently assigned to positions in a unit."""
    user_ids = (
        PositionAssignment.objects.filter(
            organizational_unit=unit, status=AppointmentStatus.ACTIVE
        )
        .values_list("person_id", flat=True)
        .distinct()
    )
    return User.objects.filter(pk__in=user_ids, is_active=True)


def get_active_assignments() -> QuerySet[PositionAssignment]:
    """Return all current position appointments."""
    return PositionAssignment.objects.filter(status=AppointmentStatus.ACTIVE)


def get_active_assignments_for_unit(
    unit: OrganizationUnit,
) -> QuerySet[PositionAssignment]:
    return get_active_assignments().filter(organizational_unit=unit)


def get_assignments_for_position(position: Position) -> QuerySet[PositionAssignment]:
    """Return the full (including historical) assignment record for a position."""
    return position.assignments.select_related("person", "appointed_by").order_by(
        "-effective_date", "-created_at"
    )


def get_assignments_for_person(person: User) -> QuerySet[PositionAssignment]:
    """Return the full assignment history of a person."""
    return person.position_assignments.select_related(
        "position", "organizational_unit"
    ).order_by("-effective_date", "-created_at")


def get_vacant_positions(unit_id=None) -> QuerySet[Position]:
    """Return positions with no active appointment."""
    return get_positions(unit_id=unit_id, include_vacant=True)


def get_vacancies(unit_id=None) -> QuerySet[Vacancy]:
    qs = Vacancy.objects.select_related("position", "organizational_unit")
    if unit_id:
        qs = qs.filter(organizational_unit_id=unit_id)
    return qs


def get_open_vacancies() -> QuerySet[Vacancy]:
    return get_vacancies().exclude(recruitment_status=VacancyStatus.FILLED)


def get_active_acting_appointments() -> QuerySet[ActingAppointment]:
    return (
        ActingAppointment.objects.filter(status=ActingAppointmentStatus.ACTIVE)
        .select_related("acting_officer", "position", "original_assignee")
        .order_by("end_date")
    )


def get_acting_appointments_for_position(
    position: Position,
) -> QuerySet[ActingAppointment]:
    return position.acting_appointments.select_related("acting_officer").order_by(
        "-effective_from", "-created_at"
    )


def get_transfer_records(person: User | None = None) -> QuerySet[TransferRecord]:
    qs = TransferRecord.objects.select_related(
        "person",
        "previous_organizational_unit",
        "new_organizational_unit",
        "previous_position",
        "new_position",
        "approved_by",
    )
    if person is not None:
        qs = qs.filter(person=person)
    return qs


def get_organization_audit_history(
    entity_type: str | None = None, entity_id=None
) -> QuerySet[OrganizationAuditRecord]:
    qs = OrganizationAuditRecord.objects.select_related("changed_by")
    if entity_type:
        qs = qs.filter(entity_type=entity_type)
    if entity_id is not None:
        qs = qs.filter(entity_id=str(entity_id))
    return qs


def get_unit_counts() -> dict[str, int]:
    """Return a summary of active units grouped by unit type."""
    rows = (
        OrganizationUnit.objects.filter(status=UnitStatus.ACTIVE)
        .values("unit_type")
        .annotate(count=Count("id"))
    )
    return {row["unit_type"]: row["count"] for row in rows}


def get_structure_summary() -> dict:
    """Return headline counts used by dashboards and index pages."""
    occupied = PositionAssignment.objects.filter(
        status=AppointmentStatus.ACTIVE
    ).values_list("position_id", flat=True)
    return {
        "unit_count": OrganizationUnit.objects.filter(status=UnitStatus.ACTIVE).count(),
        "position_count": Position.objects.filter(status=PositionStatus.ACTIVE).count(),
        "occupied_position_count": Position.objects.filter(
            status=PositionStatus.ACTIVE, pk__in=occupied
        ).count(),
        "vacancy_count": Vacancy.objects.exclude(
            recruitment_status=VacancyStatus.FILLED
        ).count(),
        "acting_count": ActingAppointment.objects.filter(
            status=ActingAppointmentStatus.ACTIVE
        ).count(),
        "assignment_count": PositionAssignment.objects.filter(
            status=AppointmentStatus.ACTIVE
        ).count(),
    }


def prefetch_position_occupancy(positions: QuerySet) -> QuerySet:
    """Attach active assignment counts to positions."""
    return positions.annotate(
        active_assignment_count=Count(
            "assignments",
            filter=Q(status=AppointmentStatus.ACTIVE),
            distinct=True,
        ),
    )
