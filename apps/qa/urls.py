from django.urls import path

from apps.qa import views

app_name = "qa"

urlpatterns = [
    # Dashboard
    path("", views.QADashboardView.as_view(), name="dashboard"),
    # Configuration
    path("configuration/", views.QAConfigurationView.as_view(), name="configuration"),
    # Test Environments
    path(
        "environments/",
        views.TestEnvironmentListView.as_view(),
        name="test_environment_list",
    ),
    path(
        "environments/create/",
        views.TestEnvironmentCreateView.as_view(),
        name="test_environment_create",
    ),
    path(
        "environments/<int:pk>/",
        views.TestEnvironmentDetailView.as_view(),
        name="test_environment_detail",
    ),
    path(
        "environments/<int:pk>/edit/",
        views.TestEnvironmentUpdateView.as_view(),
        name="test_environment_update",
    ),
    # Test Data Sets
    path("data-sets/", views.TestDataSetListView.as_view(), name="test_data_set_list"),
    path(
        "data-sets/create/",
        views.TestDataSetCreateView.as_view(),
        name="test_data_set_create",
    ),
    path(
        "data-sets/<int:pk>/",
        views.TestDataSetDetailView.as_view(),
        name="test_data_set_detail",
    ),
    # Test Plans
    path("plans/", views.TestPlanListView.as_view(), name="test_plan_list"),
    path("plans/create/", views.TestPlanCreateView.as_view(), name="test_plan_create"),
    path(
        "plans/<int:pk>/", views.TestPlanDetailView.as_view(), name="test_plan_detail"
    ),
    path(
        "plans/<int:pk>/edit/",
        views.TestPlanUpdateView.as_view(),
        name="test_plan_update",
    ),
    path(
        "plans/<int:pk>/approve/",
        views.TestPlanApproveView.as_view(),
        name="test_plan_approve",
    ),
    # Test Suites
    path(
        "plans/<int:test_plan_pk>/suites/create/",
        views.TestSuiteCreateView.as_view(),
        name="test_suite_create",
    ),
    path(
        "suites/<int:pk>/edit/",
        views.TestSuiteUpdateView.as_view(),
        name="test_suite_update",
    ),
    # Test Cases
    path("cases/", views.TestCaseListView.as_view(), name="test_case_list"),
    path(
        "suites/<int:test_suite_pk>/cases/create/",
        views.TestCaseCreateView.as_view(),
        name="test_case_create",
    ),
    path(
        "cases/<int:pk>/", views.TestCaseDetailView.as_view(), name="test_case_detail"
    ),
    path(
        "cases/<int:pk>/edit/",
        views.TestCaseUpdateView.as_view(),
        name="test_case_update",
    ),
    # Test Scenarios
    path(
        "plans/<int:test_plan_pk>/scenarios/create/",
        views.TestScenarioCreateView.as_view(),
        name="test_scenario_create",
    ),
    # Test Executions
    path(
        "executions/", views.TestExecutionListView.as_view(), name="test_execution_list"
    ),
    path(
        "plans/<int:test_plan_pk>/executions/",
        views.TestExecutionListView.as_view(),
        name="test_execution_list_by_plan",
    ),
    path(
        "suites/<int:test_suite_pk>/executions/",
        views.TestExecutionListView.as_view(),
        name="test_execution_list_by_suite",
    ),
    path(
        "cases/<int:test_case_pk>/executions/",
        views.TestExecutionListView.as_view(),
        name="test_execution_list_by_case",
    ),
    path(
        "executions/<int:pk>/",
        views.TestExecutionDetailView.as_view(),
        name="test_execution_detail",
    ),
    path(
        "cases/<int:test_case_pk>/execute/",
        views.TestExecutionStartView.as_view(),
        name="test_execution_start",
    ),
    path(
        "executions/<int:pk>/complete/",
        views.TestExecutionCompleteView.as_view(),
        name="test_execution_complete",
    ),
    # Defects
    path("defects/", views.DefectListView.as_view(), name="defect_list"),
    path("defects/create/", views.DefectCreateView.as_view(), name="defect_create"),
    path(
        "plans/<int:test_plan_pk>/defects/create/",
        views.DefectCreateView.as_view(),
        name="defect_create_for_plan",
    ),
    path(
        "suites/<int:test_suite_pk>/defects/create/",
        views.DefectCreateView.as_view(),
        name="defect_create_for_suite",
    ),
    path(
        "cases/<int:test_case_pk>/defects/create/",
        views.DefectCreateView.as_view(),
        name="defect_create_for_case",
    ),
    path(
        "executions/<int:test_execution_pk>/defects/create/",
        views.DefectCreateView.as_view(),
        name="defect_create_for_execution",
    ),
    path("defects/<int:pk>/", views.DefectDetailView.as_view(), name="defect_detail"),
    path(
        "defects/<int:pk>/edit/", views.DefectUpdateView.as_view(), name="defect_update"
    ),
    path(
        "defects/<int:pk>/resolve/",
        views.DefectResolveView.as_view(),
        name="defect_resolve",
    ),
    path(
        "defects/<int:pk>/verify/",
        views.DefectVerifyView.as_view(),
        name="defect_verify",
    ),
    path(
        "defects/<int:pk>/close/", views.DefectCloseView.as_view(), name="defect_close"
    ),
    # Release Candidates
    path(
        "releases/",
        views.ReleaseCandidateListView.as_view(),
        name="release_candidate_list",
    ),
    path(
        "releases/create/",
        views.ReleaseCandidateCreateView.as_view(),
        name="release_candidate_create",
    ),
    path(
        "releases/<int:pk>/",
        views.ReleaseCandidateDetailView.as_view(),
        name="release_candidate_detail",
    ),
    path(
        "releases/<int:pk>/submit/",
        views.ReleaseCandidateSubmitView.as_view(),
        name="release_candidate_submit",
    ),
    path(
        "releases/<int:pk>/approve/",
        views.ReleaseCandidateApproveView.as_view(),
        name="release_candidate_approve",
    ),
    # Quality Metrics
    path("metrics/", views.QualityMetricListView.as_view(), name="quality_metric_list"),
    path(
        "metrics/create/",
        views.QualityMetricCreateView.as_view(),
        name="quality_metric_create",
    ),
    path(
        "metrics/calculate/",
        views.QualityMetricCalculateView.as_view(),
        name="quality_metric_calculate",
    ),
    # Quality Dashboards
    path(
        "dashboards/",
        views.QualityDashboardListView.as_view(),
        name="quality_dashboard_list",
    ),
    path(
        "dashboards/create/",
        views.QualityDashboardCreateView.as_view(),
        name="quality_dashboard_create",
    ),
    path(
        "dashboards/<int:pk>/",
        views.QualityDashboardDetailView.as_view(),
        name="quality_dashboard_detail",
    ),
    # Notifications
    path(
        "notifications/",
        views.QANotificationListView.as_view(),
        name="notification_list",
    ),
    path(
        "notifications/<int:pk>/read/",
        views.QANotificationMarkReadView.as_view(),
        name="notification_mark_read",
    ),
    path(
        "notifications/mark-all-read/",
        views.QANotificationMarkAllReadView.as_view(),
        name="notification_mark_all_read",
    ),
    # Audit
    path(
        "audit/", views.QAAuditReferenceListView.as_view(), name="audit_reference_list"
    ),
    path(
        "audit/<int:pk>/",
        views.QAAuditReferenceDetailView.as_view(),
        name="audit_reference_detail",
    ),
    # API Endpoints
    path("api/dashboard-data/", views.qa_dashboard_data_api, name="api_dashboard_data"),
    path(
        "api/notification-count/",
        views.qa_notification_count_api,
        name="api_notification_count",
    ),
    path(
        "api/test-case-autocomplete/",
        views.test_case_autocomplete_api,
        name="api_test_case_autocomplete",
    ),
    path(
        "api/defect-autocomplete/",
        views.defect_autocomplete_api,
        name="api_defect_autocomplete",
    ),
]
