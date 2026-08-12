"""Administrative inspection and configuration for Organizational Registers."""

# ruff: noqa: RUF012 - Django admin options are declarative class attributes.

from django.contrib import admin

from .models import (
    Register,
    RegisterActivity,
    RegisterAttachment,
    RegisterCategory,
    RegisterEntry,
    RegisterRelationship,
    RegisterReview,
    RegisterTemplate,
    RegisterValidation,
    RegisterVersion,
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


@admin.register(RegisterCategory)
class RegisterCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "number_prefix",
        "default_confidentiality",
        "is_active",
    )
    list_filter = ("default_confidentiality", "retention_policy", "is_active")
    search_fields = ("name", "code", "number_prefix")
    ordering = ("sort_order", "name")


@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = (
        "reference_number",
        "name",
        "code",
        "category",
        "owner",
        "confidentiality",
        "status",
        "is_active",
    )
    list_filter = ("status", "confidentiality", "approval_required", "category")
    search_fields = ("reference_number", "name", "code")
    autocomplete_fields = ("owner",)
    readonly_fields = ("reference_number", "created_at", "updated_at")


@admin.register(RegisterTemplate)
class RegisterTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "register", "is_default", "is_active")
    list_filter = ("is_default", "is_active", "register")
    search_fields = ("name", "code")


@admin.register(RegisterEntry)
class RegisterEntryAdmin(admin.ModelAdmin):
    list_display = (
        "reference_number",
        "title",
        "register",
        "owner",
        "confidentiality",
        "approval_status",
        "status",
    )
    list_filter = ("register", "approval_status", "confidentiality", "status")
    search_fields = ("reference_number", "title", "keywords")
    autocomplete_fields = ("owner", "register", "template")
    readonly_fields = ("reference_number", "created_at", "updated_at")


@admin.register(RegisterVersion)
class RegisterVersionAdmin(ServiceManagedAdmin):
    list_display = ("entry", "version_number", "author", "created_at")
    search_fields = ("entry__reference_number",)


@admin.register(RegisterAttachment)
class RegisterAttachmentAdmin(ServiceManagedAdmin):
    list_display = ("entry", "original_filename", "size", "created_at")
    search_fields = ("entry__reference_number", "original_filename")


@admin.register(RegisterRelationship)
class RegisterRelationshipAdmin(ServiceManagedAdmin):
    list_display = ("entry", "relationship_type", "object_id", "created_at")
    list_filter = ("relationship_type",)


@admin.register(RegisterReview)
class RegisterReviewAdmin(ServiceManagedAdmin):
    list_display = ("entry", "reviewer", "decision", "reviewed_at")
    list_filter = ("decision",)


@admin.register(RegisterActivity)
class RegisterActivityAdmin(ServiceManagedAdmin):
    list_display = ("entry", "action", "actor", "new_status", "created_at")
    list_filter = ("action",)


@admin.register(RegisterValidation)
class RegisterValidationAdmin(ServiceManagedAdmin):
    list_display = ("entry", "rule_code", "passed", "checked_at")
