from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    IntegrationSettings,
    SystemSettings,
    UserSettings,
    UserSettingsDefault,
)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "density", "email_notifications", "in_app_notifications", "created_at")
    list_filter = ("theme", "density", "email_notifications", "in_app_notifications", "browser_notifications")
    search_fields = ("user__email", "user__username", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user",)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("system_name", "system_status", "maintenance_mode", "session_timeout_minutes", "audit_log_enabled")
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IntegrationSettings)
class IntegrationSettingsAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "integration_type", "is_active", "last_status", "last_sync")
    list_filter = ("integration_type", "is_active", "last_status")
    search_fields = ("name", "slug")
    readonly_fields = ("created_at", "updated_at", "last_sync", "last_status", "last_error")


@admin.register(UserSettingsDefault)
class UserSettingsDefaultAdmin(admin.ModelAdmin):
    list_display = ("key", "default_theme", "default_language", "default_timezone")
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        return not UserSettingsDefault.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False