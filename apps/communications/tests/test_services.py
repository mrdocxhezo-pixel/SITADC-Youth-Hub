"""Communication service tests."""

from __future__ import annotations

from apps.communications.exceptions import InvalidStateTransitionError
from apps.communications.models import CommunicationTimeline
from apps.communications.services import (
    CampaignService,
    CommunicationService,
    MediaAssetService,
    NewsletterService,
    allocate_reference,
    create_notification,
    get_dashboard_analytics,
)
from apps.core.constants import StatusConstants

from .base import CommunicationsTestCase


class CommunicationServiceTests(CommunicationsTestCase):
    """Tests for the CommunicationService."""

    def test_create_communication_service(self):
        """Test creating a communication through the service."""
        service = CommunicationService(user=self.user)
        data = {
            "title": "Service Communication",
            "summary": "Created through the service.",
            "body": "Body content.",
            "status": StatusConstants.DRAFT,
        }
        instance = service.create(data)
        self.assertTrue(instance.reference_number)
        self.assertEqual(instance.title, "Service Communication")
        self.assertEqual(instance.created_by, self.user)
        self.assertEqual(instance.status, StatusConstants.DRAFT)
        self.assertEqual(CommunicationTimeline.objects.count(), 1)

    def test_create_assigns_reference_number(self):
        """Test that create allocates a reference number."""
        service = CommunicationService(user=self.user)
        instance = service.create({"title": "Ref Test", "body": "Body."})
        self.assertIsNotNone(instance.reference_number)

    def test_update_communication_service(self):
        """Test updating a communication through the service."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication()
        updated = service.update(instance, {"title": "Updated Title"})
        updated.refresh_from_db()
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.updated_by, self.user)
        self.assertEqual(CommunicationTimeline.objects.count(), 1)

    def test_submit_for_review(self):
        """Test transitioning to pending review."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.DRAFT)
        service.submit_for_review(self.user, instance)
        instance.refresh_from_db()
        self.assertEqual(instance.status, StatusConstants.PENDING_REVIEW)
        self.assertEqual(instance.reviewer, self.user)

    def test_submit_for_review_rejects_non_draft(self):
        """Test that only draft records can be submitted."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.APPROVED)
        with self.assertRaises(InvalidStateTransitionError):
            service.submit_for_review(self.user, instance)

    def test_approve(self):
        """Test approving a communication."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.PENDING_REVIEW)
        service.approve(self.user, instance)
        instance.refresh_from_db()
        self.assertEqual(instance.status, StatusConstants.APPROVED)
        self.assertEqual(instance.approver, self.user)

    def test_approve_rejects_unsubmitted(self):
        """Test that only reviewed records can be approved."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.DRAFT)
        with self.assertRaises(InvalidStateTransitionError):
            service.approve(self.user, instance)

    def test_publish(self):
        """Test publishing a communication."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.APPROVED)
        service.publish(self.user, instance)
        instance.refresh_from_db()
        self.assertEqual(instance.status, StatusConstants.ACTIVE)
        self.assertIsNotNone(instance.published_at)

    def test_publish_rejects_unapproved(self):
        """Test that only approved records can be published."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.DRAFT)
        with self.assertRaises(InvalidStateTransitionError):
            service.publish(self.user, instance)

    def test_archive(self):
        """Test archiving a communication."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.ACTIVE)
        service.archive(self.user, instance)
        instance.refresh_from_db()
        self.assertEqual(instance.status, StatusConstants.ARCHIVED)

    def test_restore(self):
        """Test restoring an archived communication."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.ARCHIVED)
        service.restore(self.user, instance)
        instance.refresh_from_db()
        self.assertEqual(instance.status, StatusConstants.DRAFT)

    def test_restore_rejects_non_archived(self):
        """Test that only archived records can be restored."""
        service = CommunicationService(user=self.user)
        instance = self.create_communication(status=StatusConstants.DRAFT)
        with self.assertRaises(InvalidStateTransitionError):
            service.restore(self.user, instance)

    def test_delete_record(self):
        """Test deleting a communication records a timeline event."""
        from apps.communications.models import Communication

        instance = self.create_communication()
        service = CommunicationService(user=self.user)
        service.delete_record(self.user, instance)
        self.assertEqual(Communication.objects.count(), 0)
        self.assertEqual(CommunicationTimeline.objects.count(), 1)

    def test_allocate_reference_idempotent(self):
        """Test that allocate_reference leaves existing references untouched."""
        instance = self.create_communication()
        original = instance.reference_number
        allocate_reference(self.user, instance, "communication")
        instance.refresh_from_db()
        self.assertEqual(instance.reference_number, original)


class CampaignServiceTests(CommunicationsTestCase):
    """Tests for the CampaignService."""

    def test_launch_campaign(self):
        """Test launching an approved campaign."""
        service = CampaignService(user=self.user)
        campaign = self.create_campaign(status=StatusConstants.APPROVED)
        service.launch(self.user, campaign)
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, StatusConstants.ACTIVE)

    def test_launch_rejects_unapproved(self):
        """Test that only approved campaigns can be launched."""
        service = CampaignService(user=self.user)
        campaign = self.create_campaign(status=StatusConstants.DRAFT)
        with self.assertRaises(InvalidStateTransitionError):
            service.launch(self.user, campaign)


class NewsletterServiceTests(CommunicationsTestCase):
    """Tests for the NewsletterService."""

    def test_distribute_newsletter(self):
        """Test distributing a newsletter to its subscribers."""
        service = NewsletterService(user=self.user)
        newsletter = self.create_newsletter(status=StatusConstants.APPROVED)
        subscriber = self.create_newsletter_subscriber()
        newsletter.subscribers.add(subscriber)
        service.distribute(self.user, newsletter)
        newsletter.refresh_from_db()
        self.assertEqual(newsletter.status, StatusConstants.ACTIVE)
        self.assertEqual(newsletter.sent_count, 1)
        self.assertIsNotNone(newsletter.sent_at)

    def test_distribute_rejects_draft(self):
        """Test that draft newsletters cannot be distributed."""
        service = NewsletterService(user=self.user)
        newsletter = self.create_newsletter(status=StatusConstants.DRAFT)
        with self.assertRaises(InvalidStateTransitionError):
            service.distribute(self.user, newsletter)


class MediaAssetServiceTests(CommunicationsTestCase):
    """Tests for the MediaAssetService."""

    def test_publish_media_asset(self):
        """Test publishing a draft media asset."""
        service = MediaAssetService(user=self.user)
        asset = self.create_media_asset(status=StatusConstants.DRAFT)
        service.publish(self.user, asset)
        asset.refresh_from_db()
        self.assertEqual(asset.status, StatusConstants.ACTIVE)

    def test_publish_rejects_non_draft(self):
        """Test that only draft media assets can be published."""
        service = MediaAssetService(user=self.user)
        asset = self.create_media_asset(status=StatusConstants.ACTIVE)
        with self.assertRaises(InvalidStateTransitionError):
            service.publish(self.user, asset)


class NotificationServiceTests(CommunicationsTestCase):
    """Tests for notification creation."""

    def test_create_notification(self):
        """Test creating a notification."""
        notification = create_notification(
            recipient=self.user,
            notification_type="PUBLICATION_COMPLETED",
            title="Published",
            message="Your communication was published.",
        )
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, "Published")


class DashboardAnalyticsTests(CommunicationsTestCase):
    """Tests for dashboard analytics."""

    def test_get_dashboard_analytics(self):
        """Test dashboard analytics counts."""
        self.create_communication(status=StatusConstants.ACTIVE)
        self.create_announcement()
        self.create_news_article()
        self.create_campaign(status=StatusConstants.ACTIVE)
        self.create_press_release()
        self.create_publication()
        self.create_media_asset(status=StatusConstants.ACTIVE)
        self.create_event_communication()
        analytics = get_dashboard_analytics(self.user)
        self.assertEqual(analytics["total_communications"], 1)
        self.assertEqual(analytics["active_communications"], 1)
        self.assertEqual(analytics["announcements"], 1)
        self.assertEqual(analytics["news_articles"], 1)
        self.assertEqual(analytics["campaigns"], 1)
        self.assertEqual(analytics["active_campaigns"], 1)
        self.assertEqual(analytics["press_releases"], 1)
        self.assertEqual(analytics["publications"], 1)
        self.assertEqual(analytics["media_assets"], 1)
        self.assertEqual(analytics["event_communications"], 1)
