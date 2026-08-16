"""Forms for Governance, Risk, Compliance and Safeguarding (Phase 29)."""

from __future__ import annotations

from django import forms
from django.forms import ModelForm, DateTimeInput, DateInput, Textarea, Select, SelectMultiple, HiddenInput
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


# Base form classes
class BaseGovernanceForm(ModelForm):
    """Base form for governance models."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.URLInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, (forms.DateInput, forms.DateTimeInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-check-input'})


# Governance Record Form
class GovernanceRecordForm(BaseGovernanceForm):
    class Meta:
        model = GovernanceRecord
        fields = [
            'reference_number', 'title', 'governance_type', 'description',
            'priority', 'confidentiality_level', 'status',
            'department', 'programme', 'project', 'region',
            'effective_date', 'expiry_date', 'review_date',
            'notes'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'notes': Textarea(attrs={'rows': 3}),
            'effective_date': DateInput(attrs={'type': 'date'}),
            'expiry_date': DateInput(attrs={'type': 'date'}),
            'review_date': DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['responsible_officer'] = forms.ModelChoiceField(
            queryset=User.objects.all(),
            required=False,
            label=_("Responsible Officer"),
            widget=forms.Select(attrs={'class': 'form-select'})
        )


# Policy Forms
class PolicyForm(BaseGovernanceForm):
    class Meta:
        model = Policy
        fields = [
            'title', 'reference_number', 'policy_category', 'description',
            'version', 'supersedes',
            'effective_date', 'expiry_date', 'review_date', 'status',
            'responsible_officer', 'notes'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'effective_date': DateInput(attrs={'type': 'date'}),
            'expiry_date': DateInput(attrs={'type': 'date'}),
            'review_date': DateInput(attrs={'type': 'date'}),
        }


class PolicyVersionForm(BaseGovernanceForm):
    class Meta:
        model = PolicyVersion
        fields = [
            'policy', 'version_number', 'effective_date', 'expiry_date',
            'changes_summary', 'document'
        ]
        widgets = {
            'changes_summary': Textarea(attrs={'rows': 4}),
            'effective_date': DateInput(attrs={'type': 'date'}),
            'expiry_date': DateInput(attrs={'type': 'date'}),
        }


class PolicyAcknowledgementForm(BaseGovernanceForm):
    class Meta:
        model = PolicyAcknowledgement
        fields = ['user', 'policy', 'expires_at', 'is_current']
        widgets = {
            'expires_at': DateTimeInput(attrs={'type': 'datetime-local'}),
        }


# Risk Management Forms
class RiskRegisterForm(BaseGovernanceForm):
    class Meta:
        model = RiskRegister
        fields = [
            'title', 'risk_category', 'description', 'root_cause',
            'likelihood', 'impact',
            'risk_owner', 'mitigation_strategy',
            'residual_likelihood', 'residual_impact',
            'review_date', 'status'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'root_cause': Textarea(attrs={'rows': 3}),
            'mitigation_strategy': Textarea(attrs={'rows': 3}),
            'review_date': DateInput(attrs={'type': 'date'}),
        }


class RiskAssessmentForm(BaseGovernanceForm):
    class Meta:
        model = RiskAssessment
        fields = [
            'risk_register', 'assessment_type', 'assessed_by',
            'assessment_date', 'likelihood', 'impact', 'assessor_notes'
        ]
        widgets = {
            'assessment_date': DateInput(attrs={'type': 'date'}),
            'assessor_notes': Textarea(attrs={'rows': 3}),
        }


class RiskTreatmentPlanForm(BaseGovernanceForm):
    class Meta:
        model = RiskTreatmentPlan
        fields = [
            'risk_register', 'treatment_type', 'description',
            'responsible_officer', 'target_completion_date', 'actual_completion_date',
            'progress_percentage', 'effectiveness_review_date', 'effectiveness_rating'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'target_completion_date': DateInput(attrs={'type': 'date'}),
            'actual_completion_date': DateInput(attrs={'type': 'date'}),
            'effectiveness_review_date': DateInput(attrs={'type': 'date'}),
        }


# Compliance Forms
class ComplianceRequirementForm(BaseGovernanceForm):
    class Meta:
        model = ComplianceRequirement
        fields = [
            'title', 'compliance_type', 'description',
            'source_organization', 'reference_document',
            'effective_date', 'expiry_date', 'is_active'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'effective_date': DateInput(attrs={'type': 'date'}),
            'expiry_date': DateInput(attrs={'type': 'date'}),
        }


class ComplianceAssessmentForm(BaseGovernanceForm):
    class Meta:
        model = ComplianceAssessment
        fields = [
            'compliance_requirement', 'assessed_by', 'assessment_date',
            'assessment_period_start', 'assessment_period_end',
            'result', 'score_percentage', 'findings', 'recommendations',
            'evidence_documents'
        ]
        widgets = {
            'assessment_date': DateInput(attrs={'type': 'date'}),
            'assessment_period_start': DateInput(attrs={'type': 'date'}),
            'assessment_period_end': DateInput(attrs={'type': 'date'}),
            'findings': Textarea(attrs={'rows': 4}),
            'recommendations': Textarea(attrs={'rows': 3}),
        }


# Internal Controls Forms
class InternalControlForm(BaseGovernanceForm):
    class Meta:
        model = InternalControl
        fields = [
            'title', 'control_type', 'description', 'objective',
            'frequency', 'responsible_officer', 'control_owner',
            'is_automated', 'is_effective', 'last_tested_date', 'next_test_date'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'objective': Textarea(attrs={'rows': 3}),
            'last_tested_date': DateInput(attrs={'type': 'date'}),
            'next_test_date': DateInput(attrs={'type': 'date'}),
        }


# Ethics Forms
class EthicsCaseForm(BaseGovernanceForm):
    class Meta:
        model = EthicsCase
        fields = [
            'title', 'case_type', 'description',
            'reported_by', 'reported_date',
            'assigned_investigator', 'investigation_start_date', 'investigation_end_date',
            'resolution', 'outcome', 'lessons_learned', 'status'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'reported_date': DateInput(attrs={'type': 'date'}),
            'investigation_start_date': DateInput(attrs={'type': 'date'}),
            'investigation_end_date': DateInput(attrs={'type': 'date'}),
            'resolution': Textarea(attrs={'rows': 3}),
            'outcome': Textarea(attrs={'rows': 3}),
            'lessons_learned': Textarea(attrs={'rows': 3}),
        }


class ConflictOfInterestDeclarationForm(BaseGovernanceForm):
    class Meta:
        model = ConflictOfInterestDeclaration
        fields = [
            'declarant', 'declaration_type', 'nature_of_conflict',
            'related_organization', 'related_individual',
            'date_declared', 'review_date',
            'mitigation_measures', 'approval_status', 'approved_by', 'approved_date'
        ]
        widgets = {
            'nature_of_conflict': Textarea(attrs={'rows': 4}),
            'mitigation_measures': Textarea(attrs={'rows': 3}),
            'date_declared': DateInput(attrs={'type': 'date'}),
            'review_date': DateInput(attrs={'type': 'date'}),
            'approved_date': DateInput(attrs={'type': 'date'}),
        }


# Safeguarding Forms
class SafeguardingCaseForm(BaseGovernanceForm):
    class Meta:
        model = SafeguardingCase
        fields = [
            'title', 'case_category', 'description',
            'reported_by', 'date_reported',
            'risk_level',
            'assigned_officer', 'date_assigned',
            'investigation_start_date', 'investigation_end_date',
            'actions_taken', 'outcome', 'closure_date', 'status'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'date_reported': DateInput(attrs={'type': 'date'}),
            'date_assigned': DateInput(attrs={'type': 'date'}),
            'investigation_start_date': DateInput(attrs={'type': 'date'}),
            'investigation_end_date': DateInput(attrs={'type': 'date'}),
            'actions_taken': Textarea(attrs={'rows': 4}),
            'outcome': Textarea(attrs={'rows': 3}),
            'closure_date': DateInput(attrs={'type': 'date'}),
        }


# Incident Forms
class IncidentReportForm(BaseGovernanceForm):
    class Meta:
        model = IncidentReport
        fields = [
            'title', 'incident_category', 'description',
            'date_occurred', 'reported_by',
            'location', 'severity',
            'immediate_actions_taken', 'investigation_required',
            'investigation_start_date', 'investigation_end_date',
            'root_cause_analysis', 'corrective_actions', 'preventive_actions',
            'safeguarding_case', 'status'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'date_occurred': DateTimeInput(attrs={'type': 'datetime-local'}),
            'immediate_actions_taken': Textarea(attrs={'rows': 3}),
            'investigation_start_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'investigation_end_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'root_cause_analysis': Textarea(attrs={'rows': 3}),
            'corrective_actions': Textarea(attrs={'rows': 4}),
            'preventive_actions': Textarea(attrs={'rows': 4}),
        }


# Complaint Forms
class ComplaintForm(BaseGovernanceForm):
    class Meta:
        model = Complaint
        fields = [
            'title', 'complaint_type', 'description',
            'complainant_name', 'complainant_contact', 'complainant_is_anonymous',
            'programme', 'service_location',
            'assigned_officer', 'date_assigned',
            'investigation_start_date', 'investigation_end_date',
            'resolution_type', 'resolution_description', 'date_resolved',
            'appeal_date', 'appeal_outcome',
            'lessons_learned', 'status'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'date_assigned': DateTimeInput(attrs={'type': 'datetime-local'}),
            'investigation_start_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'investigation_end_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'resolution_description': Textarea(attrs={'rows': 3}),
            'appeal_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'appeal_outcome': Textarea(attrs={'rows': 3}),
            'lessons_learned': Textarea(attrs={'rows': 3}),
        }


# Whistleblower Forms
class WhistleblowerReportForm(BaseGovernanceForm):
    class Meta:
        model = WhistleblowerReport
        fields = [
            'title', 'report_type', 'description',
            'reporter_is_anonymous', 'reporter_name', 'reporter_contact', 'reporter_relationship',
            'alleged_subjects',
            'assigned_investigator', 'date_assigned',
            'investigation_start_date', 'investigation_end_date',
            'evidence_documents',
            'outcome', 'date_closed', 'status'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'date_assigned': DateTimeInput(attrs={'type': 'datetime-local'}),
            'investigation_start_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'investigation_end_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'outcome': Textarea(attrs={'rows': 4}),
            'date_closed': DateTimeInput(attrs={'type': 'datetime-local'}),
        }


# CAPA Forms
class CorrectivePreventiveActionForm(BaseGovernanceForm):
    class Meta:
        model = CorrectivePreventiveAction
        fields = [
            'title', 'action_type', 'description',
            'source_incident', 'source_complaint', 'source_audit_finding', 'source_risk_assessment',
            'source_whistleblower_report', 'source_safeguarding_case', 'source_ethics_case',
            'root_cause', 'corrective_action_description', 'preventive_action_description',
            'responsible_officer', 'due_date', 'completion_date', 'verification_date', 'verified_by',
            'effectiveness_rating', 'lessons_learned', 'status'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'root_cause': Textarea(attrs={'rows': 4}),
            'corrective_action_description': Textarea(attrs={'rows': 4}),
            'preventive_action_description': Textarea(attrs={'rows': 4}),
            'due_date': DateInput(attrs={'type': 'date'}),
            'completion_date': DateInput(attrs={'type': 'date'}),
            'verification_date': DateInput(attrs={'type': 'date'}),
            'lessons_learned': Textarea(attrs={'rows': 3}),
        }


# Document Forms
class DocumentForm(BaseGovernanceForm):
    class Meta:
        model = Document
        fields = [
            'title', 'document_type', 'description', 'file',
            'version', 'is_current_version',
            'confidentiality_level',
            'related_policies', 'related_risks', 'related_compliance', 'related_incidents'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
        }


# Governance Meeting Forms
class GovernanceMeetingForm(BaseGovernanceForm):
    class Meta:
        model = GovernanceMeeting
        fields = [
            'title', 'meeting_type', 'governance_type', 'description',
            'scheduled_date', 'actual_start_time', 'actual_end_time',
            'location', 'meeting_chair',
            'minutes', 'action_items', 'decisions_made',
            'attendance',
            'status'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'governance_type': HiddenInput(),
            'scheduled_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'actual_start_time': DateTimeInput(attrs={'type': 'datetime-local'}),
            'actual_end_time': DateTimeInput(attrs={'type': 'datetime-local'}),
            'minutes': Textarea(attrs={'rows': 4}),
            'action_items': Textarea(attrs={'rows': 3}),
            'decisions_made': Textarea(attrs={'rows': 3}),
        }


class MeetingAttendanceForm(BaseGovernanceForm):
    class Meta:
        model = MeetingAttendance
        fields = ['meeting', 'user', 'attendance_status', 'joined_at', 'left_at', 'apologies_note']
        widgets = {
            'joined_at': DateTimeInput(attrs={'type': 'datetime-local'}),
            'left_at': DateTimeInput(attrs={'type': 'datetime-local'}),
            'apologies_note': Textarea(attrs={'rows': 3}),
        }


# Notification Forms
class GovernanceNotificationForm(BaseGovernanceForm):
    class Meta:
        model = GovernanceNotification
        fields = [
            'title', 'notification_type', 'message',
            'recipient', 'is_read', 'read_at',
            'sent_via_email', 'sent_via_sms', 'sent_at'
        ]
        widgets = {
            'message': Textarea(attrs={'rows': 4}),
            'read_at': DateTimeInput(attrs={'type': 'datetime-local'}),
            'sent_at': DateTimeInput(attrs={'type': 'datetime-local'}),
        }


# Timeline Forms
class GovernanceTimelineForm(BaseGovernanceForm):
    class Meta:
        model = GovernanceTimeline
        fields = [
            'event_type', 'description', 'event_date',
            'performed_by', 'module', 'reference_number', 'action_performed', 'status_after_event',
            'remarks'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'event_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'remarks': Textarea(attrs={'rows': 3}),
        }