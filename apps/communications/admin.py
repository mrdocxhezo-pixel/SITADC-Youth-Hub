"""Admin configuration for Communication and Media (Phase 30)."""

from django.contrib import admin

from .models import (
    Announcement,
    BrandAsset,
    BrandGuideline,
    Campaign,
    CampaignActivity,
    Communication,
    CommunicationCategory,
    CommunicationNotification,
    CommunicationTimeline,
    EventCommunication,
    MediaAlbum,
    MediaAsset,
    NewsArticle,
    Newsletter,
    NewsletterSubscriber,
    Photograph,
    PressRelease,
    Publication,
    SocialMediaAccount,
    SocialMediaPost,
    Video,
    WebsiteContent,
    WebsitePage,
)


class BaseCommunicationAdmin(admin.ModelAdmin):
    """Base admin class for communication models."""

    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25


# Communication Administration
@admin.register(CommunicationCategory)
class CommunicationCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Communication)
class CommunicationAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "communication_type",
        "priority",
        "status",
        "publication_date",
        "created_at",
    )
    list_filter = (
        "communication_type",
        "priority",
        "confidentiality_level",
        "status",
        "audience",
    )
    search_fields = (
        "title",
        "summary",
        "reference_number",
        "project",
        "programme",
    )


@admin.register(Announcement)
class AnnouncementAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "is_breaking",
        "priority",
        "status",
        "starts_at",
        "ends_at",
    )
    list_filter = ("is_breaking", "priority", "confidentiality_level", "status")
    search_fields = ("title", "summary", "reference_number")


@admin.register(NewsArticle)
class NewsArticleAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "news_category",
        "is_featured",
        "status",
        "publication_date",
    )
    list_filter = ("news_category", "is_featured", "is_breaking", "status")
    search_fields = ("title", "summary", "reference_number")


@admin.register(Newsletter)
class NewsletterAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "subject",
        "status",
        "scheduled_send",
        "sent_at",
        "sent_count",
    )
    list_filter = ("status", "audience", "priority")
    search_fields = ("title", "subject", "reference_number")
    filter_horizontal = ("subscribers",)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "audience_segment",
        "is_active",
        "subscribed_at",
    )
    list_filter = ("is_active", "audience_segment")
    search_fields = ("email", "first_name", "last_name")


@admin.register(PressRelease)
class PressReleaseAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "press_release_type",
        "priority",
        "status",
        "release_date",
        "embargo_date",
    )
    list_filter = ("press_release_type", "priority", "confidentiality_level", "status")
    search_fields = ("title", "summary", "reference_number")


@admin.register(SocialMediaAccount)
class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = (
        "platform",
        "account_name",
        "handle",
        "is_active",
        "is_default",
    )
    list_filter = ("platform", "is_active", "is_default")
    search_fields = ("account_name", "handle")


@admin.register(SocialMediaPost)
class SocialMediaPostAdmin(BaseCommunicationAdmin):
    list_display = (
        "platform",
        "content",
        "account",
        "scheduled_time",
        "published_at",
        "status",
    )
    list_filter = ("platform", "status", "campaign")
    search_fields = ("content",)


@admin.register(Campaign)
class CampaignAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "campaign_type",
        "priority",
        "status",
        "start_date",
        "end_date",
    )
    list_filter = ("campaign_type", "priority", "confidentiality_level", "status")
    search_fields = ("title", "summary", "reference_number", "objectives")


@admin.register(CampaignActivity)
class CampaignActivityAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "title",
        "activity_type",
        "activity_date",
        "is_completed",
    )
    list_filter = ("is_completed", "channel")
    search_fields = ("title", "activity_type", "description")


@admin.register(MediaAlbum)
class MediaAlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "is_featured", "created_at")
    list_filter = ("is_featured",)
    search_fields = ("title", "description")


@admin.register(MediaAsset)
class MediaAssetAdmin(BaseCommunicationAdmin):
    list_display = (
        "title",
        "asset_type",
        "media_category",
        "version",
        "status",
        "created_at",
    )
    list_filter = ("asset_type", "media_category", "confidentiality_level", "status")
    search_fields = ("title", "description", "tags", "reference_number")


@admin.register(Photograph)
class PhotographAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "photographer",
        "taken_date",
        "media_category",
        "is_featured",
    )
    list_filter = ("media_category", "is_featured")
    search_fields = ("title", "caption", "event_name")


@admin.register(Video)
class VideoAdmin(BaseCommunicationAdmin):
    list_display = (
        "title",
        "duration_seconds",
        "is_published",
        "is_streamable",
        "status",
        "created_at",
    )
    list_filter = ("is_published", "is_streamable", "download_allowed", "status")
    search_fields = ("title", "description")


@admin.register(Publication)
class PublicationAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "publication_type",
        "version",
        "status",
        "publication_date",
        "download_count",
    )
    list_filter = ("publication_type", "priority", "confidentiality_level", "status")
    search_fields = ("title", "summary", "reference_number", "isbn")


@admin.register(BrandAsset)
class BrandAssetAdmin(BaseCommunicationAdmin):
    list_display = (
        "title",
        "asset_type",
        "is_approved",
        "version",
        "status",
        "created_at",
    )
    list_filter = ("asset_type", "is_approved", "confidentiality_level", "status")
    search_fields = ("title", "description")


@admin.register(BrandGuideline)
class BrandGuidelineAdmin(admin.ModelAdmin):
    list_display = ("title", "effective_date", "is_current")
    list_filter = ("is_current",)
    search_fields = ("title",)


@admin.register(WebsitePage)
class WebsitePageAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "slug",
        "page_type",
        "is_published",
        "status",
    )
    list_filter = ("page_type", "is_published", "status")
    search_fields = ("title", "slug", "reference_number", "url_path")


@admin.register(WebsiteContent)
class WebsiteContentAdmin(admin.ModelAdmin):
    list_display = ("page", "section_key", "section_title", "order", "is_published")
    list_filter = ("is_published", "page")
    search_fields = ("section_key", "section_title", "content")


@admin.register(EventCommunication)
class EventCommunicationAdmin(BaseCommunicationAdmin):
    list_display = (
        "reference_number",
        "title",
        "event_name",
        "event_date",
        "location",
        "status",
    )
    list_filter = ("event_communication_type", "priority", "status")
    search_fields = ("title", "event_name", "location", "reference_number")


@admin.register(CommunicationNotification)
class CommunicationNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "notification_type",
        "recipient",
        "is_read",
        "sent_at",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "sent_via_email", "sent_via_sms")
    search_fields = ("title", "message", "recipient__email")


@admin.register(CommunicationTimeline)
class CommunicationTimelineAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "description",
        "reference_number",
        "performed_by",
        "event_date",
    )
    list_filter = ("event_type", "module", "status_after_event")
    search_fields = ("description", "reference_number", "remarks")
