from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    AccessScope,
    PermissionCategory,
    Role,
    RoleHistory,
    UserRoleAssignment,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "status",
        "priority",
        "is_system",
        "is_archived",
        "group",
        "created_at",
    )
    list_filter = ("status", "is_system", "is_archived", "created_at")
    search_fields = ("name", "slug", "description")
    ordering = ("priority", "name")
    readonly_fields = ("id", "created_at", "updated_at")
    filter_horizontal = ("permissions",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "status",
                    "priority",
                    "is_system",
                    "group",
                )
            },
        ),
        (_("Permissions"), {"fields": ("permissions",)}),
        (
            _("Audit"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
    )


@admin.register(RoleHistory)
class RoleHistoryAdmin(admin.ModelAdmin):
    list_display = ("role", "action", "changed_by", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("role__name", "role__slug", "notes")
    readonly_fields = (
        "role",
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


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "access_scope",
        "is_primary",
        "status",
        "effective_from",
        "expires_at",
        "assigned_by",
    )
    list_filter = ("status", "is_primary", "role", "access_scope")
    search_fields = ("user__email", "user__first_name", "user__last_name", "role__name")
    autocomplete_fields = ("user",)
    raw_id_fields = ("user",)


@admin.register(AccessScope)
class AccessScopeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "level", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")
    ordering = ("level",)


@admin.register(PermissionCategory)
class PermissionCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "sort_order")
    search_fields = ("code", "name", "description")
    ordering = ("sort_order", "name")
