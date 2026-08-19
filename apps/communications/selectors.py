"""Communication and Media selectors.

All selectors are fail-closed: a user without the relevant ``communications.*``
permission receives an empty queryset rather than data.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from apps.communications.models import (
    Announcement,
    BrandAsset,
    Campaign,
    CampaignActivity,
    Communication,
    CommunicationCategory,
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
from apps.communications.permissions import (
    user_can_access_communications,
    user_can_manage_communications,
)

User = get_user_model()


def get_accessible_communications(user: User) -> QuerySet[Communication]:
    """Communications the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return Communication.objects.none()
    return Communication.objects.all()


def get_accessible_announcements(user: User) -> QuerySet[Announcement]:
    """Announcements the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return Announcement.objects.none()
    return Announcement.objects.all()


def get_accessible_news_articles(user: User) -> QuerySet[NewsArticle]:
    """News articles the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return NewsArticle.objects.none()
    return NewsArticle.objects.all()


def get_accessible_newsletters(user: User) -> QuerySet[Newsletter]:
    """Newsletters the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return Newsletter.objects.none()
    return Newsletter.objects.all()


def get_accessible_newsletter_subscribers(user: User) -> QuerySet[NewsletterSubscriber]:
    """Newsletter subscribers the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return NewsletterSubscriber.objects.none()
    return NewsletterSubscriber.objects.all()


def get_accessible_press_releases(user: User) -> QuerySet[PressRelease]:
    """Press releases the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return PressRelease.objects.none()
    return PressRelease.objects.all()


def get_accessible_social_media_accounts(user: User) -> QuerySet[SocialMediaAccount]:
    """Social media accounts the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return SocialMediaAccount.objects.none()
    return SocialMediaAccount.objects.all()


def get_accessible_social_media_posts(user: User) -> QuerySet[SocialMediaPost]:
    """Social media posts the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return SocialMediaPost.objects.none()
    return SocialMediaPost.objects.all()


def get_accessible_campaigns(user: User) -> QuerySet[Campaign]:
    """Campaigns the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return Campaign.objects.none()
    return Campaign.objects.all()


def get_accessible_campaign_activities(user: User) -> QuerySet[CampaignActivity]:
    """Campaign activities the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return CampaignActivity.objects.none()
    return CampaignActivity.objects.all()


def get_accessible_website_pages(user: User) -> QuerySet[WebsitePage]:
    """Website pages the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return WebsitePage.objects.none()
    return WebsitePage.objects.all()


def get_accessible_website_content(user: User) -> QuerySet[WebsiteContent]:
    """Website content sections the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return WebsiteContent.objects.none()
    return WebsiteContent.objects.all()


def get_accessible_media_assets(user: User) -> QuerySet[MediaAsset]:
    """Media assets the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return MediaAsset.objects.none()
    return MediaAsset.objects.all()


def get_accessible_media_albums(user: User) -> QuerySet[MediaAlbum]:
    """Media albums the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return MediaAlbum.objects.none()
    return MediaAlbum.objects.all()


def get_accessible_photographs(user: User) -> QuerySet[Photograph]:
    """Photographs the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return Photograph.objects.none()
    return Photograph.objects.all()


def get_accessible_videos(user: User) -> QuerySet[Video]:
    """Videos the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return Video.objects.none()
    return Video.objects.all()


def get_accessible_publications(user: User) -> QuerySet[Publication]:
    """Publications the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return Publication.objects.none()
    return Publication.objects.all()


def get_accessible_brand_assets(user: User) -> QuerySet[BrandAsset]:
    """Brand assets the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return BrandAsset.objects.none()
    return BrandAsset.objects.all()


def get_accessible_event_communications(user: User) -> QuerySet[EventCommunication]:
    """Event communications the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return EventCommunication.objects.none()
    return EventCommunication.objects.all()


def get_accessible_communication_categories(
    user: User,
) -> QuerySet[CommunicationCategory]:
    """Communication categories the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return CommunicationCategory.objects.none()
    return CommunicationCategory.objects.all()


def get_accessible_timeline(user: User) -> QuerySet[CommunicationTimeline]:
    """Communication timeline events the user may view (empty queryset when denied)."""
    if not user_can_access_communications(user):
        return CommunicationTimeline.objects.none()
    return CommunicationTimeline.objects.all()


def can_manage_communications(user: User) -> bool:
    """Whether the actor holds the master communications-management permission."""
    return user_can_manage_communications(user)


def get_dashboard_summary(user: User) -> dict[str, int]:
    """Return a summary of communication records for the dashboard."""
    if not user_can_access_communications(user):
        return {}
    return {
        "communications": Communication.objects.count(),
        "announcements": Announcement.objects.count(),
        "news_articles": NewsArticle.objects.count(),
        "campaigns": Campaign.objects.count(),
        "press_releases": PressRelease.objects.count(),
        "publications": Publication.objects.count(),
        "media_assets": MediaAsset.objects.count(),
        "videos": Video.objects.count(),
        "social_posts": SocialMediaPost.objects.count(),
        "website_pages": WebsitePage.objects.count(),
        "event_communications": EventCommunication.objects.count(),
    }


def get_recent_communications(user: User, limit: int = 8) -> QuerySet[Communication]:
    """Return the most recent communications the user may view."""
    if not user_can_access_communications(user):
        return Communication.objects.none()
    return Communication.objects.order_by("-created_at")[:limit]


def get_upcoming_event_communications(
    user: User, limit: int = 8
) -> QuerySet[EventCommunication]:
    """Return upcoming event communications the user may view."""
    if not user_can_access_communications(user):
        return EventCommunication.objects.none()
    from django.utils import timezone

    return EventCommunication.objects.filter(event_date__gte=timezone.now()).order_by(
        "event_date"
    )[:limit]
