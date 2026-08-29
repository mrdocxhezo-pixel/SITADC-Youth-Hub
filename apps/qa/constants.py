from django.utils.translation import gettext_lazy as _


class TestPlanStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

    CHOICES = [  # noqa: RUF012
        (DRAFT, _("Draft")),
        (ACTIVE, _("Active")),
        (COMPLETED, _("Completed")),
        (ARCHIVED, _("Archived")),
    ]


class TestSuiteStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

    CHOICES = [  # noqa: RUF012
        (DRAFT, _("Draft")),
        (ACTIVE, _("Active")),
        (COMPLETED, _("Completed")),
        (ARCHIVED, _("Archived")),
    ]


class TestCaseStatus:
    DRAFT = "DRAFT"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    ARCHIVED = "ARCHIVED"

    CHOICES = [  # noqa: RUF012
        (DRAFT, _("Draft")),
        (READY, _("Ready")),
        (IN_PROGRESS, _("In Progress")),
        (PASSED, _("Passed")),
        (FAILED, _("Failed")),
        (BLOCKED, _("Blocked")),
        (SKIPPED, _("Skipped")),
        (ARCHIVED, _("Archived")),
    ]


class TestExecutionStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"

    CHOICES = [  # noqa: RUF012
        (PENDING, _("Pending")),
        (RUNNING, _("Running")),
        (PASSED, _("Passed")),
        (FAILED, _("Failed")),
        (BLOCKED, _("Blocked")),
        (SKIPPED, _("Skipped")),
        (ERROR, _("Error")),
    ]


class TestPriority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    CHOICES = [  # noqa: RUF012
        (LOW, _("Low")),
        (MEDIUM, _("Medium")),
        (HIGH, _("High")),
        (CRITICAL, _("Critical")),
    ]


class TestCategory:
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    FUNCTIONAL = "FUNCTIONAL"
    END_TO_END = "END_TO_END"
    API = "API"
    DATABASE = "DATABASE"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    ACCESSIBILITY = "ACCESSIBILITY"
    COMPATIBILITY = "COMPATIBILITY"
    REGRESSION = "REGRESSION"
    USER_ACCEPTANCE = "USER_ACCEPTANCE"
    SMOKE = "SMOKE"
    SANITY = "SANITY"

    CHOICES = [  # noqa: RUF012
        (UNIT, _("Unit Testing")),
        (INTEGRATION, _("Integration Testing")),
        (FUNCTIONAL, _("Functional Testing")),
        (END_TO_END, _("End-to-End Testing")),
        (API, _("API Testing")),
        (DATABASE, _("Database Testing")),
        (SECURITY, _("Security Testing")),
        (PERFORMANCE, _("Performance Testing")),
        (ACCESSIBILITY, _("Accessibility Testing")),
        (COMPATIBILITY, _("Compatibility Testing")),
        (REGRESSION, _("Regression Testing")),
        (USER_ACCEPTANCE, _("User Acceptance Testing")),
        (SMOKE, _("Smoke Testing")),
        (SANITY, _("Sanity Testing")),
    ]


class DefectStatus:
    NEW = "NEW"
    CLASSIFIED = "CLASSIFIED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    DEVELOPER_VERIFIED = "DEVELOPER_VERIFIED"
    QA_VERIFIED = "QA_VERIFIED"
    REGRESSION_TESTED = "REGRESSION_TESTED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"

    CHOICES = [  # noqa: RUF012
        (NEW, _("New")),
        (CLASSIFIED, _("Classified")),
        (ASSIGNED, _("Assigned")),
        (IN_PROGRESS, _("In Progress")),
        (DEVELOPER_VERIFIED, _("Developer Verified")),
        (QA_VERIFIED, _("QA Verified")),
        (REGRESSION_TESTED, _("Regression Tested")),
        (CLOSED, _("Closed")),
        (REOPENED, _("Reopened")),
        (REJECTED, _("Rejected")),
        (DEFERRED, _("Deferred")),
    ]


class DefectSeverity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    BLOCKER = "BLOCKER"

    CHOICES = [  # noqa: RUF012
        (LOW, _("Low")),
        (MEDIUM, _("Medium")),
        (HIGH, _("High")),
        (CRITICAL, _("Critical")),
        (BLOCKER, _("Blocker")),
    ]


class EnvironmentType:
    LOCAL = "LOCAL"
    DEVELOPMENT = "DEVELOPMENT"
    INTEGRATION = "INTEGRATION"
    QA = "QA"
    UAT = "UAT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

    CHOICES = [  # noqa: RUF012
        (LOCAL, _("Local Development")),
        (DEVELOPMENT, _("Development")),
        (INTEGRATION, _("Integration")),
        (QA, _("Quality Assurance")),
        (UAT, _("User Acceptance Testing")),
        (STAGING, _("Staging")),
        (PRODUCTION, _("Production")),
    ]


class ReleaseCandidateStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    TESTING = "TESTING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPLOYED = "DEPLOYED"
    ROLLED_BACK = "ROLLED_BACK"

    CHOICES = [  # noqa: RUF012
        (DRAFT, _("Draft")),
        (SUBMITTED, _("Submitted")),
        (TESTING, _("Testing")),
        (APPROVED, _("Approved")),
        (REJECTED, _("Rejected")),
        (DEPLOYED, _("Deployed")),
        (ROLLED_BACK, _("Rolled Back")),
    ]


class ReleaseApprovalStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"

    CHOICES = [  # noqa: RUF012
        (PENDING, _("Pending")),
        (APPROVED, _("Approved")),
        (REJECTED, _("Rejected")),
        (CONDITIONAL, _("Conditional")),
    ]


class QANotificationType:
    TEST_EXECUTION_STARTED = "TEST_EXECUTION_STARTED"
    TEST_EXECUTION_COMPLETED = "TEST_EXECUTION_COMPLETED"
    TEST_FAILURE = "TEST_FAILURE"
    CRITICAL_DEFECT = "CRITICAL_DEFECT"
    REGRESSION_COMPLETED = "REGRESSION_COMPLETED"
    SECURITY_SCAN_COMPLETED = "SECURITY_SCAN_COMPLETED"
    ACCESSIBILITY_VALIDATION_COMPLETED = "ACCESSIBILITY_VALIDATION_COMPLETED"
    PERFORMANCE_BENCHMARK_COMPLETED = "PERFORMANCE_BENCHMARK_COMPLETED"
    RELEASE_CANDIDATE_APPROVED = "RELEASE_CANDIDATE_APPROVED"
    RELEASE_BLOCKED = "RELEASE_BLOCKED"

    CHOICES = [  # noqa: RUF012
        (TEST_EXECUTION_STARTED, _("Test Execution Started")),
        (TEST_EXECUTION_COMPLETED, _("Test Execution Completed")),
        (TEST_FAILURE, _("Test Failure")),
        (CRITICAL_DEFECT, _("Critical Defect Detected")),
        (REGRESSION_COMPLETED, _("Regression Completed")),
        (SECURITY_SCAN_COMPLETED, _("Security Scan Completed")),
        (ACCESSIBILITY_VALIDATION_COMPLETED, _("Accessibility Validation Completed")),
        (PERFORMANCE_BENCHMARK_COMPLETED, _("Performance Benchmark Completed")),
        (RELEASE_CANDIDATE_APPROVED, _("Release Candidate Approved")),
        (RELEASE_BLOCKED, _("Release Blocked")),
    ]


class TestScenarioType:
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    BOUNDARY = "BOUNDARY"
    EDGE_CASE = "EDGE_CASE"
    ERROR_HANDLING = "ERROR_HANDLING"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    ACCESSIBILITY = "ACCESSIBILITY"

    CHOICES = [  # noqa: RUF012
        (POSITIVE, _("Positive")),
        (NEGATIVE, _("Negative")),
        (BOUNDARY, _("Boundary")),
        (EDGE_CASE, _("Edge Case")),
        (ERROR_HANDLING, _("Error Handling")),
        (PERFORMANCE, _("Performance")),
        (SECURITY, _("Security")),
        (ACCESSIBILITY, _("Accessibility")),
    ]


class UATSessionStatus:
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    CHOICES = [  # noqa: RUF012
        (PLANNED, _("Planned")),
        (IN_PROGRESS, _("In Progress")),
        (COMPLETED, _("Completed")),
        (CANCELLED, _("Cancelled")),
    ]


class QualityMetricType:
    TEST_COVERAGE = "TEST_COVERAGE"
    AUTOMATED_COVERAGE = "AUTOMATED_COVERAGE"
    MANUAL_COMPLETION = "MANUAL_COMPLETION"
    DEFECT_DENSITY = "DEFECT_DENSITY"
    CRITICAL_DEFECT_COUNT = "CRITICAL_DEFECT_COUNT"
    MEAN_TIME_TO_DETECT = "MEAN_TIME_TO_DETECT"
    MEAN_TIME_TO_RESOLVE = "MEAN_TIME_TO_RESOLVE"
    REGRESSION_PASS_RATE = "REGRESSION_PASS_RATE"
    UAT_PASS_RATE = "UAT_PASS_RATE"
    RELEASE_SUCCESS_RATE = "RELEASE_SUCCESS_RATE"
    CODE_QUALITY_SCORE = "CODE_QUALITY_SCORE"
    SECURITY_VALIDATION_SCORE = "SECURITY_VALIDATION_SCORE"
    ACCESSIBILITY_COMPLIANCE_SCORE = "ACCESSIBILITY_COMPLIANCE_SCORE"
    PERFORMANCE_VALIDATION_SCORE = "PERFORMANCE_VALIDATION_SCORE"

    CHOICES = [  # noqa: RUF012
        (TEST_COVERAGE, _("Test Coverage Percentage")),
        (AUTOMATED_COVERAGE, _("Automated Test Coverage")),
        (MANUAL_COMPLETION, _("Manual Test Completion")),
        (DEFECT_DENSITY, _("Defect Density")),
        (CRITICAL_DEFECT_COUNT, _("Critical Defect Count")),
        (MEAN_TIME_TO_DETECT, _("Mean Time to Detect Defects")),
        (MEAN_TIME_TO_RESOLVE, _("Mean Time to Resolve Defects")),
        (REGRESSION_PASS_RATE, _("Regression Pass Rate")),
        (UAT_PASS_RATE, _("UAT Pass Rate")),
        (RELEASE_SUCCESS_RATE, _("Release Success Rate")),
        (CODE_QUALITY_SCORE, _("Code Quality Score")),
        (SECURITY_VALIDATION_SCORE, _("Security Validation Score")),
        (ACCESSIBILITY_COMPLIANCE_SCORE, _("Accessibility Compliance Score")),
        (PERFORMANCE_VALIDATION_SCORE, _("Performance Validation Score")),
    ]


class QualityDashboardWidgetType:
    OVERALL_QUALITY_SCORE = "OVERALL_QUALITY_SCORE"
    TEST_EXECUTION_PROGRESS = "TEST_EXECUTION_PROGRESS"
    AUTOMATED_TEST_RESULTS = "AUTOMATED_TEST_RESULTS"
    MANUAL_TEST_RESULTS = "MANUAL_TEST_RESULTS"
    DEFECT_SUMMARY = "DEFECT_SUMMARY"
    DEFECTS_BY_SEVERITY = "DEFECTS_BY_SEVERITY"
    TEST_COVERAGE_PERCENTAGE = "TEST_COVERAGE_PERCENTAGE"
    REGRESSION_TESTING_STATUS = "REGRESSION_TESTING_STATUS"
    RELEASE_READINESS = "RELEASE_READINESS"
    OPEN_CRITICAL_DEFECTS = "OPEN_CRITICAL_DEFECTS"
    QUALITY_TRENDS = "QUALITY_TRENDS"
    MODULE_QUALITY_SCORES = "MODULE_QUALITY_SCORES"
    TEST_AUTOMATION_COVERAGE = "TEST_AUTOMATION_COVERAGE"
    ENVIRONMENT_STATUS = "ENVIRONMENT_STATUS"

    CHOICES = [  # noqa: RUF012
        (OVERALL_QUALITY_SCORE, _("Overall Quality Score")),
        (TEST_EXECUTION_PROGRESS, _("Test Execution Progress")),
        (AUTOMATED_TEST_RESULTS, _("Automated Test Results")),
        (MANUAL_TEST_RESULTS, _("Manual Test Results")),
        (DEFECT_SUMMARY, _("Defect Summary")),
        (DEFECTS_BY_SEVERITY, _("Defects by Severity")),
        (TEST_COVERAGE_PERCENTAGE, _("Test Coverage Percentage")),
        (REGRESSION_TESTING_STATUS, _("Regression Testing Status")),
        (RELEASE_READINESS, _("Release Readiness")),
        (OPEN_CRITICAL_DEFECTS, _("Open Critical Defects")),
        (QUALITY_TRENDS, _("Quality Trends")),
        (MODULE_QUALITY_SCORES, _("Module Quality Scores")),
        (TEST_AUTOMATION_COVERAGE, _("Test Automation Coverage")),
        (ENVIRONMENT_STATUS, _("Environment Status")),
    ]
