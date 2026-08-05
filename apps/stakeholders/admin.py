"""Administrative inspection and configuration for stakeholder records."""

# ruff: noqa: RUF012 - Django admin options are declarative class attributes.

from django.contrib import admin

from .models import (
    Stakeholder,
    StakeholderAccessGrant,
    StakeholderActionItem,
    StakeholderAgreement,
    StakeholderAgreementRenewal,
    StakeholderAgreementVersion,
    StakeholderAssessment,
    StakeholderCommitment,
    StakeholderCommunication,
    StakeholderConflictOfInterest,
    StakeholderContact,
    StakeholderContribution,
    StakeholderDocument,
    StakeholderDueDiligence,
    StakeholderDuplicateReview,
    StakeholderEngagement,
    StakeholderEngagementPlan,
    StakeholderNote,
    StakeholderNoteVersion,
    StakeholderPerformanceDimension,
    StakeholderPerformanceReview,
    StakeholderPerformanceScore,
    StakeholderReferenceData,
    StakeholderRisk,
    StakeholderStatusHistory,
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


@admin.register(StakeholderReferenceData)
class StakeholderReferenceDataAdmin(admin.ModelAdmin):
    list_display = ("kind", "code", "name", "active", "order")
    list_filter = ("kind", "active")
    search_fields = ("code", "name")
    ordering = ("kind", "order", "name")


@admin.register(StakeholderPerformanceDimension)
class StakeholderPerformanceDimensionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "weight", "active", "order")
    list_filter = ("active",)
    search_fields = ("code", "name")


@admin.register(Stakeholder)
class StakeholderAdmin(ServiceManagedAdmin):
    list_display = (
        "reference_number",
        "legal_name",
        "entity_type",
        "status",
        "confidentiality",
        "province_or_region",
    )
    list_filter = ("status", "entity_type", "confidentiality", "province_or_region")
    search_fields = ("reference_number", "legal_name", "registration_number")


@admin.register(StakeholderAgreement)
class StakeholderAgreementAdmin(ServiceManagedAdmin):
    list_display = ("reference_number", "title", "stakeholder", "status", "expiry_date")
    list_filter = ("status", "agreement_type")
    search_fields = ("reference_number", "title", "stakeholder__legal_name")


@admin.register(StakeholderActionItem)
class StakeholderActionAdmin(ServiceManagedAdmin):
    list_display = ("title", "stakeholder", "assigned_to", "due_date", "status")
    list_filter = ("status", "priority")


@admin.register(StakeholderStatusHistory)
class StakeholderStatusHistoryAdmin(ServiceManagedAdmin):
    list_display = (
        "stakeholder",
        "from_status",
        "to_status",
        "changed_by",
        "created_at",
    )
    list_filter = ("to_status",)


OPERATIONAL_MODELS = (
    StakeholderAccessGrant,
    StakeholderAgreementRenewal,
    StakeholderAgreementVersion,
    StakeholderAssessment,
    StakeholderCommunication,
    StakeholderCommitment,
    StakeholderConflictOfInterest,
    StakeholderContact,
    StakeholderContribution,
    StakeholderDocument,
    StakeholderDueDiligence,
    StakeholderDuplicateReview,
    StakeholderEngagement,
    StakeholderEngagementPlan,
    StakeholderNote,
    StakeholderNoteVersion,
    StakeholderPerformanceReview,
    StakeholderPerformanceScore,
    StakeholderRisk,
)

admin.site.register(OPERATIONAL_MODELS, ServiceManagedAdmin)
