"""Base test classes and utilities for communication tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.core.constants import StatusConstants

User = get_user_model()


class CommunicationsTestCase(TestCase):
    """Base test case for communications tests with common setup."""

    def setUp(self):
        """Set up test users."""
        self._ref_counters: dict[str, int] = {}
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )

    def _next_ref(self, prefix: str) -> str:
        """Generate the next reference number for a prefix."""
        self._ref_counters[prefix] = self._ref_counters.get(prefix, 0) + 1
        return f"{prefix}-{self._ref_counters[prefix]:03d}"

    def grant_communications_permissions(self, user, actions=None):
        """Grant communications permissions to a user via a test role."""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.rbac.models import Role, UserRoleAssignment

        if actions is None:
            actions = [
                "communications.view",
                "communications.view_confidential",
                "communications.create",
                "communications.update",
                "communications.delete",
                "communications.approve",
                "communications.publish",
                "communications.archive",
                "communications.restore",
                "communications.export",
                "communications.manage",
            ]
        content_type = ContentType.objects.get_for_model(Role)
        perms = []
        for code in actions:
            perm, _ = Permission.objects.get_or_create(
                codename=code,
                defaults={
                    "name": f"Can {code.split('.')[1].replace('_', ' ')} "
                    "communications",
                    "content_type": content_type,
                },
            )
            perms.append(perm)
        role = Role.objects.create(
            name="Test Communications Role",
            slug="test-communications-role",
            description="Test role for communications",
        )
        role.permissions.add(*perms)
        return UserRoleAssignment.objects.create(user=user, role=role, status="ACTIVE")

    def create_communication(self, **kwargs):
        """Helper to create a communication record."""
        from apps.communications.models import Communication

        defaults = {
            "title": "Test Communication",
            "reference_number": self._next_ref("COM"),
            "summary": "A test communication summary.",
            "body": "This is the body of the test communication.",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Communication.objects.create(**defaults)

    def create_announcement(self, **kwargs):
        """Helper to create an announcement."""
        from apps.communications.models import Announcement

        defaults = {
            "title": "Test Announcement",
            "reference_number": self._next_ref("ANN"),
            "summary": "A test announcement summary.",
            "body": "This is the body of the test announcement.",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Announcement.objects.create(**defaults)

    def create_news_article(self, **kwargs):
        """Helper to create a news article."""
        from apps.communications.models import NewsArticle

        defaults = {
            "title": "Test News Article",
            "reference_number": self._next_ref("NWS"),
            "summary": "A test news summary.",
            "body": "This is the body of the test news article.",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return NewsArticle.objects.create(**defaults)

    def create_newsletter(self, **kwargs):
        """Helper to create a newsletter."""
        from apps.communications.models import Newsletter

        defaults = {
            "title": "Test Newsletter",
            "reference_number": self._next_ref("NWL"),
            "summary": "A test newsletter summary.",
            "subject": "Test Newsletter Subject",
            "content": "This is the newsletter content.",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Newsletter.objects.create(**defaults)

    def create_newsletter_subscriber(self, **kwargs):
        """Helper to create a newsletter subscriber."""
        from apps.communications.models import NewsletterSubscriber

        defaults = {
            "email": "subscriber@example.com",
            "first_name": "Test",
            "last_name": "Subscriber",
            "is_active": True,
        }
        defaults.update(kwargs)
        return NewsletterSubscriber.objects.create(**defaults)

    def create_press_release(self, **kwargs):
        """Helper to create a press release."""
        from apps.communications.models import PressRelease

        defaults = {
            "title": "Test Press Release",
            "reference_number": self._next_ref("PRS"),
            "summary": "A test press release summary.",
            "body": "This is the body of the test press release.",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return PressRelease.objects.create(**defaults)

    def create_campaign(self, **kwargs):
        """Helper to create a campaign."""
        from apps.communications.models import Campaign

        defaults = {
            "title": "Test Campaign",
            "reference_number": self._next_ref("CAM"),
            "summary": "A test campaign summary.",
            "objectives": "Raise awareness of the initiative.",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Campaign.objects.create(**defaults)

    def create_campaign_activity(self, campaign=None, **kwargs):
        """Helper to create a campaign activity."""
        from apps.communications.models import CampaignActivity

        if campaign is None:
            campaign = self.create_campaign()
        defaults = {
            "campaign": campaign,
            "activity_type": "POSTER_DISTRIBUTION",
            "title": "Distribute posters",
            "activity_date": "2026-09-01",
            "is_completed": False,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return CampaignActivity.objects.create(**defaults)

    def create_media_asset(self, **kwargs):
        """Helper to create a media asset."""
        from apps.communications.models import MediaAsset

        defaults = {
            "asset_type": "IMAGE",
            "media_category": "OTHER",
            "title": "Test Media Asset",
            "description": "A test media asset.",
            "status": StatusConstants.ACTIVE,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return MediaAsset.objects.create(**defaults)

    def create_media_album(self, **kwargs):
        """Helper to create a media album."""
        from apps.communications.models import MediaAlbum

        defaults = {
            "title": "Test Media Album",
            "description": "A test media album.",
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return MediaAlbum.objects.create(**defaults)

    def create_photograph(self, **kwargs):
        """Helper to create a photograph."""
        from apps.communications.models import Photograph

        defaults = {
            "title": "Test Photograph",
            "caption": "A test photograph caption.",
            "media_category": "OTHER",
            "is_featured": False,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Photograph.objects.create(**defaults)

    def create_video(self, **kwargs):
        """Helper to create a video."""
        from apps.communications.models import Video

        defaults = {
            "title": "Test Video",
            "description": "A test video description.",
            "status": StatusConstants.ACTIVE,
            "is_published": False,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Video.objects.create(**defaults)

    def create_publication(self, **kwargs):
        """Helper to create a publication."""
        from apps.communications.models import Publication

        defaults = {
            "title": "Test Publication",
            "reference_number": self._next_ref("PUB"),
            "summary": "A test publication summary.",
            "publication_type": "BROCHURE",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Publication.objects.create(**defaults)

    def create_brand_asset(self, **kwargs):
        """Helper to create a brand asset."""
        from apps.communications.models import BrandAsset

        defaults = {
            "asset_type": "LOGO",
            "title": "Test Logo",
            "description": "A test brand asset.",
            "is_approved": False,
            "status": StatusConstants.DRAFT,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return BrandAsset.objects.create(**defaults)

    def create_brand_guideline(self, **kwargs):
        """Helper to create a brand guideline."""
        from apps.communications.models import BrandGuideline

        defaults = {
            "title": "Test Brand Guideline",
            "guidelines": "Always use the official logo.",
            "is_current": True,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return BrandGuideline.objects.create(**defaults)

    def create_website_page(self, **kwargs):
        """Helper to create a website page."""
        from apps.communications.models import WebsitePage

        defaults = {
            "title": "Test Website Page",
            "reference_number": self._next_ref("WEB"),
            "summary": "A test website page.",
            "slug": f"test-website-page-{self._ref_counters.get('WEB', 0)}",
            "is_published": False,
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return WebsitePage.objects.create(**defaults)

    def create_website_content(self, page=None, **kwargs):
        """Helper to create website content."""
        from apps.communications.models import WebsiteContent

        if page is None:
            page = self.create_website_page()
        defaults = {
            "page": page,
            "section_key": "about",
            "section_title": "About",
            "content": "Test content section.",
            "order": 1,
            "is_published": True,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return WebsiteContent.objects.create(**defaults)

    def create_social_media_account(self, **kwargs):
        """Helper to create a social media account."""
        from apps.communications.models import SocialMediaAccount

        defaults = {
            "platform": "FACEBOOK",
            "account_name": "SITADC Facebook",
            "handle": "sitadc",
            "is_active": True,
            "is_default": True,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return SocialMediaAccount.objects.create(**defaults)

    def create_social_media_post(self, account=None, **kwargs):
        """Helper to create a social media post."""
        from apps.communications.models import SocialMediaPost

        if account is None:
            account = self.create_social_media_account()
        defaults = {
            "account": account,
            "platform": account.platform,
            "content": "A test social media post.",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return SocialMediaPost.objects.create(**defaults)

    def create_event_communication(self, **kwargs):
        """Helper to create an event communication."""
        from apps.communications.models import EventCommunication

        defaults = {
            "title": "Test Event Communication",
            "reference_number": self._next_ref("EVC"),
            "summary": "A test event communication.",
            "event_communication_type": "ANNOUNCEMENT",
            "event_name": "Youth Summit 2026",
            "event_date": timezone.now() + timezone.timedelta(days=30),
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return EventCommunication.objects.create(**defaults)

    def create_communication_category(self, **kwargs):
        """Helper to create a communication category."""
        from apps.communications.models import CommunicationCategory

        defaults = {
            "name": "General",
            "code": f"GENERAL{self._ref_counters.get('GEN', 0) + 1}",
            "description": "General communications.",
            "is_active": True,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return CommunicationCategory.objects.create(**defaults)
