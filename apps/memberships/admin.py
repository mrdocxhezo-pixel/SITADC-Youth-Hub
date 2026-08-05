"""
Admin registration for the membership management module.
"""

from django.contrib import admin

from .models import (
    AlumniRecord,
    MemberBenefitAssignment,
    MemberCommittee,
    MemberCommitteeAssignment,
    MemberComplaint,
    MemberDisciplinaryRecord,
    MemberInterest,
    MemberLeave,
    MemberOrganizationAssignment,
    MemberParticipation,
    MemberProfile,
    MemberRecognition,
    MembershipApplication,
    MembershipAttendance,
    MembershipAuditRecord,
    MembershipBenefit,
    MembershipCard,
    MembershipCategory,
    MembershipCommunication,
    MembershipDocument,
    MembershipExit,
    MembershipFee,
    MembershipFeeAdjustment,
    MembershipLevel,
    MembershipPayment,
    MembershipRenewal,
    MembershipStatus,
    MembershipStatusHistory,
    MembershipSuspension,
    MembershipTermination,
    MembershipTransfer,
    MembershipType,
    MembershipUpgrade,
    MemberSkill,
    MemberTrainingRecord,
    RenewalRule,
)


@admin.register(MembershipCategory)
class MembershipCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "is_active",
        "sort_order",
        "default_fee_amount",
        "currency",
    ]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]
    ordering = ["sort_order", "name"]


@admin.register(MembershipType)
class MembershipTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "sort_order"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(MembershipLevel)
class MembershipLevelAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "sort_order"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(MembershipStatus)
class MembershipStatusAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "sort_order"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(MembershipBenefit)
class MembershipBenefitAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "sort_order"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(RenewalRule)
class RenewalRuleAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "is_active",
        "notice_period_days",
        "grace_period_days",
        "renewal_period_months",
        "auto_expire_lapsed_members",
    ]


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = [
        "membership_id",
        "user",
        "category",
        "membership_type",
        "level",
        "status",
        "district",
        "date_joined",
        "expiry_date",
    ]
    list_filter = ["status", "category", "membership_type", "level", "gender"]
    search_fields = [
        "membership_id",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone_primary",
        "national_id",
    ]
    readonly_fields = ["membership_id", "created_at", "updated_at"]


@admin.register(MembershipApplication)
class MembershipApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "first_name",
        "last_name",
        "email",
        "category",
        "status",
        "created_at",
    ]
    list_filter = ["status", "category", "membership_type"]
    search_fields = ["reference_number", "first_name", "last_name", "email"]
    readonly_fields = ["reference_number", "created_at", "updated_at"]


@admin.register(MembershipRenewal)
class MembershipRenewalAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "previous_expiry",
        "new_expiry",
        "status",
        "payment_status",
        "created_at",
    ]
    list_filter = ["status", "payment_status"]
    search_fields = ["member__membership_id", "member__user__email"]


@admin.register(MembershipUpgrade)
class MembershipUpgradeAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "from_category",
        "to_category",
        "effective_date",
        "status",
    ]
    list_filter = ["status"]
    search_fields = ["member__membership_id"]


@admin.register(MembershipTransfer)
class MembershipTransferAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "from_district",
        "to_district",
        "effective_date",
        "status",
    ]
    list_filter = ["status"]
    search_fields = ["member__membership_id", "member__user__email"]


@admin.register(MembershipSuspension)
class MembershipSuspensionAdmin(admin.ModelAdmin):
    list_display = ["member", "effective_date", "review_date", "is_active", "lifted_at"]
    list_filter = ["is_active"]
    search_fields = ["member__membership_id"]


@admin.register(MembershipTermination)
class MembershipTerminationAdmin(admin.ModelAdmin):
    list_display = ["member", "reason", "effective_date", "authorized_by", "created_at"]
    list_filter = ["reason"]
    search_fields = ["member__membership_id"]
    readonly_fields = [
        "member",
        "reason",
        "reason_detail",
        "effective_date",
        "authorized_by",
        "created_at",
        "updated_at",
        "notes",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MembershipExit)
class MembershipExitAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "exit_type",
        "effective_date",
        "status",
        "transition_to_alumni",
    ]
    list_filter = ["status", "exit_type", "transition_to_alumni"]
    search_fields = ["member__membership_id"]


@admin.register(AlumniRecord)
class AlumniRecordAdmin(admin.ModelAdmin):
    list_display = ["member", "alumni_since", "previous_category", "rejoining_eligible"]
    list_filter = ["rejoining_eligible", "alumni_engagement"]
    search_fields = ["member__membership_id", "member__user__email"]


@admin.register(MembershipAttendance)
class MembershipAttendanceAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "activity_name",
        "activity_type",
        "activity_date",
        "status",
    ]
    list_filter = ["status", "activity_type", "activity_date"]
    search_fields = ["member__membership_id", "activity_name"]


@admin.register(MemberParticipation)
class MemberParticipationAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "activity_name",
        "participation_type",
        "start_date",
        "status",
    ]
    list_filter = ["status", "participation_type"]
    search_fields = ["member__membership_id", "activity_name"]


@admin.register(MemberCommittee)
class MemberCommitteeAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(MemberCommitteeAssignment)
class MemberCommitteeAssignmentAdmin(admin.ModelAdmin):
    list_display = ["member", "committee", "position", "appointment_date", "status"]
    list_filter = ["status", "committee"]
    search_fields = ["member__membership_id", "committee__name"]


@admin.register(MembershipFee)
class MembershipFeeAdmin(admin.ModelAdmin):
    list_display = [
        "category",
        "fee_name",
        "amount",
        "currency",
        "billing_frequency_months",
        "is_active",
    ]
    list_filter = ["is_active", "currency", "category"]
    search_fields = ["category__name", "fee_name"]


@admin.register(MembershipPayment)
class MembershipPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "receipt_number",
        "member",
        "amount",
        "payment_method",
        "payment_date",
        "status",
    ]
    list_filter = ["status", "payment_method", "payment_date"]
    search_fields = ["receipt_number", "member__membership_id", "transaction_reference"]
    readonly_fields = ["receipt_number", "created_at", "updated_at"]


@admin.register(MembershipFeeAdjustment)
class MembershipFeeAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "adjustment_type",
        "amount",
        "percentage",
        "effective_from",
        "status",
    ]
    list_filter = ["status", "adjustment_type"]
    search_fields = ["member__membership_id"]


@admin.register(MemberLeave)
class MemberLeaveAdmin(admin.ModelAdmin):
    list_display = ["member", "leave_type", "start_date", "end_date", "status"]
    list_filter = ["status", "leave_type"]
    search_fields = ["member__membership_id"]


@admin.register(MemberComplaint)
class MemberComplaintAdmin(admin.ModelAdmin):
    list_display = ["member", "complaint_type", "status", "created_at", "resolved_at"]
    list_filter = ["status", "complaint_type"]
    search_fields = ["member__membership_id", "description"]


@admin.register(MemberDisciplinaryRecord)
class MemberDisciplinaryRecordAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "disciplinary_type",
        "incident_date",
        "status",
        "is_confidential",
    ]
    list_filter = ["status", "disciplinary_type", "is_confidential"]
    search_fields = ["member__membership_id"]


@admin.register(MembershipDocument)
class MembershipDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "title",
        "category",
        "status",
        "version",
        "confidentiality",
    ]
    list_filter = ["status", "category", "confidentiality"]
    search_fields = ["member__membership_id", "title"]


@admin.register(MembershipCard)
class MembershipCardAdmin(admin.ModelAdmin):
    list_display = ["card_number", "member", "issue_date", "expiry_date", "status"]
    list_filter = ["status", "issue_date"]
    search_fields = ["card_number", "member__membership_id"]
    readonly_fields = [
        "card_number",
        "verification_code",
        "issue_date",
        "created_at",
        "updated_at",
    ]


@admin.register(MemberBenefitAssignment)
class MemberBenefitAssignmentAdmin(admin.ModelAdmin):
    list_display = ["member", "benefit", "granted_at", "expires_at", "status"]
    list_filter = ["status"]
    search_fields = ["member__membership_id", "benefit__name"]


@admin.register(MemberOrganizationAssignment)
class MemberOrganizationAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "organizational_unit",
        "assignment_type",
        "effective_from",
        "is_primary",
        "status",
    ]
    list_filter = ["status", "is_primary"]
    search_fields = ["member__membership_id"]


@admin.register(MembershipCommunication)
class MembershipCommunicationAdmin(admin.ModelAdmin):
    list_display = [
        "subject",
        "communication_type",
        "status",
        "scheduled_for",
        "sent_at",
        "sent_by",
    ]
    list_filter = ["status", "communication_type"]
    search_fields = ["subject", "body"]


@admin.register(MemberSkill)
class MemberSkillAdmin(admin.ModelAdmin):
    list_display = ["member", "name", "proficiency"]
    search_fields = ["member__membership_id", "name"]


@admin.register(MemberInterest)
class MemberInterestAdmin(admin.ModelAdmin):
    list_display = ["member", "name"]
    search_fields = ["member__membership_id", "name"]


@admin.register(MemberTrainingRecord)
class MemberTrainingRecordAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "title",
        "provider",
        "start_date",
        "completion_date",
        "certificate_issued",
    ]
    list_filter = ["certificate_issued"]
    search_fields = ["member__membership_id", "title"]


@admin.register(MemberRecognition)
class MemberRecognitionAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "title",
        "recognition_type",
        "award_date",
        "issuing_authority",
    ]
    list_filter = ["recognition_type", "award_date"]
    search_fields = ["member__membership_id", "title"]


@admin.register(MembershipStatusHistory)
class MembershipStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["member", "from_status", "to_status", "changed_by", "created_at"]
    list_filter = ["to_status"]
    search_fields = ["member__membership_id"]
    readonly_fields = [
        "member",
        "from_status",
        "to_status",
        "changed_by",
        "reason",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MembershipAuditRecord)
class MembershipAuditRecordAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "entity_id", "action", "changed_by", "created_at"]
    list_filter = ["action", "entity_type"]
    search_fields = ["entity_id", "entity_type"]
    readonly_fields = [
        "entity_type",
        "entity_id",
        "action",
        "changed_by",
        "from_data",
        "to_data",
        "ip_address",
        "notes",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
