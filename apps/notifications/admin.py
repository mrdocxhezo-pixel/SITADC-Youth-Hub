"""Admin registrations for the Notifications & Announcements module."""

from django.contrib import admin

from .models import (
    AnnouncementDelivery,
    AnnouncementDismissal,
    Notification,
    NotificationAuditRecord,
    NotificationCategory,
    NotificationDelivery,
    NotificationDigest,
    NotificationEvent,
    NotificationPreference,
    NotificationRule,
    NotificationTemplate,
    SystemAnnouncement,
)


class ReadOnlyMixin:
    """Base mixin rendering models in admin as read-only."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NotificationCategory)
class NotificationCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "color", "sort_order", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_active",)
    ordering = ("sort_order", "name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "title",
        "recipient",
        "notification_type",
        "priority",
        "status",
        "read_status",
        "created_at",
    )
    list_filter = (
        "status",
        "read_status",
        "notification_type",
        "priority",
        "category",
        "is_archived",
    )
    search_fields = ("reference", "title", "message", "recipient__email")
    readonly_fields = (
        "reference",
        "recipient",
        "category",
        "notification_type",
        "priority",
        "status",
        "read_status",
        "created_at",
        "updated_at",
        "sent_at",
    )
    date_hierarchy = "created_at"
    autocomplete_fields = ("recipient",)
    raw_id_fields = ("recipient", "actor")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "notification",
        "channel",
        "status",
        "attempt_number",
        "retry_count",
        "queued_at",
        "delivered_at",
    )
    list_filter = ("channel", "status")
    search_fields = ("notification__reference", "recipient__email")


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "category",
        "channel",
        "priority",
        "version",
        "is_active",
    )
    list_filter = ("category", "channel", "priority", "is_active")
    search_fields = ("code", "name", "event_type")


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "event_type",
        "notification_type",
        "priority",
        "recipient_role",
        "is_active",
    )
    list_filter = ("event_type", "notification_type", "priority", "is_active")
    search_fields = ("name", "event_type")
    raw_id_fields = ("recipient_user", "recipient_role", "template")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "in_app_enabled",
        "email_enabled",
        "digest_frequency",
        "quiet_hours_enabled",
    )
    list_filter = ("digest_frequency", "quiet_hours_enabled")
    search_fields = ("user__email",)


@admin.register(NotificationEvent)
class NotificationEventAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ("event_type", "source_app", "actor", "processed", "created_at")
    list_filter = ("source_app", "processed", "event_type")
    search_fields = ("event_type", "source_model", "deduplication_key")


@admin.register(SystemAnnouncement)
class SystemAnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "title",
        "announcement_type",
        "audience_type",
        "priority",
        "is_published",
        "publish_at",
    )
    list_filter = ("announcement_type", "audience_type", "priority", "is_published")
    search_fields = ("reference", "title", "message")


@admin.register(AnnouncementDelivery)
class AnnouncementDeliveryAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = (
        "announcement",
        "recipient",
        "delivered_at",
        "read_at",
        "dismissed_at",
    )
    list_filter = ("delivered_at",)
    search_fields = ("announcement__title", "recipient__email")


@admin.register(AnnouncementDismissal)
class AnnouncementDismissalAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ("announcement", "user", "dismissed_at")
    search_fields = ("announcement__title", "user__email")


@admin.register(NotificationAuditRecord)
class NotificationAuditRecordAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ("action", "actor", "target_type", "target_id", "created_at")
    list_filter = ("action",)
    search_fields = ("action", "actor__email", "target_id")


@admin.register(NotificationDigest)
class NotificationDigestAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "frequency",
        "notification_count",
        "period_start",
        "period_end",
        "sent_at",
    )
    list_filter = ("frequency",)
    search_fields = ("user__email",)
