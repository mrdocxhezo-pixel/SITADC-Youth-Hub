"""Models for Communication and Media (Phase 30)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.communications.constants import (
    AudienceType,
    BrandAssetType,
    CampaignType,
    CommunicationType,
    ConfidentialityLevel,
    DistributionChannel,
    EventCommunicationType,
    MediaAssetType,
    MediaCategory,
    NewsCategory,
    NotificationType,
    PressReleaseType,
    Priority,
    PublicationType,
    SocialPlatform,
    TimelineEventType,
    WebsitePageType,
)
from apps.core.models import (
    CreatedByModel,
    NotesModel,
    StatusModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)


class CommunicationRecord(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    StatusModel,
    NotesModel,
):
    """Abstract base record for communication entities.

    Carries the standardized communication metadata framework so every
    communication record exposes a consistent reference number, lifecycle,
    audience, priority, confidentiality classification and organizational
    scope (programme / project / region / district / community).
    """

    title = models.CharField(_("Title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    summary = models.TextField(_("Summary"), blank=True)

    communication_type = models.CharField(
        _("Communication type"),
        max_length=20,
        choices=CommunicationType.choices,
        default=CommunicationType.INTERNAL,
    )

    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )

    audience = models.CharField(
        _("Audience"),
        max_length=20,
        choices=AudienceType.choices,
        blank=True,
    )

    # Publication metadata
    publication_date = models.DateField(_("Publication date"), null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_author",
        verbose_name=_("Author"),
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_reviewer",
        verbose_name=_("Reviewer"),
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_approver",
        verbose_name=_("Approver"),
    )

    # Organizational scope
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    region = models.CharField(_("Region"), max_length=100, blank=True)
    district = models.CharField(_("District"), max_length=100, blank=True)
    community = models.CharField(_("Community"), max_length=100, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title}"

    def clean(self) -> None:
        """Validate publication scheduling."""
        super().clean()


class CommunicationCategory(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """Configurable communication categories."""

    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Code"), max_length=50, unique=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is active"), default=True)

    class Meta:
        verbose_name = _("Communication Category")
        verbose_name_plural = _("Communication Categories")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Communication(CommunicationRecord):
    """Core internal / external communication record."""

    category = models.ForeignKey(
        CommunicationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications",
        verbose_name=_("Category"),
    )
    body = models.TextField(_("Body content"))
    distribution_channel = models.CharField(
        _("Distribution channel"),
        max_length=20,
        choices=DistributionChannel.choices,
        default=DistributionChannel.WEBSITE,
    )
    scheduled_date = models.DateTimeField(
        _("Scheduled date and time"), null=True, blank=True
    )
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)
    is_featured = models.BooleanField(_("Is featured"), default=False)

    class Meta:
        verbose_name = _("Communication")
        verbose_name_plural = _("Communications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["communication_type", "status"]),
            models.Index(fields=["publication_date"]),
        ]


class Announcement(CommunicationRecord):
    """Organization-wide announcements."""

    is_breaking = models.BooleanField(_("Is breaking news"), default=False)
    starts_at = models.DateField(_("Starts at"), null=True, blank=True)
    ends_at = models.DateField(_("Ends at"), null=True, blank=True)
    body = models.TextField(_("Announcement body"))
    target_roles = models.CharField(_("Target roles"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")
        ordering = ["-starts_at"]
        indexes = [
            models.Index(fields=["is_breaking", "status"]),
            models.Index(fields=["starts_at"]),
        ]


class NewsArticle(CommunicationRecord):
    """News and featured stories management."""

    news_category = models.CharField(
        _("News category"),
        max_length=20,
        choices=NewsCategory.choices,
        default=NewsCategory.GENERAL,
    )
    body = models.TextField(_("Article body"))
    is_featured = models.BooleanField(_("Is featured"), default=False)
    is_breaking = models.BooleanField(_("Is breaking news"), default=False)
    scheduled_publication = models.DateTimeField(
        _("Scheduled publication"), null=True, blank=True
    )
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)
    allow_comments = models.BooleanField(_("Allow comments"), default=False)
    featured_image = models.ForeignKey(
        "MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="featured_news",
        verbose_name=_("Featured image"),
    )

    class Meta:
        verbose_name = _("News Article")
        verbose_name_plural = _("News Articles")
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["news_category", "status"]),
            models.Index(fields=["is_featured", "status"]),
        ]


class Newsletter(CommunicationRecord):
    """Newsletter creation and distribution."""

    subject = models.CharField(_("Subject"), max_length=200)
    content = models.TextField(_("Newsletter content"))
    template_name = models.CharField(_("Template name"), max_length=100, blank=True)
    scheduled_send = models.DateTimeField(_("Scheduled send"), null=True, blank=True)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    sent_count = models.PositiveIntegerField(_("Sent count"), default=0)
    open_count = models.PositiveIntegerField(_("Open count"), default=0)
    click_count = models.PositiveIntegerField(_("Click-through count"), default=0)
    subscribers = models.ManyToManyField(
        "NewsletterSubscriber",
        blank=True,
        related_name="newsletters",
        verbose_name=_("Subscribers"),
    )

    class Meta:
        verbose_name = _("Newsletter")
        verbose_name_plural = _("Newsletters")
        ordering = ["-scheduled_send"]
        indexes = [
            models.Index(fields=["status", "scheduled_send"]),
        ]


class NewsletterSubscriber(UUIDModel, TimeStampedModel):
    """Newsletter subscriber records."""

    email = models.EmailField(_("Email"), max_length=254, unique=True)
    first_name = models.CharField(_("First name"), max_length=100, blank=True)
    last_name = models.CharField(_("Last name"), max_length=100, blank=True)
    audience_segment = models.CharField(
        _("Audience segment"),
        max_length=20,
        choices=AudienceType.choices,
        blank=True,
    )
    is_active = models.BooleanField(_("Is active"), default=True)
    subscribed_at = models.DateTimeField(_("Subscribed at"), auto_now_add=True)
    unsubscribed_at = models.DateTimeField(_("Unsubscribed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Newsletter Subscriber")
        verbose_name_plural = _("Newsletter Subscribers")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email


class PressRelease(CommunicationRecord):
    """Press release management."""

    press_release_type = models.CharField(
        _("Press release type"),
        max_length=15,
        choices=PressReleaseType.choices,
        default=PressReleaseType.NEWS,
    )
    body = models.TextField(_("Press release body"))
    media_contacts = models.TextField(_("Media contacts"), blank=True)
    embargo_date = models.DateTimeField(_("Embargo date"), null=True, blank=True)
    release_date = models.DateTimeField(_("Release date"), null=True, blank=True)
    attachment = models.FileField(
        _("Attachment"), upload_to="communications/press_releases/", blank=True
    )
    distribution_history = models.TextField(_("Distribution history"), blank=True)

    class Meta:
        verbose_name = _("Press Release")
        verbose_name_plural = _("Press Releases")
        ordering = ["-release_date"]
        indexes = [
            models.Index(fields=["press_release_type", "status"]),
            models.Index(fields=["embargo_date"]),
        ]


class SocialMediaAccount(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Registered organizational social media accounts."""

    platform = models.CharField(
        _("Platform"),
        max_length=15,
        choices=SocialPlatform.choices,
    )
    account_name = models.CharField(_("Account name"), max_length=100)
    handle = models.CharField(_("Handle"), max_length=100, blank=True)
    account_url = models.URLField(_("Account URL"), blank=True)
    is_active = models.BooleanField(_("Is active"), default=True)
    is_default = models.BooleanField(_("Is default account"), default=False)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Social Media Account")
        verbose_name_plural = _("Social Media Accounts")
        ordering = ["platform", "account_name"]
        unique_together = ("platform", "account_name")

    def __str__(self) -> str:
        return f"{self.get_platform_display()} - {self.account_name}"


class Campaign(CommunicationRecord):
    """Communication campaign management."""

    campaign_type = models.CharField(
        _("Campaign type"),
        max_length=20,
        choices=CampaignType.choices,
        default=CampaignType.AWARENESS,
    )
    objectives = models.TextField(_("Objectives"))
    target_audience = models.CharField(_("Target audience"), max_length=200, blank=True)
    channels = models.CharField(_("Channels"), max_length=200, blank=True)
    start_date = models.DateField(_("Start date"), null=True, blank=True)
    end_date = models.DateField(_("End date"), null=True, blank=True)
    budget_reference = models.CharField(
        _("Budget reference"), max_length=100, blank=True
    )
    budget_amount = models.DecimalField(
        _("Budget amount"), max_digits=14, decimal_places=2, null=True, blank=True
    )
    key_performance_indicators = models.TextField(
        _("Key performance indicators"), blank=True
    )
    results = models.TextField(_("Results"), blank=True)
    lessons_learned = models.TextField(_("Lessons learned"), blank=True)

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["campaign_type", "status"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def clean(self) -> None:
        """Validate campaign date ordering."""
        super().clean()
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": _("End date cannot be before the start date.")}
            )


class CampaignActivity(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Activities executed within a campaign."""

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name=_("Campaign"),
    )
    activity_type = models.CharField(_("Activity type"), max_length=100)
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    activity_date = models.DateField(_("Activity date"))
    channel = models.CharField(
        _("Channel"),
        max_length=20,
        choices=DistributionChannel.choices,
        blank=True,
    )
    is_completed = models.BooleanField(_("Is completed"), default=False)

    class Meta:
        verbose_name = _("Campaign Activity")
        verbose_name_plural = _("Campaign Activities")
        ordering = ["activity_date"]

    def __str__(self) -> str:
        return f"{self.campaign.title} - {self.title}"


class MediaAlbum(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Albums organizing media assets."""

    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    is_featured = models.BooleanField(_("Is featured"), default=False)

    class Meta:
        verbose_name = _("Media Album")
        verbose_name_plural = _("Media Albums")
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class MediaAsset(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel
):
    """Centralized media asset management."""

    asset_type = models.CharField(
        _("Asset type"),
        max_length=15,
        choices=MediaAssetType.choices,
        default=MediaAssetType.IMAGE,
    )
    media_category = models.CharField(
        _("Media category"),
        max_length=15,
        choices=MediaCategory.choices,
        default=MediaCategory.OTHER,
    )
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    file = models.FileField(_("File"), upload_to="communications/media/")
    thumbnail = models.ImageField(
        _("Thumbnail"), upload_to="communications/thumbnails/", blank=True
    )
    album = models.ForeignKey(
        MediaAlbum,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        verbose_name=_("Album"),
    )
    tags = models.CharField(_("Tags"), max_length=200, blank=True)
    file_size = models.PositiveIntegerField(
        _("File size (bytes)"), null=True, blank=True
    )
    mime_type = models.CharField(_("MIME type"), max_length=100, blank=True)
    version = models.CharField(_("Version"), max_length=20, default="1.0")
    copyright_info = models.CharField(_("Copyright info"), max_length=200, blank=True)
    licensing_info = models.CharField(_("Licensing info"), max_length=200, blank=True)
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("Media Asset")
        verbose_name_plural = _("Media Assets")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["asset_type", "status"]),
            models.Index(fields=["media_category", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_asset_type_display()})"


class Photograph(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Organizational photography management."""

    title = models.CharField(_("Title"), max_length=200)
    caption = models.TextField(_("Caption"), blank=True)
    image = models.ImageField(_("Image"), upload_to="communications/photographs/")
    photographer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="photographed_communications",
        verbose_name=_("Photographer"),
    )
    taken_date = models.DateField(_("Taken date"), null=True, blank=True)
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    event_name = models.CharField(_("Event name"), max_length=200, blank=True)
    media_category = models.CharField(
        _("Media category"),
        max_length=15,
        choices=MediaCategory.choices,
        default=MediaCategory.OTHER,
    )
    is_featured = models.BooleanField(_("Is featured"), default=False)

    class Meta:
        verbose_name = _("Photograph")
        verbose_name_plural = _("Photographs")
        ordering = ["-taken_date"]
        indexes = [
            models.Index(fields=["media_category", "taken_date"]),
        ]

    def __str__(self) -> str:
        return self.title


class Video(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel):
    """Videography management."""

    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    video_file = models.FileField(_("Video file"), upload_to="communications/videos/")
    thumbnail = models.ImageField(
        _("Thumbnail"), upload_to="communications/video_thumbnails/", blank=True
    )
    captions = models.FileField(
        _("Captions file"), upload_to="communications/captions/", blank=True
    )
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    duration_seconds = models.PositiveIntegerField(
        _("Duration (seconds)"), null=True, blank=True
    )
    is_streamable = models.BooleanField(_("Is streamable"), default=True)
    download_allowed = models.BooleanField(_("Download allowed"), default=False)
    is_published = models.BooleanField(_("Is published"), default=False)

    class Meta:
        verbose_name = _("Video")
        verbose_name_plural = _("Videos")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_published"]),
        ]

    def __str__(self) -> str:
        return self.title


class Publication(CommunicationRecord):
    """Organizational publications management."""

    publication_type = models.CharField(
        _("Publication type"),
        max_length=20,
        choices=PublicationType.choices,
        default=PublicationType.BROCHURE,
    )
    file = models.FileField(
        _("Publication file"), upload_to="communications/publications/"
    )
    cover_image = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publication_covers",
        verbose_name=_("Cover image"),
    )
    isbn = models.CharField(_("ISBN"), max_length=20, blank=True)
    page_count = models.PositiveIntegerField(_("Page count"), null=True, blank=True)
    version = models.CharField(_("Version"), max_length=20, default="1.0")
    download_count = models.PositiveIntegerField(_("Download count"), default=0)

    class Meta:
        verbose_name = _("Publication")
        verbose_name_plural = _("Publications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["publication_type", "status"]),
        ]


class BrandAsset(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel
):
    """Centralized brand asset management."""

    asset_type = models.CharField(
        _("Asset type"),
        max_length=20,
        choices=BrandAssetType.choices,
    )
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    file = models.FileField(_("File"), upload_to="communications/brand/")
    usage_guidelines = models.TextField(_("Usage guidelines"), blank=True)
    is_approved = models.BooleanField(_("Is approved"), default=False)
    version = models.CharField(_("Version"), max_length=20, default="1.0")
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )

    class Meta:
        verbose_name = _("Brand Asset")
        verbose_name_plural = _("Brand Assets")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["asset_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_asset_type_display()})"


class BrandGuideline(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Brand usage guidelines."""

    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    guidelines = models.TextField(_("Guidelines"))
    file = models.FileField(
        _("Guideline document"),
        upload_to="communications/brand_guidelines/",
        blank=True,
    )
    effective_date = models.DateField(_("Effective date"), null=True, blank=True)
    is_current = models.BooleanField(_("Is current"), default=True)

    class Meta:
        verbose_name = _("Brand Guideline")
        verbose_name_plural = _("Brand Guidelines")
        ordering = ["-effective_date"]

    def __str__(self) -> str:
        return self.title


class SocialMediaPost(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel
):
    """Social media content and scheduling."""

    account = models.ForeignKey(
        SocialMediaAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name=_("Account"),
    )
    platform = models.CharField(
        _("Platform"),
        max_length=15,
        choices=SocialPlatform.choices,
    )
    content = models.TextField(_("Post content"))
    media = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="social_posts",
        verbose_name=_("Media"),
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="social_posts",
        verbose_name=_("Campaign"),
    )
    scheduled_time = models.DateTimeField(_("Scheduled time"), null=True, blank=True)
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)
    post_url = models.URLField(_("Post URL"), blank=True)
    engagement_likes = models.PositiveIntegerField(_("Likes"), default=0)
    engagement_comments = models.PositiveIntegerField(_("Comments"), default=0)
    engagement_shares = models.PositiveIntegerField(_("Shares"), default=0)
    engagement_reach = models.PositiveIntegerField(_("Reach"), default=0)

    class Meta:
        verbose_name = _("Social Media Post")
        verbose_name_plural = _("Social Media Posts")
        ordering = ["-scheduled_time"]
        indexes = [
            models.Index(fields=["platform", "status"]),
            models.Index(fields=["scheduled_time"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_platform_display()} - {self.content[:50]}"


class WebsitePage(CommunicationRecord):
    """Website page management."""

    page_type = models.CharField(
        _("Page type"),
        max_length=15,
        choices=WebsitePageType.choices,
        default=WebsitePageType.OTHER,
    )
    slug = models.SlugField(_("Slug"), max_length=200, unique=True)
    url_path = models.CharField(_("URL path"), max_length=200, blank=True)
    is_published = models.BooleanField(_("Is published"), default=False)
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Website Page")
        verbose_name_plural = _("Website Pages")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["page_type", "status"]),
            models.Index(fields=["slug"]),
        ]


class WebsiteContent(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Content sections published on website pages."""

    page = models.ForeignKey(
        WebsitePage,
        on_delete=models.CASCADE,
        related_name="content_sections",
        verbose_name=_("Page"),
    )
    section_key = models.CharField(_("Section key"), max_length=100)
    section_title = models.CharField(_("Section title"), max_length=200, blank=True)
    content = models.TextField(_("Content"))
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_published = models.BooleanField(_("Is published"), default=True)

    class Meta:
        verbose_name = _("Website Content")
        verbose_name_plural = _("Website Content")
        ordering = ["page", "order"]
        unique_together = ("page", "section_key")

    def __str__(self) -> str:
        return f"{self.page.title} - {self.section_title or self.section_key}"


class EventCommunication(CommunicationRecord):
    """Communications associated with organizational events."""

    event_communication_type = models.CharField(
        _("Event communication type"),
        max_length=15,
        choices=EventCommunicationType.choices,
        default=EventCommunicationType.ANNOUNCEMENT,
    )
    event_name = models.CharField(_("Event name"), max_length=200)
    event_date = models.DateTimeField(_("Event date and time"))
    location = models.CharField(_("Location"), max_length=200, blank=True)
    speaker_profiles = models.TextField(_("Speaker profiles"), blank=True)
    programme_schedule = models.TextField(_("Programme schedule"), blank=True)
    thank_you_message = models.TextField(_("Thank-you message"), blank=True)
    attendee_count = models.PositiveIntegerField(_("Attendee count"), default=0)

    class Meta:
        verbose_name = _("Event Communication")
        verbose_name_plural = _("Event Communications")
        ordering = ["-event_date"]
        indexes = [
            models.Index(fields=["event_communication_type", "status"]),
            models.Index(fields=["event_date"]),
        ]


class CommunicationNotification(UUIDModel, TimeStampedModel):
    """Notifications generated by communication activities."""

    notification_type = models.CharField(
        _("Notification type"),
        max_length=30,
        choices=NotificationType.choices,
    )
    title = models.CharField(_("Notification title"), max_length=200)
    message = models.TextField(_("Notification message"))
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="communications_notifications",
        verbose_name=_("Recipient"),
    )
    is_read = models.BooleanField(_("Is read"), default=False)
    read_at = models.DateTimeField(_("Read at"), null=True, blank=True)
    sent_via_email = models.BooleanField(_("Sent via email"), default=False)
    sent_via_sms = models.BooleanField(_("Sent via SMS"), default=False)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Communication Notification")
        verbose_name_plural = _("Communication Notifications")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} - {self.recipient.get_full_name()}"


class CommunicationTimeline(UUIDModel, TimeStampedModel):
    """Chronological timeline of communication activities."""

    event_type = models.CharField(
        _("Event type"),
        max_length=30,
        choices=TimelineEventType.choices,
    )
    description = models.TextField(_("Event description"))
    event_date = models.DateTimeField(_("Event date and time"))
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications_timeline_events",
        verbose_name=_("Performed by"),
    )
    module = models.CharField(_("Module"), max_length=50, blank=True)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, blank=True
    )
    action_performed = models.CharField(
        _("Action performed"), max_length=100, blank=True
    )
    status_after_event = models.CharField(
        _("Status after event"), max_length=50, blank=True
    )
    remarks = models.TextField(_("Remarks"), blank=True)

    class Meta:
        verbose_name = _("Communication Timeline Event")
        verbose_name_plural = _("Communication Timeline Events")
        ordering = ["-event_date"]
        indexes = [
            models.Index(fields=["event_type", "event_date"]),
        ]

    def __str__(self) -> str:
        dt = self.event_date.strftime("%Y-%m-%d %H:%M")
        return f"{self.event_type} - {dt}"


class CommunicationAttachment(UUIDModel, TimeStampedModel):
    """Attachments associated with communication records."""

    communication = models.ForeignKey(
        Communication,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Communication"),
    )
    file = models.FileField(_("File"), upload_to="communications/attachments/")
    file_name = models.CharField(_("File name"), max_length=200, blank=True)
    file_size = models.PositiveIntegerField(
        _("File size (bytes)"), null=True, blank=True
    )
    mime_type = models.CharField(_("MIME type"), max_length=100, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_communication_attachments",
        verbose_name=_("Uploaded by"),
    )

    class Meta:
        verbose_name = _("Communication Attachment")
        verbose_name_plural = _("Communication Attachments")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.file_name or self.file.name
