"""Views for Governance, Risk, Compliance and Safeguarding (Phase 29)."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from apps.core.constants import StatusConstants
from .models import (
    GovernanceRecord,
    Policy,
    PolicyVersion,
    PolicyAcknowledgement,
    RiskRegister,
    RiskAssessment,
    RiskTreatmentPlan,
    ComplianceRequirement,
    ComplianceAssessment,
    InternalControl,
    EthicsCase,
    ConflictOfInterestDeclaration,
    SafeguardingCase,
    IncidentReport,
    Complaint,
    WhistleblowerReport,
    CorrectivePreventiveAction,
    Document,
    GovernanceMeeting,
    MeetingAttendance,
    GovernanceNotification,
    GovernanceTimeline,
)
from .forms import (
    GovernanceRecordForm,
    PolicyForm,
    PolicyVersionForm,
    PolicyAcknowledgementForm,
    RiskRegisterForm,
    RiskAssessmentForm,
    RiskTreatmentPlanForm,
    ComplianceRequirementForm,
    ComplianceAssessmentForm,
    InternalControlForm,
    EthicsCaseForm,
    ConflictOfInterestDeclarationForm,
    SafeguardingCaseForm,
    IncidentReportForm,
    ComplaintForm,
    WhistleblowerReportForm,
    CorrectivePreventiveActionForm,
    DocumentForm,
    GovernanceMeetingForm,
    MeetingAttendanceForm,
    GovernanceNotificationForm,
    GovernanceTimelineForm,
)

# Generic view functions for CRUD operations
def object_list(request, model, template_name='governance/object_list.html', context_name='object_list', paginate_by=25):
    """Generic list view for a model."""
    queryset = model.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    paginator = Paginator(queryset, paginate_by)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        context_name: page_obj,
        'search_query': search_query,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, template_name, context)

def object_create(request, model_form, template_name, success_url, success_message):
    """Generic create view for a model."""
    if request.method == 'POST':
        form = model_form(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = model_form()
    context = {
        'form': form,
        'list_url': success_url,
    }
    return render(request, template_name, context)

def object_update(request, model, model_form, pk, template_name, success_url, success_message):
    """Generic update view for a model."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        form = model_form(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = model_form(instance=obj)
    context = {
        'form': form,
        'object': obj,
        'list_url': success_url,
    }
    return render(request, template_name, context)

def object_delete(request, model, pk, success_url, success_message, template_name='governance/object_confirm_delete.html'):
    """Generic delete view for a model."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, success_message)
        return redirect(success_url)
    context = {
        'object': obj,
        'list_url': success_url,
        'model_name': model._meta.verbose_name,
    }
    return render(request, template_name, context)


# Governance Dashboard
@login_required
def governance_dashboard(request):
    """Overview of governance, risk, compliance and safeguarding activities."""
    active_risks = RiskRegister.objects.filter(status=StatusConstants.ACTIVE)
    high_risks = [r for r in active_risks if r.likelihood * r.impact >= 11]
    critical_risks = [r for r in active_risks if r.likelihood * r.impact >= 16]

    pending_statuses = [StatusConstants.DRAFT, StatusConstants.PENDING_REVIEW]
    now = timezone.now()

    context = {
        'total_policies': Policy.objects.filter(status=StatusConstants.ACTIVE).count(),
        'pending_policies': Policy.objects.filter(status__in=pending_statuses).count(),
        'total_risks': active_risks.count(),
        'high_risks': len(high_risks),
        'critical_risks': len(critical_risks),
        'total_safeguarding_cases': SafeguardingCase.objects.exclude(
            status=StatusConstants.ARCHIVED
        ).count(),
        'total_compliance_reqs': ComplianceRequirement.objects.filter(is_active=True).count(),
        'total_controls': InternalControl.objects.filter(is_effective=True).count(),
        'total_ethics_cases': EthicsCase.objects.exclude(status=StatusConstants.ARCHIVED).count(),
        'total_incidents': IncidentReport.objects.exclude(
            status=StatusConstants.ARCHIVED
        ).count(),
        'total_complaints': Complaint.objects.exclude(status=StatusConstants.ARCHIVED).count(),
        'total_whistleblower_reports': WhistleblowerReport.objects.exclude(
            status=StatusConstants.ARCHIVED
        ).count(),
        'total_capas': CorrectivePreventiveAction.objects.exclude(
            status=StatusConstants.ARCHIVED
        ).count(),
        'total_documents': Document.objects.count(),
        'total_meetings': GovernanceMeeting.objects.exclude(
            status=StatusConstants.ARCHIVED
        ).count(),
        'upcoming_meetings': GovernanceMeeting.objects.filter(
            scheduled_date__gte=now
        ).order_by('scheduled_date')[:5],
        'unread_notifications': GovernanceNotification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count(),
        'recent_policies': Policy.objects.order_by('-created_at')[:5],
        'recent_risks': RiskRegister.objects.order_by('-created_at')[:5],
        'recent_incidents': IncidentReport.objects.order_by('-created_at')[:5],
        'recent_complaints': Complaint.objects.order_by('-created_at')[:5],
    }
    return render(request, 'governance/dashboard.html', context)


# Governance Record Views
@login_required
def governance_record_list(request):
    return object_list(request, GovernanceRecord, 'governance/governance_record_list.html', 'governance_records')

@login_required
def governance_record_create(request):
    return object_create(
        request,
        GovernanceRecordForm,
        'governance/governance_record_form.html',
        'governance:governance_record_list',
        'Governance record created successfully.'
    )

@login_required
def governance_record_update(request, pk):
    return object_update(
        request,
        GovernanceRecord,
        GovernanceRecordForm,
        pk,
        'governance/governance_record_form.html',
        'governance:governance_record_list',
        'Governance record updated successfully.'
    )

@login_required
def governance_record_delete(request, pk):
    return object_delete(
        request,
        GovernanceRecord,
        pk,
        'governance:governance_record_list',
        'Governance record deleted successfully.'
    )

@login_required
def governance_record_detail(request, pk):
    return object_detail(
        request,
        GovernanceRecord,
        pk,
        'governance/governance_record_detail.html',
        'governance_record'
    )

# Policy Views
@login_required
def policy_list(request):
    return object_list(request, Policy, 'governance/policy_list.html', 'policies')

@login_required
def policy_create(request):
    return object_create(
        request,
        PolicyForm,
        'governance/policy_form.html',
        'governance:policy_list',
        'Policy created successfully.'
    )

@login_required
def policy_update(request, pk):
    return object_update(
        request,
        Policy,
        PolicyForm,
        pk,
        'governance/policy_form.html',
        'governance:policy_list',
        'Policy updated successfully.'
    )

@login_required
def policy_delete(request, pk):
    return object_delete(
        request,
        Policy,
        pk,
        'governance:policy_list',
        'Policy deleted successfully.'
    )

@login_required
def policy_detail(request, pk):
    return object_detail(
        request,
        Policy,
        pk,
        'governance/policy_detail.html',
        'policy'
    )

# Policy Version Views
@login_required
def policy_version_list(request):
    return object_list(request, PolicyVersion, 'governance/policy_version_list.html', 'policy_versions')

@login_required
def policy_version_create(request):
    return object_create(
        request,
        PolicyVersionForm,
        'governance/policy_version_form.html',
        'governance:policy_version_list',
        'Policy version created successfully.'
    )

@login_required
def policy_version_update(request, pk):
    return object_update(
        request,
        PolicyVersion,
        PolicyVersionForm,
        pk,
        'governance/policy_version_form.html',
        'governance:policy_version_list',
        'Policy version updated successfully.'
    )

@login_required
def policy_version_delete(request, pk):
    return object_delete(
        request,
        PolicyVersion,
        pk,
        'governance:policy_version_list',
        'Policy version deleted successfully.'
    )

@login_required
def policy_version_detail(request, pk):
    return object_detail(
        request,
        PolicyVersion,
        pk,
        'governance/policy_version_detail.html',
        'policy_version'
    )

# Policy Acknowledgement Views
@login_required
def policy_acknowledgement_list(request):
    return object_list(request, PolicyAcknowledgement, 'governance/policy_acknowledgement_list.html', 'policy_acknowledgements')

@login_required
def policy_acknowledgement_create(request):
    return object_create(
        request,
        PolicyAcknowledgementForm,
        'governance/policy_acknowledgement_form.html',
        'governance:policy_acknowledgement_list',
        'Policy acknowledgement created successfully.'
    )

@login_required
def policy_acknowledgement_update(request, pk):
    return object_update(
        request,
        PolicyAcknowledgement,
        PolicyAcknowledgementForm,
        pk,
        'governance/policy_acknowledgement_form.html',
        'governance:policy_acknowledgement_list',
        'Policy acknowledgement updated successfully.'
    )

@login_required
def policy_acknowledgement_delete(request, pk):
    return object_delete(
        request,
        PolicyAcknowledgement,
        pk,
        'governance:policy_acknowledgement_list',
        'Policy acknowledgement deleted successfully.'
    )

@login_required
def policy_acknowledgement_detail(request, pk):
    return object_detail(
        request,
        PolicyAcknowledgement,
        pk,
        'governance/policy_acknowledgement_detail.html',
        'policy_acknowledgement'
    )

# Risk Register Views
@login_required
def risk_register_list(request):
    return object_list(request, RiskRegister, 'governance/risk_register_list.html', 'risk_registers')

@login_required
def risk_register_create(request):
    return object_create(
        request,
        RiskRegisterForm,
        'governance/risk_register_form.html',
        'governance:risk_register_list',
        'Risk register created successfully.'
    )

@login_required
def risk_register_update(request, pk):
    return object_update(
        request,
        RiskRegister,
        RiskRegisterForm,
        pk,
        'governance/risk_register_form.html',
        'governance:risk_register_list',
        'Risk register updated successfully.'
    )

@login_required
def risk_register_delete(request, pk):
    return object_delete(
        request,
        RiskRegister,
        pk,
        'governance:risk_register_list',
        'Risk register deleted successfully.'
    )

@login_required
def risk_register_detail(request, pk):
    return object_detail(
        request,
        RiskRegister,
        pk,
        'governance/risk_register_detail.html',
        'risk_register'
    )

# Risk Assessment Views
@login_required
def risk_assessment_list(request):
    return object_list(request, RiskAssessment, 'governance/risk_assessment_list.html', 'risk_assessments')

@login_required
def risk_assessment_create(request):
    return object_create(
        request,
        RiskAssessmentForm,
        'governance/risk_assessment_form.html',
        'governance:risk_assessment_list',
        'Risk assessment created successfully.'
    )

@login_required
def risk_assessment_update(request, pk):
    return object_update(
        request,
        RiskAssessment,
        RiskAssessmentForm,
        pk,
        'governance/risk_assessment_form.html',
        'governance:risk_assessment_list',
        'Risk assessment updated successfully.'
    )

@login_required
def risk_assessment_delete(request, pk):
    return object_delete(
        request,
        RiskAssessment,
        pk,
        'governance:risk_assessment_list',
        'Risk assessment deleted successfully.'
    )

@login_required
def risk_assessment_detail(request, pk):
    return object_detail(
        request,
        RiskAssessment,
        pk,
        'governance/risk_assessment_detail.html',
        'risk_assessment'
    )

# Risk Treatment Plan Views
@login_required
def risk_treatment_plan_list(request):
    return object_list(request, RiskTreatmentPlan, 'governance/risk_treatment_plan_list.html', 'risk_treatment_plans')

@login_required
def risk_treatment_plan_create(request):
    return object_create(
        request,
        RiskTreatmentPlanForm,
        'governance/risk_treatment_plan_form.html',
        'governance:risk_treatment_plan_list',
        'Risk treatment plan created successfully.'
    )

@login_required
def risk_treatment_plan_update(request, pk):
    return object_update(
        request,
        RiskTreatmentPlan,
        RiskTreatmentPlanForm,
        pk,
        'governance/risk_treatment_plan_form.html',
        'governance:risk_treatment_plan_list',
        'Risk treatment plan updated successfully.'
    )

@login_required
def risk_treatment_plan_delete(request, pk):
    return object_delete(
        request,
        RiskTreatmentPlan,
        pk,
        'governance:risk_treatment_plan_list',
        'Risk treatment plan deleted successfully.'
    )

@login_required
def risk_treatment_plan_detail(request, pk):
    return object_detail(
        request,
        RiskTreatmentPlan,
        pk,
        'governance/risk_treatment_plan_detail.html',
        'risk_treatment_plan'
    )

# Compliance Requirement Views
@login_required
def compliance_requirement_list(request):
    return object_list(request, ComplianceRequirement, 'governance/compliance_requirement_list.html', 'compliance_requirements')

@login_required
def compliance_requirement_create(request):
    return object_create(
        request,
        ComplianceRequirementForm,
        'governance/compliance_requirement_form.html',
        'governance:compliance_requirement_list',
        'Compliance requirement created successfully.'
    )

@login_required
def compliance_requirement_update(request, pk):
    return object_update(
        request,
        ComplianceRequirement,
        ComplianceRequirementForm,
        pk,
        'governance/compliance_requirement_form.html',
        'governance:compliance_requirement_list',
        'Compliance requirement updated successfully.'
    )

@login_required
def compliance_requirement_delete(request, pk):
    return object_delete(
        request,
        ComplianceRequirement,
        pk,
        'governance:compliance_requirement_list',
        'Compliance requirement deleted successfully.'
    )

@login_required
def compliance_requirement_detail(request, pk):
    return object_detail(
        request,
        ComplianceRequirement,
        pk,
        'governance/compliance_requirement_detail.html',
        'compliance_requirement'
    )

# Compliance Assessment Views
@login_required
def compliance_assessment_list(request):
    return object_list(request, ComplianceAssessment, 'governance/compliance_assessment_list.html', 'compliance_assessments')

@login_required
def compliance_assessment_create(request):
    return object_create(
        request,
        ComplianceAssessmentForm,
        'governance/compliance_assessment_form.html',
        'governance:compliance_assessment_list',
        'Compliance assessment created successfully.'
    )

@login_required
def compliance_assessment_update(request, pk):
    return object_update(
        request,
        ComplianceAssessment,
        ComplianceAssessmentForm,
        pk,
        'governance/compliance_assessment_form.html',
        'governance:compliance_assessment_list',
        'Compliance assessment updated successfully.'
    )

@login_required
def compliance_assessment_delete(request, pk):
    return object_delete(
        request,
        ComplianceAssessment,
        pk,
        'governance:compliance_assessment_list',
        'Compliance assessment deleted successfully.'
    )

@login_required
def compliance_assessment_detail(request, pk):
    return object_detail(
        request,
        ComplianceAssessment,
        pk,
        'governance/compliance_assessment_detail.html',
        'compliance_assessment'
    )

# Internal Control Views
@login_required
def internal_control_list(request):
    return object_list(request, InternalControl, 'governance/internal_control_list.html', 'internal_controls')

@login_required
def internal_control_create(request):
    return object_create(
        request,
        InternalControlForm,
        'governance/internal_control_form.html',
        'governance:internal_control_list',
        'Internal control created successfully.'
    )

@login_required
def internal_control_update(request, pk):
    return object_update(
        request,
        InternalControl,
        InternalControlForm,
        pk,
        'governance/internal_control_form.html',
        'governance:internal_control_list',
        'Internal control updated successfully.'
    )

@login_required
def internal_control_delete(request, pk):
    return object_delete(
        request,
        InternalControl,
        pk,
        'governance:internal_control_list',
        'Internal control deleted successfully.'
    )

@login_required
def internal_control_detail(request, pk):
    return object_detail(
        request,
        InternalControl,
        pk,
        'governance/internal_control_detail.html',
        'internal_control'
    )

# Ethics Case Views
@login_required
def ethics_case_list(request):
    return object_list(request, EthicsCase, 'governance/ethics_case_list.html', 'ethics_cases')

@login_required
def ethics_case_create(request):
    return object_create(
        request,
        EthicsCaseForm,
        'governance/ethics_case_form.html',
        'governance:ethics_case_list',
        'Ethics case created successfully.'
    )

@login_required
def ethics_case_update(request, pk):
    return object_update(
        request,
        EthicsCase,
        EthicsCaseForm,
        pk,
        'governance/ethics_case_form.html',
        'governance:ethics_case_list',
        'Ethics case updated successfully.'
    )

@login_required
def ethics_case_delete(request, pk):
    return object_delete(
        request,
        EthicsCase,
        pk,
        'governance:ethics_case_list',
        'Ethics case deleted successfully.'
    )

@login_required
def ethics_case_detail(request, pk):
    return object_detail(
        request,
        EthicsCase,
        pk,
        'governance/ethics_case_detail.html',
        'ethics_case'
    )

# Safeguarding Case Views
@login_required
def safeguarding_case_list(request):
    return object_list(request, SafeguardingCase, 'governance/safeguarding_case_list.html', 'safeguarding_cases')

@login_required
def safeguarding_case_create(request):
    return object_create(
        request,
        SafeguardingCaseForm,
        'governance/safeguarding_case_form.html',
        'governance:safeguarding_case_list',
        'Safeguarding case created successfully.'
    )

@login_required
def safeguarding_case_update(request, pk):
    return object_update(
        request,
        SafeguardingCase,
        SafeguardingCaseForm,
        pk,
        'governance/safeguarding_case_form.html',
        'governance:safeguarding_case_list',
        'Safeguarding case updated successfully.'
    )

@login_required
def safeguarding_case_delete(request, pk):
    return object_delete(
        request,
        SafeguardingCase,
        pk,
        'governance:safeguarding_case_list',
        'Safeguarding case deleted successfully.'
    )

@login_required
def safeguarding_case_detail(request, pk):
    return object_detail(
        request,
        SafeguardingCase,
        pk,
        'governance/safeguarding_case_detail.html',
        'safeguarding_case'
    )

# Incident Report Views
@login_required
def incident_report_list(request):
    return object_list(request, IncidentReport, 'governance/incident_report_list.html', 'incident_reports')

@login_required
def incident_report_create(request):
    return object_create(
        request,
        IncidentReportForm,
        'governance/incident_report_form.html',
        'governance:incident_report_list',
        'Incident report created successfully.'
    )

@login_required
def incident_report_update(request, pk):
    return object_update(
        request,
        IncidentReport,
        IncidentReportForm,
        pk,
        'governance/incident_report_form.html',
        'governance:incident_report_list',
        'Incident report updated successfully.'
    )

@login_required
def incident_report_delete(request, pk):
    return object_delete(
        request,
        IncidentReport,
        pk,
        'governance:incident_report_list',
        'Incident report deleted successfully.'
    )

@login_required
def incident_report_detail(request, pk):
    return object_detail(
        request,
        IncidentReport,
        pk,
        'governance/incident_report_detail.html',
        'incident_report'
    )

# Whistleblower Report Views
@login_required
def whistleblower_report_list(request):
    return object_list(request, WhistleblowerReport, 'governance/whistleblower_report_list.html', 'whistleblower_reports')

@login_required
def whistleblower_report_create(request):
    return object_create(
        request,
        WhistleblowerReportForm,
        'governance/whistleblower_report_form.html',
        'governance:whistleblower_report_list',
        'Whistleblower report created successfully.'
    )

@login_required
def whistleblower_report_update(request, pk):
    return object_update(
        request,
        WhistleblowerReport,
        WhistleblowerReportForm,
        pk,
        'governance/whistleblower_report_form.html',
        'governance:whistleblower_report_list',
        'Whistleblower report updated successfully.'
    )

@login_required
def whistleblower_report_delete(request, pk):
    return object_delete(
        request,
        WhistleblowerReport,
        pk,
        'governance:whistleblower_report_list',
        'Whistleblower report deleted successfully.'
    )

@login_required
def whistleblower_report_detail(request, pk):
    return object_detail(
        request,
        WhistleblowerReport,
        pk,
        'governance/whistleblower_report_detail.html',
        'whistleblower_report'
    )

# Conflict of Interest Declaration Views
@login_required
def conflict_of_interest_declaration_list(request):
    return object_list(
        request,
        ConflictOfInterestDeclaration,
        'governance/conflict_of_interest_declaration_list.html',
        'conflict_of_interest_declarations'
    )

@login_required
def conflict_of_interest_declaration_create(request):
    return object_create(
        request,
        ConflictOfInterestDeclarationForm,
        'governance/conflict_of_interest_declaration_list',
        'Conflict of interest declaration created successfully.'
    )

@login_required
def conflict_of_interest_declaration_update(request, pk):
    return object_update(
        request,
        ConflictOfInterestDeclaration,
        ConflictOfInterestDeclarationForm,
        pk,
        'governance/conflict_of_interest_declaration_list',
        'Conflict of interest declaration updated successfully.'
    )

@login_required
def conflict_of_interest_declaration_delete(request, pk):
    return object_delete(
        request,
        ConflictOfInterestDeclaration,
        pk,
        'governance/conflict_of_interest_declaration_list',
        'Conflict of interest declaration deleted successfully.'
    )

@login_required
def conflict_of_interest_declaration_detail(request, pk):
    return object_detail(
        request,
        ConflictOfInterestDeclaration,
        pk,
        'governance/conflict_of_interest_declaration_detail.html',
        'conflict_of_interest_declaration'
    )

# Complaint Views
@login_required
def complaint_list(request):
    return object_list(request, Complaint, 'governance/complaint_list.html', 'complaints')

@login_required
def complaint_create(request):
    return object_create(
        request,
        ComplaintForm,
        'governance/complaint_list',
        'Complaint created successfully.'
    )

@login_required
def complaint_update(request, pk):
    return object_update(
        request,
        Complaint,
        ComplaintForm,
        pk,
        'governance/complaint_list',
        'Complaint updated successfully.'
    )

@login_required
def complaint_delete(request, pk):
    return object_delete(
        request,
        Complaint,
        pk,
        'governance:complaint_list',
        'Complaint deleted successfully.'
    )

@login_required
def complaint_detail(request, pk):
    return object_detail(
        request,
        Complaint,
        pk,
        'governance/complaint_detail.html',
        'complaint'
    )

# Risk Assessment Score AJAX endpoint
@login_required
def update_risk_assessment_scores(request):
    """AJAX endpoint to update likelihood/impact and compute risk scores."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        risk_pk = request.POST.get('risk_id')
        likelihood = request.POST.get('likelihood')
        impact = request.POST.get('impact')
        risk = RiskRegister.objects.get(pk=risk_pk)
        if likelihood:
            risk.likelihood = int(likelihood)
        if impact:
            risk.impact = int(impact)
        risk.save(update_fields=['likelihood', 'impact'])
        return JsonResponse({
            'success': True,
            'risk_rating': risk.risk_rating,
        })
    except (RiskRegister.DoesNotExist, ValueError, TypeError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)

# Legacy placeholder views for integration with existing modules
_PLACEHOLDER_MESSAGE = (
    "This module is scheduled for integration with the Finance and Resource "
    "Mobilization phase. Please use the dedicated finance views once available."
)

def _render_placeholder(request, title):
    """Render a simple placeholder page for modules pending integration."""
    return render(request, 'governance/placeholder.html', {
        'placeholder_title': title,
        'placeholder_message': _PLACEHOLDER_MESSAGE,
    })

@login_required
def financial_year_list(request):
    return _render_placeholder(request, "Financial Years")

@login_required
def financial_year_create(request):
    return _render_placeholder(request, "Create Financial Year")

@login_required
def budget_list(request):
    return _render_placeholder(request, "Budgets")

@login_required
def budget_create(request):
    return _render_placeholder(request, "Create Budget")

@login_required
def transaction_list(request):
    return _render_placeholder(request, "Transactions")

@login_required
def transaction_create(request):
    return _render_placeholder(request, "Create Transaction")

@login_required
def budget_allocation_list(request):
    return _render_placeholder(request, "Budget Allocations")

@login_required
def budget_allocation_create(request):
    return _render_placeholder(request, "Create Budget Allocation")

# Corrective Preventive Action Views
@login_required
def corrective_preventive_action_list(request):
    return object_list(request, CorrectivePreventiveAction, 'governance/corrective_preventive_action_list.html', 'corrective_preventive_actions')

@login_required
def corrective_preventive_action_create(request):
    return object_create(
        request,
        CorrectivePreventiveActionForm,
        'governance/corrective_preventive_action_form.html',
        'governance:corrective_preventive_action_list',
        'Corrective preventive action created successfully.'
    )

@login_required
def corrective_preventive_action_update(request, pk):
    return object_update(
        request,
        CorrectivePreventiveAction,
        CorrectivePreventiveActionForm,
        pk,
        'governance/corrective_preventive_action_form.html',
        'governance:corrective_preventive_action_list',
        'Corrective preventive action updated successfully.'
    )

@login_required
def corrective_preventive_action_delete(request, pk):
    return object_delete(
        request,
        CorrectivePreventiveAction,
        pk,
        'governance:corrective_preventive_action_list',
        'Corrective preventive action deleted successfully.'
    )

@login_required
def corrective_preventive_action_detail(request, pk):
    return object_detail(
        request,
        CorrectivePreventiveAction,
        pk,
        'governance/corrective_preventive_action_detail.html',
        'corrective_preventive_action'
    )

# Document Views
@login_required
def document_list(request):
    return object_list(request, Document, 'governance/document_list.html', 'documents')

@login_required
def document_create(request):
    return object_create(
        request,
        DocumentForm,
        'governance/document_form.html',
        'governance:document_list',
        'Document created successfully.'
    )

@login_required
def document_update(request, pk):
    return object_update(
        request,
        Document,
        DocumentForm,
        pk,
        'governance/document_form.html',
        'governance:document_list',
        'Document updated successfully.'
    )

@login_required
def document_delete(request, pk):
    return object_delete(
        request,
        Document,
        pk,
        'governance:document_list',
        'Document deleted successfully.'
    )

@login_required
def document_detail(request, pk):
    return object_detail(
        request,
        Document,
        pk,
        'governance/document_detail.html',
        'document'
    )

# Governance Meeting Views
@login_required
def governance_meeting_list(request):
    return object_list(request, GovernanceMeeting, 'governance/governance_meeting_list.html', 'governance_meetings')

@login_required
def governance_meeting_create(request):
    return object_create(
        request,
        GovernanceMeetingForm,
        'governance/governance_meeting_form.html',
        'governance:governance_meeting_list',
        'Governance meeting created successfully.'
    )

@login_required
def governance_meeting_update(request, pk):
    return object_update(
        request,
        GovernanceMeeting,
        GovernanceMeetingForm,
        pk,
        'governance/governance_meeting_form.html',
        'governance:governance_meeting_list',
        'Governance meeting updated successfully.'
    )

@login_required
def governance_meeting_delete(request, pk):
    return object_delete(
        request,
        GovernanceMeeting,
        pk,
        'governance:governance_meeting_list',
        'Governance meeting deleted successfully.'
    )

@login_required
def governance_meeting_detail(request, pk):
    return object_detail(
        request,
        GovernanceMeeting,
        pk,
        'governance/governance_meeting_detail.html',
        'governance_meeting'
    )

@login_required
def meeting_attendance_create(request, meeting_pk):
    meeting = get_object_or_404(GovernanceMeeting, pk=meeting_pk)
    if request.method == 'POST':
        form = MeetingAttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.meeting = meeting
            attendance.created_by = request.user
            attendance.updated_by = request.user
            attendance.save()
            messages.success(request, 'Meeting attendance recorded successfully.')
            return redirect('governance:governance_meeting_detail', pk=meeting_pk)
    else:
        form = MeetingAttendanceForm()
    context = {
        'form': form,
        'meeting': meeting,
    }
    return render(request, 'governance/meeting_attendance_form.html', context)

# Governance Notification Views
@login_required
def governance_notification_list(request):
    return object_list(request, GovernanceNotification, 'governance/governance_notification_list.html', 'governance_notifications')

@login_required
def governance_notification_mark_as_read(request, pk):
    notification = get_object_or_404(GovernanceNotification, pk=pk)
    if request.method == 'POST':
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        messages.success(request, 'Notification marked as read.')
        return redirect('governance:governance_notification_list')
    context = {
        'notification': notification,
    }
    return render(request, 'governance/governance_notification_confirm_mark_as_read.html', context)

# Governance Timeline Views
@login_required
def governance_timeline_list(request):
    return object_list(request, GovernanceTimeline, 'governance/governance_timeline_list.html', 'governance_timelines')

def object_detail(request, model, pk, template_name, context_name):
    """Generic detail view for a model."""
    obj = get_object_or_404(model, pk=pk)
    context = {
        context_name: obj,
    }
    return render(request, template_name, context)


# Note: We need to import timezone for the governance_notification_mark_as_read view.
# We'll add the import at the top of the file.
