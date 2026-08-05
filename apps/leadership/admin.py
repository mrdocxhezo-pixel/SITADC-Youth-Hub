"""Django admin registrations for the Leadership Management module."""

from django.contrib import admin

from .models import (
    CoachingRecord,
    DisciplinaryRecord,
    LeadershipAppointment,
    LeadershipAttendance,
    LeadershipAuditRecord,
    LeadershipDocument,
    LeadershipGoal,
    LeadershipKPI,
    LeadershipLeave,
    LeadershipProfile,
    LeadershipScorecard,
    LeadershipStatusHistory,
    LeadershipTask,
    MentorshipRecord,
    PerformanceReview,
    RecognitionRecord,
    SuccessionPlan,
)


@admin.register(LeadershipProfile)
class LeadershipProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "reference_number",
        "leadership_level",
        "status",
        "organizational_unit",
    )
    search_fields = (
        "reference_number",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    list_filter = ("status", "leadership_level")
    readonly_fields = ("reference_number",)


@admin.register(LeadershipAppointment)
class LeadershipAppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "position",
        "appointment_type",
        "status",
        "term_start",
        "term_end",
    )
    search_fields = (
        "profile__reference_number",
        "profile__user__email",
    )
    list_filter = ("status", "appointment_type")
    readonly_fields = ("reference_number",)


@admin.register(LeadershipStatusHistory)
class LeadershipStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "from_status",
        "to_status",
        "changed_at",
        "changed_by",
    )
    list_filter = ("to_status",)


@admin.register(LeadershipAttendance)
class LeadershipAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "attendance_date",
        "attendance_type",
        "activity_name",
        "status",
    )
    list_filter = ("status", "attendance_type")
    search_fields = ("profile__user__email",)


@admin.register(LeadershipLeave)
class LeadershipLeaveAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "leave_type",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("status", "leave_type")


@admin.register(LeadershipTask)
class LeadershipTaskAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "title",
        "priority",
        "status",
        "due_date",
    )
    list_filter = ("status", "priority")


@admin.register(LeadershipGoal)
class LeadershipGoalAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "title",
        "status",
        "due_date",
        "current_value",
        "target_value",
    )
    list_filter = ("status",)


@admin.register(LeadershipKPI)
class LeadershipKPIAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "name",
        "category",
        "target_value",
        "actual_value",
        "status",
    )
    list_filter = ("status", "category")


@admin.register(CoachingRecord)
class CoachingRecordAdmin(admin.ModelAdmin):
    list_display = (
        "leader",
        "coach",
        "category",
        "session_date",
        "is_confidential",
    )
    list_filter = ("category", "is_confidential")


@admin.register(MentorshipRecord)
class MentorshipRecordAdmin(admin.ModelAdmin):
    list_display = (
        "mentee",
        "mentor",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("status",)


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "reviewer",
        "review_cycle",
        "overall_rating",
        "status",
    )
    list_filter = ("status", "review_cycle")


@admin.register(RecognitionRecord)
class RecognitionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "award_name",
        "category",
        "date_awarded",
    )
    list_filter = ("category",)


@admin.register(DisciplinaryRecord)
class DisciplinaryRecordAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "record_type",
        "incident_date",
        "status",
        "is_confidential",
    )
    list_filter = ("record_type", "status")


@admin.register(SuccessionPlan)
class SuccessionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "position",
        "current_holder",
        "readiness_level",
        "risk",
        "is_active",
    )
    list_filter = ("readiness_level", "risk", "is_active")


@admin.register(LeadershipDocument)
class LeadershipDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "category",
        "title",
        "version",
        "confidentiality",
    )
    list_filter = ("category", "confidentiality")


@admin.register(LeadershipScorecard)
class LeadershipScorecardAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "period_start",
        "period_end",
        "overall_rating",
        "status",
    )
    list_filter = ("status",)


@admin.register(LeadershipAuditRecord)
class LeadershipAuditRecordAdmin(admin.ModelAdmin):
    list_display = (
        "entity_type",
        "entity_id",
        "action",
        "changed_by",
    )
    list_filter = ("action", "entity_type")
    search_fields = (
        "entity_id",
        "changed_by__email",
    )
