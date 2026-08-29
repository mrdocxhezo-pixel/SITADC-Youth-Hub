from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from apps.qa.models import (
    Defect,
    QAAuditReference,
    QAConfiguration,
    QANotification,
    QATimeline,
    QualityDashboard,
    QualityMetric,
    ReleaseCandidate,
    TestCase,
    TestDataSet,
    TestEnvironment,
    TestExecution,
    TestPlan,
    TestScenario,
    TestSuite,
)
from apps.rbac.authorization import get_effective_permission_codes

User = get_user_model()


def user_has_perm(user: User, perm: str) -> bool:
    """Check if user has a specific permission."""
    if not user or not user.is_authenticated:
        return False
    return perm in get_effective_permission_codes(user)


def user_can_view_qa(user: User) -> bool:
    """Check if user has any QA view permission."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.view_qaconfiguration")


def user_can_manage_qa(user: User) -> bool:
    """Check if user has QA management permission."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.manage_qaconfiguration")


def user_can_view_test_plans(user: User) -> bool:
    """Check if user can view test plans."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.view_testplan")


def user_can_manage_test_plans(user: User) -> bool:
    """Check if user can manage test plans."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.manage_testplan")


def user_can_view_test_cases(user: User) -> bool:
    """Check if user can view test cases."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.view_testcase")


def user_can_manage_test_cases(user: User) -> bool:
    """Check if user can manage test cases."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.manage_testcase")


def user_can_view_test_executions(user: User) -> bool:
    """Check if user can view test executions."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.view_testexecution")


def user_can_manage_test_executions(user: User) -> bool:
    """Check if user can manage test executions."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.manage_testexecution")


def user_can_view_defects(user: User) -> bool:
    """Check if user can view defects."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.view_defect")


def user_can_manage_defects(user: User) -> bool:
    """Check if user can manage defects."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.manage_defect")


def user_can_view_release_candidates(user: User) -> bool:
    """Check if user can view release candidates."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.view_releasecandidate")


def user_can_manage_release_candidates(user: User) -> bool:
    """Check if user can manage release candidates."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.manage_releasecandidate")


def user_can_approve_release(user: User) -> bool:
    """Check if user can approve releases."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.approve_release")


def user_can_view_quality_metrics(user: User) -> bool:
    """Check if user can view quality metrics."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.view_qualitymetric")


def user_can_manage_quality_metrics(user: User) -> bool:
    """Check if user can manage quality metrics."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.manage_qualitymetric")


def user_can_view_quality_dashboards(user: User) -> bool:
    """Check if user can view quality dashboards."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.view_qualitydashboard")


def user_can_manage_quality_dashboards(user: User) -> bool:
    """Check if user can manage quality dashboards."""
    if not user or not user.is_authenticated:
        return False
    return user_has_perm(user, "qa.manage_qualitydashboard")


def get_qa_configuration() -> QAConfiguration | None:
    """Get the singleton QA configuration."""
    return QAConfiguration.get_solo()


def get_active_test_environments(user: User | None = None) -> QuerySet[TestEnvironment]:
    """Get active test environments user can view."""
    queryset = TestEnvironment.objects.filter(is_active=True)
    if user and not user_can_manage_qa(user):
        pass
    return queryset.select_related("created_by", "updated_by")


def get_test_environment(pk: Any, user: User | None = None) -> TestEnvironment | None:
    """Get test environment by PK if user has access."""
    if user and not user_can_view_qa(user):
        return None
    try:
        return TestEnvironment.objects.select_related("created_by", "updated_by").get(
            pk=pk, is_active=True
        )
    except TestEnvironment.DoesNotExist:
        return None


def get_test_data_sets(user: User | None = None) -> QuerySet[TestDataSet]:
    """Get test data sets user can view."""
    queryset = TestDataSet.objects.filter(is_active=True)
    if user and not user_can_manage_qa(user):
        pass
    return queryset.select_related("environment", "created_by", "updated_by")


def get_test_data_set(pk: Any, user: User | None = None) -> TestDataSet | None:
    """Get test data set by PK if user has access."""
    if user and not user_can_view_qa(user):
        return None
    try:
        return TestDataSet.objects.select_related(
            "environment", "created_by", "updated_by"
        ).get(pk=pk, is_active=True)
    except TestDataSet.DoesNotExist:
        return None


def get_test_plans(user: User | None = None) -> QuerySet[TestPlan]:
    """Get test plans user can view."""
    if user and not user_can_view_test_plans(user):
        return TestPlan.objects.none()
    queryset = (
        TestPlan.objects.filter(is_active=True)
        .select_related("release_candidate", "approved_by", "created_by", "updated_by")
        .prefetch_related("test_suites")
    )
    return queryset


def get_test_plan(pk: Any, user: User | None = None) -> TestPlan | None:
    """Get test plan by PK if user has access."""
    if user and not user_can_view_test_plans(user):
        return None
    try:
        return (
            TestPlan.objects.select_related(
                "release_candidate", "approved_by", "created_by", "updated_by"
            )
            .prefetch_related("test_suites__test_cases")
            .get(pk=pk, is_active=True)
        )
    except TestPlan.DoesNotExist:
        return None


def get_test_suites(
    test_plan: TestPlan | None = None, user: User | None = None
) -> QuerySet[TestSuite]:
    """Get test suites user can view."""
    if user and not user_can_view_test_plans(user):
        return TestSuite.objects.none()
    queryset = TestSuite.objects.filter(is_active=True).select_related(
        "test_plan", "parent", "created_by", "updated_by"
    )
    if test_plan:
        queryset = queryset.filter(test_plan=test_plan)
    return queryset


def get_test_suite(pk: Any, user: User | None = None) -> TestSuite | None:
    """Get test suite by PK if user has access."""
    if user and not user_can_view_test_plans(user):
        return None
    try:
        return (
            TestSuite.objects.select_related(
                "test_plan", "parent", "created_by", "updated_by"
            )
            .prefetch_related("children", "test_cases")
            .get(pk=pk, is_active=True)
        )
    except TestSuite.DoesNotExist:
        return None


def get_test_cases(
    test_suite: TestSuite | None = None, user: User | None = None
) -> QuerySet[TestCase]:
    """Get test cases user can view."""
    if user and not user_can_view_test_cases(user):
        return TestCase.objects.none()
    queryset = TestCase.objects.filter(is_active=True).select_related(
        "test_suite",
        "test_suite__test_plan",
        "assigned_to",
        "reviewed_by",
        "created_by",
        "updated_by",
    )
    if test_suite:
        queryset = queryset.filter(test_suite=test_suite)
    return queryset


def get_test_case(pk: Any, user: User | None = None) -> TestCase | None:
    """Get test case by PK if user has access."""
    if user and not user_can_view_test_cases(user):
        return None
    try:
        return TestCase.objects.select_related(
            "test_suite",
            "test_suite__test_plan",
            "assigned_to",
            "reviewed_by",
            "created_by",
            "updated_by",
        ).get(pk=pk, is_active=True)
    except TestCase.DoesNotExist:
        return None


def get_test_scenarios(
    test_plan: TestPlan | None = None, user: User | None = None
) -> QuerySet[TestScenario]:
    """Get test scenarios user can view."""
    if user and not user_can_view_test_plans(user):
        return TestScenario.objects.none()
    queryset = (
        TestScenario.objects.filter(is_active=True)
        .select_related("test_plan", "created_by", "updated_by")
        .prefetch_related("test_cases")
    )
    if test_plan:
        queryset = queryset.filter(test_plan=test_plan)
    return queryset


def get_test_scenario(pk: Any, user: User | None = None) -> TestScenario | None:
    """Get test scenario by PK if user has access."""
    if user and not user_can_view_test_plans(user):
        return None
    try:
        return (
            TestScenario.objects.select_related("test_plan", "created_by", "updated_by")
            .prefetch_related("test_cases")
            .get(pk=pk, is_active=True)
        )
    except TestScenario.DoesNotExist:
        return None


def get_test_executions(
    test_plan: TestPlan | None = None,
    test_suite: TestSuite | None = None,
    test_case: TestCase | None = None,
    user: User | None = None,
) -> QuerySet[TestExecution]:
    """Get test executions user can view."""
    if user and not user_can_view_test_executions(user):
        return TestExecution.objects.none()
    queryset = TestExecution.objects.filter(is_active=True).select_related(
        "test_case",
        "test_plan",
        "test_suite",
        "environment",
        "test_data_set",
        "executed_by",
        "defect",
        "created_by",
        "updated_by",
    )
    if test_plan:
        queryset = queryset.filter(test_plan=test_plan)
    if test_suite:
        queryset = queryset.filter(test_suite=test_suite)
    if test_case:
        queryset = queryset.filter(test_case=test_case)
    return queryset


def get_test_execution(pk: Any, user: User | None = None) -> TestExecution | None:
    """Get test execution by PK if user has access."""
    if user and not user_can_view_test_executions(user):
        return None
    try:
        return (
            TestExecution.objects.select_related(
                "test_case",
                "test_plan",
                "test_suite",
                "environment",
                "test_data_set",
                "executed_by",
                "defect",
                "created_by",
                "updated_by",
            )
            .prefetch_related("test_results", "evidence")
            .get(pk=pk, is_active=True)
        )
    except TestExecution.DoesNotExist:
        return None


def get_defects(
    module: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    assigned_to: User | None = None,
    user: User | None = None,
) -> QuerySet[Defect]:
    """Get defects user can view."""
    if user and not user_can_view_defects(user):
        return Defect.objects.none()
    queryset = (
        Defect.objects.filter(is_active=True)
        .select_related(
            "environment",
            "test_execution",
            "test_case",
            "reported_by",
            "assigned_to",
            "verified_by",
            "resolved_by",
            "regression_tested_by",
            "closed_by",
            "created_by",
            "updated_by",
        )
        .prefetch_related("related_defects")
    )
    if module:
        queryset = queryset.filter(module=module)
    if status:
        queryset = queryset.filter(status=status)
    if severity:
        queryset = queryset.filter(severity=severity)
    if assigned_to:
        queryset = queryset.filter(assigned_to=assigned_to)
    return queryset


def get_defect(pk: Any, user: User | None = None) -> Defect | None:
    """Get defect by PK if user has access."""
    if user and not user_can_view_defects(user):
        return None
    try:
        return (
            Defect.objects.select_related(
                "environment",
                "test_execution",
                "test_case",
                "reported_by",
                "assigned_to",
                "verified_by",
                "resolved_by",
                "regression_tested_by",
                "closed_by",
                "created_by",
                "updated_by",
            )
            .prefetch_related("related_defects", "assignments", "resolutions")
            .get(pk=pk, is_active=True)
        )
    except Defect.DoesNotExist:
        return None


def get_release_candidates(user: User | None = None) -> QuerySet[ReleaseCandidate]:
    """Get release candidates user can view."""
    if user and not user_can_view_release_candidates(user):
        return ReleaseCandidate.objects.none()
    return (
        ReleaseCandidate.objects.filter(is_active=True)
        .select_related("deployed_by", "test_plan", "created_by", "updated_by")
        .prefetch_related("approvals", "uat_sessions", "regression_tests")
    )


def get_release_candidate(pk: Any, user: User | None = None) -> ReleaseCandidate | None:
    """Get release candidate by PK if user has access."""
    if user and not user_can_view_release_candidates(user):
        return None
    try:
        return (
            ReleaseCandidate.objects.select_related(
                "deployed_by", "test_plan", "created_by", "updated_by"
            )
            .prefetch_related("approvals", "uat_sessions", "regression_tests")
            .get(pk=pk, is_active=True)
        )
    except ReleaseCandidate.DoesNotExist:
        return None


def get_quality_metrics(
    metric_type: str | None = None, module: str | None = None, user: User | None = None
) -> QuerySet[QualityMetric]:
    """Get quality metrics user can view."""
    if user and not user_can_view_quality_metrics(user):
        return QualityMetric.objects.none()
    queryset = QualityMetric.objects.filter(is_active=True).select_related(
        "calculated_by", "created_by", "updated_by"
    )
    if metric_type:
        queryset = queryset.filter(metric_type=metric_type)
    if module:
        queryset = queryset.filter(module=module)
    return queryset


def get_quality_dashboard(user: User | None = None) -> QualityDashboard | None:
    """Get default quality dashboard user can view."""
    if user and not user_can_view_quality_dashboards(user):
        return None
    try:
        return (
            QualityDashboard.objects.filter(is_active=True, is_default=True)
            .select_related("owner", "created_by", "updated_by")
            .first()
        )
    except QualityDashboard.DoesNotExist:
        return None


def get_qa_notifications(
    user: User, unread_only: bool = False
) -> QuerySet[QANotification]:
    """Get QA notifications for user."""
    if not user or not user.is_authenticated:
        return QANotification.objects.none()
    queryset = QANotification.objects.filter(
        recipient=user, is_active=True
    ).select_related("recipient")
    if unread_only:
        queryset = queryset.filter(is_read=False)
    return queryset


def get_qa_timeline(
    module: str | None = None, event_type: str | None = None, user: User | None = None
) -> QuerySet[QATimeline]:
    """Get QA timeline events."""
    if user and not user_can_view_qa(user):
        return QATimeline.objects.none()
    queryset = QATimeline.objects.filter(is_active=True).select_related(
        "tester", "created_by", "updated_by"
    )
    if module:
        queryset = queryset.filter(module=module)
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    return queryset


def get_qa_audit_references(
    reference_id: str | None = None,
    event_type: str | None = None,
    module: str | None = None,
    user: User | None = None,
) -> QuerySet[QAAuditReference]:
    """Get QA audit references."""
    if user and not user_can_manage_qa(user):
        return QAAuditReference.objects.none()
    queryset = QAAuditReference.objects.select_related("user")
    if reference_id:
        queryset = queryset.filter(reference_id=reference_id)
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    if module:
        queryset = queryset.filter(module=module)
    return queryset
