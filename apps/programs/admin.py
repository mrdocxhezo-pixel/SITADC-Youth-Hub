"""Administrative inspection and configuration for program records."""

# ruff: noqa: RUF012 - Django admin options are declarative class attributes.

from django.contrib import admin

from .models import (
    Activity,
    BeneficiaryParticipation,
    BeneficiaryRecord,
    ChangeRequest,
    Deliverable,
    EvidenceRecord,
    EvidenceVersion,
    Issue,
    LessonsLearned,
    Milestone,
    ProcurementRequest,
    Program,
    ProgramBudget,
    ProgramBudgetLineItem,
    ProgramDocument,
    ProgramEvaluation,
    ProgramIndicator,
    ProgramPortfolio,
    ProgramReferenceData,
    ProgramRisk,
    ProgramStakeholderLink,
    ProgramStatusHistory,
    ProgramTeamMember,
    ProgressUpdate,
    Project,
    ProjectClosure,
    ProjectReport,
    ProjectResult,
    ProjectStatusHistory,
    ProjectTimeline,
    ResourceAllocation,
    Task,
    WBSNode,
    WorkPlan,
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


@admin.register(ProgramReferenceData)
class ProgramReferenceDataAdmin(admin.ModelAdmin):
    list_display = ("kind", "code", "name", "active", "order")
    list_filter = ("kind", "active")
    search_fields = ("code", "name")
    ordering = ("kind", "order", "name")


@admin.register(ProgramPortfolio)
class ProgramPortfolioAdmin(admin.ModelAdmin):
    list_display = ("name", "reference_number", "status", "portfolio_manager")
    list_filter = ("status",)
    search_fields = ("name", "reference_number")


@admin.register(Program)
class ProgramAdmin(ServiceManagedAdmin):
    list_display = (
        "reference_number",
        "title",
        "status",
        "priority",
        "program_manager",
    )
    list_filter = ("status", "priority")
    search_fields = ("reference_number", "title", "short_title")


@admin.register(Project)
class ProjectAdmin(ServiceManagedAdmin):
    list_display = (
        "reference_number",
        "title",
        "program",
        "status",
        "project_manager",
    )
    list_filter = ("status",)
    search_fields = ("reference_number", "title", "program__title")


@admin.register(ProgramStatusHistory)
class ProgramStatusHistoryAdmin(ServiceManagedAdmin):
    list_display = ("program", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status",)


@admin.register(ProjectStatusHistory)
class ProjectStatusHistoryAdmin(ServiceManagedAdmin):
    list_display = ("project", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status",)


OPERATIONAL_MODELS = (
    Activity,
    BeneficiaryParticipation,
    BeneficiaryRecord,
    ChangeRequest,
    Deliverable,
    EvidenceRecord,
    EvidenceVersion,
    Issue,
    LessonsLearned,
    Milestone,
    ProcurementRequest,
    ProgramBudget,
    ProgramBudgetLineItem,
    ProgramDocument,
    ProgramEvaluation,
    ProgramIndicator,
    ProgramRisk,
    ProgramStakeholderLink,
    ProgramTeamMember,
    ProgressUpdate,
    ProjectClosure,
    ProjectReport,
    ProjectResult,
    ProjectTimeline,
    ResourceAllocation,
    Task,
    WBSNode,
    WorkPlan,
)

admin.site.register(OPERATIONAL_MODELS, ServiceManagedAdmin)
