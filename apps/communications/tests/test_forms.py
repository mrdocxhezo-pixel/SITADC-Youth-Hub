"""Communication form tests."""

from __future__ import annotations

from apps.communications.forms import (
    AnnouncementForm,
    CommunicationForm,
    EventCommunicationForm,
    MediaAssetForm,
    NewsletterForm,
    NewsletterSubscriberForm,
    PressReleaseForm,
    SocialMediaAccountForm,
)

from .base import CommunicationsTestCase


class CommunicationFormTests(CommunicationsTestCase):
    """Tests for communication forms."""

    def test_communication_form_valid(self):
        """Test a valid communication form."""
        category = self.create_communication_category()
        form = CommunicationForm(
            data={
                "title": "Form Communication",
                "summary": "Summary.",
                "category": category.pk,
                "communication_type": "INTERNAL",
                "body": "Body.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "audience": "",
                "distribution_channel": "WEBSITE",
                "status": "DRAFT",
                "is_featured": False,
                "notes": "",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_communication_form_requires_body(self):
        """Test that body is required."""
        form = CommunicationForm(data={"title": "No body"})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)


class AnnouncementFormTests(CommunicationsTestCase):
    """Tests for the announcement form."""

    def test_announcement_form_valid(self):
        """Test a valid announcement form."""
        form = AnnouncementForm(
            data={
                "title": "Form Announcement",
                "summary": "Summary.",
                "communication_type": "INTERNAL",
                "body": "Body.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "audience": "",
                "status": "DRAFT",
                "is_breaking": False,
                "notes": "",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_announcement_form_inverted_dates(self):
        """Test that inverted dates are rejected."""
        form = AnnouncementForm(
            data={
                "title": "Bad Dates",
                "communication_type": "INTERNAL",
                "body": "Body.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "audience": "",
                "status": "DRAFT",
                "is_breaking": False,
                "starts_at": "2026-12-01",
                "ends_at": "2026-01-01",
            }
        )
        self.assertFalse(form.is_valid())


class NewsletterFormTests(CommunicationsTestCase):
    """Tests for the newsletter form."""

    def test_newsletter_form_valid(self):
        """Test a valid newsletter form."""
        form = NewsletterForm(
            data={
                "title": "Form Newsletter",
                "subject": "Subject",
                "summary": "Summary.",
                "content": "Content.",
                "communication_type": "INTERNAL",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "audience": "",
                "status": "DRAFT",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class NewsletterSubscriberFormTests(CommunicationsTestCase):
    """Tests for the newsletter subscriber form."""

    def test_newsletter_subscriber_form_valid(self):
        """Test a valid subscriber form."""
        form = NewsletterSubscriberForm(
            data={
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "Subscriber",
                "audience_segment": "",
                "is_active": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_newsletter_subscriber_form_invalid_email(self):
        """Test that an invalid email is rejected."""
        form = NewsletterSubscriberForm(
            data={"email": "not-an-email", "is_active": True}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class PressReleaseFormTests(CommunicationsTestCase):
    """Tests for the press release form."""

    def test_press_release_form_valid(self):
        """Test a valid press release form."""
        form = PressReleaseForm(
            data={
                "title": "Form Press Release",
                "summary": "Summary.",
                "press_release_type": "NEWS",
                "communication_type": "EXTERNAL",
                "body": "Body.",
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "audience": "",
                "status": "DRAFT",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class SocialMediaAccountFormTests(CommunicationsTestCase):
    """Tests for the social media account form."""

    def test_social_media_account_form_valid(self):
        """Test a valid social media account form."""
        form = SocialMediaAccountForm(
            data={
                "platform": "FACEBOOK",
                "account_name": "SITADC Page",
                "handle": "sitadc",
                "account_url": "https://facebook.com/sitadc",
                "is_active": True,
                "is_default": True,
                "notes": "",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class MediaAssetFormTests(CommunicationsTestCase):
    """Tests for the media asset form."""

    def test_media_asset_form_requires_file(self):
        """Test that media asset file is required."""
        form = MediaAssetForm(
            data={
                "asset_type": "IMAGE",
                "media_category": "OTHER",
                "title": "No file asset",
                "status": "DRAFT",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)


class EventCommunicationFormTests(CommunicationsTestCase):
    """Tests for the event communication form."""

    def test_event_communication_form_valid(self):
        """Test a valid event communication form."""
        form = EventCommunicationForm(
            data={
                "title": "Form Event",
                "summary": "Summary.",
                "event_communication_type": "ANNOUNCEMENT",
                "communication_type": "INTERNAL",
                "event_name": "Youth Summit",
                "event_date": "2026-10-15 09:00:00",
                "location": "Hall A",
                "attendee_count": 0,
                "priority": "MEDIUM",
                "confidentiality_level": "INTERNAL",
                "audience": "",
                "status": "DRAFT",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
