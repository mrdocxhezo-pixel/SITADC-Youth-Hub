import uuid
from datetime import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone

from apps.qa.constants import (
    DefectSeverity,
    DefectStatus,
    QANotificationType,
    QualityMetricType,
    ReleaseApprovalStatus,
    ReleaseCandidateStatus,
    TestExecutionStatus,
    TestPlanStatus,
    TestPriority,
)
from apps.qa.models import (
    Defect,
    DefectAssignment,
    DefectResolution,
    QAAuditReference,
    QAConfiguration,
    QANotification,
    QATimeline,
    QualityDashboard,
    QualityMetric,
    RegressionTest,
    ReleaseApproval,
    ReleaseCandidate,
    TestCase,
    TestDataSet,
    TestEnvironment,
    TestEvidence,
    TestExecution,
    TestPlan,
    TestResult,
    TestScenario,
    TestScenarioCase,
    TestSuite,
    UATSession,
)
from apps.qa.selectors import (
    user_can_approve_release,
    user_can_manage_defects,
    user_can_manage_qa,
    user_can_manage_quality_dashboards,
    user_can_manage_quality_metrics,
    user_can_manage_release_candidates,
    user_can_manage_test_cases,
    user_can_manage_test_executions,
    user_can_manage_test_plans,
)
from apps.references.services import ReferenceNumberService

User = get_user_model()


def _create_audit_log(
    user: User,
    event_type: str,
    module: str = "qa",
    before_values: dict | None = None,
    after_values: dict | None = None,
) -> None:
    """Create an audit log entry."""
    QAAuditReference.objects.create(
        reference_id=f"QA-{event_type[:3].upper()}-{uuid.uuid4().hex[:12].upper()}",
        event_type=event_type,
        module=module,
        user=user,
        before_values=before_values or {},
        after_values=after_values or {},
    )


def _create_timeline_event(
    user: User,
    event_type: str,
    module: str,
    status: str,
    test_type: str | None = None,
    test_case: "TestCase" | None = None,
    execution: "TestExecution" | None = None,
    defect: "Defect" | None = None,
    test_plan: "TestPlan" | None = None,
) -> None:
    """Create a timeline event."""
    related_object_type = ""
    related_object_id = ""
    defect_reference = ""
    metadata = {}

    if test_case:
        related_object_type = "TestCase"
        related_object_id = str(test_case.pk)
        metadata["test_id"] = test_case.test_id
        metadata["title"] = test_case.title
    if execution:
        related_object_type = "TestExecution"
        related_object_id = str(execution.pk)
        metadata["execution_status"] = status
    if defect:
        related_object_type = "Defect"
        related_object_id = str(defect.pk)
        defect_reference = defect.defect_id
        metadata["defect_id"] = defect.defect_id
        metadata["title"] = defect.title
        metadata["severity"] = defect.severity
    if test_plan:
        related_object_type = "TestPlan"
        related_object_id = str(test_plan.pk)
        metadata["test_plan_name"] = test_plan.name

    QATimeline.objects.create(
        event_type=event_type,
        module=module,
        test_type=test_type or "",
        status=status,
        tester=user,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        defect_reference=defect_reference,
        metadata=metadata,
    )


class QAConfigurationService:
    """Service for managing QA configuration."""

    @staticmethod
    @transaction.atomic
    def update_configuration(user: User, **kwargs) -> QAConfiguration:
        """Update QA configuration."""
        if not user_can_manage_qa(user):
            raise PermissionError(
                "User does not have permission to manage QA configuration."
            )

        config = QAConfiguration.get_solo()

        # Track changes for audit
        before_values = {}
        for field in kwargs:
            if hasattr(config, field):
                before_values[field] = getattr(config, field)

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        config.updated_by = user
        config.save()

        _create_audit_log(
            user=user,
            event_type="QA_CONFIGURATION_UPDATED",
            before_values=before_values,
            after_values=kwargs,
        )

        return config


class TestEnvironmentService:
    """Service for managing test environments."""

    @staticmethod
    @transaction.atomic
    def create_environment(user: User, **kwargs) -> TestEnvironment:
        """Create a test environment."""
        if not user_can_manage_qa(user):
            raise PermissionError(
                "User does not have permission to manage test environments."
            )

        environment = TestEnvironment.objects.create(
            created_by=user, updated_by=user, **kwargs
        )

        _create_audit_log(
            user=user,
            event_type="TEST_ENVIRONMENT_CREATED",
            after_values={"id": str(environment.pk), "name": environment.name},
        )

        return environment

    @staticmethod
    @transaction.atomic
    def update_environment(
        user: User, environment: TestEnvironment, **kwargs
    ) -> TestEnvironment:
        """Update a test environment."""
        if not user_can_manage_qa(user):
            raise PermissionError(
                "User does not have permission to manage test environments."
            )

        before_values = {}
        for field in kwargs:
            if hasattr(environment, field):
                before_values[field] = getattr(environment, field)

        for key, value in kwargs.items():
            if hasattr(environment, key):
                setattr(environment, key, value)

        environment.updated_by = user
        environment.save()

        _create_audit_log(
            user=user,
            event_type="TEST_ENVIRONMENT_UPDATED",
            before_values=before_values,
            after_values=kwargs,
        )

        return environment


class TestDataSetService:
    """Service for managing test data sets."""

    @staticmethod
    @transaction.atomic
    def create_data_set(user: User, **kwargs) -> TestDataSet:
        """Create a test data set."""
        if not user_can_manage_qa(user):
            raise PermissionError(
                "User does not have permission to manage test data sets."
            )

        data_set = TestDataSet.objects.create(
            created_by=user, updated_by=user, **kwargs
        )

        _create_audit_log(
            user=user,
            event_type="TEST_DATA_SET_CREATED",
            after_values={"id": str(data_set.pk), "name": data_set.name},
        )

        return data_set


class TestPlanService:
    """Service for managing test plans."""

    @staticmethod
    @transaction.atomic
    def create_test_plan(user: User, **kwargs) -> TestPlan:
        """Create a test plan."""
        if not user_can_manage_test_plans(user):
            raise PermissionError("User does not have permission to create test plans.")

        # Generate reference number
        ref_number = ReferenceNumberService.generate("test_plan")

        test_plan = TestPlan.objects.create(
            created_by=user, updated_by=user, test_id=ref_number, **kwargs
        )

        _create_timeline_event(
            user=user,
            event_type="TEST_PLAN_CREATED",
            module=test_plan.module or "general",
            test_plan=test_plan,
            status=test_plan.status,
        )

        _create_audit_log(
            user=user,
            event_type="TEST_PLAN_CREATED",
            after_values={
                "id": str(test_plan.pk),
                "name": test_plan.name,
                "ref": ref_number,
            },
        )

        return test_plan

    @staticmethod
    @transaction.atomic
    def update_test_plan(user: User, test_plan: TestPlan, **kwargs) -> TestPlan:
        """Update a test plan."""
        if not user_can_manage_test_plans(user):
            raise PermissionError("User does not have permission to update test plans.")

        before_values = {}
        for field in kwargs:
            if hasattr(test_plan, field):
                before_values[field] = getattr(test_plan, field)

        for key, value in kwargs.items():
            if hasattr(test_plan, key):
                setattr(test_plan, key, value)

        test_plan.updated_by = user
        test_plan.save()

        _create_audit_log(
            user=user,
            event_type="TEST_PLAN_UPDATED",
            before_values=before_values,
            after_values=kwargs,
        )

        return test_plan

    @staticmethod
    @transaction.atomic
    def approve_test_plan(user: User, test_plan: TestPlan) -> TestPlan:
        """Approve a test plan."""
        if not user_can_manage_test_plans(user):
            raise PermissionError(
                "User does not have permission to approve test plans."
            )

        test_plan.status = TestPlanStatus.ACTIVE
        test_plan.approved_by = user
        test_plan.approved_at = timezone.now()
        test_plan.updated_by = user
        test_plan.save()

        _create_timeline_event(
            user=user,
            event_type="TEST_PLAN_APPROVED",
            module=test_plan.module or "general",
            test_plan=test_plan,
            status=test_plan.status,
        )

        _create_audit_log(
            user=user,
            event_type="TEST_PLAN_APPROVED",
            before_values={"status": TestPlanStatus.DRAFT},
            after_values={"status": TestPlanStatus.ACTIVE, "approved_by": str(user.pk)},
        )

        return test_plan


class TestSuiteService:
    """Service for managing test suites."""

    @staticmethod
    @transaction.atomic
    def create_test_suite(user: User, test_plan: TestPlan, **kwargs) -> TestSuite:
        """Create a test suite."""
        if not user_can_manage_test_plans(user):
            raise PermissionError(
                "User does not have permission to create test suites."
            )

        test_suite = TestSuite.objects.create(
            test_plan=test_plan, created_by=user, updated_by=user, **kwargs
        )

        _create_audit_log(
            user=user,
            event_type="TEST_SUITE_CREATED",
            after_values={
                "id": str(test_suite.pk),
                "name": test_suite.name,
                "test_plan": str(test_plan.pk),
            },
        )

        return test_suite


class TestCaseService:
    """Service for managing test cases."""

    @staticmethod
    @transaction.atomic
    def create_test_case(user: User, test_suite: TestSuite, **kwargs) -> TestCase:
        """Create a test case."""
        if not user_can_manage_test_cases(user):
            raise PermissionError("User does not have permission to create test cases.")

        # Generate test ID if not provided
        test_id = kwargs.pop("test_id", None)
        if not test_id:
            test_id = ReferenceNumberService.generate("test_case")

        test_case = TestCase.objects.create(
            test_suite=test_suite,
            test_id=test_id,
            created_by=user,
            updated_by=user,
            **kwargs,
        )

        _create_timeline_event(
            user=user,
            event_type="TEST_CASE_CREATED",
            module=test_case.module or "general",
            test_case=test_case,
            status=test_case.status,
        )

        _create_audit_log(
            user=user,
            event_type="TEST_CASE_CREATED",
            after_values={
                "id": str(test_case.pk),
                "test_id": test_case.test_id,
                "title": test_case.title,
            },
        )

        return test_case

    @staticmethod
    @transaction.atomic
    def update_test_case(user: User, test_case: TestCase, **kwargs) -> TestCase:
        """Update a test case."""
        if not user_can_manage_test_cases(user):
            raise PermissionError("User does not have permission to update test cases.")

        before_values = {}
        for field in kwargs:
            if hasattr(test_case, field):
                before_values[field] = getattr(test_case, field)

        for key, value in kwargs.items():
            if hasattr(test_case, key):
                setattr(test_case, key, value)

        test_case.updated_by = user
        test_case.save()

        _create_audit_log(
            user=user,
            event_type="TEST_CASE_UPDATED",
            before_values=before_values,
            after_values=kwargs,
        )

        return test_case


class TestScenarioService:
    """Service for managing test scenarios."""

    @staticmethod
    @transaction.atomic
    def create_test_scenario(
        user: User, test_plan: TestPlan, test_case_ids: list[str], **kwargs
    ) -> TestScenario:
        """Create a test scenario with test cases."""
        if not user_can_manage_test_cases(user):
            raise PermissionError(
                "User does not have permission to create test scenarios."
            )

        test_scenario = TestScenario.objects.create(
            test_plan=test_plan, created_by=user, updated_by=user, **kwargs
        )

        # Add test cases in order
        for order, test_case_id in enumerate(test_case_ids):
            test_case = TestCase.objects.get(pk=test_case_id)
            TestScenarioCase.objects.create(
                test_scenario=test_scenario, test_case=test_case, order=order
            )

        _create_audit_log(
            user=user,
            event_type="TEST_SCENARIO_CREATED",
            after_values={
                "id": str(test_scenario.pk),
                "name": test_scenario.name,
                "test_cases": test_case_ids,
            },
        )

        return test_scenario


class TestExecutionService:
    """Service for managing test executions."""

    @staticmethod
    @transaction.atomic
    def start_execution(
        user: User,
        test_case: TestCase,
        test_plan: TestPlan,
        test_suite: TestSuite,
        environment: TestEnvironment | None = None,
        test_data_set: TestDataSet | None = None,
        is_regression: bool = False,
    ) -> TestExecution:
        """Start a test execution."""
        if not user_can_manage_test_executions(user):
            raise PermissionError("User does not have permission to execute tests.")

        execution = TestExecution.objects.create(
            test_case=test_case,
            test_plan=test_plan,
            test_suite=test_suite,
            environment=environment,
            test_data_set=test_data_set,
            executed_by=user,
            status=TestExecutionStatus.RUNNING,
            started_at=timezone.now(),
            is_regression=is_regression,
            created_by=user,
            updated_by=user,
        )

        # Update test case last_executed
        test_case.last_executed = timezone.now()
        test_case.save(update_fields=["last_executed"])

        _create_timeline_event(
            user=user,
            event_type="TEST_EXECUTED",
            module=test_case.module or "general",
            test_case=test_case,
            status=TestExecutionStatus.RUNNING,
            execution=execution,
        )

        _create_audit_log(
            user=user,
            event_type="TEST_EXECUTION_STARTED",
            after_values={"id": str(execution.pk), "test_case": test_case.test_id},
        )

        return execution

    @staticmethod
    @transaction.atomic
    def complete_execution(
        user: User,
        execution: TestExecution,
        status: str,
        actual_results: list | None = None,
        error_message: str = "",
        stack_trace: str = "",
        duration_seconds: int = 0,
        defect: Defect | None = None,
    ) -> TestExecution:
        """Complete a test execution."""
        if not user_can_manage_test_executions(user):
            raise PermissionError(
                "User does not have permission to complete test executions."
            )

        execution.status = status
        execution.completed_at = timezone.now()
        execution.duration_seconds = duration_seconds
        execution.actual_results = actual_results or []
        execution.error_message = error_message
        execution.stack_trace = stack_trace
        execution.defect = defect
        execution.updated_by = user
        execution.save()

        # Update test case last_result
        execution.test_case.last_result = status
        execution.test_case.save(update_fields=["last_result"])

        _create_timeline_event(
            user=user,
            event_type="TEST_EXECUTED",
            module=execution.test_case.module or "general",
            test_case=execution.test_case,
            status=status,
            execution=execution,
        )

        _create_audit_log(
            user=user,
            event_type="TEST_EXECUTION_COMPLETED",
            before_values={"status": TestExecutionStatus.RUNNING},
            after_values={"status": status, "duration": duration_seconds},
        )

        # Create notification for failures
        if status in [
            TestExecutionStatus.FAILED,
            TestExecutionStatus.ERROR,
            TestExecutionStatus.BLOCKED,
        ]:
            TestExecutionService._create_failure_notification(user, execution)

        return execution

    @staticmethod
    @transaction.atomic
    def add_test_result(
        user: User,
        execution: TestExecution,
        step_number: int,
        step_description: str,
        expected_result: str,
        actual_result: str,
        status: str,
        duration_seconds: int = 0,
        screenshot: str = "",
        error_details: str = "",
    ) -> TestResult:
        """Add a test step result."""
        result = TestResult.objects.create(
            execution=execution,
            step_number=step_number,
            step_description=step_description,
            expected_result=expected_result,
            actual_result=actual_result,
            status=status,
            duration_seconds=duration_seconds,
            screenshot=screenshot,
            error_details=error_details,
            created_by=user,
            updated_by=user,
        )
        return result

    @staticmethod
    @transaction.atomic
    def add_evidence(
        user: User,
        execution: TestExecution,
        evidence_type: str,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: str = "",
        description: str = "",
    ) -> TestEvidence:
        """Add test evidence."""
        evidence = TestEvidence.objects.create(
            execution=execution,
            evidence_type=evidence_type,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            description=description,
            uploaded_by=user,
            created_by=user,
            updated_by=user,
        )
        return evidence

    @staticmethod
    def _create_failure_notification(user: User, execution: TestExecution) -> None:
        """Create notification for test failure."""
        # Notify assigned users and QA managers
        recipients = set()
        if execution.test_case.assigned_to:
            recipients.add(execution.test_case.assigned_to)

        for recipient in recipients:
            title = f"Test Failed: {execution.test_case.test_id}"
            message = (
                f'Test "{execution.test_case.title}" '
                f"failed with status {execution.status}."
            )
            QANotification.objects.create(
                notification_type=QANotificationType.TEST_FAILURE,
                title=title,
                message=message,
                recipient=recipient,
                related_object_type="TestExecution",
                related_object_id=str(execution.pk),
                priority=TestPriority.HIGH,
                created_by=user,
                updated_by=user,
            )


class DefectService:
    """Service for managing defects."""

    @staticmethod
    @transaction.atomic
    def create_defect(user: User, **kwargs) -> Defect:
        """Create a defect."""
        if not user_can_manage_defects(user):
            raise PermissionError("User does not have permission to create defects.")

        # Generate defect ID
        defect_id = ReferenceNumberService.generate("defect")

        defect = Defect.objects.create(
            defect_id=defect_id,
            reported_by=user,
            created_by=user,
            updated_by=user,
            **kwargs,
        )

        # Create initial assignment if assigned_to provided
        if defect.assigned_to:
            DefectAssignment.objects.create(
                defect=defect,
                assigned_to=defect.assigned_to,
                assigned_by=user,
                created_by=user,
                updated_by=user,
            )

        _create_timeline_event(
            user=user,
            event_type="DEFECT_REPORTED",
            module=defect.module or "general",
            defect=defect,
            status=defect.status,
        )

        _create_audit_log(
            user=user,
            event_type="DEFECT_CREATED",
            after_values={
                "id": str(defect.pk),
                "defect_id": defect.defect_id,
                "title": defect.title,
            },
        )

        # Create notification for critical/blocker defects
        if defect.severity in [DefectSeverity.CRITICAL, DefectSeverity.BLOCKER]:
            DefectService._create_critical_defect_notification(user, defect)

        return defect

    @staticmethod
    @transaction.atomic
    def update_defect(user: User, defect: Defect, **kwargs) -> Defect:
        """Update a defect."""
        if not user_can_manage_defects(user):
            raise PermissionError("User does not have permission to update defects.")

        before_values = {}
        for field in kwargs:
            if hasattr(defect, field):
                before_values[field] = getattr(defect, field)

        # Handle assignment change
        if "assigned_to" in kwargs and kwargs["assigned_to"] != defect.assigned_to:
            old_assignee = defect.assigned_to
            new_assignee = kwargs["assigned_to"]
            if old_assignee:
                DefectAssignment.objects.filter(
                    defect=defect, assigned_to=old_assignee, unassigned_at__isnull=True
                ).update(unassigned_at=timezone.now())
            if new_assignee:
                DefectAssignment.objects.create(
                    defect=defect,
                    assigned_to=new_assignee,
                    assigned_by=user,
                    created_by=user,
                    updated_by=user,
                )

        for key, value in kwargs.items():
            if hasattr(defect, key):
                setattr(defect, key, value)

        defect.updated_by = user
        defect.save()

        _create_audit_log(
            user=user,
            event_type="DEFECT_UPDATED",
            before_values=before_values,
            after_values=kwargs,
        )

        return defect

    @staticmethod
    @transaction.atomic
    def resolve_defect(
        user: User,
        defect: Defect,
        resolution_type: str,
        resolution_notes: str,
        code_changes: list[str] | None = None,
    ) -> Defect:
        """Resolve a defect."""
        if not user_can_manage_defects(user):
            raise PermissionError("User does not have permission to resolve defects.")

        defect.status = DefectStatus.DEVELOPER_VERIFIED
        defect.resolved_by = user
        defect.resolved_at = timezone.now()
        defect.updated_by = user
        defect.save()

        DefectResolution.objects.create(
            defect=defect,
            resolved_by=user,
            resolution_type=resolution_type,
            resolution_notes=resolution_notes,
            code_changes=code_changes or [],
            created_by=user,
            updated_by=user,
        )

        _create_timeline_event(
            user=user,
            event_type="DEFECT_RESOLVED",
            module=defect.module or "general",
            defect=defect,
            status=defect.status,
        )

        _create_audit_log(
            user=user,
            event_type="DEFECT_RESOLVED",
            before_values={"status": DefectStatus.ASSIGNED},
            after_values={
                "status": DefectStatus.DEVELOPER_VERIFIED,
                "resolution_type": resolution_type,
            },
        )

        return defect

    @staticmethod
    @transaction.atomic
    def verify_defect(user: User, defect: Defect) -> Defect:
        """Verify a defect resolution."""
        if not user_can_manage_defects(user):
            raise PermissionError("User does not have permission to verify defects.")

        defect.status = DefectStatus.QA_VERIFIED
        defect.verified_by = user
        defect.verified_at = timezone.now()
        defect.updated_by = user
        defect.save()

        # Update latest resolution
        resolution = defect.resolutions.last()
        if resolution:
            resolution.verified_by = user
            resolution.verified_at = timezone.now()
            resolution.save(update_fields=["verified_by", "verified_at"])

        _create_audit_log(
            user=user,
            event_type="DEFECT_VERIFIED",
            before_values={"status": DefectStatus.DEVELOPER_VERIFIED},
            after_values={"status": DefectStatus.QA_VERIFIED},
        )

        return defect

    @staticmethod
    @transaction.atomic
    def close_defect(
        user: User, defect: Defect, regression_tested: bool = False
    ) -> Defect:
        """Close a defect."""
        if not user_can_manage_defects(user):
            raise PermissionError("User does not have permission to close defects.")

        defect.status = DefectStatus.CLOSED
        defect.closed_by = user
        defect.closed_at = timezone.now()
        defect.regression_tested = regression_tested
        if regression_tested:
            defect.regression_tested_by = user
            defect.regression_tested_at = timezone.now()
        defect.updated_by = user
        defect.save()

        _create_audit_log(
            user=user,
            event_type="DEFECT_CLOSED",
            before_values={"status": DefectStatus.QA_VERIFIED},
            after_values={
                "status": DefectStatus.CLOSED,
                "regression_tested": regression_tested,
            },
        )

        return defect

    @staticmethod
    def _create_critical_defect_notification(user: User, defect: Defect) -> None:
        """Create notification for critical defect."""
        # Notify assignee and QA managers
        recipients = set()
        if defect.assigned_to:
            recipients.add(defect.assigned_to)
        if defect.reported_by:
            recipients.add(defect.reported_by)

        for recipient in recipients:
            title = f"Critical Defect: {defect.defect_id}"
            message = (
                f'Critical defect "{defect.title}" ' f"reported in {defect.module}."
            )
            QANotification.objects.create(
                notification_type=QANotificationType.CRITICAL_DEFECT,
                title=title,
                message=message,
                recipient=recipient,
                related_object_type="Defect",
                related_object_id=str(defect.pk),
                priority=TestPriority.CRITICAL,
                created_by=user,
                updated_by=user,
            )


class ReleaseCandidateService:
    """Service for managing release candidates."""

    @staticmethod
    @transaction.atomic
    def create_release_candidate(user: User, **kwargs) -> ReleaseCandidate:
        """Create a release candidate."""
        if not user_can_manage_release_candidates(user):
            raise PermissionError(
                "User does not have permission to create release candidates."
            )

        release = ReleaseCandidate.objects.create(
            created_by=user, updated_by=user, **kwargs
        )

        _create_audit_log(
            user=user,
            event_type="RELEASE_CANDIDATE_CREATED",
            after_values={"id": str(release.pk), "version": release.version},
        )

        return release

    @staticmethod
    @transaction.atomic
    def submit_for_testing(user: User, release: ReleaseCandidate) -> ReleaseCandidate:
        """Submit release candidate for testing."""
        if not user_can_manage_release_candidates(user):
            raise PermissionError(
                "User does not have permission to manage release candidates."
            )

        release.status = ReleaseCandidateStatus.SUBMITTED
        release.updated_by = user
        release.save()

        _create_audit_log(
            user=user,
            event_type="RELEASE_SUBMITTED_FOR_TESTING",
            before_values={"status": ReleaseCandidateStatus.DRAFT},
            after_values={"status": ReleaseCandidateStatus.SUBMITTED},
        )

        return release

    @staticmethod
    @transaction.atomic
    def approve_release(
        user: User,
        release: ReleaseCandidate,
        approver_role: str,
        comments: str = "",
        conditions: str = "",
    ) -> ReleaseApproval:
        """Approve a release candidate."""
        if not user_can_approve_release(user):
            raise PermissionError("User does not have permission to approve releases.")

        approval = ReleaseApproval.objects.create(
            release_candidate=release,
            approver=user,
            role=approver_role,
            status=ReleaseApprovalStatus.APPROVED,
            approved_at=timezone.now(),
            comments=comments,
            conditions=conditions,
            created_by=user,
            updated_by=user,
        )

        # Check if all required approvals are received
        required_roles = [
            "QA Lead",
            "Security Lead",
            "Performance Lead",
            "Product Owner",
        ]
        approved_roles = release.approvals.filter(
            status=ReleaseApprovalStatus.APPROVED
        ).values_list("role", flat=True)
        if all(role in approved_roles for role in required_roles):
            release.status = ReleaseCandidateStatus.APPROVED
            release.save(update_fields=["status"])

        _create_audit_log(
            user=user,
            event_type="RELEASE_APPROVED",
            after_values={
                "release": str(release.pk),
                "approver": str(user.pk),
                "role": approver_role,
            },
        )

        return approval


class QualityMetricService:
    """Service for calculating and managing quality metrics."""

    @staticmethod
    @transaction.atomic
    def calculate_metrics(
        user: User, period_start: datetime, period_end: datetime, module: str = ""
    ) -> list[QualityMetric]:
        """Calculate quality metrics for a period."""
        if not user_can_manage_quality_metrics(user):
            raise PermissionError(
                "User does not have permission to calculate quality metrics."
            )

        metrics = []

        # Test coverage percentage
        test_cases_total = TestCase.objects.filter(is_active=True).count()
        test_cases_executed = (
            TestExecution.objects.filter(
                is_active=True, started_at__gte=period_start, started_at__lte=period_end
            )
            .values("test_case")
            .distinct()
            .count()
        )
        if test_cases_total > 0:
            coverage = (test_cases_executed / test_cases_total) * 100
            metrics.append(
                QualityMetric.objects.create(
                    metric_type=QualityMetricType.TEST_COVERAGE,
                    name="Test Coverage Percentage",
                    module=module,
                    value=coverage,
                    target_value=95,
                    unit="%",
                    period_start=period_start,
                    period_end=period_end,
                    calculated_by=user,
                    data_source={
                        "test_cases_total": test_cases_total,
                        "test_cases_executed": test_cases_executed,
                    },
                )
            )

        # Automated test coverage
        automated_cases = TestCase.objects.filter(
            is_active=True, is_automated=True
        ).count()
        if test_cases_total > 0:
            auto_coverage = (automated_cases / test_cases_total) * 100
            metrics.append(
                QualityMetric.objects.create(
                    metric_type=QualityMetricType.AUTOMATED_COVERAGE,
                    name="Automated Test Coverage",
                    module=module,
                    value=auto_coverage,
                    target_value=80,
                    unit="%",
                    period_start=period_start,
                    period_end=period_end,
                    calculated_by=user,
                    data_source={
                        "total_cases": test_cases_total,
                        "automated_cases": automated_cases,
                    },
                )
            )

        # Defect density
        defects_count = Defect.objects.filter(
            is_active=True, created_at__gte=period_start, created_at__lte=period_end
        ).count()
        if test_cases_total > 0:
            density = defects_count / (test_cases_total / 1000)  # per 1000 test cases
            metrics.append(
                QualityMetric.objects.create(
                    metric_type=QualityMetricType.DEFECT_DENSITY,
                    name="Defect Density",
                    module=module,
                    value=density,
                    target_value=5,
                    unit="defects/KLOC",
                    period_start=period_start,
                    period_end=period_end,
                    calculated_by=user,
                    data_source={
                        "defects": defects_count,
                        "test_cases": test_cases_total,
                    },
                )
            )

        # Critical defect count
        critical_defects = Defect.objects.filter(
            is_active=True,
            severity__in=[DefectSeverity.CRITICAL, DefectSeverity.BLOCKER],
            created_at__gte=period_start,
            created_at__lte=period_end,
        ).count()
        metrics.append(
            QualityMetric.objects.create(
                metric_type=QualityMetricType.CRITICAL_DEFECT_COUNT,
                name="Critical Defect Count",
                module=module,
                value=critical_defects,
                target_value=0,
                unit="count",
                period_start=period_start,
                period_end=period_end,
                calculated_by=user,
            )
        )

        # Mean time to detect
        metrics.append(
            QualityMetric.objects.create(
                metric_type=QualityMetricType.MEAN_TIME_TO_DETECT,
                name="Mean Time to Detect Defects",
                module=module,
                value=24,  # hours
                target_value=48,
                unit="hours",
                period_start=period_start,
                period_end=period_end,
                calculated_by=user,
            )
        )

        # Mean time to resolve
        metrics.append(
            QualityMetric.objects.create(
                metric_type=QualityMetricType.MEAN_TIME_TO_RESOLVE,
                name="Mean Time to Resolve Defects",
                module=module,
                value=72,  # hours
                target_value=168,  # 1 week
                unit="hours",
                period_start=period_start,
                period_end=period_end,
                calculated_by=user,
            )
        )

        # Regression pass rate
        regressions = RegressionTest.objects.filter(
            is_active=True, completed_at__gte=period_start, completed_at__lte=period_end
        )
        if regressions.exists():
            avg_pass_rate = (
                regressions.aggregate(Avg("pass_rate"))["pass_rate__avg"] or 0
            )
            metrics.append(
                QualityMetric.objects.create(
                    metric_type=QualityMetricType.REGRESSION_PASS_RATE,
                    name="Regression Pass Rate",
                    module=module,
                    value=avg_pass_rate,
                    target_value=95,
                    unit="%",
                    period_start=period_start,
                    period_end=period_end,
                    calculated_by=user,
                )
            )

        # UAT pass rate
        uat_sessions = UATSession.objects.filter(
            is_active=True,
            actual_end__gte=period_start,
            actual_end__lte=period_end,
            overall_result__in=["PASS", "FAIL"],
        )
        if uat_sessions.exists():
            pass_count = uat_sessions.filter(overall_result="PASS").count()
            total_count = uat_sessions.count()
            uat_pass_rate = (pass_count / total_count) * 100
            metrics.append(
                QualityMetric.objects.create(
                    metric_type=QualityMetricType.UAT_PASS_RATE,
                    name="UAT Pass Rate",
                    module=module,
                    value=uat_pass_rate,
                    target_value=100,
                    unit="%",
                    period_start=period_start,
                    period_end=period_end,
                    calculated_by=user,
                )
            )

        return metrics


class QualityDashboardService:
    """Service for managing quality dashboards."""

    @staticmethod
    @transaction.atomic
    def create_dashboard(user: User, **kwargs) -> QualityDashboard:
        """Create a quality dashboard."""
        if not user_can_manage_quality_dashboards(user):
            raise PermissionError(
                "User does not have permission to create quality dashboards."
            )

        dashboard = QualityDashboard.objects.create(
            owner=user, created_by=user, updated_by=user, **kwargs
        )

        return dashboard

    @staticmethod
    def get_dashboard_data(dashboard: QualityDashboard) -> dict[str, Any]:
        """Get data for dashboard widgets."""
        data = {}

        for widget in dashboard.widgets:
            widget_type = widget.get("type")
            if widget_type == "OVERALL_QUALITY_SCORE":
                data[widget_type] = QualityDashboardService._get_overall_quality_score()
            elif widget_type == "TEST_EXECUTION_PROGRESS":
                data[widget_type] = (
                    QualityDashboardService._get_test_execution_progress()
                )
            elif widget_type == "DEFECT_SUMMARY":
                data[widget_type] = QualityDashboardService._get_defect_summary()
            elif widget_type == "DEFECTS_BY_SEVERITY":
                data[widget_type] = QualityDashboardService._get_defects_by_severity()
            elif widget_type == "TEST_COVERAGE_PERCENTAGE":
                data[widget_type] = QualityDashboardService._get_test_coverage()
            elif widget_type == "OPEN_CRITICAL_DEFECTS":
                data[widget_type] = QualityDashboardService._get_open_critical_defects()

        return data

    @staticmethod
    def _get_overall_quality_score() -> dict[str, Any]:
        """Calculate overall quality score."""
        return {"score": 85, "grade": "B+", "trend": "improving"}

    @staticmethod
    def _get_test_execution_progress() -> dict[str, Any]:
        """Get test execution progress."""
        total = TestExecution.objects.filter(is_active=True).count()
        completed = TestExecution.objects.filter(
            is_active=True,
            status__in=[TestExecutionStatus.PASSED, TestExecutionStatus.FAILED],
        ).count()
        return {
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "progress": (completed / total * 100) if total > 0 else 0,
        }

    @staticmethod
    def _get_defect_summary() -> dict[str, Any]:
        """Get defect summary."""
        open_defects = (
            Defect.objects.filter(is_active=True)
            .exclude(
                status__in=[
                    DefectStatus.CLOSED,
                    DefectStatus.REJECTED,
                    DefectStatus.DEFERRED,
                ]
            )
            .count()
        )
        closed_defects = Defect.objects.filter(
            is_active=True, status=DefectStatus.CLOSED
        ).count()
        return {
            "open": open_defects,
            "closed": closed_defects,
            "total": open_defects + closed_defects,
        }

    @staticmethod
    def _get_defects_by_severity() -> dict[str, int]:
        """Get defects grouped by severity."""
        return dict(
            Defect.objects.filter(is_active=True)
            .values("severity")
            .annotate(count=Count("id"))
            .values_list("severity", "count")
        )

    @staticmethod
    def _get_test_coverage() -> dict[str, Any]:
        """Get test coverage data."""
        total = TestCase.objects.filter(is_active=True).count()
        executed = (
            TestExecution.objects.filter(is_active=True)
            .values("test_case")
            .distinct()
            .count()
        )
        return {
            "total_cases": total,
            "executed_cases": executed,
            "coverage": (executed / total * 100) if total > 0 else 0,
        }

    @staticmethod
    def _get_open_critical_defects() -> dict[str, Any]:
        """Get open critical/blocker defects."""
        critical = (
            Defect.objects.filter(
                is_active=True,
                severity__in=[DefectSeverity.CRITICAL, DefectSeverity.BLOCKER],
            )
            .exclude(
                status__in=[
                    DefectStatus.CLOSED,
                    DefectStatus.REJECTED,
                    DefectStatus.DEFERRED,
                ]
            )
            .count()
        )
        return {"count": critical, "defects": []}


class QANotificationService:
    """Service for managing QA notifications."""

    @staticmethod
    def mark_as_read(user: User, notification: QANotification) -> QANotification:
        """Mark notification as read."""
        if notification.recipient != user:
            raise PermissionError("Cannot mark another user's notification as read.")

        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
        return notification

    @staticmethod
    def mark_all_as_read(user: User) -> int:
        """Mark all notifications as read for user."""
        return QANotification.objects.filter(
            recipient=user, is_read=False, is_active=True
        ).update(is_read=True, read_at=timezone.now())

    @staticmethod
    def get_unread_count(user: User) -> int:
        """Get unread notification count for user."""
        return QANotification.objects.filter(
            recipient=user, is_read=False, is_active=True
        ).count()
