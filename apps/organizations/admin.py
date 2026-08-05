from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    ActingAppointment,
    OrganizationAuditRecord,
    OrganizationLevel,
    OrganizationUnit,
    Position,
    PositionAssignment,
    PositionClassification,
    ReportingRelationship,
    TransferRecord,
    Vacancy,
)


@admin.register(OrganizationLevel)
class OrganizationLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "description")
    ordering = ("sort_order", "name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(PositionClassification)
class PositionClassificationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "description")
    ordering = ("sort_order", "name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "name",
        "unit_type",
        "level",
        "parent",
        "status",
        "unit_head",
        "access_scope",
        "is_archived",
        "created_at",
    )
    list_filter = ("unit_type", "status", "is_archived", "level")
    search_fields = ("identifier", "name", "short_name", "description")
    ordering = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("parent",)
    fieldsets = (
        (
            _("Identity"),
            {
                "fields": (
                    "identifier",
                    "name",
                    "short_name",
                    "description",
                )
            },
        ),
        (
            _("Hierarchy"),
            {
                "fields": (
                    "level",
                    "parent",
                    "unit_type",
                    "unit_head",
                    "access_scope",
                )
            },
        ),
        (
            _("Contact"),
            {
                "fields": (
                    "office_location",
                    "contact_email",
                    "contact_phone",
                )
            },
        ),
        (
            _("Lifecycle"),
            {
                "fields": (
                    "status",
                    "effective_date",
                    "established_date",
                    "is_archived",
                )
            },
        ),
        (
            _("Audit"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
    )


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "organizational_unit",
        "classification",
        "status",
        "is_protected",
        "is_archived",
        "created_at",
    )
    list_filter = ("status", "is_protected", "is_archived", "classification")
    search_fields = ("title", "slug", "organizational_unit__name")
    ordering = ("title",)
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("organizational_unit",)
    fieldsets = (
        (
            _("Identity"),
            {"fields": ("title", "slug", "organizational_unit", "classification")},
        ),
        (
            _("Role"),
            {
                "fields": (
                    "appointment_type",
                    "responsibilities",
                    "required_competencies",
                    "effective_date",
                    "is_protected",
                )
            },
        ),
        (
            _("Lifecycle"),
            {"fields": ("status", "is_archived")},
        ),
        (
            _("Audit"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
    )


@admin.register(ReportingRelationship)
class ReportingRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "position",
        "supervisor",
        "is_primary",
        "is_active",
        "effective_from",
        "effective_to",
    )
    list_filter = ("is_primary", "is_active")
    search_fields = ("position__title", "supervisor__title")
    autocomplete_fields = ("position", "supervisor")


@admin.register(PositionAssignment)
class PositionAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "position",
        "organizational_unit",
        "appointment_type",
        "status",
        "effective_date",
        "term_end",
        "appointed_by",
    )
    list_filter = ("status", "appointment_type", "renewal_eligible")
    search_fields = (
        "person__email",
        "person__first_name",
        "person__last_name",
        "position__title",
    )
    autocomplete_fields = ("person", "position", "organizational_unit")
    readonly_fields = ("id", "created_at")


@admin.register(ActingAppointment)
class ActingAppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "acting_officer",
        "position",
        "original_assignee",
        "effective_from",
        "end_date",
        "status",
        "approval_authority",
    )
    list_filter = ("status",)
    search_fields = (
        "acting_officer__email",
        "acting_officer__first_name",
        "acting_officer__last_name",
        "position__title",
    )
    autocomplete_fields = ("acting_officer", "position", "original_assignee")
    readonly_fields = ("id", "created_at")


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        "position",
        "organizational_unit",
        "date_vacant",
        "recruitment_status",
        "expected_appointment_date",
    )
    list_filter = ("recruitment_status",)
    search_fields = ("position__title", "organizational_unit__name")
    autocomplete_fields = ("position", "organizational_unit", "acting_appointment")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TransferRecord)
class TransferRecordAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "previous_position",
        "new_position",
        "effective_date",
        "status",
        "approved_by",
    )
    list_filter = ("status",)
    search_fields = ("person__email", "person__first_name", "person__last_name")
    autocomplete_fields = ("person",)
    readonly_fields = ("id", "created_at")


@admin.register(OrganizationAuditRecord)
class OrganizationAuditRecordAdmin(admin.ModelAdmin):
    list_display = ("entity_type", "entity_id", "action", "changed_by", "created_at")
    list_filter = ("action", "entity_type", "created_at")
    search_fields = ("entity_id", "notes", "entity_type")
    readonly_fields = (
        "entity_type",
        "entity_id",
        "action",
        "changed_by",
        "from_data",
        "to_data",
        "notes",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
