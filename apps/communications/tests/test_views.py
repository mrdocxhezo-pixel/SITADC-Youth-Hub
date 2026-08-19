"""Communication view tests."""

from __future__ import annotations

from django.urls import reverse

from apps.core.constants import StatusConstants

from .base import CommunicationsTestCase


class CommunicationViewTests(CommunicationsTestCase):
    """Tests for communication views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)
        self.communication = self.create_communication()

    # Dashboard Tests
    def test_dashboard(self):
        """Test the communications dashboard."""
        response = self.client.get(reverse("communications:communications_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Communications Dashboard")

    # Communication Tests
    def test_communication_list(self):
        """Test the communication list view."""
        response = self.client.get(reverse("communications:communication_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Communication")

    def test_communication_detail(self):
        """Test the communication detail view."""
        response = self.client.get(
            reverse("communications:communication_detail", args=[self.communication.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Communication")

    def test_communication_create(self):
        """Test the communication create view."""
        category = self.create_communication_category()
        response = self.client.post(
            reverse("communications:communication_create"),
            {
                "title": "Created Communication",
                "summary": "Summary.",
                "category": category.pk,
                "communication_type": "INTERNAL",
                "body": "Body.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "distribution_channel": "WEBSITE",
                "status": "DRAFT",
                "is_featured": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("communications:communication_list"))

    def test_communication_update(self):
        """Test the communication update view."""
        response = self.client.post(
            reverse(
                "communications:communication_update",
                args=[self.communication.pk],
            ),
            {
                "title": "Updated Communication",
                "summary": "Summary.",
                "communication_type": "INTERNAL",
                "body": "Body.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "distribution_channel": "WEBSITE",
                "status": "DRAFT",
                "is_featured": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.communication.refresh_from_db()
        self.assertEqual(self.communication.title, "Updated Communication")

    def test_communication_delete(self):
        """Test the communication delete view."""
        response = self.client.post(
            reverse(
                "communications:communication_delete",
                args=[self.communication.pk],
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            self.communication.__class__.objects.filter(
                pk=self.communication.pk
            ).exists()
        )

    def test_communication_approve(self):
        """Test the communication approve view."""
        comm = self.create_communication(status=StatusConstants.PENDING_REVIEW)
        response = self.client.post(
            reverse("communications:communication_approve", args=[comm.pk])
        )
        self.assertEqual(response.status_code, 302)
        comm.refresh_from_db()
        self.assertEqual(comm.status, StatusConstants.APPROVED)

    def test_communication_publish(self):
        """Test the communication publish view."""
        comm = self.create_communication(status=StatusConstants.APPROVED)
        response = self.client.post(
            reverse("communications:communication_publish", args=[comm.pk])
        )
        self.assertEqual(response.status_code, 302)
        comm.refresh_from_db()
        self.assertEqual(comm.status, StatusConstants.ACTIVE)

    def test_communication_archive(self):
        """Test the communication archive view."""
        comm = self.create_communication(status=StatusConstants.ACTIVE)
        response = self.client.post(
            reverse("communications:communication_archive", args=[comm.pk])
        )
        self.assertEqual(response.status_code, 302)
        comm.refresh_from_db()
        self.assertEqual(comm.status, StatusConstants.ARCHIVED)

    def test_communication_restore(self):
        """Test the communication restore view."""
        comm = self.create_communication(status=StatusConstants.ARCHIVED)
        response = self.client.post(
            reverse("communications:communication_restore", args=[comm.pk])
        )
        self.assertEqual(response.status_code, 302)
        comm.refresh_from_db()
        self.assertEqual(comm.status, StatusConstants.DRAFT)


class AnnouncementViewTests(CommunicationsTestCase):
    """Tests for announcement views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)
        self.announcement = self.create_announcement()

    def test_announcement_list(self):
        """Test the announcement list view."""
        response = self.client.get(reverse("communications:announcement_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Announcement")

    def test_announcement_create(self):
        """Test the announcement create view."""
        response = self.client.post(
            reverse("communications:announcement_create"),
            {
                "title": "Created Announcement",
                "summary": "Summary.",
                "communication_type": "INTERNAL",
                "body": "Body.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "status": "DRAFT",
                "is_breaking": False,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_announcement_publish(self):
        """Test the announcement publish view."""
        announcement = self.create_announcement(
            status=StatusConstants.APPROVED,
            reference_number="ANN-002",
        )
        response = self.client.post(
            reverse(
                "communications:announcement_publish",
                args=[announcement.pk],
            )
        )
        self.assertEqual(response.status_code, 302)
        announcement.refresh_from_db()
        self.assertEqual(announcement.status, StatusConstants.ACTIVE)


class NewsArticleViewTests(CommunicationsTestCase):
    """Tests for news article views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)

    def test_news_article_list(self):
        """Test the news article list view."""
        self.create_news_article()
        response = self.client.get(reverse("communications:news_article_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test News Article")

    def test_news_article_create(self):
        """Test the news article create view."""
        response = self.client.post(
            reverse("communications:news_article_create"),
            {
                "title": "Created News",
                "summary": "Summary.",
                "news_category": "GENERAL",
                "communication_type": "EXTERNAL",
                "body": "Body.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "status": "DRAFT",
                "is_featured": False,
                "is_breaking": False,
                "allow_comments": False,
            },
        )
        self.assertEqual(response.status_code, 302)


class NewsletterViewTests(CommunicationsTestCase):
    """Tests for newsletter views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)
        self.newsletter = self.create_newsletter()

    def test_newsletter_list(self):
        """Test the newsletter list view."""
        response = self.client.get(reverse("communications:newsletter_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Newsletter")

    def test_newsletter_detail(self):
        """Test the newsletter detail view."""
        response = self.client.get(
            reverse("communications:newsletter_detail", args=[self.newsletter.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_newsletter_distribute(self):
        """Test the newsletter distribute view."""
        newsletter = self.create_newsletter(
            status=StatusConstants.APPROVED,
            reference_number="NWL-002",
        )
        response = self.client.post(
            reverse(
                "communications:newsletter_distribute",
                args=[newsletter.pk],
            )
        )
        self.assertEqual(response.status_code, 302)
        newsletter.refresh_from_db()
        self.assertEqual(newsletter.status, StatusConstants.ACTIVE)


class NewsletterSubscriberViewTests(CommunicationsTestCase):
    """Tests for newsletter subscriber views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)

    def test_newsletter_subscriber_list(self):
        """Test the subscriber list view."""
        self.create_newsletter_subscriber()
        response = self.client.get(reverse("communications:newsletter_subscriber_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "subscriber@example.com")


class PressReleaseViewTests(CommunicationsTestCase):
    """Tests for press release views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)

    def test_press_release_list(self):
        """Test the press release list view."""
        self.create_press_release()
        response = self.client.get(reverse("communications:press_release_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Press Release")

    def test_press_release_publish(self):
        """Test the press release publish view."""
        pr = self.create_press_release(
            status=StatusConstants.APPROVED,
            reference_number="PRS-002",
        )
        response = self.client.post(
            reverse("communications:press_release_publish", args=[pr.pk])
        )
        self.assertEqual(response.status_code, 302)
        pr.refresh_from_db()
        self.assertEqual(pr.status, StatusConstants.ACTIVE)


class SocialMediaViewTests(CommunicationsTestCase):
    """Tests for social media views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)
        self.account = self.create_social_media_account()

    def test_social_media_account_list(self):
        """Test the social media account list view."""
        response = self.client.get(reverse("communications:social_media_account_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SITADC Facebook")

    def test_social_media_post_list(self):
        """Test the social media post list view."""
        self.create_social_media_post(account=self.account)
        response = self.client.get(reverse("communications:social_media_post_list"))
        self.assertEqual(response.status_code, 200)

    def test_social_media_post_publish(self):
        """Test the social media post publish view."""
        post = self.create_social_media_post(
            account=self.account,
            status=StatusConstants.APPROVED,
        )
        response = self.client.post(
            reverse("communications:social_media_post_publish", args=[post.pk])
        )
        self.assertEqual(response.status_code, 302)
        post.refresh_from_db()
        self.assertEqual(post.status, StatusConstants.ACTIVE)


class CampaignViewTests(CommunicationsTestCase):
    """Tests for campaign views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)
        self.campaign = self.create_campaign()

    def test_campaign_list(self):
        """Test the campaign list view."""
        response = self.client.get(reverse("communications:campaign_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Campaign")

    def test_campaign_detail(self):
        """Test the campaign detail view."""
        response = self.client.get(
            reverse("communications:campaign_detail", args=[self.campaign.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_campaign_create(self):
        """Test the campaign create view."""
        response = self.client.post(
            reverse("communications:campaign_create"),
            {
                "title": "Created Campaign",
                "summary": "Summary.",
                "campaign_type": "AWARENESS",
                "communication_type": "EXTERNAL",
                "objectives": "Raise awareness.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "status": "DRAFT",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_campaign_launch(self):
        """Test the campaign launch view."""
        campaign = self.create_campaign(
            status=StatusConstants.APPROVED,
            reference_number="CAM-002",
        )
        response = self.client.post(
            reverse("communications:campaign_launch", args=[campaign.pk])
        )
        self.assertEqual(response.status_code, 302)
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, StatusConstants.ACTIVE)


class CampaignActivityViewTests(CommunicationsTestCase):
    """Tests for campaign activity views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)

    def test_campaign_activity_list(self):
        """Test the campaign activity list view."""
        self.create_campaign_activity()
        response = self.client.get(reverse("communications:campaign_activity_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Distribute posters")


class MediaViewTests(CommunicationsTestCase):
    """Tests for media views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)

    def test_media_album_list(self):
        """Test the media album list view."""
        self.create_media_album()
        response = self.client.get(reverse("communications:media_album_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Media Album")

    def test_media_asset_list(self):
        """Test the media asset list view."""
        self.create_media_asset()
        response = self.client.get(reverse("communications:media_asset_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Media Asset")

    def test_media_asset_publish(self):
        """Test the media asset publish view (draft to active)."""
        asset = self.create_media_asset(status=StatusConstants.DRAFT)
        response = self.client.post(
            reverse("communications:media_asset_publish", args=[asset.pk])
        )
        self.assertEqual(response.status_code, 302)
        asset.refresh_from_db()
        self.assertEqual(asset.status, StatusConstants.ACTIVE)

    def test_photograph_list(self):
        """Test the photograph list view."""
        self.create_photograph()
        response = self.client.get(reverse("communications:photograph_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Photograph")

    def test_video_list(self):
        """Test the video list view."""
        self.create_video()
        response = self.client.get(reverse("communications:video_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Video")


class PublicationViewTests(CommunicationsTestCase):
    """Tests for publication views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)

    def test_publication_list(self):
        """Test the publication list view."""
        self.create_publication()
        response = self.client.get(reverse("communications:publication_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Publication")

    def test_publication_publish(self):
        """Test the publication publish view."""
        pub = self.create_publication(
            status=StatusConstants.APPROVED,
            reference_number="PUB-002",
        )
        response = self.client.post(
            reverse("communications:publication_publish", args=[pub.pk])
        )
        self.assertEqual(response.status_code, 302)
        pub.refresh_from_db()
        self.assertEqual(pub.status, StatusConstants.ACTIVE)


class BrandViewTests(CommunicationsTestCase):
    """Tests for brand views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)

    def test_brand_asset_list(self):
        """Test the brand asset list view."""
        self.create_brand_asset()
        response = self.client.get(reverse("communications:brand_asset_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Logo")

    def test_brand_guideline_list(self):
        """Test the brand guideline list view."""
        self.create_brand_guideline()
        response = self.client.get(reverse("communications:brand_guideline_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Brand Guideline")


class WebsiteViewTests(CommunicationsTestCase):
    """Tests for website views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)
        self.page = self.create_website_page()

    def test_website_page_list(self):
        """Test the website page list view."""
        response = self.client.get(reverse("communications:website_page_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Website Page")

    def test_website_page_detail(self):
        """Test the website page detail view."""
        response = self.client.get(
            reverse("communications:website_page_detail", args=[self.page.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_website_content_list(self):
        """Test the website content list view."""
        self.create_website_content(page=self.page)
        response = self.client.get(reverse("communications:website_content_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About")


class EventCommunicationViewTests(CommunicationsTestCase):
    """Tests for event communication views."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)
        self.event = self.create_event_communication()

    def test_event_communication_list(self):
        """Test the event communication list view."""
        response = self.client.get(reverse("communications:event_communication_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event Communication")

    def test_event_communication_detail(self):
        """Test the event communication detail view."""
        response = self.client.get(
            reverse(
                "communications:event_communication_detail",
                args=[self.event.pk],
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_event_communication_publish(self):
        """Test the event communication publish view."""
        event = self.create_event_communication(
            status=StatusConstants.APPROVED,
            reference_number="EVC-002",
        )
        response = self.client.post(
            reverse(
                "communications:event_communication_publish",
                args=[event.pk],
            )
        )
        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.status, StatusConstants.ACTIVE)


class TimelineViewTests(CommunicationsTestCase):
    """Tests for the timeline view."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)
        self.client.force_login(self.user)

    def test_timeline_list(self):
        """Test the timeline list view."""
        from django.utils import timezone

        from apps.communications.models import CommunicationTimeline

        CommunicationTimeline.objects.create(
            event_type="CONTENT_CREATED",
            description="A communication was created.",
            event_date=timezone.now(),
            performed_by=self.user,
            module="communications",
        )
        response = self.client.get(reverse("communications:timeline_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A communication was created.")


class PermissionEnforcementTests(CommunicationsTestCase):
    """Tests that server-side authorization is enforced."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.communication = self.create_communication()

    def test_view_requires_login(self):
        """Test that anonymous users are redirected to login."""
        self.client.logout()
        response = self.client.get(reverse("communications:communication_list"))
        self.assertIn(response.status_code, [302, 403])

    def test_create_requires_permission(self):
        """Test that users without permission get a 403 on create."""
        response = self.client.get(reverse("communications:communication_create"))
        self.assertEqual(response.status_code, 403)

    def test_update_requires_permission(self):
        """Test that users without permission get a 403 on update."""
        response = self.client.get(
            reverse(
                "communications:communication_update",
                args=[self.communication.pk],
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_approve_requires_permission(self):
        """Test that users without permission get a 403 on approve."""
        response = self.client.get(
            reverse(
                "communications:communication_approve",
                args=[self.communication.pk],
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_view_only_user_can_list(self):
        """Test that a view-only user can list but not create."""
        self.grant_communications_permissions(
            self.user, actions=["communications.view"]
        )
        response = self.client.get(reverse("communications:communication_list"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("communications:communication_create"))
        self.assertEqual(response.status_code, 403)
