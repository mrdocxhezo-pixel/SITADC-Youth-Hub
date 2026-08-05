"""
Admin registration for the volunteer management module.
"""

# ruff: noqa: RUF012 - Django admin options are declarative class attributes.

from typing import Protocol, cast

from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from .models import (
    VolunteerActivityLog,
    VolunteerApplication,
    VolunteerAssignment,
    VolunteerAttendance,
    VolunteerAuditRecord,
    VolunteerCategory,
    VolunteerCommunication,
    VolunteerDeploymentHistory,
    VolunteerDisciplinaryRecord,
    VolunteerDocument,
    VolunteerExit,
    VolunteerInterest,
    VolunteerInterview,
    VolunteerLeave,
    VolunteerLevel,
    VolunteerOnboarding,
    VolunteerPerformance,
    VolunteerProfile,
    VolunteerRecognition,
    VolunteerRecruitment,
    VolunteerScreening,
    VolunteerSkill,
    VolunteerStatusHistory,
    VolunteerTraining,
    VolunteerType,
    VolunteerWelfare,
)


class _ModelAdminProtocol(Protocol):
    model: type[models.Model]


class ServiceManagedAdminMixin:
    """Prevent admin writes that would bypass audited domain services."""

    def get_readonly_fields(
        self, request: HttpRequest, obj: models.Model | None = None
    ) -> list[str]:
        model = cast(_ModelAdminProtocol, self).model
        return [field.name for field in model._meta.fields]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: models.Model | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: models.Model | None = None
    ) -> bool:
        return False


@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = [
        "reference_number",
        "user",
        "category",
        "volunteer_type",
        "status",
        "region",
        "district",
    ]
    list_filter = ["status", "category", "volunteer_type", "volunteer_level", "region"]
    search_fields = [
        "reference_number",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone_number",
    ]
    readonly_fields = ["reference_number", "created_at", "updated_at"]


@admin.register(VolunteerRecruitment)
class VolunteerRecruitmentAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = [
        "reference_number",
        "title",
        "category",
        "vacancies",
        "application_deadline",
        "status",
    ]
    list_filter = ["status", "category"]
    search_fields = ["reference_number", "title"]
    readonly_fields = ["reference_number", "created_at", "updated_at"]


@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = [
        "reference_number",
        "applicant_name",
        "email",
        "category",
        "status",
        "created_at",
    ]
    list_filter = ["status", "category"]
    search_fields = ["reference_number", "applicant_name", "email"]
    readonly_fields = ["reference_number", "created_at", "updated_at"]


@admin.register(VolunteerAssignment)
class VolunteerAssignmentAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = [
        "profile",
        "title",
        "program_name",
        "project_name",
        "start_date",
        "is_active",
    ]
    list_filter = ["is_active", "start_date"]
    search_fields = ["profile__reference_number", "title"]


@admin.register(VolunteerAttendance)
class VolunteerAttendanceAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = [
        "profile",
        "date",
        "activity_name",
        "category",
        "status",
        "hours_served",
    ]
    list_filter = ["status", "category", "date"]
    search_fields = ["profile__reference_number", "activity_name"]


@admin.register(VolunteerTraining)
class VolunteerTrainingAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = [
        "profile",
        "title",
        "provider",
        "start_date",
        "completion_date",
        "certificate_issued",
    ]
    list_filter = ["certificate_issued", "start_date"]


@admin.register(VolunteerPerformance)
class VolunteerPerformanceAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = ["profile", "review_period", "overall_score", "review_date"]
    list_filter = ["review_date"]


@admin.register(VolunteerRecognition)
class VolunteerRecognitionAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = ["profile", "title", "category", "award_date"]
    list_filter = ["category", "award_date"]


@admin.register(VolunteerLeave)
class VolunteerLeaveAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = ["profile", "leave_type", "start_date", "end_date", "status"]
    list_filter = ["status", "leave_type"]


@admin.register(VolunteerExit)
class VolunteerExitAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    list_display = ["profile", "reason", "effective_date", "status"]
    list_filter = ["status", "reason"]


@admin.register(VolunteerAuditRecord)
class VolunteerAuditRecordAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "entity_id", "action", "changed_by", "created_at"]
    list_filter = ["action", "entity_type"]
    readonly_fields = [
        "entity_type",
        "entity_id",
        "action",
        "changed_by",
        "from_data",
        "to_data",
        "notes",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VolunteerStatusHistory, VolunteerDeploymentHistory)
class ImmutableVolunteerRecordAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ServiceManagedRecordAdmin(ServiceManagedAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(VolunteerScreening, ServiceManagedRecordAdmin)
admin.site.register(VolunteerInterview, ServiceManagedRecordAdmin)
admin.site.register(VolunteerOnboarding, ServiceManagedRecordAdmin)
admin.site.register(VolunteerSkill, ServiceManagedRecordAdmin)
admin.site.register(VolunteerInterest, ServiceManagedRecordAdmin)
admin.site.register(VolunteerWelfare, ServiceManagedRecordAdmin)
admin.site.register(VolunteerDocument, ServiceManagedRecordAdmin)
admin.site.register(VolunteerActivityLog, ServiceManagedRecordAdmin)
admin.site.register(VolunteerDisciplinaryRecord, ServiceManagedRecordAdmin)
admin.site.register(VolunteerCommunication, ServiceManagedRecordAdmin)
admin.site.register(VolunteerCategory, ServiceManagedRecordAdmin)
admin.site.register(VolunteerType, ServiceManagedRecordAdmin)
admin.site.register(VolunteerLevel, ServiceManagedRecordAdmin)
