from django import forms
from django.contrib.auth import get_user_model

from apps.qa.constants import (
    DefectSeverity,
    DefectStatus,
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
from apps.qa.models import (
    Defect,
    DefectAssignment,
    DefectResolution,
    QAConfiguration,
    QANotification,
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

User = get_user_model()


class QAConfigurationForm(forms.ModelForm):
    """Form for QA configuration."""

    class Meta:
        model = QAConfiguration
        fields = [  # noqa: RUF012
            "testing_policies",
            "quality_thresholds",
            "code_coverage_targets",
            "test_execution_schedules",
            "automated_testing_config",
            "regression_testing_rules",
            "defect_severity_rules",
            "release_approval_workflows",
            "uat_settings",
            "test_notification_settings",
            "test_retention_policies",
            "quality_dashboards_config",
            "is_active",
        ]
        widgets = {  # noqa: RUF012
            "testing_policies": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "quality_thresholds": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "code_coverage_targets": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "test_execution_schedules": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "automated_testing_config": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "regression_testing_rules": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "defect_severity_rules": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "release_approval_workflows": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "uat_settings": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "test_notification_settings": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "test_retention_policies": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "quality_dashboards_config": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
        }


class TestEnvironmentForm(forms.ModelForm):
    """Form for test environment."""

    class Meta:
        model = TestEnvironment
        fields = [  # noqa: RUF012
            "name",
            "environment_type",
            "description",
            "base_url",
            "is_default",
            "is_active",
            "database_config",
            "cache_config",
            "credentials",
            "configuration_consistency",
            "isolation_level",
            "secure_credentials",
            "test_database_config",
            "logging_config",
            "monitoring_config",
            "backup_procedures",
        ]
        widgets = {  # noqa: RUF012
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "environment_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "base_url": forms.URLInput(attrs={"class": "form-control"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "database_config": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "cache_config": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "credentials": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "configuration_consistency": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "isolation_level": forms.TextInput(attrs={"class": "form-control"}),
            "secure_credentials": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "test_database_config": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "logging_config": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "monitoring_config": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "backup_procedures": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
        }


class TestDataSetForm(forms.ModelForm):
    """Form for test data set."""

    class Meta:
        model = TestDataSet
        fields = [  # noqa: RUF012
            "name",
            "description",
            "data_type",
            "version",
            "file_path",
            "data_schema",
            "record_count",
            "size_bytes",
            "checksum",
            "environment",
            "is_reproducible",
            "is_active",
        ]
        widgets = {  # noqa: RUF012
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "data_type": forms.Select(attrs={"class": "form-select"}),
            "version": forms.TextInput(attrs={"class": "form-control"}),
            "file_path": forms.TextInput(attrs={"class": "form-control"}),
            "data_schema": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "record_count": forms.NumberInput(attrs={"class": "form-control"}),
            "size_bytes": forms.NumberInput(attrs={"class": "form-control"}),
            "checksum": forms.TextInput(attrs={"class": "form-control"}),
            "environment": forms.Select(attrs={"class": "form-select"}),
            "is_reproducible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TestPlanForm(forms.ModelForm):
    """Form for test plan."""

    class Meta:
        model = TestPlan
        fields = [  # noqa: RUF012
            "name",
            "description",
            "version",
            "status",
            "start_date",
            "end_date",
            "release_candidate",
            "modules",
            "test_categories",
            "quality_thresholds",
            "entry_criteria",
            "exit_criteria",
            "risks",
            "assumptions",
        ]
        widgets = {  # noqa: RUF012
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "version": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=TestPlanStatus.CHOICES,
            ),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "release_candidate": forms.Select(attrs={"class": "form-select"}),
            "modules": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "test_categories": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "quality_thresholds": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "entry_criteria": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "exit_criteria": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "risks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "assumptions": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class TestSuiteForm(forms.ModelForm):
    """Form for test suite."""

    class Meta:
        model = TestSuite
        fields = [  # noqa: RUF012
            "name",
            "description",
            "test_plan",
            "parent",
            "status",
            "order",
            "module",
            "feature",
            "requirement_references",
            "tags",
        ]
        widgets = {  # noqa: RUF012
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "test_plan": forms.Select(attrs={"class": "form-select"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=TestSuiteStatus.CHOICES,
            ),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "module": forms.TextInput(attrs={"class": "form-control"}),
            "feature": forms.TextInput(attrs={"class": "form-control"}),
            "requirement_references": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "tags": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class TestCaseForm(forms.ModelForm):
    """Form for test case."""

    class Meta:
        model = TestCase
        fields = [  # noqa: RUF012
            "test_suite",
            "test_id",
            "title",
            "description",
            "preconditions",
            "postconditions",
            "steps",
            "expected_results",
            "status",
            "priority",
            "category",
            "test_type",
            "is_automated",
            "automation_script",
            "automation_framework",
            "requirement_reference",
            "module",
            "feature",
            "estimated_duration",
            "tags",
            "assigned_to",
            "reviewed_by",
            "reviewed_at",
        ]
        widgets = {  # noqa: RUF012
            "test_suite": forms.Select(attrs={"class": "form-select"}),
            "test_id": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "preconditions": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "postconditions": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "steps": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "expected_results": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=TestCaseStatus.CHOICES,
            ),
            "priority": forms.Select(
                attrs={"class": "form-select"},
                choices=TestPriority.CHOICES,
            ),
            "category": forms.Select(
                attrs={"class": "form-select"},
                choices=TestCategory.CHOICES,
            ),
            "test_type": forms.Select(
                attrs={"class": "form-select"},
                choices=TestScenarioType.CHOICES,
            ),
            "is_automated": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "automation_script": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "automation_framework": forms.TextInput(attrs={"class": "form-control"}),
            "requirement_reference": forms.TextInput(attrs={"class": "form-control"}),
            "module": forms.TextInput(attrs={"class": "form-control"}),
            "feature": forms.TextInput(attrs={"class": "form-control"}),
            "estimated_duration": forms.NumberInput(attrs={"class": "form-control"}),
            "tags": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "reviewed_by": forms.Select(attrs={"class": "form-select"}),
            "reviewed_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["test_id"].required = False
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True)
        self.fields["reviewed_by"].queryset = User.objects.filter(is_active=True)


class TestScenarioForm(forms.ModelForm):
    """Form for test scenario."""

    class Meta:
        model = TestScenario
        fields = [  # noqa: RUF012
            "name",
            "description",
            "test_plan",
            "scenario_type",
            "priority",
            "module",
            "feature",
        ]
        widgets = {  # noqa: RUF012
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "test_plan": forms.Select(attrs={"class": "form-select"}),
            "scenario_type": forms.Select(
                attrs={"class": "form-select"},
                choices=TestScenarioType.CHOICES,
            ),
            "priority": forms.Select(
                attrs={"class": "form-select"},
                choices=TestPriority.CHOICES,
            ),
            "module": forms.TextInput(attrs={"class": "form-control"}),
            "feature": forms.TextInput(attrs={"class": "form-control"}),
        }


class TestScenarioCaseForm(forms.ModelForm):
    """Form for test scenario case ordering."""

    class Meta:
        model = TestScenarioCase
        fields = ["test_case", "order"]  # noqa: RUF012
        widgets = {  # noqa: RUF012
            "test_case": forms.Select(attrs={"class": "form-select"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TestExecutionForm(forms.ModelForm):
    """Form for test execution."""

    class Meta:
        model = TestExecution
        fields = [  # noqa: RUF012
            "test_case",
            "test_plan",
            "test_suite",
            "environment",
            "test_data_set",
            "status",
            "executed_by",
            "started_at",
            "completed_at",
            "duration_seconds",
            "actual_results",
            "error_message",
            "stack_trace",
            "screenshots",
            "logs",
            "is_regression",
            "defect",
        ]
        widgets = {  # noqa: RUF012
            "test_case": forms.Select(attrs={"class": "form-select"}),
            "test_plan": forms.Select(attrs={"class": "form-select"}),
            "test_suite": forms.Select(attrs={"class": "form-select"}),
            "environment": forms.Select(attrs={"class": "form-select"}),
            "test_data_set": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=TestExecutionStatus.CHOICES,
            ),
            "executed_by": forms.Select(attrs={"class": "form-select"}),
            "started_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "completed_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "duration_seconds": forms.NumberInput(attrs={"class": "form-control"}),
            "actual_results": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "error_message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "stack_trace": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "screenshots": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "logs": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "is_regression": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "defect": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["executed_by"].queryset = User.objects.filter(is_active=True)


class TestResultForm(forms.ModelForm):
    """Form for test result."""

    class Meta:
        model = TestResult
        fields = [  # noqa: RUF012
            "execution",
            "step_number",
            "step_description",
            "expected_result",
            "actual_result",
            "status",
            "duration_seconds",
            "screenshot",
            "error_details",
        ]
        widgets = {  # noqa: RUF012
            "execution": forms.Select(attrs={"class": "form-select"}),
            "step_number": forms.NumberInput(attrs={"class": "form-control"}),
            "step_description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "expected_result": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "actual_result": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=TestExecutionStatus.CHOICES,
            ),
            "duration_seconds": forms.NumberInput(attrs={"class": "form-control"}),
            "screenshot": forms.TextInput(attrs={"class": "form-control"}),
            "error_details": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class TestEvidenceForm(forms.ModelForm):
    """Form for test evidence."""

    class Meta:
        model = TestEvidence
        fields = [  # noqa: RUF012
            "execution",
            "evidence_type",
            "file_path",
            "file_name",
            "file_size",
            "mime_type",
            "description",
        ]
        widgets = {  # noqa: RUF012
            "execution": forms.Select(attrs={"class": "form-select"}),
            "evidence_type": forms.Select(attrs={"class": "form-select"}),
            "file_path": forms.TextInput(attrs={"class": "form-control"}),
            "file_name": forms.TextInput(attrs={"class": "form-control"}),
            "file_size": forms.NumberInput(attrs={"class": "form-control"}),
            "mime_type": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class DefectForm(forms.ModelForm):
    """Form for defect."""

    class Meta:
        model = Defect
        fields = [  # noqa: RUF012
            "defect_id",
            "title",
            "description",
            "steps_to_reproduce",
            "expected_result",
            "actual_result",
            "status",
            "severity",
            "priority",
            "module",
            "feature",
            "environment",
            "test_execution",
            "test_case",
            "assigned_to",
            "resolution_notes",
            "regression_tested",
            "tags",
            "screenshots",
            "attachments",
        ]
        widgets = {  # noqa: RUF012
            "defect_id": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "steps_to_reproduce": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "expected_result": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "actual_result": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=DefectStatus.CHOICES,
            ),
            "severity": forms.Select(
                attrs={"class": "form-select"},
                choices=DefectSeverity.CHOICES,
            ),
            "priority": forms.Select(
                attrs={"class": "form-select"},
                choices=TestPriority.CHOICES,
            ),
            "module": forms.TextInput(attrs={"class": "form-control"}),
            "feature": forms.TextInput(attrs={"class": "form-control"}),
            "environment": forms.Select(attrs={"class": "form-select"}),
            "test_execution": forms.Select(attrs={"class": "form-select"}),
            "test_case": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "resolution_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "regression_tested": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "tags": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "screenshots": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "attachments": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["defect_id"].required = False
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True)


class DefectAssignmentForm(forms.ModelForm):
    """Form for defect assignment."""

    class Meta:
        model = DefectAssignment
        fields = ["defect", "assigned_to", "assigned_by", "notes"]  # noqa: RUF012
        widgets = {  # noqa: RUF012
            "defect": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "assigned_by": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class DefectResolutionForm(forms.ModelForm):
    """Form for defect resolution."""

    class Meta:
        model = DefectResolution
        fields = [  # noqa: RUF012
            "defect",
            "resolved_by",
            "resolution_type",
            "resolution_notes",
            "code_changes",
            "verified_by",
            "verified_at",
        ]
        widgets = {  # noqa: RUF012
            "defect": forms.Select(attrs={"class": "form-select"}),
            "resolved_by": forms.Select(attrs={"class": "form-select"}),
            "resolution_type": forms.Select(attrs={"class": "form-select"}),
            "resolution_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "code_changes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "verified_by": forms.Select(attrs={"class": "form-select"}),
            "verified_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
        }


class RegressionTestForm(forms.ModelForm):
    """Form for regression test."""

    class Meta:
        model = RegressionTest
        fields = [  # noqa: RUF012
            "name",
            "description",
            "trigger",
            "test_suites",
            "environment",
            "status",
            "triggered_by",
            "release_candidate",
        ]
        widgets = {  # noqa: RUF012
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "trigger": forms.Select(attrs={"class": "form-select"}),
            "test_suites": forms.SelectMultiple(attrs={"class": "form-select"}),
            "environment": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=TestExecutionStatus.CHOICES,
            ),
            "triggered_by": forms.Select(attrs={"class": "form-select"}),
            "release_candidate": forms.Select(attrs={"class": "form-select"}),
        }


class UATSessionForm(forms.ModelForm):
    """Form for UAT session."""

    class Meta:
        model = UATSession
        fields = [  # noqa: RUF012
            "name",
            "description",
            "release_candidate",
            "status",
            "planned_start",
            "planned_end",
            "participants",
            "facilitator",
            "test_scenarios",
            "acceptance_criteria",
            "overall_result",
            "sign_off_by",
            "notes",
        ]
        widgets = {  # noqa: RUF012
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "release_candidate": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=UATSessionStatus.CHOICES,
            ),
            "planned_start": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "planned_end": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "participants": forms.SelectMultiple(attrs={"class": "form-select"}),
            "facilitator": forms.Select(attrs={"class": "form-select"}),
            "test_scenarios": forms.SelectMultiple(attrs={"class": "form-select"}),
            "acceptance_criteria": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "overall_result": forms.Select(attrs={"class": "form-select"}),
            "sign_off_by": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ReleaseCandidateForm(forms.ModelForm):
    """Form for release candidate."""

    class Meta:
        model = ReleaseCandidate
        fields = [  # noqa: RUF012
            "version",
            "name",
            "description",
            "status",
            "branch",
            "commit_hash",
            "build_number",
            "build_url",
            "changelog",
            "release_notes",
            "planned_release_date",
            "test_plan",
        ]
        widgets = {  # noqa: RUF012
            "version": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=ReleaseCandidateStatus.CHOICES,
            ),
            "branch": forms.TextInput(attrs={"class": "form-control"}),
            "commit_hash": forms.TextInput(attrs={"class": "form-control"}),
            "build_number": forms.TextInput(attrs={"class": "form-control"}),
            "build_url": forms.URLInput(attrs={"class": "form-control"}),
            "changelog": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "release_notes": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "planned_release_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "test_plan": forms.Select(attrs={"class": "form-select"}),
        }


class ReleaseApprovalForm(forms.ModelForm):
    """Form for release approval."""

    class Meta:
        model = ReleaseApproval
        fields = [  # noqa: RUF012
            "release_candidate",
            "approver",
            "role",
            "status",
            "conditions",
            "comments",
        ]
        widgets = {  # noqa: RUF012
            "release_candidate": forms.Select(attrs={"class": "form-select"}),
            "approver": forms.Select(attrs={"class": "form-select"}),
            "role": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=ReleaseApprovalStatus.CHOICES,
            ),
            "conditions": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "comments": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class QualityMetricForm(forms.ModelForm):
    """Form for quality metric."""

    class Meta:
        model = QualityMetric
        fields = [  # noqa: RUF012
            "metric_type",
            "name",
            "description",
            "module",
            "value",
            "target_value",
            "threshold_warning",
            "threshold_critical",
            "unit",
            "period_start",
            "period_end",
            "data_source",
            "metadata",
        ]
        widgets = {  # noqa: RUF012
            "metric_type": forms.Select(
                attrs={"class": "form-select"},
                choices=QualityMetricType.CHOICES,
            ),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "module": forms.TextInput(attrs={"class": "form-control"}),
            "value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "target_value": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "threshold_warning": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "threshold_critical": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "period_start": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "period_end": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "data_source": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "metadata": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class QualityDashboardForm(forms.ModelForm):
    """Form for quality dashboard."""

    class Meta:
        model = QualityDashboard
        fields = [  # noqa: RUF012
            "name",
            "description",
            "widgets",
            "layout",
            "is_default",
            "role_access",
            "refresh_interval",
            "owner",
        ]
        widgets = {  # noqa: RUF012
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "widgets": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "layout": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "role_access": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "refresh_interval": forms.NumberInput(attrs={"class": "form-control"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
        }


class QANotificationForm(forms.ModelForm):
    """Form for QA notification."""

    class Meta:
        model = QANotification
        fields = [  # noqa: RUF012
            "notification_type",
            "title",
            "message",
            "recipient",
            "related_object_type",
            "related_object_id",
            "priority",
        ]
        widgets = {  # noqa: RUF012
            "notification_type": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "recipient": forms.Select(attrs={"class": "form-select"}),
            "related_object_type": forms.TextInput(attrs={"class": "form-control"}),
            "related_object_id": forms.TextInput(attrs={"class": "form-control"}),
            "priority": forms.Select(
                attrs={"class": "form-select"},
                choices=TestPriority.CHOICES,
            ),
        }
