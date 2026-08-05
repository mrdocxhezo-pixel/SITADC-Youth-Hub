"""Django admin registration for the reference numbering module."""

from django.contrib import admin

from .models import (
    GeneratedReferenceNumber,
    ReferenceNumberAuditRecord,
    ReferenceNumberScheme,
    ReferenceSequence,
)


@admin.register(ReferenceNumberScheme)
class ReferenceNumberSchemeAdmin(admin.ModelAdmin):
    """Admin for reference number schemes."""

    list_display = (
        "name",
        "code",
        "module",
        "record_type",
        "prefix",
        "reset_period",
        "is_active",
        "status",
        "created_at",
    )
    list_filter = ("module", "status", "reset_period")
    search_fields = ("name", "code", "prefix", "record_type")
    readonly_fields = ("status", "created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(ReferenceSequence)
class ReferenceSequenceAdmin(admin.ModelAdmin):
    """Admin for sequence rows."""

    list_display = (
        "scheme",
        "period_key",
        "start_value",
        "current_value",
        "next_value",
        "updated_at",
    )
    list_filter = ("scheme__module",)
    search_fields = ("scheme__name", "period_key")
    readonly_fields = ("current_value", "next_value", "created_at", "updated_at")


@admin.register(GeneratedReferenceNumber)
class GeneratedReferenceNumberAdmin(admin.ModelAdmin):
    """Admin for the generated reference registry (immutable)."""

    list_display = (
        "reference_number",
        "scheme",
        "status",
        "record_type",
        "record_id",
        "reserved_at",
        "assigned_at",
    )
    list_filter = ("status", "scheme__module")
    search_fields = ("reference_number", "record_type", "record_id")
    readonly_fields = ("reference_number", "scheme", "status", "created_at")
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReferenceNumberAuditRecord)
class ReferenceNumberAuditRecordAdmin(admin.ModelAdmin):
    """Admin for the immutable reference audit trail."""

    list_display = (
        "changed_by",
        "action",
        "entity_type",
        "entity_id",
        "notes",
        "created_at",
    )
    list_filter = ("action", "entity_type")
    search_fields = ("changed_by__username", "entity_type", "notes")
    readonly_fields = (
        "changed_by",
        "action",
        "entity_type",
        "entity_id",
        "from_data",
        "to_data",
        "notes",
        "created_at",
    )
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
