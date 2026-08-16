"""URL configuration for Governance, Risk, Compliance and Safeguarding (Phase 29)."""

from django.urls import path
from . import views

app_name = 'governance'

urlpatterns = [
    # Dashboard
    path('', views.governance_dashboard, name='governance_dashboard'),
    
    # Policy URLs
    path('policies/', views.policy_list, name='policy_list'),
    path('policies/create/', views.policy_create, name='policy_create'),
    path('policies/<int:pk>/update/', views.policy_update, name='policy_update'),
    path('policies/<int:pk>/delete/', views.policy_delete, name='policy_delete'),
    path('policies/<int:pk>/', views.policy_detail, name='policy_detail'),
    path('policies/<int:policy_pk>/versions/create/', views.policy_version_create, name='policy_version_create'),
    
    # Risk Management URLs
    path('risks/', views.risk_register_list, name='risk_register_list'),
    path('risks/create/', views.risk_register_create, name='risk_register_create'),
    path('risks/<int:pk>/update/', views.risk_register_update, name='risk_register_update'),
    path('risks/<int:pk>/', views.risk_register_detail, name='risk_register_detail'),
    path('risks/<int:risk_pk>/assessments/create/', views.risk_assessment_create, name='risk_assessment_create'),
    path('risks/<int:risk_pk>/treatment-plans/create/', views.risk_treatment_plan_create, name='risk_treatment_plan_create'),
    
    # Risk Assessment and Treatment Plan URLs (standalone)
    path('risk-assessments/create/', views.risk_assessment_create, name='risk_assessment_create_standalone'),
    path('risk-treatment-plans/create/', views.risk_treatment_plan_create, name='risk_treatment_plan_create_standalone'),
    
    # Compliance URLs
    path('compliance/requirements/', views.compliance_requirement_list, name='compliance_requirement_list'),
    path('compliance/requirements/create/', views.compliance_requirement_create, name='compliance_requirement_create'),
    path('compliance/requirements/<int:pk>/update/', views.compliance_requirement_update, name='compliance_requirement_update'),
    path('compliance/requirements/<int:requirement_pk>/assessments/create/', views.compliance_assessment_create, name='compliance_assessment_create'),
    
    # Internal Controls URLs
    path('controls/', views.internal_control_list, name='internal_control_list'),
    path('controls/create/', views.internal_control_create, name='internal_control_create'),
    path('controls/<int:pk>/update/', views.internal_control_update, name='internal_control_update'),
    
    # Ethics URLs
    path('ethics/cases/', views.ethics_case_list, name='ethics_case_list'),
    path('ethics/cases/create/', views.ethics_case_create, name='ethics_case_create'),
    path('ethics/cases/<int:pk>/update/', views.ethics_case_update, name='ethics_case_update'),
    
    # Conflict of Interest URLs
    path('conflicts/', views.conflict_of_interest_declaration_list, name='conflict_of_interest_declaration_list'),
    path('conflicts/create/', views.conflict_of_interest_declaration_create, name='conflict_of_interest_declaration_create'),
    path('conflicts/<int:pk>/update/', views.conflict_of_interest_declaration_update, name='conflict_of_interest_declaration_update'),
    
    # Safeguarding URLs
    path('safeguarding/cases/', views.safeguarding_case_list, name='safeguarding_case_list'),
    path('safeguarding/cases/create/', views.safeguarding_case_create, name='safeguarding_case_create'),
    path('safeguarding/cases/<int:pk>/update/', views.safeguarding_case_update, name='safeguarding_case_update'),
    
    # Incident Reporting URLs
    path('incidents/', views.incident_report_list, name='incident_report_list'),
    path('incidents/create/', views.incident_report_create, name='incident_report_create'),
    path('incidents/<int:pk>/update/', views.incident_report_update, name='incident_report_update'),
    
    # Complaint URLs
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/create/', views.complaint_create, name='complaint_create'),
    path('complaints/<int:pk>/update/', views.complaint_update, name='complaint_update'),
    
    # Whistleblower URLs
    path('whistleblower/reports/', views.whistleblower_report_list, name='whistleblower_report_list'),
    path('whistleblower/reports/create/', views.whistleblower_report_create, name='whistleblower_report_create'),
    path('whistleblower/reports/<int:pk>/update/', views.whistleblower_report_update, name='whistleblower_report_update'),
    
    # CAPA URLs
    path('capas/', views.corrective_preventive_action_list, name='corrective_preventive_action_list'),
    path('capas/create/', views.corrective_preventive_action_create, name='corrective_preventive_action_create'),
    path('capas/<int:pk>/update/', views.corrective_preventive_action_update, name='corrective_preventive_action_update'),
    
    # Document URLs
    path('documents/', views.document_list, name='document_list'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/<int:pk>/update/', views.document_update, name='document_update'),
    
    # Governance Meeting URLs
    path('meetings/', views.governance_meeting_list, name='governance_meeting_list'),
    path('meetings/create/', views.governance_meeting_create, name='governance_meeting_create'),
    path('meetings/<int:pk>/update/', views.governance_meeting_update, name='governance_meeting_update'),
    path('meetings/<int:meeting_pk>/attendance/create/', views.meeting_attendance_create, name='meeting_attendance_create'),
    
    # Notification URLs
    path('notifications/', views.governance_notification_list, name='governance_notification_list'),
    path('notifications/<int:pk>/mark-as-read/', views.governance_notification_mark_as_read, name='governance_notification_mark_as_read'),
    
    # Timeline URLs
    path('timeline/', views.governance_timeline_list, name='governance_timeline_list'),
    
    # AJAX endpoints
    path('ajax/update-risk-assessment-scores/', views.update_risk_assessment_scores, name='update_risk_assessment_scores'),
    
    # Legacy placeholder views for integration with existing modules
    path('financial-years/', views.financial_year_list, name='financial_year_list'),
    path('financial-years/create/', views.financial_year_create, name='financial_year_create'),
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('budget-allocations/', views.budget_allocation_list, name='budget_allocation_list'),
    path('budget-allocations/create/', views.budget_allocation_create, name='budget_allocation_create'),
]