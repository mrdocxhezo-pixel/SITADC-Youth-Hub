"""Administrative inspection and configuration for MEAL records."""

# ruff: noqa: RUF012 - Django admin options are declarative class attributes.

from django.contrib import admin

from .models import (
    BestPractice,
    Complaint,
    CorrectiveAction,
    DataCollectionPlan,
    DataCollectionTool,
    DataQualityAssessment,
    DataSource,
    DataSubmission,
    DQADimensionScore,
    Evaluation,
    EvaluationRecommendation,
    Feedback,
    Indicator,
    IndicatorBaseline,
    IndicatorCategory,
    IndicatorResult,
    IndicatorTarget,
    LearningLog,
    LessonLearned,
    LogframeRow,
    LogicalFramework,
    MEALAuditRecord,
    MEALReferenceData,
    MEALReport,
    MEALStatusHistory,
    MonitoringFinding,
    MonitoringPlan,
    MonitoringVisit,
    OrganizationalKPI,
    OutcomeHarvest,
    PerformanceScorecard,
    ResultsFramework,
    ResultStatement,
    ScorecardDimension,
    TheoryOfChange,
)


class ServiceManagedAdmin(admin.ModelAdmin):
    """Make operational data read-only so services cannot be bypassed."""

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MEALReferenceData)
class MEALReferenceDataAdmin(admin.ModelAdmin):
    list_display = ("kind", "code", "name", "active", "order")
    list_filter = ("kind", "active")
    search_fields = ("code", "name")
    ordering = ("kind", "order", "name")


@admin.register(IndicatorCategory)
class IndicatorCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "source_type", "is_active")
    list_filter = ("source_type", "is_active")
    search_fields = ("name", "code")


@admin.register(DataCollectionTool)
class DataCollectionToolAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tool_type", "is_active")
    list_filter = ("tool_type", "is_active")
    search_fields = ("name", "code")


@admin.register(TheoryOfChange)
class TheoryOfChangeAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "title", "program", "status")
    list_filter = ("status",)
    search_fields = ("reference_number", "title")


@admin.register(ResultsFramework)
class ResultsFrameworkAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "title", "program", "status")
    list_filter = ("status",)
    search_fields = ("reference_number", "title")


@admin.register(LogicalFramework)
class LogicalFrameworkAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "title", "program", "status")
    list_filter = ("status",)
    search_fields = ("reference_number", "title")


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "title", "code", "indicator_type", "status")
    list_filter = ("indicator_type", "status")
    search_fields = ("reference_number", "title", "code")


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "title", "evaluation_type", "status")
    list_filter = ("evaluation_type", "status")
    search_fields = ("reference_number", "title")


@admin.register(MonitoringVisit)
class MonitoringVisitAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "community", "visit_date", "status")
    list_filter = ("status",)
    search_fields = ("reference_number", "community")


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "source", "priority", "status")
    list_filter = ("priority", "status")
    search_fields = ("reference_number", "description")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "source", "status")
    list_filter = ("status",)
    search_fields = ("reference_number", "description")


@admin.register(MEALReport)
class MEALReportAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "title", "report_type", "status")
    list_filter = ("report_type", "status")
    search_fields = ("reference_number", "title")


@admin.register(MEALStatusHistory)
class MEALStatusHistoryAdmin(ServiceManagedAdmin):
    list_display = (
        "entity_type",
        "entity_id",
        "action",
        "from_status",
        "to_status",
        "created_at",
    )
    list_filter = ("entity_type", "action")


@admin.register(MEALAuditRecord)
class MEALAuditRecordAdmin(ServiceManagedAdmin):
    list_display = ("action", "entity_type", "entity_id", "created_at")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_id",)


OPERATIONAL_MODELS = (
    ResultStatement,
    LogframeRow,
    IndicatorBaseline,
    IndicatorTarget,
    IndicatorResult,
    DataCollectionPlan,
    DataSubmission,
    MonitoringPlan,
    MonitoringFinding,
    CorrectiveAction,
    EvaluationRecommendation,
    DataQualityAssessment,
    DQADimensionScore,
    OutcomeHarvest,
    LearningLog,
    BestPractice,
    LessonLearned,
    OrganizationalKPI,
    PerformanceScorecard,
    ScorecardDimension,
)

admin.site.register(OPERATIONAL_MODELS, ServiceManagedAdmin)
