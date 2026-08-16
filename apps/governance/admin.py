"""Admin configuration for Governance, Risk, Compliance and Safeguarding (Phase 29)."""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

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


# Base admin classes
class BaseGovernanceAdmin(admin.ModelAdmin):
    """Base admin class for governance models."""
    
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    search_fields = ('title', 'reference_number', 'description')
    list_filter = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(qs, 'filter'):
            # Filter out soft-deleted records by default
            if hasattr(self.model, 'is_deleted'):
                qs = qs.filter(is_deleted=False)
        return qs


class TimestampedAdmin(BaseGovernanceAdmin):
    """Admin for models with timestamps."""
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')


# Policy Administration
@admin.register(Policy)
class PolicyAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'reference_number', 'policy_category', 'version', 'status', 'created_at')
    list_filter = BaseGovernanceAdmin.list_filter + ('policy_category', 'version', 'status')
    search_fields = BaseGovernanceAdmin.search_fields + ('policy_category',)
    
    fieldsets = (
        (_('Policy Information'), {
            'fields': ('title', 'reference_number', 'policy_category', 'description')
        }),
        (_('Version Control'), {
            'fields': ('version', 'supersedes')
        }),
        (_('Lifecycle'), {
            'fields': ('effective_date', 'expiry_date', 'review_date', 'status')
        }),
        (_('Responsibility'), {
            'fields': ('responsible_officer',)
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PolicyVersion)
class PolicyVersionAdmin(BaseGovernanceAdmin):
    list_display = ('policy', 'version_number', 'effective_date', 'expiry_date')
    list_filter = ('effective_date', 'expiry_date')
    search_fields = ('policy__title', 'version_number')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Version Information'), {
            'fields': ('policy', 'version_number', 'effective_date', 'expiry_date', 'changes_summary')
        }),
        (_('Document'), {
            'fields': ('document',)
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PolicyAcknowledgement)
class PolicyAcknowledgementAdmin(BaseGovernanceAdmin):
    list_display = ('user', 'policy', 'acknowledged_at', 'expires_at', 'is_current')
    list_filter = ('acknowledged_at', 'expires_at', 'is_current', 'policy__policy_category')
    search_fields = ('user__first_name', 'user__last_name', 'policy__title')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('acknowledged_at',)
    
    fieldsets = (
        (_('Acknowledgement Information'), {
            'fields': ('user', 'policy', 'acknowledged_at', 'expires_at', 'is_current')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Risk Management Administration
@admin.register(RiskRegister)
class RiskRegisterAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'risk_category', 'risk_rating_display', 'risk_owner', 'status', 'review_date')
    list_filter = BaseGovernanceAdmin.list_filter + ('risk_category', 'status', 'review_date')
    search_fields = ('title', 'description', 'root_cause')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('risk_rating_display',)
    
    def risk_rating_display(self, obj):
        risk_rating = obj.risk_rating
        color = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred'
        }.get(risk_rating, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            risk_rating
        )
    risk_rating_display.short_description = _('Risk Rating')
    
    fieldsets = (
        (_('Risk Information'), {
            'fields': ('title', 'risk_category', 'description', 'root_cause')
        }),
        (_('Risk Assessment'), {
            'fields': ('likelihood', 'impact', 'risk_rating_display')
        }),
        (_('Ownership & Mitigation'), {
            'fields': ('risk_owner', 'mitigation_strategy', 'residual_likelihood', 'residual_impact')
        }),
        (_('Review Schedule'), {
            'fields': ('review_date', 'status')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(BaseGovernanceAdmin):
    list_display = ('risk_register', 'assessment_type', 'assessed_by', 'assessment_date', 'likelihood', 'impact', 'risk_score')
    list_filter = ('assessment_type', 'assessment_date')
    search_fields = ('risk_register__title', 'assessor_notes')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('risk_score', 'created_at', 'updated_at')
    
    fieldsets = (
        (_('Assessment Information'), {
            'fields': ('risk_register', 'assessment_type', 'assessed_by', 'assessment_date')
        }),
        (_('Assessment Results'), {
            'fields': ('likelihood', 'impact', 'risk_score', 'assessor_notes')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RiskTreatmentPlan)
class RiskTreatmentPlanAdmin(BaseGovernanceAdmin):
    list_display = ('risk_register', 'treatment_type', 'responsible_officer', 'target_completion_date', 'progress_percentage', 'effectiveness_rating')
    list_filter = ('treatment_type', 'target_completion_date', 'actual_completion_date')
    search_fields = ('risk_register__title', 'description', 'responsible_officer__first_name', 'responsible_officer__last_name')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Treatment Information'), {
            'fields': ('risk_register', 'treatment_type', 'description')
        }),
        (_('Implementation'), {
            'fields': ('responsible_officer', 'target_completion_date', 'actual_completion_date', 'progress_percentage')
        }),
        (_('Effectiveness Review'), {
            'fields': ('effectiveness_review_date', 'effectiveness_rating')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Compliance Administration
@admin.register(ComplianceRequirement)
class ComplianceRequirementAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'compliance_type', 'source_organization', 'effective_date', 'expiry_date', 'is_active')
    list_filter = ('compliance_type', 'is_active', 'effective_date', 'expiry_date')
    search_fields = ('title', 'description', 'source_organization', 'reference_document')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Requirement Information'), {
            'fields': ('title', 'compliance_type', 'description')
        }),
        (_('Source & References'), {
            'fields': ('source_organization', 'reference_document')
        }),
        (_('Lifecycle'), {
            'fields': ('effective_date', 'expiry_date', 'is_active')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ComplianceAssessment)
class ComplianceAssessmentAdmin(BaseGovernanceAdmin):
    list_display = ('compliance_requirement', 'assessed_by', 'assessment_date', 'result', 'score_percentage')
    list_filter = ('result', 'assessment_date')
    search_fields = ('compliance_requirement__title', 'findings', 'recommendations')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Assessment Information'), {
            'fields': ('compliance_requirement', 'assessed_by', 'assessment_date')
        }),
        (_('Assessment Period'), {
            'fields': ('assessment_period_start', 'assessment_period_end')
        }),
        (_('Results'), {
            'fields': ('result', 'score_percentage', 'findings', 'recommendations')
        }),
        (_('Evidence'), {
            'fields': ('evidence_documents',)
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Internal Controls Administration
@admin.register(InternalControl)
class InternalControlAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'control_type', 'frequency', 'responsible_officer', 'is_effective', 'last_tested_date', 'next_test_date')
    list_filter = ('control_type', 'frequency', 'is_effective', 'last_tested_date', 'next_test_date')
    search_fields = ('title', 'description', 'objective')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Control Information'), {
            'fields': ('title', 'control_type', 'description', 'objective')
        }),
        (_('Schedule & Responsibility'), {
            'fields': ('frequency', 'responsible_officer', 'control_owner')
        }),
        (_('Automation & Effectiveness'), {
            'fields': ('is_automated', 'is_effective', 'last_tested_date', 'next_test_date')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Ethics Administration
@admin.register(EthicsCase)
class EthicsCaseAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'case_type', 'reported_date', 'reported_by', 'assigned_investigator', 'status')
    list_filter = ('case_type', 'status', 'reported_date', 'investigation_start_date', 'investigation_end_date')
    search_fields = ('title', 'description', 'resolution', 'outcome')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        (_('Case Information'), {
            'fields': ('title', 'case_type', 'description')
        }),
        (_('Reporting'), {
            'fields': ('reported_by', 'reported_date')
        }),
        (_('Investigation'), {
            'fields': ('assigned_investigator', 'investigation_start_date', 'investigation_end_date')
        }),
        (_('Resolution'), {
            'fields': ('resolution', 'outcome', 'lessons_learned')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConflictOfInterestDeclaration)
class ConflictOfInterestDeclarationAdmin(BaseGovernanceAdmin):
    list_display = ('declarant', 'declaration_type', 'date_declared', 'review_date', 'approval_status', 'approved_by')
    list_filter = ('declaration_type', 'approval_status', 'date_declared', 'review_date')
    search_fields = ('declarant__first_name', 'declarant__last_name', 'nature_of_conflict', 'related_organization', 'related_individual')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Declaration Information'), {
            'fields': ('declarant', 'declaration_type', 'nature_of_conflict')
        }),
        (_('Related Parties'), {
            'fields': ('related_organization', 'related_individual')
        }),
        (_('Timeline'), {
            'fields': ('date_declared', 'review_date')
        }),
        (_('Mitigation & Approval'), {
            'fields': ('mitigation_measures', 'approval_status', 'approved_by', 'approved_date')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Safeguarding Administration
@admin.register(SafeguardingCase)
class SafeguardingCaseAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'case_category', 'date_reported', 'reported_by', 'risk_level', 'assigned_officer', 'status')
    list_filter = ('case_category', 'risk_level', 'status', 'date_reported', 'date_assigned')
    search_fields = ('title', 'description', 'actions_taken', 'outcome')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at', 'created_by', 'updated_by', 'confidentiality_level')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Safeguarding cases are highly confidential - restrict access
        if not request.user.is_superuser:
            # In a real implementation, you'd check for specific safeguarding permissions
            # For now, we'll allow all authenticated users but note this should be restricted
            pass
        return qs
    
    fieldsets = (
        (_('Case Information'), {
            'fields': ('title', 'case_category', 'description')
        }),
        (_('Reporting'), {
            'fields': ('reported_by', 'date_reported')
        }),
        (_('Risk Assessment'), {
            'fields': ('risk_level',)
        }),
        (_('Investigation'), {
            'fields': ('assigned_officer', 'date_assigned', 'investigation_start_date', 'investigation_end_date')
        }),
        (_('Outcome'), {
            'fields': ('actions_taken', 'outcome', 'closure_date')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# Incident Administration
@admin.register(IncidentReport)
class IncidentReportAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'incident_category', 'date_occurred', 'date_reported', 'reported_by', 'severity', 'status')
    list_filter = ('incident_category', 'severity', 'status', 'date_occurred', 'date_reported')
    search_fields = ('title', 'description', 'location', 'immediate_actions_taken')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        (_('Incident Information'), {
            'fields': ('title', 'incident_category', 'description')
        }),
        (_('Timing'), {
            'fields': ('date_occurred', 'date_reported')
        }),
        (_('Location & Severity'), {
            'fields': ('location', 'severity')
        }),
        (_('Reporting'), {
            'fields': ('reported_by',)
        }),
        (_('Response'), {
            'fields': ('immediate_actions_taken', 'investigation_required', 'investigation_start_date', 'investigation_end_date')
        }),
        (_('Analysis & Actions'), {
            'fields': ('root_cause_analysis', 'corrective_actions', 'preventive_actions')
        }),
        (_('Related Records'), {
            'fields': ('safeguarding_case',)
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# Complaint Administration
@admin.register(Complaint)
class ComplaintAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'complaint_type', 'date_received', 'complainant_name', 'complainant_is_anonymous', 'assigned_officer', 'resolution_type', 'status')
    list_filter = ('complaint_type', 'resolution_type', 'status', 'date_received', 'complainant_is_anonymous')
    search_fields = ('title', 'description', 'complainant_name', 'complainant_contact')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        (_('Complaint Information'), {
            'fields': ('title', 'complaint_type', 'description')
        }),
        (_('Complainant Information'), {
            'fields': ('complainant_name', 'complainant_contact', 'complainant_is_anonymous')
        }),
        (_('Context'), {
            'fields': ('programme', 'service_location')
        }),
        (_('Investigation'), {
            'fields': ('assigned_officer', 'date_assigned', 'investigation_start_date', 'investigation_end_date')
        }),
        (_('Resolution'), {
            'fields': ('resolution_type', 'resolution_description', 'date_resolved', 'appeal_date', 'appeal_outcome')
        }),
        (_('Learning'), {
            'fields': ('lessons_learned',)
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# Whistleblower Administration
@admin.register(WhistleblowerReport)
class WhistleblowerReportAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'report_type', 'date_reported', 'reporter_is_anonymous', 'assigned_investigator', 'status')
    list_filter = ('report_type', 'status', 'date_reported')
    search_fields = ('title', 'description', 'outcome')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at', 'created_by', 'updated_by', 'confidentiality_level')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Whistleblower reports are highly confidential - restrict access
        # In a real implementation, only authorized investigators and senior management should see these
        if not request.user.is_superuser:
            # For demonstration, we'll show all but note this needs proper restrictions
            pass
        return qs
    
    fieldsets = (
        (_('Report Information'), {
            'fields': ('title', 'report_type', 'description')
        }),
        (_('Reporter Information'), {
            'fields': ('reporter_is_anonymous', 'reporter_name', 'reporter_contact', 'reporter_relationship')
        }),
        (_('Alleged Subjects'), {
            'fields': ('alleged_subjects',)
        }),
        (_('Investigation'), {
            'fields': ('assigned_investigator', 'date_assigned', 'investigation_start_date', 'investigation_end_date')
        }),
        (_('Evidence'), {
            'fields': ('evidence_documents',)
        }),
        (_('Outcome'), {
            'fields': ('outcome', 'date_closed')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# CAPA Administration
@admin.register(CorrectivePreventiveAction)
class CorrectivePreventiveActionAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'action_type', 'responsible_officer', 'due_date', 'completion_date', 'verification_date', 'effectiveness_rating', 'status')
    list_filter = ('action_type', 'status', 'due_date', 'completion_date', 'verification_date')
    search_fields = ('title', 'description', 'root_cause', 'corrective_action_description', 'preventive_action_description')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Action Information'), {
            'fields': ('title', 'action_type', 'description')
        }),
        (_('Source Issue'), {
            'fields': ('source_incident', 'source_complaint', 'source_audit_finding', 'source_risk_assessment', 'source_whistleblower_report', 'source_safeguarding_case', 'source_ethics_case')
        }),
        (_('Root Cause & Actions'), {
            'fields': ('root_cause', 'corrective_action_description', 'preventive_action_description')
        }),
        (_('Implementation'), {
            'fields': ('responsible_officer', 'due_date', 'completion_date', 'verification_date', 'verified_by')
        }),
        (_('Effectiveness'), {
            'fields': ('effectiveness_rating', 'lessons_learned')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Document Administration
@admin.register(Document)
class DocumentAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'document_type', 'version', 'is_current_version', 'confidentiality_level', 'file_size', 'created_at')
    list_filter = ('document_type', 'is_current_version', 'confidentiality_level', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('file_size', 'mime_type', 'created_at', 'updated_at')
    
    fieldsets = (
        (_('Document Information'), {
            'fields': ('title', 'document_type', 'description')
        }),
        (_('File Details'), {
            'fields': ('file', 'file_size', 'mime_type', 'version', 'is_current_version')
        }),
        (_('Access Control'), {
            'fields': ('confidentiality_level',)
        }),
        (_('Related Records'), {
            'fields': ('related_policies', 'related_risks', 'related_compliance', 'related_incidents')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# Governance Meeting Administration
@admin.register(GovernanceMeeting)
class GovernanceMeetingAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'meeting_type', 'scheduled_date', 'actual_start_time', 'actual_end_time', 'meeting_chair', 'status')
    list_filter = ('meeting_type', 'status', 'scheduled_date', 'actual_start_time', 'actual_end_time')
    search_fields = ('title', 'description', 'location', 'minutes', 'action_items', 'decisions_made')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        (_('Meeting Information'), {
            'fields': ('title', 'meeting_type', 'description')
        }),
        (_('Scheduling'), {
            'fields': ('scheduled_date', 'actual_start_time', 'actual_end_time', 'location')
        }),
        (_('Leadership'), {
            'fields': ('meeting_chair',)
        }),
        (_('Content'), {
            'fields': ('minutes', 'action_items', 'decisions_made')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(BaseGovernanceAdmin):
    list_display = ('user', 'meeting', 'attendance_status', 'joined_at', 'left_at')
    list_filter = ('attendance_status', 'joined_at', 'left_at')
    search_fields = ('user__first_name', 'user__last_name', 'meeting__title')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Attendance Information'), {
            'fields': ('meeting', 'user', 'attendance_status')
        }),
        (_('Timing'), {
            'fields': ('joined_at', 'left_at')
        }),
        (_('Notes'), {
            'fields': ('apologies_note',)
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Notification Administration
@admin.register(GovernanceNotification)
class GovernanceNotificationAdmin(BaseGovernanceAdmin):
    list_display = ('title', 'notification_type', 'recipient', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at', 'sent_via_email', 'sent_via_sms')
    search_fields = ('title', 'message', 'recipient__first_name', 'recipient__last_name')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('read_at', 'sent_at', 'created_at', 'updated_at')
    
    fieldsets = (
        (_('Notification Information'), {
            'fields': ('title', 'notification_type', 'message')
        }),
        (_('Recipient & Status'), {
            'fields': ('recipient', 'is_read', 'read_at')
        }),
        (_('Delivery'), {
            'fields': ('sent_via_email', 'sent_via_sms', 'sent_at')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Timeline Administration
@admin.register(GovernanceTimeline)
class GovernanceTimelineAdmin(BaseGovernanceAdmin):
    list_display = ('event_type', 'event_date', 'performed_by', 'module', 'reference_number', 'action_performed')
    list_filter = ('event_type', 'event_date', 'module', 'action_performed')
    search_fields = ('description', 'reference_number', 'action_performed', 'remarks')
    readonly_fields = BaseGovernanceAdmin.readonly_fields + ('event_date', 'created_at', 'updated_at')
    
    fieldsets = (
        (_('Event Information'), {
            'fields': ('event_type', 'description', 'event_date')
        }),
        (_('Actor & Context'), {
            'fields': ('performed_by', 'module', 'reference_number', 'action_performed', 'status_after_event')
        }),
        (_('Notes'), {
            'fields': ('remarks',)
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )