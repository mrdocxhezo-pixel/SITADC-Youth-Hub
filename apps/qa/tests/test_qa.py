from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.qa.constants import (
    DefectSeverity,
    DefectStatus,
    EnvironmentType,
    QualityDashboardWidgetType,
    QualityMetricType,
    ReleaseCandidateStatus,
    TestCaseStatus,
    TestCategory,
    TestExecutionStatus,
    TestPlanStatus,
    TestPriority,
)
from apps.qa.models import (
    Defect,
    QAAuditReference,
    QAConfiguration,
    QANotification,
    QualityDashboard,
    QualityMetric,
    ReleaseCandidate,
    TestCase,
    TestDataSet,
    TestEnvironment,
    TestExecution,
    TestPlan,
    TestSuite,
)
from apps.qa.selectors import (
    get_active_test_environments,
    get_defects,
    get_qa_configuration,
    get_qa_notifications,
    get_release_candidates,
    get_test_cases,
    get_test_plans,
    get_test_suites,
    user_can_manage_qa,
    user_can_view_qa,
)
from apps.qa.services import (
    DefectService,
    QualityDashboardService,
    QualityMetricService,
    ReleaseCandidateService,
    TestCaseService,
    TestExecutionService,
    TestPlanService,
    TestSuiteService,
)

User = get_user_model()


# Fixtures


@pytest.fixture
def user():
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def user2():
    return User.objects.create_user(
        username="testuser2", email="test2@example.com", password="testpass123"
    )


@pytest.fixture
def test_plan(user):
    return TestPlan.objects.create(
        name="Test Plan",
        version="1.0",
        status=TestPlanStatus.DRAFT,
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timedelta(days=30)).date(),
        created_by=user,
        updated_by=user,
    )


@pytest.fixture
def test_suite(user, test_plan):
    return TestSuite.objects.create(
        name="Test Suite", test_plan=test_plan, created_by=user, updated_by=user
    )


@pytest.fixture
def test_case(user, test_suite):
    return TestCase.objects.create(
        test_suite=test_suite,
        test_id="TC-001",
        title="Test Case 1",
        status=TestCaseStatus.DRAFT,
        priority=TestPriority.HIGH,
        category=TestCategory.FUNCTIONAL,
        created_by=user,
        updated_by=user,
    )


# QAConfiguration Tests


@pytest.mark.django_db
def test_qa_configuration_singleton(user):
    """Test QAConfiguration singleton behavior."""
    config1 = QAConfiguration.objects.create(
        testing_policies={"policy": "test"}, created_by=user, updated_by=user
    )
    config2 = QAConfiguration.get_solo()
    assert config1.pk == config2.pk

    # Should not allow second instance
    with pytest.raises(ValueError):
        QAConfiguration.objects.create(
            testing_policies={"policy": "test2"}, created_by=user, updated_by=user
        )


@pytest.mark.django_db
def test_qa_configuration_get_solo(user):
    """Test QAConfiguration.get_solo creates instance if not exists."""
    QAConfiguration.objects.all().delete()
    config = QAConfiguration.get_solo()
    assert config is not None
    assert QAConfiguration.objects.count() == 1


# TestEnvironment Tests


@pytest.mark.django_db
def test_test_environment_creation(user):
    """Test TestEnvironment creation."""
    env = TestEnvironment.objects.create(
        name="Test Environment",
        environment_type=EnvironmentType.QA,
        base_url="https://qa.example.com",
        created_by=user,
        updated_by=user,
    )
    assert env.name == "Test Environment"
    assert env.environment_type == EnvironmentType.QA
    assert env.is_active is True


@pytest.mark.django_db
def test_test_environment_is_default(user):
    """Test TestEnvironment default behavior."""
    env1 = TestEnvironment.objects.create(
        name="Env 1",
        environment_type=EnvironmentType.QA,
        is_default=True,
        created_by=user,
        updated_by=user,
    )
    env2 = TestEnvironment.objects.create(
        name="Env 2",
        environment_type=EnvironmentType.DEVELOPMENT,
        is_default=True,
        created_by=user,
        updated_by=user,
    )
    env1.refresh_from_db()
    assert env1.is_default is False
    assert env2.is_default is True


# TestDataSet Tests


@pytest.mark.django_db
def test_test_data_set_creation(user):
    """Test TestDataSet creation."""
    env = TestEnvironment.objects.create(
        name="Test Env",
        environment_type=EnvironmentType.QA,
        created_by=user,
        updated_by=user,
    )
    data_set = TestDataSet.objects.create(
        name="Test Data",
        data_type="SYNTHETIC",
        version="1.0",
        environment=env,
        created_by=user,
        updated_by=user,
    )
    assert data_set.name == "Test Data"
    assert data_set.data_type == "SYNTHETIC"


# TestPlan Tests


@pytest.mark.django_db
def test_test_plan_creation(user):
    """Test TestPlan creation."""
    plan = TestPlan.objects.create(
        name="Test Plan",
        version="1.0",
        status=TestPlanStatus.DRAFT,
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timedelta(days=30)).date(),
        created_by=user,
        updated_by=user,
    )
    assert plan.name == "Test Plan"
    assert plan.status == TestPlanStatus.DRAFT


@pytest.mark.django_db
def test_test_plan_test_id_generation(user):
    """Test TestPlan test_id generation via ReferenceNumberService."""
    plan = TestPlan.objects.create(name="Test Plan", created_by=user, updated_by=user)
    assert plan.test_id is not None
    assert plan.test_id.startswith("TPL")


# TestSuite Tests


@pytest.mark.django_db
def test_test_suite_creation(user, test_plan):
    """Test TestSuite creation."""
    suite = TestSuite.objects.create(
        name="Test Suite", test_plan=test_plan, created_by=user, updated_by=user
    )
    assert suite.name == "Test Suite"
    assert suite.test_plan == test_plan


# TestCase Tests


@pytest.mark.django_db
def test_test_case_creation(user, test_suite):
    """Test TestCase creation."""
    case = TestCase.objects.create(
        test_suite=test_suite,
        test_id="TC-001",
        title="Test Case 1",
        status=TestCaseStatus.DRAFT,
        priority=TestPriority.HIGH,
        category=TestCategory.FUNCTIONAL,
        created_by=user,
        updated_by=user,
    )
    assert case.test_id == "TC-001"
    assert case.status == TestCaseStatus.DRAFT
    assert case.is_active is True


@pytest.mark.django_db
def test_test_case_test_id_generation(user, test_suite):
    """Test TestCase test_id generation."""
    case = TestCase.objects.create(
        test_suite=test_suite, title="Test Case 1", created_by=user, updated_by=user
    )
    assert case.test_id is not None
    assert case.test_id.startswith("TCS")


# TestExecution Tests


@pytest.mark.django_db
def test_test_execution_creation(user, test_plan, test_suite, test_case):
    """Test TestExecution creation."""
    execution = TestExecution.objects.create(
        test_case=test_case,
        test_plan=test_plan,
        test_suite=test_suite,
        executed_by=user,
        status=TestExecutionStatus.PENDING,
        created_by=user,
        updated_by=user,
    )
    assert execution.test_case == test_case
    assert execution.status == TestExecutionStatus.PENDING


# Defect Tests


@pytest.mark.django_db
def test_defect_creation(user):
    """Test Defect creation."""
    defect = Defect.objects.create(
        defect_id="DEF-001",
        title="Test Defect",
        description="Test defect description",
        severity=DefectSeverity.HIGH,
        priority=TestPriority.HIGH,
        reported_by=user,
        created_by=user,
        updated_by=user,
    )
    assert defect.defect_id == "DEF-001"
    assert defect.severity == DefectSeverity.HIGH
    assert defect.status == DefectStatus.NEW


@pytest.mark.django_db
def test_defect_defect_id_generation(user):
    """Test Defect defect_id generation."""
    defect = Defect.objects.create(
        title="Test Defect",
        description="Test defect description",
        created_by=user,
        updated_by=user,
    )
    assert defect.defect_id is not None
    assert defect.defect_id.startswith("DEF")


# ReleaseCandidate Tests


@pytest.mark.django_db
def test_release_candidate_creation(user):
    """Test ReleaseCandidate creation."""
    release = ReleaseCandidate.objects.create(
        version="1.0.0",
        name="Release 1.0",
        status=ReleaseCandidateStatus.DRAFT,
        branch="main",
        created_by=user,
        updated_by=user,
    )
    assert release.version == "1.0.0"
    assert release.status == ReleaseCandidateStatus.DRAFT


# QualityMetric Tests


@pytest.mark.django_db
def test_quality_metric_creation(user):
    """Test QualityMetric creation."""
    metric = QualityMetric.objects.create(
        metric_type=QualityMetricType.TEST_COVERAGE,
        name="Test Coverage",
        module="qa",
        value=85.5,
        target_value=95.0,
        unit="%",
        period_start=timezone.now() - timedelta(days=7),
        period_end=timezone.now(),
        calculated_by=user,
    )
    assert metric.metric_type == QualityMetricType.TEST_COVERAGE
    assert metric.value == 85.5


# QualityDashboard Tests


@pytest.mark.django_db
def test_quality_dashboard_singleton_default(user):
    """Test QualityDashboard default singleton behavior."""
    dashboard1 = QualityDashboard.objects.create(
        name="Dashboard 1", is_default=True, created_by=user, updated_by=user
    )
    dashboard2 = QualityDashboard.objects.create(
        name="Dashboard 2", is_default=True, created_by=user, updated_by=user
    )
    dashboard1.refresh_from_db()
    assert dashboard1.is_default is False
    assert dashboard2.is_default is True


# QANotification Tests


@pytest.mark.django_db
def test_qa_notification_creation(user):
    """Test QANotification creation."""
    notification = QANotification.objects.create(
        notification_type="TEST_FAILURE",
        title="Test Failed",
        message="A test failed",
        recipient=user,
        priority=TestPriority.HIGH,
        created_by=user,
        updated_by=user,
    )
    assert notification.notification_type == "TEST_FAILURE"
    assert notification.is_read is False


# QAAuditReference Tests


@pytest.mark.django_db
def test_qa_audit_reference_immutable(user):
    """Test QAAuditReference immutability."""
    audit = QAAuditReference.objects.create(
        reference_id="QA-AUD-001",
        event_type="TEST_PLAN_CREATED",
        module="qa",
        user=user,
        after_values={"name": "Test Plan"},
    )
    assert audit.reference_id == "QA-AUD-001"

    # Should not allow update
    with pytest.raises(ValueError):
        audit.event_type = "UPDATED"
        audit.save()

    # Should not allow delete
    with pytest.raises(ValueError):
        audit.delete()


# Service Tests


@pytest.mark.django_db
def test_test_plan_service_create(user):
    """Test TestPlanService.create_test_plan."""
    plan = TestPlanService.create_test_plan(
        user,
        name="Test Plan",
        version="1.0",
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timedelta(days=30)).date(),
    )
    assert plan.name == "Test Plan"
    assert plan.test_id is not None


@pytest.mark.django_db
def test_test_plan_service_approve(user):
    """Test TestPlanService.approve_test_plan."""
    plan = TestPlanService.create_test_plan(user, name="Test Plan")
    plan = TestPlanService.approve_test_plan(user, plan)
    assert plan.status == TestPlanStatus.ACTIVE
    assert plan.approved_by == user


@pytest.mark.django_db
def test_test_suite_service_create(user, test_plan):
    """Test TestSuiteService.create_test_suite."""
    suite = TestSuiteService.create_test_suite(user, test_plan, name="Test Suite")
    assert suite.name == "Test Suite"
    assert suite.test_plan == test_plan


@pytest.mark.django_db
def test_test_case_service_create(user, test_suite):
    """Test TestCaseService.create_test_case."""
    case = TestCaseService.create_test_case(
        user,
        test_suite,
        title="Test Case 1",
        priority=TestPriority.HIGH,
        category=TestCategory.FUNCTIONAL,
    )
    assert case.title == "Test Case 1"
    assert case.test_id is not None


@pytest.mark.django_db
def test_test_execution_service_start_complete(user, test_plan, test_suite, test_case):
    """Test TestExecutionService start and complete."""
    execution = TestExecutionService.start_execution(
        user, test_case, test_plan, test_suite
    )
    assert execution.status == TestExecutionStatus.RUNNING

    execution = TestExecutionService.complete_execution(
        user,
        execution,
        TestExecutionStatus.PASSED,
        actual_results=["All steps passed"],
        duration_seconds=120,
    )
    assert execution.status == TestExecutionStatus.PASSED
    assert execution.duration_seconds == 120


@pytest.mark.django_db
def test_defect_service_create_resolve(user):
    """Test DefectService create and resolve."""
    defect = DefectService.create_defect(
        user,
        title="Test Defect",
        description="Test description",
        severity=DefectSeverity.HIGH,
        priority=TestPriority.HIGH,
        module="qa",
    )
    assert defect.defect_id == "DEF-001"
    assert defect.status == DefectStatus.NEW

    defect = DefectService.resolve_defect(user, defect, "FIXED", "Fixed the issue")
    assert defect.status == DefectStatus.DEVELOPER_VERIFIED


@pytest.mark.django_db
def test_release_candidate_service_create(user):
    """Test ReleaseCandidateService.create_release_candidate."""
    release = ReleaseCandidateService.create_release_candidate(
        user, version="1.0.0", name="Release 1.0"
    )
    assert release.version == "1.0.0"
    assert release.status == ReleaseCandidateStatus.DRAFT


@pytest.mark.django_db
def test_quality_metric_service_calculate(user):
    """Test QualityMetricService.calculate_metrics."""
    period_start = timezone.now() - timedelta(days=7)
    period_end = timezone.now()
    metrics = QualityMetricService.calculate_metrics(user, period_start, period_end)
    assert len(metrics) > 0


@pytest.mark.django_db
def test_quality_dashboard_service_get_data(user):
    """Test QualityDashboardService.get_dashboard_data."""
    dashboard = QualityDashboard.objects.create(
        name="Test Dashboard",
        is_default=True,
        widgets=[
            {"type": QualityDashboardWidgetType.OVERALL_QUALITY_SCORE},
            {"type": QualityDashboardWidgetType.TEST_EXECUTION_PROGRESS},
        ],
        created_by=user,
        updated_by=user,
    )
    data = QualityDashboardService.get_dashboard_data(dashboard)
    assert "OVERALL_QUALITY_SCORE" in data
    assert "TEST_EXECUTION_PROGRESS" in data


# Selector Tests


@pytest.mark.django_db
def test_get_qa_configuration(user):
    """Test get_qa_configuration."""
    config = get_qa_configuration()
    assert isinstance(config, QAConfiguration)


@pytest.mark.django_db
def test_get_test_environments(user):
    """Test get_active_test_environments."""
    TestEnvironment.objects.create(
        name="Env 1",
        environment_type=EnvironmentType.QA,
        created_by=user,
        updated_by=user,
    )
    TestEnvironment.objects.create(
        name="Env 2",
        environment_type=EnvironmentType.DEVELOPMENT,
        is_active=False,
        created_by=user,
        updated_by=user,
    )
    envs = get_active_test_environments(user)
    assert envs.count() == 1
    assert envs.first().name == "Env 1"


@pytest.mark.django_db
def test_get_test_plans(user):
    """Test get_test_plans."""
    TestPlan.objects.create(name="Plan 1", created_by=user, updated_by=user)
    TestPlan.objects.create(
        name="Plan 2", is_active=False, created_by=user, updated_by=user
    )
    plans = get_test_plans(user)
    assert plans.count() == 1


@pytest.mark.django_db
def test_get_test_suites(user, test_plan):
    """Test get_test_suites."""
    TestSuite.objects.create(
        name="Suite 1", test_plan=test_plan, created_by=user, updated_by=user
    )
    TestSuite.objects.create(
        name="Suite 2",
        test_plan=test_plan,
        is_active=False,
        created_by=user,
        updated_by=user,
    )
    suites = get_test_suites(test_plan, user)
    assert suites.count() == 1


@pytest.mark.django_db
def test_get_test_cases(user, test_suite):
    """Test get_test_cases."""
    TestCase.objects.create(
        test_suite=test_suite,
        test_id="TC-001",
        title="Case 1",
        created_by=user,
        updated_by=user,
    )
    TestCase.objects.create(
        test_suite=test_suite,
        test_id="TC-002",
        title="Case 2",
        is_active=False,
        created_by=user,
        updated_by=user,
    )
    cases = get_test_cases(test_suite, user)
    assert cases.count() == 1


@pytest.mark.django_db
def test_get_defects(user):
    """Test get_defects."""
    Defect.objects.create(
        defect_id="DEF-001",
        title="Defect 1",
        severity=DefectSeverity.HIGH,
        created_by=user,
        updated_by=user,
    )
    Defect.objects.create(
        defect_id="DEF-002",
        title="Defect 2",
        severity=DefectSeverity.LOW,
        created_by=user,
        updated_by=user,
    )
    defects = get_defects(user=user)
    assert defects.count() == 2


@pytest.mark.django_db
def test_get_release_candidates(user):
    """Test get_release_candidates."""
    ReleaseCandidate.objects.create(version="1.0.0", created_by=user, updated_by=user)
    ReleaseCandidate.objects.create(
        version="2.0.0", is_active=False, created_by=user, updated_by=user
    )
    releases = get_release_candidates(user)
    assert releases.count() == 1


@pytest.mark.django_db
def test_get_qa_notifications(user):
    """Test get_qa_notifications."""
    QANotification.objects.create(
        notification_type="TEST_FAILURE",
        title="Test",
        message="Msg",
        recipient=user,
        created_by=user,
        updated_by=user,
    )
    QANotification.objects.create(
        notification_type="TEST_FAILURE",
        title="Test 2",
        message="Msg",
        recipient=user,
        is_read=True,
        created_by=user,
        updated_by=user,
    )
    notifications = get_qa_notifications(user, unread_only=True)
    assert notifications.count() == 1


# Permission Tests


@pytest.mark.django_db
def test_user_can_view_qa_false_for_anonymous():
    """Test user_can_view_qa returns False for anonymous user."""
    assert user_can_view_qa(None) is False


@pytest.mark.django_db
def test_user_can_manage_qa_false_for_regular_user(user):
    """Test user_can_manage_qa returns False for regular user without perms."""
    assert user_can_manage_qa(user) is False
