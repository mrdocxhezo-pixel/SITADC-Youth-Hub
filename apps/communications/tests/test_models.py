"""Communication model tests."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.communications.models import (
    CampaignActivity,
    CommunicationNotification,
    CommunicationTimeline,
)
from apps.core.constants import StatusConstants

from .base import CommunicationsTestCase


class CommunicationModelTests(CommunicationsTestCase):
    """Tests for the core Communication model."""

    def test_create_communication(self):
        """Test creating a communication record."""
        comm = self.create_communication()
        self.assertEqual(comm.title, "Test Communication")
        self.assertEqual(comm.reference_number, "COM-001")
        self.assertEqual(comm.status, StatusConstants.APPROVED)
        self.assertEqual(str(comm), "COM-001 - Test Communication")

    def test_reference_number_unique(self):
        """Test reference numbers are unique."""
        self.create_communication(reference_number="COM-001")
        with self.assertRaises(IntegrityError):
            self.create_communication(reference_number="COM-001")

    def test_communication_str(self):
        """Test the string representation."""
        comm = self.create_communication()
        self.assertEqual(str(comm), "COM-001 - Test Communication")

    def test_communication_category(self):
        """Test creating a communication category."""
        category = self.create_communication_category()
        self.assertEqual(category.name, "General")
        self.assertEqual(str(category), "General")


class AnnouncementModelTests(CommunicationsTestCase):
    """Tests for the Announcement model."""

    def test_create_announcement(self):
        """Test creating an announcement."""
        announcement = self.create_announcement()
        self.assertEqual(announcement.title, "Test Announcement")
        self.assertEqual(str(announcement), "ANN-001 - Test Announcement")


class NewsArticleModelTests(CommunicationsTestCase):
    """Tests for the NewsArticle model."""

    def test_create_news_article(self):
        """Test creating a news article."""
        article = self.create_news_article()
        self.assertEqual(article.title, "Test News Article")
        self.assertEqual(str(article), "NWS-001 - Test News Article")


class NewsletterModelTests(CommunicationsTestCase):
    """Tests for the Newsletter model."""

    def test_create_newsletter(self):
        """Test creating a newsletter."""
        newsletter = self.create_newsletter()
        self.assertEqual(newsletter.subject, "Test Newsletter Subject")
        self.assertEqual(str(newsletter), "NWL-001 - Test Newsletter")

    def test_newsletter_subscriber(self):
        """Test creating a newsletter subscriber."""
        subscriber = self.create_newsletter_subscriber()
        self.assertEqual(subscriber.email, "subscriber@example.com")
        self.assertEqual(str(subscriber), "subscriber@example.com")

    def test_newsletter_subscriber_email_unique(self):
        """Test subscriber email is unique."""
        self.create_newsletter_subscriber()
        with self.assertRaises(IntegrityError):
            self.create_newsletter_subscriber()


class PressReleaseModelTests(CommunicationsTestCase):
    """Tests for the PressRelease model."""

    def test_create_press_release(self):
        """Test creating a press release."""
        press_release = self.create_press_release()
        self.assertEqual(press_release.title, "Test Press Release")
        self.assertEqual(str(press_release), "PRS-001 - Test Press Release")


class SocialMediaModelTests(CommunicationsTestCase):
    """Tests for social media models."""

    def test_create_social_media_account(self):
        """Test creating a social media account."""
        account = self.create_social_media_account()
        self.assertEqual(account.platform, "FACEBOOK")
        self.assertEqual(str(account), "Facebook - SITADC Facebook")

    def test_social_media_account_unique_together(self):
        """Test platform/account_name uniqueness."""
        self.create_social_media_account()
        with self.assertRaises(IntegrityError):
            self.create_social_media_account()

    def test_create_social_media_post(self):
        """Test creating a social media post."""
        post = self.create_social_media_post()
        self.assertEqual(post.platform, "FACEBOOK")
        self.assertTrue("test social media post" in str(post))


class CampaignModelTests(CommunicationsTestCase):
    """Tests for campaign models."""

    def test_create_campaign(self):
        """Test creating a campaign."""
        campaign = self.create_campaign()
        self.assertEqual(campaign.title, "Test Campaign")
        self.assertEqual(str(campaign), "CAM-001 - Test Campaign")

    def test_campaign_date_validation(self):
        """Test campaign rejects inverted dates."""
        campaign = self.create_campaign(start_date="2026-12-01", end_date="2026-01-01")
        with self.assertRaises(ValidationError):
            campaign.full_clean()

    def test_create_campaign_activity(self):
        """Test creating a campaign activity."""
        activity = self.create_campaign_activity()
        self.assertEqual(activity.title, "Distribute posters")
        self.assertEqual(str(activity), "Test Campaign - Distribute posters")

    def test_campaign_activity_requires_campaign(self):
        """Test campaign activity without campaign fails."""
        with self.assertRaises(IntegrityError):
            CampaignActivity.objects.create(
                activity_type="POSTER_DISTRIBUTION",
                title="No campaign activity",
                activity_date="2026-09-01",
                created_by=self.user,
                updated_by=self.user,
            )


class MediaModelTests(CommunicationsTestCase):
    """Tests for media models."""

    def test_create_media_asset(self):
        """Test creating a media asset."""
        asset = self.create_media_asset()
        self.assertEqual(asset.title, "Test Media Asset")
        self.assertEqual(str(asset), "Test Media Asset (Image)")

    def test_create_media_album(self):
        """Test creating a media album."""
        album = self.create_media_album()
        self.assertEqual(album.title, "Test Media Album")
        self.assertEqual(str(album), "Test Media Album")

    def test_create_photograph(self):
        """Test creating a photograph."""
        photo = self.create_photograph()
        self.assertEqual(photo.title, "Test Photograph")
        self.assertEqual(str(photo), "Test Photograph")

    def test_create_video(self):
        """Test creating a video."""
        video = self.create_video()
        self.assertEqual(video.title, "Test Video")
        self.assertEqual(str(video), "Test Video")


class PublicationModelTests(CommunicationsTestCase):
    """Tests for the Publication model."""

    def test_create_publication(self):
        """Test creating a publication."""
        publication = self.create_publication()
        self.assertEqual(publication.title, "Test Publication")
        self.assertEqual(str(publication), "PUB-001 - Test Publication")


class BrandModelTests(CommunicationsTestCase):
    """Tests for brand models."""

    def test_create_brand_asset(self):
        """Test creating a brand asset."""
        asset = self.create_brand_asset()
        self.assertEqual(asset.title, "Test Logo")
        self.assertEqual(str(asset), "Test Logo (Official Logo)")

    def test_create_brand_guideline(self):
        """Test creating a brand guideline."""
        guideline = self.create_brand_guideline()
        self.assertEqual(guideline.title, "Test Brand Guideline")
        self.assertEqual(str(guideline), "Test Brand Guideline")


class WebsiteModelTests(CommunicationsTestCase):
    """Tests for website models."""

    def test_create_website_page(self):
        """Test creating a website page."""
        page = self.create_website_page()
        self.assertEqual(page.title, "Test Website Page")
        self.assertEqual(str(page), "WEB-001 - Test Website Page")

    def test_create_website_content(self):
        """Test creating website content."""
        content = self.create_website_content()
        self.assertEqual(content.section_key, "about")
        self.assertEqual(str(content), "Test Website Page - About")

    def test_website_content_unique_section_key(self):
        """Test page/section_key uniqueness."""
        page = self.create_website_page()
        self.create_website_content(page=page)
        with self.assertRaises(IntegrityError):
            self.create_website_content(page=page)


class EventCommunicationModelTests(CommunicationsTestCase):
    """Tests for the EventCommunication model."""

    def test_create_event_communication(self):
        """Test creating an event communication."""
        event = self.create_event_communication()
        self.assertEqual(event.title, "Test Event Communication")
        self.assertEqual(str(event), "EVC-001 - Test Event Communication")


class NotificationAndTimelineModelTests(CommunicationsTestCase):
    """Tests for notification and timeline models."""

    def test_create_communication_notification(self):
        """Test creating a communication notification."""
        from django.utils import timezone

        notification = CommunicationNotification.objects.create(
            notification_type="PUBLICATION_COMPLETED",
            title="Published",
            message="The communication was published.",
            recipient=self.user,
            sent_at=timezone.now(),
        )
        self.assertEqual(notification.title, "Published")

    def test_create_timeline_event(self):
        """Test creating a timeline event."""
        from django.utils import timezone

        event = CommunicationTimeline.objects.create(
            event_type="CONTENT_CREATED",
            description="A communication was created.",
            event_date=timezone.now(),
            performed_by=self.user,
            module="communications",
            reference_number="COM-001",
        )
        self.assertEqual(event.module, "communications")


class RelatedModelTests(CommunicationsTestCase):
    """Tests for model relationships."""

    def test_newsletter_subscribers_relationship(self):
        """Test newsletter to subscribers M2M."""
        newsletter = self.create_newsletter()
        subscriber = self.create_newsletter_subscriber()
        newsletter.subscribers.add(subscriber)
        self.assertEqual(newsletter.subscribers.count(), 1)

    def test_campaign_activities_relationship(self):
        """Test campaign to activities FK."""
        campaign = self.create_campaign()
        self.create_campaign_activity(campaign=campaign)
        self.assertEqual(campaign.activities.count(), 1)

    def test_news_article_featured_image_relationship(self):
        """Test news article to featured media asset FK."""
        asset = self.create_media_asset()
        article = self.create_news_article(featured_image=asset)
        self.assertEqual(article.featured_image, asset)
