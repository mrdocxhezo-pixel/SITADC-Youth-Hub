"""Admin registration for the Export Engine (Phase 27)."""

from django.contrib import admin

from .models import ExportActivity, ExportConfiguration, ExportRequest, ExportTemplate


class ImmutableActivityAdminMixin:
    """Block mutation of append-only export activity records."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ExportConfigurationAdmin(admin.ModelAdmin):
    """Singleton engine configuration (read-mostly, admin managed)."""

    list_display = ("short_name", "default_format", "enabled_formats", "updated_at")
    readonly_fields = (
        "singleton_key",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Branding",
            {
                "fields": (
                    "organization_name",
                    "short_name",
                    "contact_email",
                    "website",
                    "logo_enabled",
                )
            },
        ),
        (
            "Defaults",
            {
                "fields": (
                    "default_format",
                    "default_page_size",
                    "default_orientation",
                    "enabled_formats",
                )
            },
        ),
        (
            "Limits",
            {
                "fields": (
                    "max_sync_rows",
                    "max_bulk_rows",
                    "max_file_size_mb",
                    "max_columns",
                    "standard_retention_hours",
                    "sensitive_retention_hours",
                    "download_expiry_hours",
                )
            },
        ),
    )
    search_fields = ("organization_name", "short_name", "contact_email")

    def has_delete_permission(self, request, obj=None):
        return False


class ExportTemplateAdmin(admin.ModelAdmin):
    """Reusable presentation templates."""

    list_display = (
        "code",
        "name",
        "source_type",
        "version",
        "is_active",
        "updated_at",
    )
    list_filter = ("source_type", "is_active", "orientation", "page_size")
    search_fields = ("code", "name", "description")
    readonly_fields = (
        "version",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )


class ExportRequestAdmin(admin.ModelAdmin):
    """Export requests and their lifecycle."""

    list_display = (
        "reference_number",
        "requested_by",
        "source_type",
        "format",
        "status",
        "record_count",
        "is_sensitive",
        "requested_at",
        "expires_at",
    )
    list_filter = ("status", "source_type", "format", "is_sensitive", "is_bulk")
    search_fields = (
        "reference_number",
        "requested_by__email",
        "requested_by__username",
    )
    readonly_fields = (
        "id",
        "reference_number",
        "requested_by",
        "source_content_type",
        "source_object_id",
        "format",
        "status",
        "filters",
        "selected_columns",
        "record_count",
        "filename",
        "storage_path",
        "mime_type",
        "file_size",
        "confidentiality",
        "is_sensitive",
        "is_bulk",
        "confirmed_sensitive",
        "requested_at",
        "started_at",
        "completed_at",
        "failed_at",
        "expires_at",
        "failure_summary",
        "error_code",
        "created_at",
        "updated_at",
    )


admin.site.register(ExportConfiguration, ExportConfigurationAdmin)
admin.site.register(ExportTemplate, ExportTemplateAdmin)
admin.site.register(ExportRequest, ExportRequestAdmin)


@admin.register(ExportActivity)
class ExportActivityAdmin(ImmutableActivityAdminMixin, admin.ModelAdmin):
    """Immutable audit timeline for export requests."""

    list_display = ("export_request", "action", "actor", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("export_request__reference_number", "actor__email")
    readonly_fields = (
        "id",
        "export_request",
        "action",
        "actor",
        "details",
        "ip_address",
        "user_agent",
        "created_at",
    )
