import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, IsActiveModel, SoftDeleteModel
from apps.qa.constants import (
    DefectSeverity,
    DefectStatus,
    EnvironmentType,
    QANotificationType,
    QualityMetricType,
    ReleaseApprovalStatus,
    ReleaseCandidateStatus,
    TestCaseStatus,
    TestCategory,
    TestExecutionStatus,
    TestPlanStatus,
    TestPriority,
    TestScenarioType,
    TestSuiteStatus,
    UATSessionStatus,
)


class QAConfiguration(BaseModel):
    """Centralized QA configuration singleton."""

    SINGLETON_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

    testing_policies = models.JSONField(
        _("Testing Policies"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for testing policies and standards."),
    )
    quality_thresholds = models.JSONField(
        _("Quality Thresholds"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for quality thresholds and targets."),
    )
    code_coverage_targets = models.JSONField(
        _("Code Coverage Targets"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for code coverage targets per module."),
    )
    test_execution_schedules = models.JSONField(
        _("Test Execution Schedules"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for test execution schedules."),
    )
    automated_testing_config = models.JSONField(
        _("Automated Testing Configuration"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for automated testing frameworks and tools."),
    )
    defect_severity_rules = models.JSONField(
        _("Defect Severity Rules"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for defect severity classification rules."),
    )
    release_approval_workflows = models.JSONField(
        _("Release Approval Workflows"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for release approval workflow definitions."),
    )
    uat_settings = models.JSONField(
        _("UAT Settings"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for User Acceptance Testing settings."),
    )
    regression_testing_rules = models.JSONField(
        _("Regression Testing Rules"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for regression testing rules and triggers."),
    )
    test_notification_settings = models.JSONField(
        _("Test Notification Settings"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for test notification preferences."),
    )
    test_retention_policies = models.JSONField(
        _("Test Retention Policies"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for test data retention policies."),
    )
    quality_dashboards_config = models.JSONField(
        _("Quality Dashboards Configuration"),
        default=dict,
        blank=True,
        help_text=_("JSON configuration for quality dashboard widgets and layouts."),
    )

    class Meta:
        verbose_name = _("QA Configuration")
        verbose_name_plural = _("QA Configuration")

    def __str__(self):
        return f"QA Configuration ({self.pk})"

    def save(self, *args, **kwargs):
        # Force the singleton UUID
        self.id = self.SINGLETON_ID
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(
            id=cls.SINGLETON_ID,
            defaults={
                "testing_policies": {},
                "quality_thresholds": {},
                "code_coverage_targets": {},
                "test_execution_schedules": {},
                "automated_testing_config": {},
                "defect_severity_rules": {},
                "release_approval_workflows": {},
                "uat_settings": {},
                "regression_testing_rules": {},
                "test_notification_settings": {},
                "test_retention_policies": {},
                "quality_dashboards_config": {},
            },
        )
        return obj


class TestEnvironment(BaseModel):
    """Testing environment configuration."""

    name = models.CharField(_("Name"), max_length=100)
    environment_type = models.CharField(
        _("Environment Type"),
        max_length=20,
        choices=EnvironmentType.CHOICES,
        default=EnvironmentType.DEVELOPMENT,
    )
    description = models.TextField(_("Description"), blank=True)
    base_url = models.URLField(_("Base URL"), blank=True)
    database_config = models.JSONField(
        _("Database Configuration"), default=dict, blank=True
    )
    cache_config = models.JSONField(_("Cache Configuration"), default=dict, blank=True)
    credentials = models.JSONField(_("Credentials"), default=dict, blank=True)
    configuration_consistency = models.JSONField(
        _("Configuration Consistency"), default=dict, blank=True
    )
    isolation_level = models.CharField(
        _("Isolation Level"), max_length=50, default="standard"
    )
    secure_credentials = models.BooleanField(_("Secure Credentials"), default=True)
    test_database_config = models.JSONField(
        _("Test Database Configuration"), default=dict, blank=True
    )
    logging_config = models.JSONField(
        _("Logging Configuration"), default=dict, blank=True
    )
    monitoring_config = models.JSONField(
        _("Monitoring Configuration"), default=dict, blank=True
    )
    backup_procedures = models.JSONField(
        _("Backup Procedures"), default=dict, blank=True
    )
    is_default = models.BooleanField(_("Is Default"), default=False)

    class Meta:
        verbose_name = _("Test Environment")
        verbose_name_plural = _("Test Environments")
        ordering = ["environment_type", "name"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} ({self.get_environment_type_display()})"

    def save(self, *args, **kwargs):
        if self.is_default:
            TestEnvironment.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class TestDataSet(BaseModel):
    """Test data management."""

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    data_type = models.CharField(
        _("Data Type"),
        max_length=50,
        choices=[
            ("SYNTHETIC", _("Synthetic")),
            ("SEED", _("Seed Data")),
            ("MOCK", _("Mock Services")),
            ("ANONYMIZED", _("Anonymized Production-like")),
            ("BOUNDARY", _("Boundary Values")),
            ("ERROR_CONDITION", _("Error Conditions")),
            ("PERFORMANCE", _("Performance")),
            ("ACCESSIBILITY", _("Accessibility")),
            ("SECURITY", _("Security Validation")),
        ],
        default="SYNTHETIC",
    )
    version = models.CharField(_("Version"), max_length=50, default="1.0")
    file_path = models.CharField(_("File Path"), max_length=500, blank=True)
    data_schema = models.JSONField(_("Data Schema"), default=dict, blank=True)
    record_count = models.PositiveIntegerField(_("Record Count"), default=0)
    size_bytes = models.PositiveBigIntegerField(_("Size (Bytes)"), default=0)
    checksum = models.CharField(_("Checksum"), max_length=64, blank=True)
    environment = models.ForeignKey(
        TestEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_data_sets",
        verbose_name=_("Environment"),
    )
    is_reproducible = models.BooleanField(_("Is Reproducible"), default=True)
    last_validated = models.DateTimeField(_("Last Validated"), null=True, blank=True)

    class Meta:
        verbose_name = _("Test Data Set")
        verbose_name_plural = _("Test Data Sets")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_data_type_display()})"


class TestPlan(BaseModel, SoftDeleteModel, IsActiveModel):
    """Test plan for a release or feature."""

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    version = models.CharField(_("Version"), max_length=50, default="1.0")
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TestPlanStatus.CHOICES,
        default=TestPlanStatus.DRAFT,
    )
    start_date = models.DateField(_("Start Date"), null=True, blank=True)
    end_date = models.DateField(_("End Date"), null=True, blank=True)
    release_candidate = models.ForeignKey(
        "ReleaseCandidate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_plans",
        verbose_name=_("Release Candidate"),
    )
    modules = models.JSONField(_("Modules"), default=list, blank=True)
    test_categories = models.JSONField(
        _("Test Categories"),
        default=list,
        blank=True,
        help_text=_("List of test categories from TestCategory choices."),
    )
    quality_thresholds = models.JSONField(
        _("Quality Thresholds"), default=dict, blank=True
    )
    entry_criteria = models.TextField(_("Entry Criteria"), blank=True)
    exit_criteria = models.TextField(_("Exit Criteria"), blank=True)
    risks = models.TextField(_("Risks"), blank=True)
    assumptions = models.TextField(_("Assumptions"), blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_test_plans",
        verbose_name=_("Approved By"),
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Test Plan")
        verbose_name_plural = _("Test Plans")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_status_display()})"


class TestSuite(BaseModel, SoftDeleteModel, IsActiveModel):
    """Test suite grouping test cases."""

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    test_plan = models.ForeignKey(
        TestPlan,
        on_delete=models.CASCADE,
        related_name="test_suites",
        verbose_name=_("Test Plan"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent Suite"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TestSuiteStatus.CHOICES,
        default=TestSuiteStatus.DRAFT,
    )
    order = models.PositiveIntegerField(_("Order"), default=0)
    module = models.CharField(_("Module"), max_length=100, blank=True)
    feature = models.CharField(_("Feature"), max_length=200, blank=True)
    requirement_references = models.JSONField(
        _("Requirement References"), default=list, blank=True
    )
    tags = models.JSONField(_("Tags"), default=list, blank=True)

    class Meta:
        verbose_name = _("Test Suite")
        verbose_name_plural = _("Test Suites")
        ordering = ["test_plan", "order", "name"]  # noqa: RUF012

    def __str__(self):
        return f"{self.test_plan.name} > {self.name}"


class TestCase(BaseModel, SoftDeleteModel, IsActiveModel):
    """Individual test case."""

    test_suite = models.ForeignKey(
        TestSuite,
        on_delete=models.CASCADE,
        related_name="test_cases",
        verbose_name=_("Test Suite"),
    )
    test_id = models.CharField(_("Test ID"), max_length=50, unique=True)
    title = models.CharField(_("Title"), max_length=300)
    description = models.TextField(_("Description"), blank=True)
    preconditions = models.TextField(_("Preconditions"), blank=True)
    postconditions = models.TextField(_("Postconditions"), blank=True)
    steps = models.JSONField(_("Steps"), default=list, blank=True)
    expected_results = models.JSONField(_("Expected Results"), default=list, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TestCaseStatus.CHOICES,
        default=TestCaseStatus.DRAFT,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=TestPriority.CHOICES,
        default=TestPriority.MEDIUM,
    )
    category = models.CharField(
        _("Category"),
        max_length=20,
        choices=TestCategory.CHOICES,
        default=TestCategory.FUNCTIONAL,
    )
    requirement_reference = models.CharField(
        _("Requirement Reference"), max_length=100, blank=True
    )
    module = models.CharField(_("Module"), max_length=100, blank=True)
    feature = models.CharField(_("Feature"), max_length=200, blank=True)
    test_type = models.CharField(
        _("Test Type"),
        max_length=20,
        choices=TestScenarioType.CHOICES,
        default=TestScenarioType.POSITIVE,
    )
    is_automated = models.BooleanField(_("Is Automated"), default=False)
    automation_script = models.TextField(_("Automation Script"), blank=True)
    automation_framework = models.CharField(
        _("Automation Framework"), max_length=100, blank=True
    )
    estimated_duration = models.PositiveIntegerField(
        _("Estimated Duration (minutes)"), default=0
    )
    tags = models.JSONField(_("Tags"), default=list, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_test_cases",
        verbose_name=_("Assigned To"),
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_test_cases",
        verbose_name=_("Reviewed By"),
    )
    reviewed_at = models.DateTimeField(_("Reviewed At"), null=True, blank=True)
    last_executed = models.DateTimeField(_("Last Executed"), null=True, blank=True)
    last_result = models.CharField(
        _("Last Result"), max_length=20, choices=TestExecutionStatus.CHOICES, blank=True
    )

    class Meta:
        verbose_name = _("Test Case")
        verbose_name_plural = _("Test Cases")
        ordering = ["test_suite", "test_id"]  # noqa: RUF012

    def __str__(self):
        return f"{self.test_id}: {self.title}"


class TestScenario(BaseModel, SoftDeleteModel, IsActiveModel):
    """Test scenario linking multiple test cases."""

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    test_plan = models.ForeignKey(
        TestPlan,
        on_delete=models.CASCADE,
        related_name="test_scenarios",
        verbose_name=_("Test Plan"),
    )
    scenario_type = models.CharField(
        _("Scenario Type"),
        max_length=20,
        choices=TestScenarioType.CHOICES,
        default=TestScenarioType.POSITIVE,
    )
    test_cases = models.ManyToManyField(
        TestCase,
        through="TestScenarioCase",
        related_name="test_scenarios",
        verbose_name=_("Test Cases"),
    )
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=TestPriority.CHOICES,
        default=TestPriority.MEDIUM,
    )
    module = models.CharField(_("Module"), max_length=100, blank=True)
    feature = models.CharField(_("Feature"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("Test Scenario")
        verbose_name_plural = _("Test Scenarios")
        ordering = ["test_plan", "name"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} ({self.get_scenario_type_display()})"


class TestScenarioCase(models.Model):
    """Through model for TestScenario-TestCase relationship with ordering."""

    test_scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE)
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        ordering = ["order"]  # noqa: RUF012
        unique_together = [["test_scenario", "test_case"]]  # noqa: RUF012

    def __str__(self):
        return f"{self.test_scenario.name} > {self.test_case.test_id}"


class TestExecution(BaseModel, SoftDeleteModel, IsActiveModel):
    """Test execution record."""

    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name="executions",
        verbose_name=_("Test Case"),
    )
    test_plan = models.ForeignKey(
        TestPlan,
        on_delete=models.CASCADE,
        related_name="executions",
        verbose_name=_("Test Plan"),
    )
    test_suite = models.ForeignKey(
        TestSuite,
        on_delete=models.CASCADE,
        related_name="executions",
        verbose_name=_("Test Suite"),
    )
    environment = models.ForeignKey(
        TestEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
        verbose_name=_("Environment"),
    )
    test_data_set = models.ForeignKey(
        TestDataSet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
        verbose_name=_("Test Data Set"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TestExecutionStatus.CHOICES,
        default=TestExecutionStatus.PENDING,
    )
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executed_tests",
        verbose_name=_("Executed By"),
    )
    started_at = models.DateTimeField(_("Started At"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(_("Duration (seconds)"), default=0)
    actual_results = models.JSONField(_("Actual Results"), default=list, blank=True)
    error_message = models.TextField(_("Error Message"), blank=True)
    stack_trace = models.TextField(_("Stack Trace"), blank=True)
    screenshots = models.JSONField(_("Screenshots"), default=list, blank=True)
    logs = models.TextField(_("Logs"), blank=True)
    is_regression = models.BooleanField(_("Is Regression"), default=False)
    defect = models.ForeignKey(
        "Defect",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_executions",
        verbose_name=_("Linked Defect"),
    )

    class Meta:
        verbose_name = _("Test Execution")
        verbose_name_plural = _("Test Executions")
        ordering = ["-started_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.test_case.test_id} - {self.get_status_display()}"


class TestResult(BaseModel, SoftDeleteModel, IsActiveModel):
    """Detailed test step results."""

    execution = models.ForeignKey(
        TestExecution,
        on_delete=models.CASCADE,
        related_name="test_results",
        verbose_name=_("Test Execution"),
    )
    step_number = models.PositiveIntegerField(_("Step Number"))
    step_description = models.TextField(_("Step Description"))
    expected_result = models.TextField(_("Expected Result"))
    actual_result = models.TextField(_("Actual Result"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TestExecutionStatus.CHOICES,
        default=TestExecutionStatus.PENDING,
    )
    duration_seconds = models.PositiveIntegerField(_("Duration (seconds)"), default=0)
    screenshot = models.CharField(_("Screenshot Path"), max_length=500, blank=True)
    error_details = models.TextField(_("Error Details"), blank=True)

    class Meta:
        verbose_name = _("Test Result")
        verbose_name_plural = _("Test Results")
        ordering = ["execution", "step_number"]  # noqa: RUF012

    def __str__(self):
        return (
            f"{self.execution} - Step {self.step_number}: {self.get_status_display()}"
        )


class TestEvidence(BaseModel, SoftDeleteModel, IsActiveModel):
    """Test evidence (screenshots, videos, logs, files)."""

    execution = models.ForeignKey(
        TestExecution,
        on_delete=models.CASCADE,
        related_name="evidence",
        verbose_name=_("Test Execution"),
    )
    evidence_type = models.CharField(
        _("Evidence Type"),
        max_length=20,
        choices=[
            ("SCREENSHOT", _("Screenshot")),
            ("VIDEO", _("Video")),
            ("LOG", _("Log File")),
            ("FILE", _("File")),
            ("API_RESPONSE", _("API Response")),
            ("DB_SNAPSHOT", _("Database Snapshot")),
        ],
        default="SCREENSHOT",
    )
    file_path = models.CharField(_("File Path"), max_length=500)
    file_name = models.CharField(_("File Name"), max_length=255)
    file_size = models.PositiveIntegerField(_("File Size (bytes)"), default=0)
    mime_type = models.CharField(_("MIME Type"), max_length=100, blank=True)
    description = models.TextField(_("Description"), blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_evidence",
        verbose_name=_("Uploaded By"),
    )

    class Meta:
        verbose_name = _("Test Evidence")
        verbose_name_plural = _("Test Evidence")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return (
            f"{self.execution} - {self.file_name} ({self.get_evidence_type_display()})"
        )


class Defect(BaseModel, SoftDeleteModel, IsActiveModel):
    """Defect/bug tracking."""

    defect_id = models.CharField(_("Defect ID"), max_length=50, unique=True)
    title = models.CharField(_("Title"), max_length=300)
    description = models.TextField(_("Description"))
    steps_to_reproduce = models.TextField(_("Steps to Reproduce"), blank=True)
    expected_result = models.TextField(_("Expected Result"), blank=True)
    actual_result = models.TextField(_("Actual Result"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DefectStatus.CHOICES,
        default=DefectStatus.NEW,
    )
    severity = models.CharField(
        _("Severity"),
        max_length=10,
        choices=DefectSeverity.CHOICES,
        default=DefectSeverity.MEDIUM,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=TestPriority.CHOICES,
        default=TestPriority.MEDIUM,
    )
    module = models.CharField(_("Module"), max_length=100, blank=True)
    feature = models.CharField(_("Feature"), max_length=200, blank=True)
    environment = models.ForeignKey(
        TestEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="defects",
        verbose_name=_("Environment"),
    )
    test_execution = models.ForeignKey(
        TestExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="defects_found",
        verbose_name=_("Test Execution"),
    )
    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="defects",
        verbose_name=_("Test Case"),
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_defects",
        verbose_name=_("Reported By"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_defects",
        verbose_name=_("Assigned To"),
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_defects",
        verbose_name=_("Verified By"),
    )
    verified_at = models.DateTimeField(_("Verified At"), null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_defects",
        verbose_name=_("Resolved By"),
    )
    resolved_at = models.DateTimeField(_("Resolved At"), null=True, blank=True)
    resolution_notes = models.TextField(_("Resolution Notes"), blank=True)
    regression_tested = models.BooleanField(_("Regression Tested"), default=False)
    regression_tested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regression_tested_defects",
        verbose_name=_("Regression Tested By"),
    )
    regression_tested_at = models.DateTimeField(
        _("Regression Tested At"), null=True, blank=True
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_defects",
        verbose_name=_("Closed By"),
    )
    closed_at = models.DateTimeField(_("Closed At"), null=True, blank=True)
    audit_reference = models.CharField(_("Audit Reference"), max_length=100, blank=True)
    screenshots = models.JSONField(_("Screenshots"), default=list, blank=True)
    attachments = models.JSONField(_("Attachments"), default=list, blank=True)
    tags = models.JSONField(_("Tags"), default=list, blank=True)
    related_defects = models.ManyToManyField(
        "self", symmetrical=False, blank=True, verbose_name=_("Related Defects")
    )

    class Meta:
        verbose_name = _("Defect")
        verbose_name_plural = _("Defects")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.defect_id}: {self.title} ({self.get_severity_display()})"


class DefectAssignment(BaseModel, SoftDeleteModel, IsActiveModel):
    """Defect assignment history."""

    defect = models.ForeignKey(
        Defect,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Defect"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="defect_assignments",
        verbose_name=_("Assigned To"),
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="defect_assignments_made",
        verbose_name=_("Assigned By"),
    )
    assigned_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)
    unassigned_at = models.DateTimeField(_("Unassigned At"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Defect Assignment")
        verbose_name_plural = _("Defect Assignments")
        ordering = ["-assigned_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.defect.defect_id} -> {self.assigned_to}"


class DefectResolution(BaseModel, SoftDeleteModel, IsActiveModel):
    """Defect resolution record."""

    defect = models.ForeignKey(
        Defect,
        on_delete=models.CASCADE,
        related_name="resolutions",
        verbose_name=_("Defect"),
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="defect_resolutions",
        verbose_name=_("Resolved By"),
    )
    resolved_at = models.DateTimeField(_("Resolved At"), auto_now_add=True)
    resolution_type = models.CharField(
        _("Resolution Type"),
        max_length=20,
        choices=[
            ("FIXED", _("Fixed")),
            ("WONT_FIX", _("Won't Fix")),
            ("DUPLICATE", _("Duplicate")),
            ("NOT_REPRODUCIBLE", _("Not Reproducible")),
            ("BY_DESIGN", _("By Design")),
            ("WORKAROUND", _("Workaround")),
        ],
        default="FIXED",
    )
    resolution_notes = models.TextField(_("Resolution Notes"))
    code_changes = models.JSONField(_("Code Changes"), default=list, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_resolutions",
        verbose_name=_("Verified By"),
    )
    verified_at = models.DateTimeField(_("Verified At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Defect Resolution")
        verbose_name_plural = _("Defect Resolutions")
        ordering = ["-resolved_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.defect.defect_id} - {self.get_resolution_type_display()}"


class RegressionTest(BaseModel, SoftDeleteModel, IsActiveModel):
    """Regression test tracking."""

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    trigger = models.CharField(
        _("Trigger"),
        max_length=50,
        choices=[
            ("RELEASE", _("Release")),
            ("HOTFIX", _("Hotfix")),
            ("SCHEDULED", _("Scheduled")),
            ("MANUAL", _("Manual")),
            ("CODE_CHANGE", _("Code Change")),
            ("CONFIG_CHANGE", _("Config Change")),
        ],
        default="RELEASE",
    )
    test_suites = models.ManyToManyField(
        TestSuite, related_name="regression_tests", verbose_name=_("Test Suites")
    )
    environment = models.ForeignKey(
        TestEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regression_tests",
        verbose_name=_("Environment"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TestExecutionStatus.CHOICES,
        default=TestExecutionStatus.PENDING,
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_regression_tests",
        verbose_name=_("Triggered By"),
    )
    started_at = models.DateTimeField(_("Started At"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    total_tests = models.PositiveIntegerField(_("Total Tests"), default=0)
    passed_tests = models.PositiveIntegerField(_("Passed Tests"), default=0)
    failed_tests = models.PositiveIntegerField(_("Failed Tests"), default=0)
    skipped_tests = models.PositiveIntegerField(_("Skipped Tests"), default=0)
    blocked_tests = models.PositiveIntegerField(_("Blocked Tests"), default=0)
    pass_rate = models.DecimalField(
        _("Pass Rate"), max_digits=5, decimal_places=2, default=0
    )
    release_candidate = models.ForeignKey(
        "ReleaseCandidate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regression_tests",
        verbose_name=_("Release Candidate"),
    )

    class Meta:
        verbose_name = _("Regression Test")
        verbose_name_plural = _("Regression Tests")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class UATSession(BaseModel, SoftDeleteModel, IsActiveModel):
    """User Acceptance Testing session."""

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    release_candidate = models.ForeignKey(
        "ReleaseCandidate",
        on_delete=models.CASCADE,
        related_name="uat_sessions",
        verbose_name=_("Release Candidate"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=UATSessionStatus.CHOICES,
        default=UATSessionStatus.PLANNED,
    )
    planned_start = models.DateTimeField(_("Planned Start"), null=True, blank=True)
    planned_end = models.DateTimeField(_("Planned End"), null=True, blank=True)
    actual_start = models.DateTimeField(_("Actual Start"), null=True, blank=True)
    actual_end = models.DateTimeField(_("Actual End"), null=True, blank=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="uat_sessions",
        verbose_name=_("Participants"),
    )
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="facilitated_uat_sessions",
        verbose_name=_("Facilitator"),
    )
    test_scenarios = models.ManyToManyField(
        TestScenario, related_name="uat_sessions", verbose_name=_("Test Scenarios")
    )
    acceptance_criteria = models.TextField(_("Acceptance Criteria"), blank=True)
    overall_result = models.CharField(
        _("Overall Result"),
        max_length=20,
        choices=[
            ("PASS", _("Pass")),
            ("FAIL", _("Fail")),
            ("CONDITIONAL_PASS", _("Conditional Pass")),
            ("INCOMPLETE", _("Incomplete")),
        ],
        blank=True,
    )
    sign_off_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signed_off_uat_sessions",
        verbose_name=_("Signed Off By"),
    )
    signed_off_at = models.DateTimeField(_("Signed Off At"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("UAT Session")
        verbose_name_plural = _("UAT Sessions")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class ReleaseCandidate(BaseModel, SoftDeleteModel, IsActiveModel):
    """Release candidate for deployment."""

    version = models.CharField(_("Version"), max_length=50)
    name = models.CharField(_("Name"), max_length=200, blank=True)
    description = models.TextField(_("Description"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ReleaseCandidateStatus.CHOICES,
        default=ReleaseCandidateStatus.DRAFT,
    )
    branch = models.CharField(_("Branch"), max_length=100, default="main")
    commit_hash = models.CharField(_("Commit Hash"), max_length=100, blank=True)
    build_number = models.CharField(_("Build Number"), max_length=50, blank=True)
    build_url = models.URLField(_("Build URL"), blank=True)
    changelog = models.TextField(_("Changelog"), blank=True)
    release_notes = models.TextField(_("Release Notes"), blank=True)
    planned_release_date = models.DateTimeField(
        _("Planned Release Date"), null=True, blank=True
    )
    actual_release_date = models.DateTimeField(
        _("Actual Release Date"), null=True, blank=True
    )
    deployed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deployed_releases",
        verbose_name=_("Deployed By"),
    )
    deployed_at = models.DateTimeField(_("Deployed At"), null=True, blank=True)
    rollback_reason = models.TextField(_("Rollback Reason"), blank=True)
    rolled_back_at = models.DateTimeField(_("Rolled Back At"), null=True, blank=True)
    test_plan = models.ForeignKey(
        TestPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="release_candidates",
        verbose_name=_("Test Plan"),
    )

    class Meta:
        verbose_name = _("Release Candidate")
        verbose_name_plural = _("Release Candidates")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.version} ({self.get_status_display()})"


class ReleaseApproval(BaseModel, SoftDeleteModel, IsActiveModel):
    """Release approval record."""

    release_candidate = models.ForeignKey(
        ReleaseCandidate,
        on_delete=models.CASCADE,
        related_name="approvals",
        verbose_name=_("Release Candidate"),
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="release_approvals",
        verbose_name=_("Approver"),
    )
    role = models.CharField(_("Role"), max_length=100)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ReleaseApprovalStatus.CHOICES,
        default=ReleaseApprovalStatus.PENDING,
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)
    conditions = models.TextField(_("Conditions"), blank=True)
    comments = models.TextField(_("Comments"), blank=True)

    class Meta:
        verbose_name = _("Release Approval")
        verbose_name_plural = _("Release Approvals")
        unique_together = [["release_candidate", "approver"]]  # noqa: RUF012
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return (
            f"{self.release_candidate.version} - {self.approver} "
            f"({self.get_status_display()})"
        )


class QualityMetric(BaseModel, SoftDeleteModel, IsActiveModel):
    """Quality metric/KPI tracking."""

    metric_type = models.CharField(
        _("Metric Type"), max_length=50, choices=QualityMetricType.CHOICES
    )
    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    module = models.CharField(_("Module"), max_length=100, blank=True)
    value = models.DecimalField(_("Value"), max_digits=10, decimal_places=2)
    target_value = models.DecimalField(
        _("Target Value"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    threshold_warning = models.DecimalField(
        _("Warning Threshold"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    threshold_critical = models.DecimalField(
        _("Critical Threshold"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    unit = models.CharField(_("Unit"), max_length=50, default="%")
    period_start = models.DateTimeField(_("Period Start"))
    period_end = models.DateTimeField(_("Period End"))
    calculated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calculated_metrics",
        verbose_name=_("Calculated By"),
    )
    calculated_at = models.DateTimeField(_("Calculated At"), auto_now_add=True)
    data_source = models.JSONField(_("Data Source"), default=dict, blank=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Quality Metric")
        verbose_name_plural = _("Quality Metrics")
        ordering = ["-period_end", "metric_type"]  # noqa: RUF012

    def __str__(self):
        return (
            f"{self.name} ({self.get_metric_type_display()}) = {self.value} {self.unit}"
        )


class QualityDashboard(BaseModel, SoftDeleteModel, IsActiveModel):
    """Quality dashboard configuration."""

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    widgets = models.JSONField(_("Widgets"), default=list, blank=True)
    layout = models.JSONField(_("Layout"), default=dict, blank=True)
    is_default = models.BooleanField(_("Is Default"), default=False)
    role_access = models.JSONField(_("Role Access"), default=list, blank=True)
    refresh_interval = models.PositiveIntegerField(
        _("Refresh Interval (seconds)"), default=300
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_dashboards",
        verbose_name=_("Owner"),
    )

    class Meta:
        verbose_name = _("Quality Dashboard")
        verbose_name_plural = _("Quality Dashboards")
        ordering = ["name"]  # noqa: RUF012

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            QualityDashboard.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class QANotification(BaseModel, SoftDeleteModel, IsActiveModel):
    """QA notification."""

    notification_type = models.CharField(
        _("Notification Type"), max_length=50, choices=QANotificationType.CHOICES
    )
    title = models.CharField(_("Title"), max_length=300)
    message = models.TextField(_("Message"))
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="qa_notifications",
        verbose_name=_("Recipient"),
    )
    related_object_type = models.CharField(
        _("Related Object Type"), max_length=50, blank=True
    )
    related_object_id = models.CharField(
        _("Related Object ID"), max_length=100, blank=True
    )
    is_read = models.BooleanField(_("Is Read"), default=False)
    read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=TestPriority.CHOICES,
        default=TestPriority.MEDIUM,
    )

    class Meta:
        verbose_name = _("QA Notification")
        verbose_name_plural = _("QA Notifications")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"


class QATimeline(BaseModel, SoftDeleteModel):
    """QA timeline for historical analysis."""

    event_type = models.CharField(
        _("Event Type"),
        max_length=50,
        choices=[
            ("TEST_PLANNED", _("Test Planned")),
            ("TEST_CASE_CREATED", _("Test Case Created")),
            ("ENVIRONMENT_PREPARED", _("Environment Prepared")),
            ("TEST_EXECUTED", _("Test Executed")),
            ("DEFECT_REPORTED", _("Defect Reported")),
            ("DEFECT_ASSIGNED", _("Defect Assigned")),
            ("DEFECT_RESOLVED", _("Defect Resolved")),
            ("REGRESSION_COMPLETED", _("Regression Completed")),
            ("UAT_COMPLETED", _("UAT Completed")),
            ("RELEASE_APPROVED", _("Release Approved")),
        ],
    )
    module = models.CharField(_("Module"), max_length=100, blank=True)
    test_type = models.CharField(
        _("Test Type"), max_length=20, choices=TestCategory.CHOICES, blank=True
    )
    status = models.CharField(_("Status"), max_length=50)
    result = models.CharField(_("Result"), max_length=50, blank=True)
    tester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="qa_timeline_events",
        verbose_name=_("Tester"),
    )
    related_object_type = models.CharField(
        _("Related Object Type"), max_length=50, blank=True
    )
    related_object_id = models.CharField(
        _("Related Object ID"), max_length=100, blank=True
    )
    defect_reference = models.CharField(
        _("Defect Reference"), max_length=100, blank=True
    )
    audit_reference = models.CharField(_("Audit Reference"), max_length=100, blank=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)

    class Meta:
        verbose_name = _("QA Timeline Event")
        verbose_name_plural = _("QA Timeline Events")
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.module} - {self.status}"


class QAAuditReference(BaseModel):
    """Immutable QA audit reference."""

    reference_id = models.CharField(_("Reference ID"), max_length=100, unique=True)
    event_type = models.CharField(_("Event Type"), max_length=50)
    module = models.CharField(_("Module"), max_length=100, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User"),
    )
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    before_values = models.JSONField(_("Before Values"), default=dict, blank=True)
    after_values = models.JSONField(_("After Values"), default=dict, blank=True)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("QA Audit Reference")
        verbose_name_plural = _("QA Audit References")
        ordering = ["-timestamp"]  # noqa: RUF012

    def __str__(self):
        return f"{self.reference_id} ({self.event_type})"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError(_("QAAuditReference records are immutable."))
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError(_("QAAuditReference records cannot be deleted."))
