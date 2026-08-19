"""URL configuration for Governance, Risk, Compliance and Safeguarding (Phase 29)."""

from django.urls import path

from . import views

app_name = "governance"

urlpatterns = [
    # Dashboard
    path("", views.governance_dashboard, name="governance_dashboard"),
    # Policy URLs
    path("policies/", views.policy_list, name="policy_list"),
    path("policies/create/", views.policy_create, name="policy_create"),
    path("policies/<uuid:pk>/update/", views.policy_update, name="policy_update"),
    path("policies/<uuid:pk>/delete/", views.policy_delete, name="policy_delete"),
    path("policies/<uuid:pk>/", views.policy_detail, name="policy_detail"),
    path(
        "policies/<uuid:policy_pk>/versions/create/",
        views.policy_version_create,
        name="policy_version_create",
    ),
    path(
        "policies/<uuid:policy_pk>/acknowledgements/create/",
        views.policy_acknowledgement_create,
        name="policy_acknowledgement_create",
    ),
    # Risk Management URLs
    path("risks/", views.risk_register_list, name="risk_register_list"),
    path("risks/create/", views.risk_register_create, name="risk_register_create"),
    path(
        "risks/<uuid:pk>/update/",
        views.risk_register_update,
        name="risk_register_update",
    ),
    path(
        "risks/<uuid:pk>/delete/",
        views.risk_register_delete,
        name="risk_register_delete",
    ),
    path("risks/<uuid:pk>/", views.risk_register_detail, name="risk_register_detail"),
    path(
        "risks/<uuid:risk_pk>/assessments/create/",
        views.risk_assessment_create,
        name="risk_assessment_create",
    ),
    path(
        "risks/<uuid:risk_pk>/treatment-plans/create/",
        views.risk_treatment_plan_create,
        name="risk_treatment_plan_create",
    ),
    # Compliance URLs
    path(
        "compliance/requirements/",
        views.compliance_requirement_list,
        name="compliance_requirement_list",
    ),
    path(
        "compliance/requirements/create/",
        views.compliance_requirement_create,
        name="compliance_requirement_create",
    ),
    path(
        "compliance/requirements/<uuid:pk>/update/",
        views.compliance_requirement_update,
        name="compliance_requirement_update",
    ),
    path(
        "compliance/requirements/<uuid:pk>/delete/",
        views.compliance_requirement_delete,
        name="compliance_requirement_delete",
    ),
    path(
        "compliance/requirements/<uuid:pk>/",
        views.compliance_requirement_detail,
        name="compliance_requirement_detail",
    ),
    path(
        "compliance/requirements/<uuid:requirement_pk>/assessments/create/",
        views.compliance_assessment_create,
        name="compliance_assessment_create",
    ),
    # Internal Controls URLs
    path("controls/", views.internal_control_list, name="internal_control_list"),
    path(
        "controls/create/",
        views.internal_control_create,
        name="internal_control_create",
    ),
    path(
        "controls/<uuid:pk>/update/",
        views.internal_control_update,
        name="internal_control_update",
    ),
    path(
        "controls/<uuid:pk>/delete/",
        views.internal_control_delete,
        name="internal_control_delete",
    ),
    path(
        "controls/<uuid:pk>/",
        views.internal_control_detail,
        name="internal_control_detail",
    ),
    # Ethics URLs
    path("ethics/cases/", views.ethics_case_list, name="ethics_case_list"),
    path("ethics/cases/create/", views.ethics_case_create, name="ethics_case_create"),
    path(
        "ethics/cases/<uuid:pk>/update/",
        views.ethics_case_update,
        name="ethics_case_update",
    ),
    path(
        "ethics/cases/<uuid:pk>/delete/",
        views.ethics_case_delete,
        name="ethics_case_delete",
    ),
    path(
        "ethics/cases/<uuid:pk>/", views.ethics_case_detail, name="ethics_case_detail"
    ),
    # Conflict of Interest URLs
    path(
        "conflicts/",
        views.conflict_of_interest_declaration_list,
        name="conflict_of_interest_declaration_list",
    ),
    path(
        "conflicts/create/",
        views.conflict_of_interest_declaration_create,
        name="conflict_of_interest_declaration_create",
    ),
    path(
        "conflicts/<uuid:pk>/update/",
        views.conflict_of_interest_declaration_update,
        name="conflict_of_interest_declaration_update",
    ),
    path(
        "conflicts/<uuid:pk>/delete/",
        views.conflict_of_interest_declaration_delete,
        name="conflict_of_interest_declaration_delete",
    ),
    path(
        "conflicts/<uuid:pk>/",
        views.conflict_of_interest_declaration_detail,
        name="conflict_of_interest_declaration_detail",
    ),
    # Safeguarding URLs
    path(
        "safeguarding/cases/",
        views.safeguarding_case_list,
        name="safeguarding_case_list",
    ),
    path(
        "safeguarding/cases/create/",
        views.safeguarding_case_create,
        name="safeguarding_case_create",
    ),
    path(
        "safeguarding/cases/<uuid:pk>/update/",
        views.safeguarding_case_update,
        name="safeguarding_case_update",
    ),
    path(
        "safeguarding/cases/<uuid:pk>/delete/",
        views.safeguarding_case_delete,
        name="safeguarding_case_delete",
    ),
    path(
        "safeguarding/cases/<uuid:pk>/",
        views.safeguarding_case_detail,
        name="safeguarding_case_detail",
    ),
    # Incident Reporting URLs
    path("incidents/", views.incident_report_list, name="incident_report_list"),
    path(
        "incidents/create/", views.incident_report_create, name="incident_report_create"
    ),
    path(
        "incidents/<uuid:pk>/update/",
        views.incident_report_update,
        name="incident_report_update",
    ),
    path(
        "incidents/<uuid:pk>/delete/",
        views.incident_report_delete,
        name="incident_report_delete",
    ),
    path(
        "incidents/<uuid:pk>/",
        views.incident_report_detail,
        name="incident_report_detail",
    ),
    # Complaint URLs
    path("complaints/", views.complaint_list, name="complaint_list"),
    path("complaints/create/", views.complaint_create, name="complaint_create"),
    path(
        "complaints/<uuid:pk>/update/", views.complaint_update, name="complaint_update"
    ),
    path(
        "complaints/<uuid:pk>/delete/", views.complaint_delete, name="complaint_delete"
    ),
    path("complaints/<uuid:pk>/", views.complaint_detail, name="complaint_detail"),
    # Whistleblower URLs
    path(
        "whistleblower/reports/",
        views.whistleblower_report_list,
        name="whistleblower_report_list",
    ),
    path(
        "whistleblower/reports/create/",
        views.whistleblower_report_create,
        name="whistleblower_report_create",
    ),
    path(
        "whistleblower/reports/<uuid:pk>/update/",
        views.whistleblower_report_update,
        name="whistleblower_report_update",
    ),
    path(
        "whistleblower/reports/<uuid:pk>/delete/",
        views.whistleblower_report_delete,
        name="whistleblower_report_delete",
    ),
    path(
        "whistleblower/reports/<uuid:pk>/",
        views.whistleblower_report_detail,
        name="whistleblower_report_detail",
    ),
    # CAPA URLs
    path(
        "capas/",
        views.corrective_preventive_action_list,
        name="corrective_preventive_action_list",
    ),
    path(
        "capas/create/",
        views.corrective_preventive_action_create,
        name="corrective_preventive_action_create",
    ),
    path(
        "capas/<uuid:pk>/update/",
        views.corrective_preventive_action_update,
        name="corrective_preventive_action_update",
    ),
    path(
        "capas/<uuid:pk>/delete/",
        views.corrective_preventive_action_delete,
        name="corrective_preventive_action_delete",
    ),
    path(
        "capas/<uuid:pk>/",
        views.corrective_preventive_action_detail,
        name="corrective_preventive_action_detail",
    ),
    # Document URLs
    path("documents/", views.document_list, name="document_list"),
    path("documents/create/", views.document_create, name="document_create"),
    path("documents/<uuid:pk>/update/", views.document_update, name="document_update"),
    path("documents/<uuid:pk>/delete/", views.document_delete, name="document_delete"),
    path("documents/<uuid:pk>/", views.document_detail, name="document_detail"),
    # Governance Meeting URLs
    path("meetings/", views.governance_meeting_list, name="governance_meeting_list"),
    path(
        "meetings/create/",
        views.governance_meeting_create,
        name="governance_meeting_create",
    ),
    path(
        "meetings/<uuid:pk>/update/",
        views.governance_meeting_update,
        name="governance_meeting_update",
    ),
    path(
        "meetings/<uuid:pk>/delete/",
        views.governance_meeting_delete,
        name="governance_meeting_delete",
    ),
    path(
        "meetings/<uuid:pk>/",
        views.governance_meeting_detail,
        name="governance_meeting_detail",
    ),
    path(
        "meetings/<uuid:meeting_pk>/attendance/create/",
        views.meeting_attendance_create,
        name="meeting_attendance_create",
    ),
    # Notification URLs
    path(
        "notifications/",
        views.governance_notification_list,
        name="governance_notification_list",
    ),
    path(
        "notifications/<uuid:pk>/mark-as-read/",
        views.governance_notification_mark_as_read,
        name="governance_notification_mark_as_read",
    ),
    # Timeline URLs
    path("timeline/", views.governance_timeline_list, name="governance_timeline_list"),
]
