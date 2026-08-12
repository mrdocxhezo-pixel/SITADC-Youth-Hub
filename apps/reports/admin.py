"""Administrative inspection and configuration for report builder records."""

# ruff: noqa: RUF012 - Django admin options are declarative class attributes.

from django.contrib import admin

from .models import (
    ConditionalLogicRule,
    DynamicField,
    FieldGroup,
    FieldOption,
    ReportCategory,
    ReportTemplate,
    ReportTemplateAuditRecord,
    ReportTemplateSettings,
    ReportTemplateStatusHistory,
    ReportTemplateVersion,
    TableColumnDefinition,
    TemplateComponent,
    TemplateReferenceRule,
    TemplateSection,
    ValidationRule,
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


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")
    ordering = ("sort_order", "name")
    list_editable = ("is_active",)


@admin.register(ReportTemplate)
class ReportTemplateAdmin(ServiceManagedAdmin):
    list_display = (
        "reference_number",
        "code",
        "title",
        "category",
        "status",
        "reporting_frequency",
        "current_version",
    )
    list_filter = ("status", "confidentiality", "category", "reporting_frequency")
    search_fields = ("reference_number", "code", "title", "description")
    ordering = ("-updated_at",)


@admin.register(ReportTemplateVersion)
class ReportTemplateVersionAdmin(ServiceManagedAdmin):
    list_display = (
        "template",
        "version_number",
        "status",
        "is_current",
        "checksum",
        "published_at",
    )
    list_filter = ("status", "is_current")
    search_fields = ("template__code", "template__title", "version_number")
    ordering = ("-major", "-minor")


@admin.register(TemplateSection)
class TemplateSectionAdmin(ServiceManagedAdmin):
    list_display = ("template", "code", "name", "sort_order", "is_repeatable")
    search_fields = ("template__code", "code", "name")


@admin.register(FieldGroup)
class FieldGroupAdmin(ServiceManagedAdmin):
    list_display = ("section", "code", "name", "sort_order")
    search_fields = ("section__template__code", "code", "name")


@admin.register(DynamicField)
class DynamicFieldAdmin(ServiceManagedAdmin):
    list_display = (
        "group",
        "code",
        "label",
        "field_type",
        "data_type",
        "required",
        "is_calculated",
    )
    list_filter = ("field_type", "data_type", "required", "is_calculated")
    search_fields = ("group__section__template__code", "code", "label")


@admin.register(FieldOption)
class FieldOptionAdmin(ServiceManagedAdmin):
    list_display = ("field", "value", "label", "sort_order")
    search_fields = ("field__code", "value", "label")


@admin.register(ValidationRule)
class ValidationRuleAdmin(ServiceManagedAdmin):
    list_display = ("field", "rule_type", "operator", "is_active", "sort_order")
    list_filter = ("rule_type", "is_active")
    search_fields = ("field__code",)


@admin.register(ConditionalLogicRule)
class ConditionalLogicRuleAdmin(ServiceManagedAdmin):
    list_display = (
        "template",
        "condition_type",
        "source_field",
        "operator",
        "target_type",
        "priority",
        "is_active",
    )
    list_filter = ("condition_type", "target_type", "is_active")
    search_fields = ("template__code",)


@admin.register(TemplateReferenceRule)
class TemplateReferenceRuleAdmin(ServiceManagedAdmin):
    list_display = ("field", "source_module", "model_name", "is_multiple")
    list_filter = ("source_module", "is_multiple")
    search_fields = ("field__code", "model_name")


@admin.register(ReportTemplateStatusHistory)
class ReportTemplateStatusHistoryAdmin(ServiceManagedAdmin):
    list_display = ("template", "from_status", "to_status", "action", "created_at")
    list_filter = ("action", "to_status")
    search_fields = ("template__code",)


@admin.register(TemplateComponent)
class TemplateComponentAdmin(ServiceManagedAdmin):
    list_display = ("template", "component_type", "code", "name", "sort_order")
    list_filter = ("component_type", "is_shared")
    search_fields = ("template__code", "name")


@admin.register(TableColumnDefinition)
class TableColumnDefinitionAdmin(ServiceManagedAdmin):
    list_display = (
        "table_field",
        "column_code",
        "column_name",
        "data_type",
        "required",
    )
    list_filter = ("data_type", "required")
    search_fields = ("table_field__code", "column_code", "column_name")


@admin.register(ReportTemplateSettings)
class ReportTemplateSettingsAdmin(admin.ModelAdmin):
    list_display = ("key", "is_active", "auto_save_interval_seconds")
    list_editable = ("is_active",)
    readonly_fields = ("key",)


@admin.register(ReportTemplateAuditRecord)
class ReportTemplateAuditRecordAdmin(ServiceManagedAdmin):
    list_display = ("entity_type", "entity_id", "action", "changed_by", "created_at")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_type", "entity_id", "notes")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
