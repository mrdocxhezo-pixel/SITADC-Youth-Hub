"""
Views for the organizational structure module.

Every protected view enforces server-side authorization through the RBAC
permission decorators; hiding navigation or buttons is never treated as a
security control.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from apps.rbac.decorators import permission_required

from . import selectors
from .constants import OrganizationAuditAction, UnitType
from .forms import (
    ActingAppointmentForm,
    OrganizationLevelForm,
    OrganizationUnitForm,
    PositionAssignmentForm,
    PositionClassificationForm,
    PositionForm,
    ReportingLineForm,
    TransferForm,
    VacancyForm,
)
from .models import (
    ActingAppointment,
    OrganizationUnit,
    Position,
    PositionAssignment,
    TransferRecord,
    Vacancy,
)
from .permissions import ORGANIZATIONS_ASSIGN, ORGANIZATIONS_MANAGE, ORGANIZATIONS_VIEW
from .services import (
    ActingAppointmentService,
    AppointmentService,
    ApproveTransferService,
    ArchiveOrganizationUnitService,
    ArchivePositionService,
    CompleteTransferService,
    EndActingAppointmentService,
    EndAppointmentService,
    OrganizationLevelService,
    OrganizationUnitService,
    PositionClassificationService,
    PositionService,
    RestoreOrganizationUnitService,
    RestorePositionService,
    RevokeAppointmentService,
    SetOrganizationUnitParentService,
    SetOrganizationUnitStatusService,
    SetPositionStatusService,
    SetReportingLineService,
    SetVacancyStatusService,
    TransferService,
    UpdateOrganizationUnitService,
    UpdatePositionService,
    VacancyService,
)

logger = logging.getLogger(__name__)


@permission_required(ORGANIZATIONS_VIEW)
def organizations_index_view(request):
    """Landing index for the organizational structure area."""
    summary = selectors.get_structure_summary()
    summary.update(selectors.get_unit_counts())
    return render(
        request,
        "organizations/index.html",
        {"summary": summary, "unit_types": UnitType.choices},
    )


@permission_required(ORGANIZATIONS_VIEW)
def unit_list_view(request):
    """List organizational units, optionally filtered by type."""
    unit_type = request.GET.get("type", "")
    units = selectors.get_organization_units(unit_type or None).annotate(
        position_count=Count("positions", distinct=True),
        member_count=Count(
            "assignments",
            filter=Q(assignments__status="ACTIVE"),
            distinct=True,
        ),
    )
    return render(
        request,
        "organizations/unit_list.html",
        {"units": units, "unit_types": UnitType.choices, "active_type": unit_type},
    )


@permission_required(ORGANIZATIONS_VIEW)
def unit_detail_view(request, unit_id):
    """Show a unit, its positions, members and history."""
    unit = get_object_or_404(OrganizationUnit, pk=unit_id)
    positions = selectors.get_positions(unit_id=unit.pk)
    members = selectors.get_unit_members(unit)
    children = unit.children.with_parent()
    history = selectors.get_organization_audit_history("OrganizationUnit", unit.pk)
    return render(
        request,
        "organizations/unit_detail.html",
        {
            "unit": unit,
            "positions": positions,
            "members": members,
            "children": children,
            "history": history,
        },
    )


@permission_required(ORGANIZATIONS_MANAGE)
def unit_create_view(request):
    """Create a new organizational unit."""
    if request.method == "POST":
        form = OrganizationUnitForm(request.POST)
        if form.is_valid():
            try:
                unit = OrganizationUnitService(user=request.user).execute(
                    identifier=form.cleaned_data["identifier"],
                    name=form.cleaned_data["name"],
                    short_name=form.cleaned_data["short_name"],
                    description=form.cleaned_data["description"],
                    level=form.cleaned_data["level"],
                    parent=form.cleaned_data["parent"],
                    unit_type=form.cleaned_data["unit_type"],
                    unit_head=form.cleaned_data["unit_head"],
                    office_location=form.cleaned_data["office_location"],
                    contact_email=form.cleaned_data["contact_email"],
                    contact_phone=form.cleaned_data["contact_phone"],
                    status=form.cleaned_data["status"],
                    effective_date=form.cleaned_data["effective_date"],
                    established_date=form.cleaned_data["established_date"],
                    access_scope=form.cleaned_data["access_scope"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(request, _("Organizational unit created."))
                return redirect("core:unit_detail", unit_id=unit.pk)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = OrganizationUnitForm()

    return render(
        request,
        "organizations/unit_form.html",
        {"form": form, "mode": "create"},
    )


@permission_required(ORGANIZATIONS_MANAGE)
def unit_update_view(request, unit_id):
    """Update an existing organizational unit."""
    unit = get_object_or_404(OrganizationUnit, pk=unit_id)
    if request.method == "POST":
        form = OrganizationUnitForm(request.POST, instance=unit)
        if form.is_valid():
            try:
                unit = UpdateOrganizationUnitService(user=request.user).execute(
                    unit=unit,
                    name=form.cleaned_data["name"],
                    short_name=form.cleaned_data["short_name"],
                    description=form.cleaned_data["description"],
                    level=form.cleaned_data["level"],
                    parent=form.cleaned_data["parent"],
                    unit_head=form.cleaned_data["unit_head"],
                    office_location=form.cleaned_data["office_location"],
                    contact_email=form.cleaned_data["contact_email"],
                    contact_phone=form.cleaned_data["contact_phone"],
                    effective_date=form.cleaned_data["effective_date"],
                    established_date=form.cleaned_data["established_date"],
                    access_scope=form.cleaned_data["access_scope"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(request, _("Organizational unit updated."))
                return redirect("core:unit_detail", unit_id=unit.pk)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = OrganizationUnitForm(instance=unit)

    return render(
        request,
        "organizations/unit_form.html",
        {"form": form, "mode": "update", "unit": unit},
    )


def _unit_action_view(request, unit_id, service, success_message):
    """Shared handler for POST-only unit lifecycle actions."""
    unit = get_object_or_404(OrganizationUnit, pk=unit_id)
    try:
        service(user=request.user).execute(unit=unit)
        messages.success(request, success_message)
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:unit_detail", unit_id=unit.pk)


@permission_required(ORGANIZATIONS_MANAGE)
@require_http_methods(["POST"])
def unit_archive_view(request, unit_id):
    return _unit_action_view(
        request, unit_id, ArchiveOrganizationUnitService, _("Unit archived.")
    )


@permission_required(ORGANIZATIONS_MANAGE)
@require_http_methods(["POST"])
def unit_restore_view(request, unit_id):
    return _unit_action_view(
        request, unit_id, RestoreOrganizationUnitService, _("Unit restored.")
    )


@permission_required(ORGANIZATIONS_MANAGE)
@require_http_methods(["POST"])
def unit_status_view(request, unit_id):
    """Activate or deactivate an organizational unit."""
    unit = get_object_or_404(OrganizationUnit, pk=unit_id)
    status = request.POST.get("status")
    try:
        SetOrganizationUnitStatusService(user=request.user).execute(
            unit=unit, status=status
        )
        messages.success(request, _("Unit status updated."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:unit_detail", unit_id=unit.pk)


@permission_required(ORGANIZATIONS_MANAGE)
@require_http_methods(["POST"])
def unit_parent_view(request, unit_id):
    """Change the parent of an organizational unit."""
    unit = get_object_or_404(OrganizationUnit, pk=unit_id)
    parent = request.POST.get("parent")
    try:
        parent_unit = OrganizationUnit.objects.get(pk=parent) if parent else None
        SetOrganizationUnitParentService(user=request.user).execute(
            unit=unit, parent=parent_unit
        )
        messages.success(request, _("Unit parent updated."))
    except (OrganizationUnit.DoesNotExist, ValidationError) as e:
        messages.error(request, getattr(e, "message", _("Invalid parent unit.")))
    return redirect("core:unit_detail", unit_id=unit.pk)


@permission_required(ORGANIZATIONS_VIEW)
def position_list_view(request):
    """List positions, optionally filtered by unit and occupancy."""
    unit_id = request.GET.get("unit", "")
    vacancy = request.GET.get("vacancy", "")
    include_vacant = None
    if vacancy == "1":
        include_vacant = True
    elif vacancy == "0":
        include_vacant = False
    positions = selectors.get_positions(
        unit_id=unit_id or None, include_vacant=include_vacant
    )
    positions = selectors.prefetch_position_occupancy(positions)
    units = selectors.get_active_units()
    return render(
        request,
        "organizations/position_list.html",
        {
            "positions": positions,
            "units": units,
            "active_unit": unit_id,
            "vacancy_filter": vacancy,
        },
    )


@permission_required(ORGANIZATIONS_VIEW)
def position_detail_view(request, slug):
    """Show a position, its reporting chain, assignments and history."""
    position = get_object_or_404(Position, slug=slug)
    chain = selectors.get_reporting_chain(position)
    relationships = selectors.get_reporting_relationships(position)
    assignments = selectors.get_assignments_for_position(position)
    acting = selectors.get_acting_appointments_for_position(position)
    subordinates = selectors.get_direct_subordinates(position)
    history = selectors.get_organization_audit_history("Position", position.pk)
    return render(
        request,
        "organizations/position_detail.html",
        {
            "position": position,
            "chain": chain,
            "relationships": relationships,
            "assignments": assignments,
            "acting": acting,
            "subordinates": subordinates,
            "history": history,
        },
    )


@permission_required(ORGANIZATIONS_MANAGE)
def position_create_view(request):
    """Create a new position."""
    if request.method == "POST":
        form = PositionForm(request.POST)
        if form.is_valid():
            try:
                position = PositionService(user=request.user).execute(
                    title=form.cleaned_data["title"],
                    organizational_unit=form.cleaned_data["organizational_unit"],
                    classification=form.cleaned_data["classification"],
                    responsibilities=form.cleaned_data["responsibilities"],
                    required_competencies=form.cleaned_data["required_competencies"],
                    appointment_type=form.cleaned_data["appointment_type"],
                    effective_date=form.cleaned_data["effective_date"],
                    is_protected=form.cleaned_data["is_protected"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(request, _("Position created."))
                return redirect("core:position_detail", slug=position.slug)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = PositionForm()

    return render(
        request,
        "organizations/position_form.html",
        {"form": form, "mode": "create"},
    )


@permission_required(ORGANIZATIONS_MANAGE)
def position_update_view(request, slug):
    """Update an existing position."""
    position = get_object_or_404(Position, slug=slug)
    if request.method == "POST":
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            try:
                position = UpdatePositionService(user=request.user).execute(
                    position=position,
                    title=form.cleaned_data["title"],
                    organizational_unit=form.cleaned_data["organizational_unit"],
                    classification=form.cleaned_data["classification"],
                    responsibilities=form.cleaned_data["responsibilities"],
                    required_competencies=form.cleaned_data["required_competencies"],
                    appointment_type=form.cleaned_data["appointment_type"],
                    effective_date=form.cleaned_data["effective_date"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(request, _("Position updated."))
                return redirect("core:position_detail", slug=position.slug)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = PositionForm(instance=position)

    return render(
        request,
        "organizations/position_form.html",
        {"form": form, "mode": "update", "position": position},
    )


def _position_action_view(request, slug, service, success_message):
    """Shared handler for POST-only position lifecycle actions."""
    position = get_object_or_404(Position, slug=slug)
    try:
        service(user=request.user).execute(position=position)
        messages.success(request, success_message)
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:position_detail", slug=position.slug)


@permission_required(ORGANIZATIONS_MANAGE)
@require_http_methods(["POST"])
def position_archive_view(request, slug):
    return _position_action_view(
        request, slug, ArchivePositionService, _("Position archived.")
    )


@permission_required(ORGANIZATIONS_MANAGE)
@require_http_methods(["POST"])
def position_restore_view(request, slug):
    return _position_action_view(
        request, slug, RestorePositionService, _("Position restored.")
    )


@permission_required(ORGANIZATIONS_MANAGE)
@require_http_methods(["POST"])
def position_status_view(request, slug):
    """Activate or deactivate a position."""
    position = get_object_or_404(Position, slug=slug)
    status = request.POST.get("status")
    try:
        SetPositionStatusService(user=request.user).execute(
            position=position, status=status
        )
        messages.success(request, _("Position status updated."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:position_detail", slug=position.slug)


@permission_required(ORGANIZATIONS_MANAGE)
def position_reporting_view(request, slug):
    """Set the primary reporting line for a position."""
    position = get_object_or_404(Position, slug=slug)
    if request.method == "POST":
        form = ReportingLineForm(request.POST, position=position)
        if form.is_valid():
            try:
                SetReportingLineService(user=request.user).execute(
                    position=position,
                    supervisor=form.cleaned_data["supervisor"],
                )
                messages.success(request, _("Reporting line updated."))
                return redirect("core:position_detail", slug=position.slug)
            except ValidationError as e:
                form.add_error("supervisor", e)
    else:
        form = ReportingLineForm(position=position)
    return render(
        request,
        "organizations/position_reporting.html",
        {"form": form, "position": position},
    )


@permission_required(ORGANIZATIONS_ASSIGN)
def position_assign_view(request, slug):
    """Appoint a person to a position."""
    position = get_object_or_404(Position, slug=slug)
    if request.method == "POST":
        form = PositionAssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                AppointmentService(user=request.user).execute(
                    person=form.cleaned_data["person"],
                    position=form.cleaned_data["position"],
                    organizational_unit=form.cleaned_data["organizational_unit"],
                    appointment_type=form.cleaned_data["appointment_type"],
                    appointment_date=form.cleaned_data["appointment_date"],
                    effective_date=form.cleaned_data["effective_date"],
                    term_start=form.cleaned_data["term_start"],
                    term_end=form.cleaned_data["term_end"],
                    renewal_eligible=form.cleaned_data["renewal_eligible"],
                    supporting_document=form.cleaned_data.get("supporting_document"),
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, _("Appointment created."))
                return redirect("core:position_detail", slug=position.slug)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = PositionAssignmentForm(initial={"position": position})
    return render(
        request,
        "organizations/assignment_form.html",
        {"form": form, "position": position},
    )


@permission_required(ORGANIZATIONS_ASSIGN)
@require_http_methods(["POST"])
def assignment_end_view(request, assignment_id):
    """End an active appointment."""
    assignment = get_object_or_404(PositionAssignment, pk=assignment_id)
    try:
        EndAppointmentService(user=request.user).execute(assignment=assignment)
        messages.success(request, _("Appointment ended."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:position_detail", slug=assignment.position.slug)


@permission_required(ORGANIZATIONS_ASSIGN)
@require_http_methods(["POST"])
def assignment_revoke_view(request, assignment_id):
    """Revoke an active appointment."""
    assignment = get_object_or_404(PositionAssignment, pk=assignment_id)
    try:
        RevokeAppointmentService(user=request.user).execute(assignment=assignment)
        messages.success(request, _("Appointment revoked."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:position_detail", slug=assignment.position.slug)


@permission_required(ORGANIZATIONS_ASSIGN)
def acting_create_view(request, slug):
    """Create a temporary acting appointment for a position."""
    position = get_object_or_404(Position, slug=slug)
    if request.method == "POST":
        form = ActingAppointmentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                ActingAppointmentService(user=request.user).execute(
                    acting_officer=form.cleaned_data["acting_officer"],
                    position=form.cleaned_data["position"],
                    original_assignee=form.cleaned_data["original_assignee"],
                    effective_from=form.cleaned_data["effective_from"],
                    end_date=form.cleaned_data["end_date"],
                    reason=form.cleaned_data.get("reason", ""),
                    approval_authority=form.cleaned_data["approval_authority"],
                    supporting_document=form.cleaned_data.get("supporting_document"),
                )
                messages.success(request, _("Acting appointment created."))
                return redirect("core:position_detail", slug=position.slug)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = ActingAppointmentForm(initial={"position": position})
    return render(
        request,
        "organizations/acting_form.html",
        {"form": form, "position": position},
    )


@permission_required(ORGANIZATIONS_ASSIGN)
@require_http_methods(["POST"])
def acting_end_view(request, acting_id):
    """End an active acting appointment."""
    appointment = get_object_or_404(ActingAppointment, pk=acting_id)
    try:
        EndActingAppointmentService(user=request.user).execute(appointment=appointment)
        messages.success(request, _("Acting appointment ended."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:position_detail", slug=appointment.position.slug)


@permission_required(ORGANIZATIONS_ASSIGN)
@require_http_methods(["POST"])
def acting_revoke_view(request, acting_id):
    """Revoke an active acting appointment."""
    appointment = get_object_or_404(ActingAppointment, pk=acting_id)
    try:
        EndActingAppointmentService(user=request.user).execute(
            appointment=appointment, revoke=True
        )
        messages.success(request, _("Acting appointment revoked."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:position_detail", slug=appointment.position.slug)


@permission_required(ORGANIZATIONS_VIEW)
def vacancy_list_view(request):
    """List vacancies."""
    unit_id = request.GET.get("unit", "")
    vacancies = selectors.get_vacancies(unit_id=unit_id or None)
    units = selectors.get_active_units()
    return render(
        request,
        "organizations/vacancy_list.html",
        {"vacancies": vacancies, "units": units, "active_unit": unit_id},
    )


@permission_required(ORGANIZATIONS_MANAGE)
def vacancy_create_view(request):
    """Open a vacancy for a vacant position."""
    if request.method == "POST":
        form = VacancyForm(request.POST)
        if form.is_valid():
            try:
                VacancyService(user=request.user).execute(
                    position=form.cleaned_data["position"],
                    organizational_unit=form.cleaned_data["organizational_unit"],
                    vacancy_reason=form.cleaned_data["vacancy_reason"],
                    date_vacant=form.cleaned_data["date_vacant"],
                    expected_appointment_date=form.cleaned_data[
                        "expected_appointment_date"
                    ],
                    acting_appointment=form.cleaned_data["acting_appointment"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(request, _("Vacancy opened."))
                return redirect("core:vacancy_list")
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = VacancyForm()
    return render(
        request,
        "organizations/vacancy_form.html",
        {"form": form, "mode": "create"},
    )


@permission_required(ORGANIZATIONS_MANAGE)
@require_http_methods(["POST"])
def vacancy_status_view(request, vacancy_id):
    """Update the recruitment status of a vacancy."""
    vacancy = get_object_or_404(Vacancy, pk=vacancy_id)
    status = request.POST.get("status")
    try:
        SetVacancyStatusService(user=request.user).execute(
            vacancy=vacancy, status=status
        )
        messages.success(request, _("Vacancy status updated."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:vacancy_list")


@permission_required(ORGANIZATIONS_VIEW)
def transfer_list_view(request):
    """List personnel transfers."""
    transfers = selectors.get_transfer_records()
    return render(request, "organizations/transfer_list.html", {"transfers": transfers})


@permission_required(ORGANIZATIONS_ASSIGN)
def transfer_create_view(request):
    """Record a personnel transfer request."""
    if request.method == "POST":
        form = TransferForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                TransferService(user=request.user).execute(
                    person=form.cleaned_data["person"],
                    previous_organizational_unit=form.cleaned_data[
                        "previous_organizational_unit"
                    ],
                    new_organizational_unit=form.cleaned_data[
                        "new_organizational_unit"
                    ],
                    previous_position=form.cleaned_data["previous_position"],
                    new_position=form.cleaned_data["new_position"],
                    effective_date=form.cleaned_data["effective_date"],
                    reason=form.cleaned_data["reason"],
                    supporting_document=form.cleaned_data.get("supporting_document"),
                )
                messages.success(request, _("Transfer recorded."))
                return redirect("core:transfer_list")
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = TransferForm()
    return render(
        request,
        "organizations/transfer_form.html",
        {"form": form, "mode": "create"},
    )


@permission_required(ORGANIZATIONS_ASSIGN)
@require_http_methods(["POST"])
def transfer_approve_view(request, transfer_id):
    """Approve a pending transfer."""
    transfer = get_object_or_404(TransferRecord, pk=transfer_id)
    try:
        ApproveTransferService(user=request.user).execute(transfer=transfer)
        messages.success(request, _("Transfer approved."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:transfer_list")


@permission_required(ORGANIZATIONS_ASSIGN)
@require_http_methods(["POST"])
def transfer_complete_view(request, transfer_id):
    """Execute an approved transfer."""
    transfer = get_object_or_404(TransferRecord, pk=transfer_id)
    try:
        CompleteTransferService(user=request.user).execute(transfer=transfer)
        messages.success(request, _("Transfer completed."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:transfer_list")


@permission_required(ORGANIZATIONS_VIEW)
def audit_list_view(request):
    """List organizational audit records."""
    entity_type = request.GET.get("entity_type", "")
    history = selectors.get_organization_audit_history(entity_type or None)
    return render(
        request,
        "organizations/audit_list.html",
        {
            "history": history,
            "active_type": entity_type,
            "entity_types": OrganizationAuditAction.choices,
        },
    )


@permission_required(ORGANIZATIONS_VIEW)
def catalogue_list_view(request):
    """List organizational levels and position classifications."""
    levels = selectors.get_levels()
    classifications = selectors.get_classifications()
    return render(
        request,
        "organizations/catalogue_list.html",
        {"levels": levels, "classifications": classifications},
    )


@permission_required(ORGANIZATIONS_MANAGE)
def level_create_view(request):
    """Create an organizational level."""
    if request.method == "POST":
        form = OrganizationLevelForm(request.POST)
        if form.is_valid():
            try:
                OrganizationLevelService(user=request.user).execute(
                    name=form.cleaned_data["name"],
                    code=form.cleaned_data["code"],
                    description=form.cleaned_data["description"],
                    sort_order=form.cleaned_data["sort_order"],
                )
                messages.success(request, _("Organizational level created."))
                return redirect("core:catalogue_list")
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = OrganizationLevelForm()
    return render(
        request, "organizations/level_form.html", {"form": form, "mode": "create"}
    )


@permission_required(ORGANIZATIONS_MANAGE)
def classification_create_view(request):
    """Create a position classification."""
    if request.method == "POST":
        form = PositionClassificationForm(request.POST)
        if form.is_valid():
            try:
                PositionClassificationService(user=request.user).execute(
                    name=form.cleaned_data["name"],
                    code=form.cleaned_data["code"],
                    description=form.cleaned_data["description"],
                    sort_order=form.cleaned_data["sort_order"],
                )
                messages.success(request, _("Position classification created."))
                return redirect("core:catalogue_list")
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = PositionClassificationForm()
    return render(
        request,
        "organizations/classification_form.html",
        {"form": form, "mode": "create"},
    )
