from django.contrib import admin
from django.utils.translation import gettext_lazy as _

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


class TestScenarioCaseInline(admin.TabularInline):
    model = TestScenarioCase
    extra = 0
    ordering = ["order"]  # noqa: RUF012
    autocomplete_fields = ["test_case"]  # noqa: RUF012


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 0
    fields = [  # noqa: RUF012
        "test_id",
        "title",
        "status",
        "priority",
        "category",
        "is_automated",
        "assigned_to",
    ]
    readonly_fields = ["test_id"]  # noqa: RUF012
    ordering = ["test_id"]  # noqa: RUF012


class TestSuiteInline(admin.TabularInline):
    model = TestSuite
    extra = 0
    fields = ["name", "status", "order", "module", "feature"]  # noqa: RUF012
    ordering = ["order", "name"]  # noqa: RUF012


class TestPlanInline(admin.TabularInline):
    model = TestPlan
    extra = 0
    fields = ["name", "version", "status", "start_date", "end_date"]  # noqa: RUF012
    ordering = ["-created_at"]  # noqa: RUF012


class TestExecutionInline(admin.TabularInline):
    model = TestExecution
    extra = 0
    fields = [  # noqa: RUF012
        "test_case",
        "environment",
        "status",
        "executed_by",
        "started_at",
        "completed_at",
    ]
    readonly_fields = ["started_at", "completed_at"]  # noqa: RUF012
    ordering = ["-started_at"]  # noqa: RUF012


class DefectAssignmentInline(admin.TabularInline):
    model = DefectAssignment
    extra = 0
    fields = [  # noqa: RUF012
        "assigned_to",
        "assigned_by",
        "assigned_at",
        "unassigned_at",
    ]
    readonly_fields = ["assigned_at"]  # noqa: RUF012
    ordering = ["-assigned_at"]  # noqa: RUF012


class DefectResolutionInline(admin.TabularInline):
    model = DefectResolution
    extra = 0
    fields = [  # noqa: RUF012
        "resolved_by",
        "resolution_type",
        "resolved_at",
        "verified_by",
        "verified_at",
    ]
    readonly_fields = ["resolved_at"]  # noqa: RUF012
    ordering = ["-resolved_at"]  # noqa: RUF012


class ReleaseApprovalInline(admin.TabularInline):
    model = ReleaseApproval
    extra = 0
    fields = ["approver", "role", "status", "approved_at", "conditions"]  # noqa: RUF012
    readonly_fields = ["approved_at"]  # noqa: RUF012
    ordering = ["-created_at"]  # noqa: RUF012


class UATSessionInline(admin.TabularInline):
    model = UATSession
    extra = 0
    fields = [  # noqa: RUF012
        "name",
        "status",
        "planned_start",
        "planned_end",
        "overall_result",
    ]
    ordering = ["-created_at"]  # noqa: RUF012


@admin.register(QAConfiguration)
class QAConfigurationAdmin(admin.ModelAdmin):
    list_display = ["pk", "is_active", "updated_at"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    fieldsets = (
        (
            _("Testing Policies"),
            {
                "fields": (
                    "testing_policies",
                    "quality_thresholds",
                    "code_coverage_targets",
                )
            },
        ),
        (
            _("Execution & Automation"),
            {
                "fields": (
                    "test_execution_schedules",
                    "automated_testing_config",
                    "regression_testing_rules",
                )
            },
        ),
        (
            _("Defects & Release"),
            {"fields": ("defect_severity_rules", "release_approval_workflows")},
        ),
        (
            _("UAT & Notifications"),
            {
                "fields": (
                    "uat_settings",
                    "test_notification_settings",
                    "test_retention_policies",
                    "quality_dashboards_config",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "is_active",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not QAConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TestEnvironment)
class TestEnvironmentAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "name",
        "environment_type",
        "base_url",
        "is_default",
        "is_active",
        "updated_at",
    ]
    list_filter = ["environment_type", "is_default", "is_active"]  # noqa: RUF012
    search_fields = ["name", "description", "base_url"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "environment_type",
                    "description",
                    "base_url",
                    "is_default",
                    "is_active",
                )
            },
        ),
        (
            _("Configuration"),
            {
                "fields": (
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
                )
            },
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )


@admin.register(TestDataSet)
class TestDataSetAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "name",
        "data_type",
        "version",
        "record_count",
        "size_bytes",
        "environment",
        "is_reproducible",
        "is_active",
    ]
    list_filter = [  # noqa: RUF012
        "data_type",
        "is_reproducible",
        "is_active",
        "environment",
    ]
    search_fields = ["name", "description", "version"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "checksum",
    ]
    autocomplete_fields = ["environment"]  # noqa: RUF012


class TestPlanAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "name",
        "version",
        "status",
        "start_date",
        "end_date",
        "approved_by",
        "created_at",
    ]
    list_filter = ["status", "release_candidate"]  # noqa: RUF012
    search_fields = ["name", "description", "version", "module"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "approved_at",
    ]
    autocomplete_fields = ["release_candidate", "approved_by"]  # noqa: RUF012
    inlines = [TestSuiteInline]  # noqa: RUF012

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "release_candidate", "approved_by", "created_by", "updated_by"
        )


class TestSuiteAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "name",
        "test_plan",
        "parent",
        "status",
        "order",
        "module",
        "feature",
    ]
    list_filter = ["status", "test_plan"]  # noqa: RUF012
    search_fields = ["name", "description", "module", "feature"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    autocomplete_fields = ["test_plan", "parent"]  # noqa: RUF012
    inlines = [TestCaseInline, TestSuiteInline]  # noqa: RUF012


class TestCaseAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "test_id",
        "title",
        "test_suite",
        "status",
        "priority",
        "category",
        "is_automated",
        "assigned_to",
    ]
    list_filter = [  # noqa: RUF012
        "status",
        "priority",
        "category",
        "test_type",
        "is_automated",
        "test_suite__test_plan",
    ]
    search_fields = [  # noqa: RUF012
        "test_id",
        "title",
        "description",
        "requirement_reference",
        "module",
        "feature",
    ]
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "last_executed",
        "last_result",
    ]
    autocomplete_fields = ["test_suite", "assigned_to", "reviewed_by"]  # noqa: RUF012
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "test_suite",
                    "test_id",
                    "title",
                    "description",
                    "status",
                    "priority",
                    "category",
                    "test_type",
                )
            },
        ),
        (
            _("Content"),
            {
                "fields": (
                    "preconditions",
                    "postconditions",
                    "steps",
                    "expected_results",
                )
            },
        ),
        (
            _("Automation"),
            {"fields": ("is_automated", "automation_script", "automation_framework")},
        ),
        (
            _("Assignment & Tracking"),
            {
                "fields": (
                    "module",
                    "feature",
                    "requirement_reference",
                    "estimated_duration",
                    "tags",
                    "assigned_to",
                    "reviewed_by",
                    "reviewed_at",
                    "last_executed",
                    "last_result",
                )
            },
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )


class TestScenarioAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "name",
        "test_plan",
        "scenario_type",
        "priority",
        "module",
        "feature",
    ]
    list_filter = ["scenario_type", "priority", "test_plan"]  # noqa: RUF012
    search_fields = ["name", "description", "module", "feature"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    autocomplete_fields = ["test_plan"]  # noqa: RUF012
    inlines = [TestScenarioCaseInline]  # noqa: RUF012


class TestResultInline(admin.TabularInline):
    model = TestResult
    extra = 0
    fields = [  # noqa: RUF012
        "step_number",
        "step_description",
        "expected_result",
        "actual_result",
        "status",
        "duration_seconds",
    ]
    readonly_fields = ["created_at", "updated_at"]  # noqa: RUF012
    ordering = ["step_number"]  # noqa: RUF012


class TestEvidenceInline(admin.TabularInline):
    model = TestEvidence
    extra = 0
    fields = [  # noqa: RUF012
        "evidence_type",
        "file_path",
        "file_name",
        "file_size",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]  # noqa: RUF012


class TestExecutionAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "test_case",
        "test_plan",
        "test_suite",
        "environment",
        "status",
        "executed_by",
        "started_at",
        "duration_seconds",
    ]
    list_filter = [  # noqa: RUF012
        "status",
        "is_regression",
        "test_plan",
        "test_suite",
        "environment",
    ]
    search_fields = [  # noqa: RUF012
        "test_case__test_id",
        "test_case__title",
        "error_message",
    ]
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "started_at",
        "completed_at",
    ]
    autocomplete_fields = [  # noqa: RUF012
        "test_case",
        "test_plan",
        "test_suite",
        "environment",
        "test_data_set",
        "executed_by",
        "defect",
    ]
    date_hierarchy = "started_at"
    inlines = [TestResultInline, TestEvidenceInline]  # noqa: RUF012


class TestResultAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "execution",
        "step_number",
        "status",
        "duration_seconds",
    ]
    list_filter = ["status"]  # noqa: RUF012
    search_fields = [  # noqa: RUF012
        "execution__test_case__test_id",
        "step_description",
    ]
    readonly_fields = ["created_at", "updated_at"]  # noqa: RUF012
    autocomplete_fields = ["execution"]  # noqa: RUF012


class TestEvidenceAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "execution",
        "evidence_type",
        "file_name",
        "file_size",
        "uploaded_by",
    ]
    list_filter = ["evidence_type"]  # noqa: RUF012
    search_fields = [  # noqa: RUF012
        "execution__test_case__test_id",
        "file_name",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]  # noqa: RUF012
    autocomplete_fields = ["execution", "uploaded_by"]  # noqa: RUF012


@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "defect_id",
        "title",
        "status",
        "severity",
        "priority",
        "module",
        "reported_by",
        "assigned_to",
        "created_at",
    ]
    list_filter = [  # noqa: RUF012
        "status",
        "severity",
        "priority",
        "module",
        "environment",
    ]
    search_fields = [  # noqa: RUF012
        "defect_id",
        "title",
        "description",
        "steps_to_reproduce",
        "module",
        "feature",
    ]
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "reported_by",
        "verified_at",
        "resolved_at",
        "closed_at",
    ]
    autocomplete_fields = [  # noqa: RUF012
        "environment",
        "test_execution",
        "test_case",
        "assigned_to",
        "verified_by",
        "resolved_by",
        "regression_tested_by",
        "closed_by",
    ]
    filter_horizontal = ["related_defects"]  # noqa: RUF012
    inlines = [DefectAssignmentInline, DefectResolutionInline]  # noqa: RUF012
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "defect_id",
                    "title",
                    "description",
                    "status",
                    "severity",
                    "priority",
                )
            },
        ),
        (
            _("Reproduction"),
            {"fields": ("steps_to_reproduce", "expected_result", "actual_result")},
        ),
        (
            _("Context"),
            {
                "fields": (
                    "module",
                    "feature",
                    "environment",
                    "test_execution",
                    "test_case",
                    "tags",
                )
            },
        ),
        (
            _("Assignment & Resolution"),
            {
                "fields": (
                    "reported_by",
                    "assigned_to",
                    "verified_by",
                    "verified_at",
                    "resolved_by",
                    "resolved_at",
                    "resolution_notes",
                    "regression_tested",
                    "regression_tested_by",
                    "regression_tested_at",
                    "closed_by",
                    "closed_at",
                )
            },
        ),
        (
            _("Attachments & Links"),
            {
                "fields": (
                    "audit_reference",
                    "screenshots",
                    "attachments",
                    "related_defects",
                )
            },
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )


class DefectAssignmentAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "defect",
        "assigned_to",
        "assigned_by",
        "assigned_at",
        "unassigned_at",
    ]
    list_filter = ["assigned_at"]  # noqa: RUF012
    search_fields = ["defect__defect_id", "defect__title"]  # noqa: RUF012
    readonly_fields = ["created_at", "updated_at", "assigned_at"]  # noqa: RUF012
    autocomplete_fields = ["defect", "assigned_to", "assigned_by"]  # noqa: RUF012


class DefectResolutionAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "defect",
        "resolved_by",
        "resolution_type",
        "resolved_at",
        "verified_by",
        "verified_at",
    ]
    list_filter = ["resolution_type", "resolved_at"]  # noqa: RUF012
    search_fields = [  # noqa: RUF012
        "defect__defect_id",
        "defect__title",
        "resolution_notes",
    ]
    readonly_fields = ["created_at", "updated_at", "resolved_at"]  # noqa: RUF012
    autocomplete_fields = ["defect", "resolved_by", "verified_by"]  # noqa: RUF012


@admin.register(RegressionTest)
class RegressionTestAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "name",
        "trigger",
        "status",
        "triggered_by",
        "started_at",
        "completed_at",
        "total_tests",
        "pass_rate",
    ]
    list_filter = ["trigger", "status", "environment"]  # noqa: RUF012
    search_fields = ["name", "description"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "started_at",
        "completed_at",
    ]
    autocomplete_fields = [  # noqa: RUF012
        "environment",
        "triggered_by",
        "release_candidate",
    ]
    filter_horizontal = ["test_suites"]  # noqa: RUF012


@admin.register(UATSession)
class UATSessionAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "name",
        "release_candidate",
        "status",
        "planned_start",
        "planned_end",
        "overall_result",
        "facilitator",
    ]
    list_filter = ["status", "release_candidate"]  # noqa: RUF012
    search_fields = ["name", "description", "acceptance_criteria"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    autocomplete_fields = [  # noqa: RUF012
        "release_candidate",
        "facilitator",
        "sign_off_by",
    ]
    filter_horizontal = ["participants", "test_scenarios"]  # noqa: RUF012
    inlines = []  # noqa: RUF012


@admin.register(ReleaseCandidate)
class ReleaseCandidateAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "version",
        "name",
        "status",
        "branch",
        "build_number",
        "planned_release_date",
        "status",
    ]
    list_filter = ["status", "branch"]  # noqa: RUF012
    search_fields = ["version", "name", "commit_hash", "build_number"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deployed_at",
        "rolled_back_at",
    ]
    autocomplete_fields = ["deployed_by", "test_plan"]  # noqa: RUF012
    inlines = [UATSessionInline, ReleaseApprovalInline, TestPlanInline]  # noqa: RUF012


class ReleaseApprovalAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "release_candidate",
        "approver",
        "role",
        "status",
        "approved_at",
    ]
    list_filter = ["status", "role"]  # noqa: RUF012
    search_fields = [  # noqa: RUF012
        "release_candidate__version",
        "approver__username",
        "comments",
    ]
    readonly_fields = ["created_at", "updated_at", "approved_at"]  # noqa: RUF012
    autocomplete_fields = ["release_candidate", "approver"]  # noqa: RUF012


@admin.register(QualityMetric)
class QualityMetricAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "name",
        "metric_type",
        "module",
        "value",
        "target_value",
        "unit",
        "period_end",
        "calculated_by",
    ]
    list_filter = ["metric_type", "module", "period_end"]  # noqa: RUF012
    search_fields = ["name", "description", "module"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "calculated_at",
    ]
    autocomplete_fields = ["calculated_by"]  # noqa: RUF012
    date_hierarchy = "period_end"


@admin.register(QualityDashboard)
class QualityDashboardAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default", "refresh_interval", "owner"]  # noqa: RUF012
    list_filter = ["is_default"]  # noqa: RUF012
    search_fields = ["name", "description"]  # noqa: RUF012
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    autocomplete_fields = ["owner"]  # noqa: RUF012
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("name", "description", "is_default", "owner")},
        ),
        (
            _("Configuration"),
            {"fields": ("widgets", "layout", "role_access", "refresh_interval")},
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )


@admin.register(QANotification)
class QANotificationAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "notification_type",
        "title",
        "recipient",
        "priority",
        "is_read",
        "created_at",
    ]
    list_filter = ["notification_type", "priority", "is_read"]  # noqa: RUF012
    search_fields = [  # noqa: RUF012
        "title",
        "message",
        "recipient__username",
        "related_object_type",
        "related_object_id",
    ]
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "read_at",
    ]
    autocomplete_fields = ["recipient"]  # noqa: RUF012
    date_hierarchy = "created_at"


@admin.register(QATimeline)
class QATimelineAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "event_type",
        "module",
        "test_type",
        "status",
        "result",
        "tester",
        "created_at",
    ]
    list_filter = ["event_type", "test_type", "status", "module"]  # noqa: RUF012
    search_fields = [  # noqa: RUF012
        "module",
        "tester__username",
        "related_object_type",
        "related_object_id",
        "defect_reference",
        "audit_reference",
    ]
    readonly_fields = [  # noqa: RUF012
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    autocomplete_fields = ["tester"]  # noqa: RUF012
    date_hierarchy = "created_at"


@admin.register(QAAuditReference)
class QAAuditReferenceAdmin(admin.ModelAdmin):
    list_display = [  # noqa: RUF012
        "reference_id",
        "event_type",
        "module",
        "user",
        "timestamp",
    ]
    list_filter = ["event_type", "module"]  # noqa: RUF012
    search_fields = [  # noqa: RUF012
        "reference_id",
        "event_type",
        "module",
        "user__username",
    ]
    readonly_fields = [  # noqa: RUF012
        "reference_id",
        "event_type",
        "module",
        "user",
        "ip_address",
        "user_agent",
        "before_values",
        "after_values",
        "timestamp",
    ]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(TestPlan, TestPlanAdmin)
admin.site.register(TestSuite, TestSuiteAdmin)
admin.site.register(TestCase, TestCaseAdmin)
admin.site.register(TestScenario, TestScenarioAdmin)
admin.site.register(TestScenarioCase)
admin.site.register(TestExecution, TestExecutionAdmin)
admin.site.register(DefectAssignment, DefectAssignmentAdmin)
admin.site.register(DefectResolution, DefectResolutionAdmin)
