"""Views for Governance, Risk, Compliance and Safeguarding (Phase 29).

All views enforce server-side authorization via the ``governance.*``
permission catalogue and remain fail-closed: list/detail data flows through
the selectors in :mod:`apps.governance.selectors`, and mutating operations
set audit metadata and allocate reference numbers through the services.
"""

from __future__ import annotations

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.rbac.decorators import any_permission_required

from . import selectors, services
from .constants import GovernanceType
from .forms import (
    ComplaintForm,
    ComplianceAssessmentForm,
    ComplianceRequirementForm,
    ConflictOfInterestDeclarationForm,
    CorrectivePreventiveActionForm,
    DocumentForm,
    EthicsCaseForm,
    GovernanceMeetingForm,
    IncidentReportForm,
    InternalControlForm,
    MeetingAttendanceForm,
    PolicyAcknowledgementForm,
    PolicyForm,
    PolicyVersionForm,
    RiskAssessmentForm,
    RiskRegisterForm,
    RiskTreatmentPlanForm,
    SafeguardingCaseForm,
    WhistleblowerReportForm,
)
from .models import (
    Complaint,
    ComplianceRequirement,
    ConflictOfInterestDeclaration,
    CorrectivePreventiveAction,
    Document,
    EthicsCase,
    GovernanceMeeting,
    GovernanceNotification,
    IncidentReport,
    InternalControl,
    Policy,
    RiskRegister,
    SafeguardingCase,
    WhistleblowerReport,
)
from .permissions import (
    GOVERNANCE_CREATE,
    GOVERNANCE_DELETE,
    GOVERNANCE_MANAGE,
    GOVERNANCE_UPDATE,
    GOVERNANCE_VIEW,
    GOVERNANCE_VIEW_CONFIDENTIAL,
)

# Authorization decorators (AND of codes is not used; ANY is applied).
_any_view = any_permission_required(GOVERNANCE_VIEW, GOVERNANCE_MANAGE)
_any_confidential_view = any_permission_required(
    GOVERNANCE_VIEW, GOVERNANCE_VIEW_CONFIDENTIAL, GOVERNANCE_MANAGE
)
_any_manage = any_permission_required(
    GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE
)
_any_delete = any_permission_required(GOVERNANCE_DELETE, GOVERNANCE_MANAGE)

# Models that carry a generated reference number must allocate one on create.
_MODEL_GOVERNANCE_TYPE: dict[type, str] = {
    Policy: GovernanceType.POLICY,
    RiskRegister: GovernanceType.RISK,
    ComplianceRequirement: GovernanceType.COMPLIANCE,
    InternalControl: GovernanceType.COMPLIANCE,
    EthicsCase: GovernanceType.ETHICS,
    SafeguardingCase: GovernanceType.SAFEGUARDING,
    IncidentReport: GovernanceType.INCIDENT,
    Complaint: GovernanceType.COMPLAINT,
    WhistleblowerReport: GovernanceType.WHISTLEBLOWER,
    CorrectivePreventiveAction: GovernanceType.CAPA,
    Document: GovernanceType.COMPLIANCE,
    GovernanceMeeting: GovernanceType.GOVERNANCE_MEETING,
}


def _allocate_reference_if_needed(request, obj) -> None:
    """Reserve a reference number for records that require one."""
    if not hasattr(obj, "reference_number") or obj.reference_number:
        return
    governance_type = _MODEL_GOVERNANCE_TYPE.get(type(obj), GovernanceType.COMPLIANCE)
    services.allocate_reference(request.user, obj, governance_type)


# ---------------------------------------------------------------------------
# Generic CRUD helpers (fail-closed querysets from the selectors layer).
# ---------------------------------------------------------------------------


def object_list(
    request,
    template_name,
    context_name,
    queryset,
    search_fields=(),
    paginate_by=25,
):
    """Generic list view fed by an already-authorized queryset."""
    queryset = queryset
    search_query = request.GET.get("search", "")
    if search_query:
        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f"{field}__icontains": search_query})
        if q_objects:
            queryset = queryset.filter(q_objects)
    paginator = Paginator(queryset, paginate_by)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        context_name: page_obj,
        "search_query": search_query,
        "is_paginated": page_obj.has_other_pages(),
    }
    return render(request, template_name, context)


def object_create(
    request,
    form_class,
    success_url,
    success_message,
    template_name="governance/object_form.html",
):
    """Generic create view for a governance record."""
    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if hasattr(obj, "created_by"):
                obj.created_by = request.user
            if hasattr(obj, "updated_by"):
                obj.updated_by = request.user
            _allocate_reference_if_needed(request, obj)
            obj.save()
            form.save_m2m()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = form_class()
    context = {
        "form": form,
        "list_url": success_url,
        "model_name": form_class.Meta.model._meta.verbose_name,
    }
    return render(request, template_name, context)


def object_update(
    request,
    model,
    form_class,
    pk,
    success_url,
    success_message,
    template_name="governance/object_form.html",
):
    """Generic update view for a governance record."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            if hasattr(obj, "updated_by"):
                obj.updated_by = request.user
            obj.save()
            form.save_m2m()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = form_class(instance=obj)
    context = {
        "form": form,
        "object": obj,
        "list_url": success_url,
        "model_name": model._meta.verbose_name,
    }
    return render(request, template_name, context)


def object_delete(
    request,
    model,
    pk,
    success_url,
    success_message,
    template_name="governance/object_confirm_delete.html",
):
    """Generic delete view for a governance record."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, success_message)
        return redirect(success_url)
    context = {
        "object": obj,
        "list_url": success_url,
        "model_name": model._meta.verbose_name,
    }
    return render(request, template_name, context)


def object_detail(request, queryset, pk, template_name, context_name):
    """Generic detail view fed by an already-authorized queryset."""
    obj = get_object_or_404(queryset, pk=pk)
    context = {context_name: obj}
    return render(request, template_name, context)


# ---------------------------------------------------------------------------
# Governance Dashboard
# ---------------------------------------------------------------------------


@_any_view
def governance_dashboard(request):
    """Overview of governance, risk, compliance and safeguarding activities."""
    provider = services.GovernanceDashboardProvider(request.user)
    summary = provider.get_summary()
    context = {
        **summary,
        "compliance_status": provider.get_compliance_status(),
        "high_risk_items": provider.get_high_risk_items(),
        "upcoming_deadlines": provider.get_upcoming_deadlines(),
        "recent_activities": provider.get_recent_activities(),
        "upcoming_meetings": provider.get_upcoming_meetings(),
        "recent_policies": provider.get_recent_policies(),
        "recent_risks": provider.get_recent_risks(),
        "recent_incidents": provider.get_recent_incidents(),
        "recent_complaints": provider.get_recent_complaints(),
        "unread_notifications": provider.get_unread_notification_count(),
    }
    return render(request, "governance/dashboard.html", context)


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------


@_any_view
def policy_list(request):
    return object_list(
        request,
        "governance/policy_list.html",
        "policies",
        selectors.get_accessible_policies(request.user),
        search_fields=("title", "reference_number", "policy_category"),
    )


@_any_manage
def policy_create(request):
    return object_create(
        request,
        PolicyForm,
        "governance:policy_list",
        "Policy created successfully.",
    )


@_any_manage
def policy_update(request, pk):
    return object_update(
        request,
        Policy,
        PolicyForm,
        pk,
        "governance:policy_list",
        "Policy updated successfully.",
    )


@_any_delete
def policy_delete(request, pk):
    return object_delete(
        request,
        Policy,
        pk,
        "governance:policy_list",
        "Policy deleted successfully.",
    )


@_any_view
def policy_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_policies(request.user),
        pk,
        "governance/policy_detail.html",
        "policy",
    )


@_any_manage
def policy_version_create(request, policy_pk):
    """Create a new version of a policy."""
    policy = get_object_or_404(
        selectors.get_accessible_policies(request.user), pk=policy_pk
    )
    if request.method == "POST":
        form = PolicyVersionForm(request.POST, request.FILES)
        if form.is_valid():
            version = form.save(commit=False)
            version.policy = policy
            version.save()
            form.save_m2m()
            messages.success(request, "Policy version created successfully.")
            return redirect("governance:policy_detail", pk=policy_pk)
    else:
        form = PolicyVersionForm()
    context = {"form": form, "policy": policy}
    return render(request, "governance/policy_version_form.html", context)


@_any_manage
def policy_acknowledgement_create(request, policy_pk):
    """Record an acknowledgement of a policy."""
    policy = get_object_or_404(
        selectors.get_accessible_policies(request.user), pk=policy_pk
    )
    if request.method == "POST":
        form = PolicyAcknowledgementForm(request.POST)
        if form.is_valid():
            acknowledgement = form.save(commit=False)
            acknowledgement.policy = policy
            acknowledgement.save()
            messages.success(request, "Policy acknowledgement recorded.")
            return redirect("governance:policy_detail", pk=policy_pk)
    else:
        form = PolicyAcknowledgementForm()
    context = {"form": form, "policy": policy}
    return render(request, "governance/policy_acknowledgement_form.html", context)


# ---------------------------------------------------------------------------
# Risks
# ---------------------------------------------------------------------------


@_any_view
def risk_register_list(request):
    return object_list(
        request,
        "governance/risk_register_list.html",
        "risk_registers",
        selectors.get_accessible_risks(request.user),
        search_fields=("title", "reference_number", "risk_category"),
    )


@_any_manage
def risk_register_create(request):
    return object_create(
        request,
        RiskRegisterForm,
        "governance:risk_register_list",
        "Risk register entry created successfully.",
    )


@_any_manage
def risk_register_update(request, pk):
    return object_update(
        request,
        RiskRegister,
        RiskRegisterForm,
        pk,
        "governance:risk_register_list",
        "Risk register entry updated successfully.",
    )


@_any_delete
def risk_register_delete(request, pk):
    return object_delete(
        request,
        RiskRegister,
        pk,
        "governance:risk_register_list",
        "Risk register entry deleted successfully.",
    )


@_any_view
def risk_register_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_risks(request.user),
        pk,
        "governance/risk_register_detail.html",
        "risk_register",
    )


@_any_manage
def risk_assessment_create(request, risk_pk):
    """Add an assessment for a risk register entry."""
    risk = get_object_or_404(selectors.get_accessible_risks(request.user), pk=risk_pk)
    if request.method == "POST":
        form = RiskAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.risk_register = risk
            assessment.save()
            messages.success(request, "Risk assessment recorded successfully.")
            return redirect("governance:risk_register_detail", pk=risk_pk)
    else:
        form = RiskAssessmentForm()
    context = {"form": form, "risk": risk}
    return render(request, "governance/risk_assessment_form.html", context)


@_any_manage
def risk_treatment_plan_create(request, risk_pk):
    """Add a treatment plan for a risk register entry."""
    risk = get_object_or_404(selectors.get_accessible_risks(request.user), pk=risk_pk)
    if request.method == "POST":
        form = RiskTreatmentPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.risk_register = risk
            plan.save()
            messages.success(request, "Risk treatment plan created successfully.")
            return redirect("governance:risk_register_detail", pk=risk_pk)
    else:
        form = RiskTreatmentPlanForm()
    context = {"form": form, "risk": risk}
    return render(request, "governance/risk_treatment_plan_form.html", context)


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------


@_any_view
def compliance_requirement_list(request):
    return object_list(
        request,
        "governance/compliance_requirement_list.html",
        "compliance_requirements",
        selectors.get_accessible_compliance_requirements(request.user),
        search_fields=("title", "reference_number", "compliance_type"),
    )


@_any_manage
def compliance_requirement_create(request):
    return object_create(
        request,
        ComplianceRequirementForm,
        "governance:compliance_requirement_list",
        "Compliance requirement created successfully.",
    )


@_any_manage
def compliance_requirement_update(request, pk):
    return object_update(
        request,
        ComplianceRequirement,
        ComplianceRequirementForm,
        pk,
        "governance:compliance_requirement_list",
        "Compliance requirement updated successfully.",
    )


@_any_delete
def compliance_requirement_delete(request, pk):
    return object_delete(
        request,
        ComplianceRequirement,
        pk,
        "governance:compliance_requirement_list",
        "Compliance requirement deleted successfully.",
    )


@_any_view
def compliance_requirement_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_compliance_requirements(request.user),
        pk,
        "governance/compliance_requirement_detail.html",
        "compliance_requirement",
    )


@_any_manage
def compliance_assessment_create(request, requirement_pk):
    """Record an assessment for a compliance requirement."""
    requirement = get_object_or_404(
        selectors.get_accessible_compliance_requirements(request.user),
        pk=requirement_pk,
    )
    if request.method == "POST":
        form = ComplianceAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.compliance_requirement = requirement
            assessment.save()
            form.save_m2m()
            messages.success(request, "Compliance assessment recorded successfully.")
            return redirect(
                "governance:compliance_requirement_detail", pk=requirement_pk
            )
    else:
        form = ComplianceAssessmentForm()
    context = {"form": form, "compliance_requirement": requirement}
    return render(request, "governance/compliance_assessment_form.html", context)


# ---------------------------------------------------------------------------
# Internal Controls
# ---------------------------------------------------------------------------


@_any_view
def internal_control_list(request):
    return object_list(
        request,
        "governance/internal_control_list.html",
        "internal_controls",
        selectors.get_accessible_internal_controls(request.user),
        search_fields=("title", "reference_number", "control_type"),
    )


@_any_manage
def internal_control_create(request):
    return object_create(
        request,
        InternalControlForm,
        "governance:internal_control_list",
        "Internal control created successfully.",
    )


@_any_manage
def internal_control_update(request, pk):
    return object_update(
        request,
        InternalControl,
        InternalControlForm,
        pk,
        "governance:internal_control_list",
        "Internal control updated successfully.",
    )


@_any_delete
def internal_control_delete(request, pk):
    return object_delete(
        request,
        InternalControl,
        pk,
        "governance:internal_control_list",
        "Internal control deleted successfully.",
    )


@_any_view
def internal_control_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_internal_controls(request.user),
        pk,
        "governance/internal_control_detail.html",
        "internal_control",
    )


# ---------------------------------------------------------------------------
# Ethics & Conflict of Interest
# ---------------------------------------------------------------------------


@_any_view
def ethics_case_list(request):
    return object_list(
        request,
        "governance/ethics_case_list.html",
        "ethics_cases",
        selectors.get_accessible_ethics_cases(request.user),
        search_fields=("title", "reference_number", "case_type"),
    )


@_any_manage
def ethics_case_create(request):
    return object_create(
        request,
        EthicsCaseForm,
        "governance:ethics_case_list",
        "Ethics case created successfully.",
    )


@_any_manage
def ethics_case_update(request, pk):
    return object_update(
        request,
        EthicsCase,
        EthicsCaseForm,
        pk,
        "governance:ethics_case_list",
        "Ethics case updated successfully.",
    )


@_any_delete
def ethics_case_delete(request, pk):
    return object_delete(
        request,
        EthicsCase,
        pk,
        "governance:ethics_case_list",
        "Ethics case deleted successfully.",
    )


@_any_view
def ethics_case_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_ethics_cases(request.user),
        pk,
        "governance/ethics_case_detail.html",
        "ethics_case",
    )


@_any_manage
def conflict_of_interest_declaration_list(request):
    return object_list(
        request,
        "governance/conflict_of_interest_declaration_list.html",
        "conflict_of_interest_declarations",
        selectors.get_accessible_conflict_declarations(request.user),
        search_fields=("nature_of_conflict", "related_organization"),
    )


@_any_manage
def conflict_of_interest_declaration_create(request):
    return object_create(
        request,
        ConflictOfInterestDeclarationForm,
        "governance:conflict_of_interest_declaration_list",
        "Conflict of interest declaration recorded successfully.",
    )


@_any_manage
def conflict_of_interest_declaration_update(request, pk):
    return object_update(
        request,
        ConflictOfInterestDeclaration,
        ConflictOfInterestDeclarationForm,
        pk,
        "governance:conflict_of_interest_declaration_list",
        "Conflict of interest declaration updated successfully.",
    )


@_any_delete
def conflict_of_interest_declaration_delete(request, pk):
    return object_delete(
        request,
        ConflictOfInterestDeclaration,
        pk,
        "governance:conflict_of_interest_declaration_list",
        "Conflict of interest declaration deleted successfully.",
    )


@_any_view
def conflict_of_interest_declaration_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_conflict_declarations(request.user),
        pk,
        "governance/conflict_of_interest_declaration_detail.html",
        "conflict_of_interest_declaration",
    )


# ---------------------------------------------------------------------------
# Safeguarding (confidential)
# ---------------------------------------------------------------------------


@_any_confidential_view
def safeguarding_case_list(request):
    return object_list(
        request,
        "governance/safeguarding_case_list.html",
        "safeguarding_cases",
        selectors.get_accessible_safeguarding_cases(request.user),
        search_fields=("title", "reference_number", "case_category"),
    )


@_any_confidential_view
def safeguarding_case_create(request):
    return object_create(
        request,
        SafeguardingCaseForm,
        "governance:safeguarding_case_list",
        "Safeguarding case created successfully.",
    )


@_any_confidential_view
def safeguarding_case_update(request, pk):
    return object_update(
        request,
        SafeguardingCase,
        SafeguardingCaseForm,
        pk,
        "governance:safeguarding_case_list",
        "Safeguarding case updated successfully.",
    )


@_any_delete
def safeguarding_case_delete(request, pk):
    return object_delete(
        request,
        SafeguardingCase,
        pk,
        "governance:safeguarding_case_list",
        "Safeguarding case deleted successfully.",
    )


@_any_confidential_view
def safeguarding_case_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_safeguarding_cases(request.user),
        pk,
        "governance/safeguarding_case_detail.html",
        "safeguarding_case",
    )


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------


@_any_view
def incident_report_list(request):
    return object_list(
        request,
        "governance/incident_report_list.html",
        "incident_reports",
        selectors.get_accessible_incidents(request.user),
        search_fields=("title", "reference_number", "incident_category"),
    )


@_any_manage
def incident_report_create(request):
    return object_create(
        request,
        IncidentReportForm,
        "governance:incident_report_list",
        "Incident report created successfully.",
    )


@_any_manage
def incident_report_update(request, pk):
    return object_update(
        request,
        IncidentReport,
        IncidentReportForm,
        pk,
        "governance:incident_report_list",
        "Incident report updated successfully.",
    )


@_any_delete
def incident_report_delete(request, pk):
    return object_delete(
        request,
        IncidentReport,
        pk,
        "governance:incident_report_list",
        "Incident report deleted successfully.",
    )


@_any_view
def incident_report_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_incidents(request.user),
        pk,
        "governance/incident_report_detail.html",
        "incident_report",
    )


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------


@_any_view
def complaint_list(request):
    return object_list(
        request,
        "governance/complaint_list.html",
        "complaints",
        selectors.get_accessible_complaints(request.user),
        search_fields=("title", "reference_number", "complaint_type"),
    )


@_any_manage
def complaint_create(request):
    return object_create(
        request,
        ComplaintForm,
        "governance:complaint_list",
        "Complaint created successfully.",
    )


@_any_manage
def complaint_update(request, pk):
    return object_update(
        request,
        Complaint,
        ComplaintForm,
        pk,
        "governance:complaint_list",
        "Complaint updated successfully.",
    )


@_any_delete
def complaint_delete(request, pk):
    return object_delete(
        request,
        Complaint,
        pk,
        "governance:complaint_list",
        "Complaint deleted successfully.",
    )


@_any_view
def complaint_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_complaints(request.user),
        pk,
        "governance/complaint_detail.html",
        "complaint",
    )


# ---------------------------------------------------------------------------
# Whistleblower (confidential)
# ---------------------------------------------------------------------------


@_any_confidential_view
def whistleblower_report_list(request):
    return object_list(
        request,
        "governance/whistleblower_report_list.html",
        "whistleblower_reports",
        selectors.get_accessible_whistleblower_reports(request.user),
        search_fields=("title", "reference_number", "report_type"),
    )


@_any_confidential_view
def whistleblower_report_create(request):
    return object_create(
        request,
        WhistleblowerReportForm,
        "governance:whistleblower_report_list",
        "Whistleblower report submitted successfully.",
    )


@_any_confidential_view
def whistleblower_report_update(request, pk):
    return object_update(
        request,
        WhistleblowerReport,
        WhistleblowerReportForm,
        pk,
        "governance:whistleblower_report_list",
        "Whistleblower report updated successfully.",
    )


@_any_delete
def whistleblower_report_delete(request, pk):
    return object_delete(
        request,
        WhistleblowerReport,
        pk,
        "governance:whistleblower_report_list",
        "Whistleblower report deleted successfully.",
    )


@_any_confidential_view
def whistleblower_report_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_whistleblower_reports(request.user),
        pk,
        "governance/whistleblower_report_detail.html",
        "whistleblower_report",
    )


# ---------------------------------------------------------------------------
# Corrective & Preventive Actions
# ---------------------------------------------------------------------------


@_any_view
def corrective_preventive_action_list(request):
    return object_list(
        request,
        "governance/corrective_preventive_action_list.html",
        "corrective_preventive_actions",
        selectors.get_accessible_capas(request.user),
        search_fields=("title", "reference_number", "action_type"),
    )


@_any_manage
def corrective_preventive_action_create(request):
    return object_create(
        request,
        CorrectivePreventiveActionForm,
        "governance:corrective_preventive_action_list",
        "Corrective & preventive action created successfully.",
    )


@_any_manage
def corrective_preventive_action_update(request, pk):
    return object_update(
        request,
        CorrectivePreventiveAction,
        CorrectivePreventiveActionForm,
        pk,
        "governance:corrective_preventive_action_list",
        "Corrective & preventive action updated successfully.",
    )


@_any_delete
def corrective_preventive_action_delete(request, pk):
    return object_delete(
        request,
        CorrectivePreventiveAction,
        pk,
        "governance:corrective_preventive_action_list",
        "Corrective & preventive action deleted successfully.",
    )


@_any_view
def corrective_preventive_action_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_capas(request.user),
        pk,
        "governance/corrective_preventive_action_detail.html",
        "corrective_preventive_action",
    )


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@_any_view
def document_list(request):
    return object_list(
        request,
        "governance/document_list.html",
        "documents",
        selectors.get_accessible_documents(request.user),
        search_fields=("title", "reference_number", "document_type"),
    )


@_any_manage
def document_create(request):
    return object_create(
        request,
        DocumentForm,
        "governance:document_list",
        "Document uploaded successfully.",
    )


@_any_manage
def document_update(request, pk):
    return object_update(
        request,
        Document,
        DocumentForm,
        pk,
        "governance:document_list",
        "Document updated successfully.",
    )


@_any_delete
def document_delete(request, pk):
    return object_delete(
        request,
        Document,
        pk,
        "governance:document_list",
        "Document deleted successfully.",
    )


@_any_view
def document_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_documents(request.user),
        pk,
        "governance/document_detail.html",
        "document",
    )


# ---------------------------------------------------------------------------
# Governance Meetings
# ---------------------------------------------------------------------------


@_any_view
def governance_meeting_list(request):
    return object_list(
        request,
        "governance/governance_meeting_list.html",
        "governance_meetings",
        selectors.get_accessible_meetings(request.user),
        search_fields=("title", "reference_number", "meeting_type"),
    )


@_any_manage
def governance_meeting_create(request):
    return object_create(
        request,
        GovernanceMeetingForm,
        "governance:governance_meeting_list",
        "Governance meeting created successfully.",
    )


@_any_manage
def governance_meeting_update(request, pk):
    return object_update(
        request,
        GovernanceMeeting,
        GovernanceMeetingForm,
        pk,
        "governance:governance_meeting_list",
        "Governance meeting updated successfully.",
    )


@_any_delete
def governance_meeting_delete(request, pk):
    return object_delete(
        request,
        GovernanceMeeting,
        pk,
        "governance:governance_meeting_list",
        "Governance meeting deleted successfully.",
    )


@_any_view
def governance_meeting_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_meetings(request.user),
        pk,
        "governance/governance_meeting_detail.html",
        "governance_meeting",
    )


@_any_manage
def meeting_attendance_create(request, meeting_pk):
    """Record attendance for a governance meeting."""
    meeting = get_object_or_404(
        selectors.get_accessible_meetings(request.user), pk=meeting_pk
    )
    if request.method == "POST":
        form = MeetingAttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.meeting = meeting
            attendance.save()
            messages.success(request, "Meeting attendance recorded successfully.")
            return redirect("governance:governance_meeting_detail", pk=meeting_pk)
    else:
        form = MeetingAttendanceForm()
    context = {"form": form, "meeting": meeting}
    return render(request, "governance/meeting_attendance_form.html", context)


# ---------------------------------------------------------------------------
# Notifications & Timeline
# ---------------------------------------------------------------------------


@_any_view
def governance_notification_list(request):
    """List governance notifications addressed to the requesting user."""
    notifications = GovernanceNotification.objects.filter(recipient=request.user)
    page_obj = Paginator(notifications, 25).get_page(request.GET.get("page"))
    context = {
        "governance_notifications": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "unread_count": selectors.get_unread_notification_count(request.user),
    }
    return render(request, "governance/governance_notification_list.html", context)


@_any_view
def governance_notification_mark_as_read(request, pk):
    """Mark a single governance notification as read."""
    notification = get_object_or_404(
        GovernanceNotification, pk=pk, recipient=request.user
    )
    if request.method == "POST":
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
        messages.success(request, "Notification marked as read.")
        return redirect("governance:governance_notification_list")
    context = {"notification": notification}
    return render(
        request, "governance/governance_notification_confirm_mark_as_read.html", context
    )


@_any_view
def governance_timeline_list(request):
    """List governance timeline events."""
    return object_list(
        request,
        "governance/governance_timeline_list.html",
        "governance_timelines",
        selectors.get_accessible_timeline(request.user),
        search_fields=("description", "reference_number", "module"),
    )
