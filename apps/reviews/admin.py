"""Admin configuration for Review and Approval module (Phase 21)."""

# ruff: noqa: RUF012 - Django admin options are declarative class attributes.

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    DelegationRecord,
    DigitalSignature,
    EscalationRecord,
    Review,
    ReviewAssignment,
    ReviewChecklist,
    ReviewChecklistItem,
    ReviewChecklistResponse,
    ReviewComment,
    ReviewConfiguration,
    ReviewDecision,
    SLAConfiguration,
    SLAEvent,
)


class ReviewAssignmentInline(admin.TabularInline):
    model = ReviewAssignment
    extra = 0
    readonly_fields = ("created_at",)


class ReviewCommentInline(admin.TabularInline):
    model = ReviewComment
    extra = 0
    readonly_fields = ("created_at",)


class ReviewDecisionInline(admin.TabularInline):
    model = ReviewDecision
    extra = 0
    readonly_fields = ("decided_at",)


class ReviewChecklistResponseInline(admin.TabularInline):
    model = ReviewChecklistResponse
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "review_number",
        "report",
        "status",
        "primary_reviewer",
        "due_date",
        "decision",
        "is_overdue",
    )
    list_filter = ("status", "decision")
    search_fields = ("report__reference_number", "report__title")
    readonly_fields = (
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
        "decision_at",
    )
    inlines = [
        ReviewAssignmentInline,
        ReviewCommentInline,
        ReviewDecisionInline,
        ReviewChecklistResponseInline,
    ]

    def is_overdue(self, obj):
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = _("Overdue")


@admin.register(ReviewAssignment)
class ReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = ("review", "assigned_to", "role", "is_active", "accepted_at")
    list_filter = ("role", "is_active")
    search_fields = ("review__report__reference_number", "assigned_to__email")


@admin.register(ReviewChecklist)
class ReviewChecklistAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "is_default")
    list_filter = ("is_active", "is_default", "category")


@admin.register(ReviewChecklistItem)
class ReviewChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("checklist", "label", "sort_order", "is_required")
    list_filter = ("checklist", "is_required")


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ("review", "comment_type", "author", "is_internal", "is_resolved")
    list_filter = ("comment_type", "is_internal", "is_resolved")
    search_fields = ("body", "author__email")


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ("review", "decision", "reviewer", "decided_at")
    list_filter = ("decision",)
    readonly_fields = ("decided_at",)


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    list_display = ("decision", "signer", "signature_type", "signed_at", "is_valid")
    list_filter = ("signature_type", "is_valid")
    readonly_fields = ("signed_at",)


@admin.register(EscalationRecord)
class EscalationRecordAdmin(admin.ModelAdmin):
    list_display = ("review", "trigger", "escalated_by", "escalated_to", "is_resolved")
    list_filter = ("trigger", "is_resolved")
    readonly_fields = ("escalated_at",)


@admin.register(DelegationRecord)
class DelegationRecordAdmin(admin.ModelAdmin):
    list_display = ("review", "delegated_by", "delegated_to", "is_active", "expires_at")
    list_filter = ("is_active",)
    readonly_fields = ("delegated_at",)


@admin.register(SLAConfiguration)
class SLAConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "review_deadline_days", "is_active")
    list_filter = ("is_active", "category")


@admin.register(SLAEvent)
class SLAEventAdmin(admin.ModelAdmin):
    list_display = ("review", "event_type", "event_date")
    list_filter = ("event_type",)
    readonly_fields = ("event_date",)


@admin.register(ReviewConfiguration)
class ReviewConfigurationAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description")
    search_fields = ("key", "description")
