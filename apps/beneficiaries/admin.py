"""Administrative inspection and configuration for beneficiary records."""

# ruff: noqa: RUF012 - Django admin options are declarative class attributes.

from django.contrib import admin

from .models import (
    AttendanceRecord,
    Beneficiary,
    BeneficiaryAssessment,
    BeneficiaryAuditRecord,
    BeneficiaryCommunication,
    BeneficiaryDocument,
    BeneficiaryEnrollment,
    BeneficiaryGroup,
    BeneficiaryHousehold,
    BeneficiaryParticipation,
    BeneficiaryReferenceData,
    BeneficiaryStatusHistory,
    CaseNote,
    ConsentRecord,
    DuplicateReviewRecord,
    ExitRecord,
    FeedbackRecord,
    FollowUpVisit,
    GroupMembership,
    GuardianRecord,
    HouseholdMember,
    OutcomeRecord,
    Referral,
    SafeguardingRecord,
    ServiceDeliveryRecord,
    SupportPlan,
    TransferRecord,
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


@admin.register(BeneficiaryReferenceData)
class BeneficiaryReferenceDataAdmin(admin.ModelAdmin):
    list_display = ("kind", "code", "name", "active", "order")
    list_filter = ("kind", "active")
    search_fields = ("code", "name")
    ordering = ("kind", "order", "name")


@admin.register(Beneficiary)
class BeneficiaryAdmin(ServiceManagedAdmin):
    list_display = (
        "reference_number",
        "full_name",
        "category",
        "status",
        "confidentiality",
        "district",
    )
    list_filter = ("status", "confidentiality", "category", "district")
    search_fields = ("reference_number", "full_name", "email", "phone_primary")


@admin.register(BeneficiaryStatusHistory)
class BeneficiaryStatusHistoryAdmin(ServiceManagedAdmin):
    list_display = (
        "beneficiary",
        "from_status",
        "to_status",
        "changed_by",
        "created_at",
    )
    list_filter = ("to_status",)


@admin.register(BeneficiaryAuditRecord)
class BeneficiaryAuditRecordAdmin(ServiceManagedAdmin):
    list_display = ("entity_type", "entity_id", "action", "changed_by", "changed_at")
    list_filter = ("action", "entity_type")


@admin.register(BeneficiaryHousehold)
class BeneficiaryHouseholdAdmin(ServiceManagedAdmin):
    list_display = (
        "reference_number",
        "household_name",
        "head",
        "status",
        "created_at",
    )
    list_filter = ("status",)


@admin.register(BeneficiaryGroup)
class BeneficiaryGroupAdmin(ServiceManagedAdmin):
    list_display = ("reference_number", "group_name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("reference_number", "group_name")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(ServiceManagedAdmin):
    list_display = ("beneficiary", "consent_type", "status", "recorded_on", "valid_to")
    list_filter = ("consent_type", "status")


@admin.register(SafeguardingRecord)
class SafeguardingRecordAdmin(ServiceManagedAdmin):
    list_display = ("beneficiary", "status", "reported_on", "reported_by")
    list_filter = ("status",)


@admin.register(BeneficiaryDocument)
class BeneficiaryDocumentAdmin(ServiceManagedAdmin):
    list_display = ("title", "beneficiary", "status", "uploaded_by", "created_at")
    list_filter = ("status", "document_type")


@admin.register(Referral)
class ReferralAdmin(ServiceManagedAdmin):
    list_display = ("reference_number", "beneficiary", "status", "referral_date")
    list_filter = ("status", "referral_type")


@admin.register(ServiceDeliveryRecord)
class ServiceDeliveryRecordAdmin(ServiceManagedAdmin):
    list_display = ("reference_number", "beneficiary", "status", "service_date")
    list_filter = ("status",)


@admin.register(OutcomeRecord)
class OutcomeRecordAdmin(ServiceManagedAdmin):
    list_display = ("beneficiary", "status", "measurement_date")
    list_filter = ("status",)


@admin.register(ExitRecord)
class ExitRecordAdmin(ServiceManagedAdmin):
    list_display = ("beneficiary", "exit_status", "exit_date", "reason")
    list_filter = ("exit_status",)


@admin.register(TransferRecord)
class TransferRecordAdmin(ServiceManagedAdmin):
    list_display = ("beneficiary", "status", "transfer_date")
    list_filter = ("status",)


@admin.register(DuplicateReviewRecord)
class DuplicateReviewRecordAdmin(ServiceManagedAdmin):
    list_display = ("review_status", "reviewed_by", "created_at")
    list_filter = ("review_status",)


OPERATIONAL_MODELS = (
    GuardianRecord,
    HouseholdMember,
    GroupMembership,
    BeneficiaryEnrollment,
    BeneficiaryParticipation,
    AttendanceRecord,
    CaseNote,
    FollowUpVisit,
    BeneficiaryAssessment,
    SupportPlan,
    BeneficiaryCommunication,
    FeedbackRecord,
)

admin.site.register(OPERATIONAL_MODELS, ServiceManagedAdmin)
