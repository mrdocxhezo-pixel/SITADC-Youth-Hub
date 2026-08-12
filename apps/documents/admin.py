"""Admin configuration for the Document Management module."""

from __future__ import annotations

from django.contrib import admin

from .models import (
    Document,
    DocumentAuditRecord,
    DocumentCategory,
    DocumentCheckout,
    DocumentDisposalRequest,
    DocumentFolder,
    DocumentHold,
    DocumentRelationship,
    DocumentSettings,
    DocumentShare,
    DocumentTag,
    DocumentTimelineEvent,
    DocumentType,
    DocumentVersion,
    RetentionCategory,
)

# ---------------------------------------------------------------------------
# Inline Admin Classes
# ---------------------------------------------------------------------------


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = [
        "version_number",
        "version_label",
        "version_type",
        "original_filename",
        "file_size",
        "checksum",
        "is_current",
        "scan_status",
        "created_at",
    ]


class DocumentShareInline(admin.TabularInline):
    model = DocumentShare
    extra = 0
    readonly_fields = ["shared_at"]


class DocumentHoldInline(admin.TabularInline):
    model = DocumentHold
    extra = 0
    readonly_fields = ["applied_at"]


class DocumentTimelineEventInline(admin.TabularInline):
    model = DocumentTimelineEvent
    extra = 0
    readonly_fields = [
        "event_type",
        "actor",
        "previous_status",
        "new_status",
        "created_at",
    ]


# ---------------------------------------------------------------------------
# Model Admin Classes
# ---------------------------------------------------------------------------


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "parent", "sort_order", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "code"]
    prepopulated_fields = {"code": ("name",)}


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "category",
        "requires_approval",
        "requires_versioning",
        "is_active",
    ]
    list_filter = ["is_active", "category", "requires_approval"]
    search_fields = ["name", "code"]
    prepopulated_fields = {"code": ("name",)}


@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    list_display = ["name", "reference_number", "parent", "sort_order", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "reference_number"]


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "is_active"]
    list_filter = ["is_active", "category"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "title",
        "category",
        "document_type",
        "status",
        "approval_status",
        "confidentiality_level",
        "owner",
        "created_at",
    ]
    list_filter = [
        "status",
        "approval_status",
        "publication_status",
        "confidentiality_level",
        "is_sensitive",
        "category",
        "document_type",
    ]
    search_fields = ["reference_number", "title", "description"]
    readonly_fields = [
        "reference_number",
        "original_filename",
        "stored_filename",
        "file_extension",
        "mime_type",
        "file_size",
        "checksum",
        "current_version_number",
        "approved_by",
        "approved_at",
        "published_by",
        "published_at",
        "archived_at",
        "created_at",
        "updated_at",
    ]
    inlines = [
        DocumentVersionInline,
        DocumentShareInline,
        DocumentHoldInline,
        DocumentTimelineEventInline,
    ]


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = [
        "document",
        "version_number",
        "version_label",
        "version_type",
        "is_current",
        "approval_status",
        "created_at",
    ]
    list_filter = ["is_current", "version_type", "approval_status"]
    search_fields = ["document__title", "version_label"]


@admin.register(DocumentCheckout)
class DocumentCheckoutAdmin(admin.ModelAdmin):
    list_display = [
        "document",
        "checked_out_by",
        "checked_out_at",
        "expected_return_date",
        "status",
    ]
    list_filter = ["status"]
    search_fields = ["document__title", "checked_out_by__email"]


@admin.register(DocumentShare)
class DocumentShareAdmin(admin.ModelAdmin):
    list_display = [
        "document",
        "shared_with_user",
        "permission_level",
        "shared_by",
        "is_active",
        "expiry_date",
    ]
    list_filter = ["is_active", "permission_level"]
    search_fields = ["document__title", "shared_with_user__email"]


@admin.register(DocumentRelationship)
class DocumentRelationshipAdmin(admin.ModelAdmin):
    list_display = ["source_document", "target_document", "relationship_type"]
    list_filter = ["relationship_type"]


@admin.register(RetentionCategory)
class RetentionCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "retention_period_days",
        "retention_trigger",
        "disposal_action",
        "is_active",
    ]
    list_filter = ["is_active", "retention_trigger"]
    search_fields = ["name", "code"]


@admin.register(DocumentHold)
class DocumentHoldAdmin(admin.ModelAdmin):
    list_display = [
        "document",
        "hold_type",
        "applied_by",
        "applied_at",
        "status",
    ]
    list_filter = ["status", "hold_type"]
    search_fields = ["document__title"]


@admin.register(DocumentDisposalRequest)
class DocumentDisposalRequestAdmin(admin.ModelAdmin):
    list_display = [
        "document",
        "status",
        "requested_by",
        "approved_by",
        "disposal_date",
    ]
    list_filter = ["status"]
    search_fields = ["document__title"]


@admin.register(DocumentAuditRecord)
class DocumentAuditRecordAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "entity_id", "action", "changed_by", "created_at"]
    list_filter = ["action", "entity_type"]
    search_fields = ["entity_type", "entity_id"]
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


@admin.register(DocumentTimelineEvent)
class DocumentTimelineEventAdmin(admin.ModelAdmin):
    list_display = [
        "document",
        "event_type",
        "actor",
        "previous_status",
        "new_status",
        "created_at",
    ]
    list_filter = ["event_type"]
    search_fields = ["document__title"]
    readonly_fields = [
        "document",
        "event_type",
        "actor",
        "previous_status",
        "new_status",
        "comments",
        "metadata",
    ]


@admin.register(DocumentSettings)
class DocumentSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "max_upload_size",
        "enable_checkout",
        "enable_versioning",
        "default_confidentiality",
    ]

    def has_add_permission(self, request):
        return not DocumentSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
