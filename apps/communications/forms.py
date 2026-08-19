"""Forms for Communication and Media (Phase 30)."""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import (
    Announcement,
    BrandAsset,
    BrandGuideline,
    Campaign,
    CampaignActivity,
    Communication,
    CommunicationCategory,
    CommunicationNotification,
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


class BaseCommunicationForm(forms.ModelForm):
    """Base form applying Bootstrap 5 styling to all widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        text_types = (
            forms.TextInput | forms.EmailInput | forms.URLInput | forms.PasswordInput
        )
        for _field_name, field in self.fields.items():
            if isinstance(field.widget, text_types):
                field.widget.attrs.update({"class": "form-control"})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": "form-control", "rows": 3})
            elif isinstance(field.widget, forms.Select | forms.SelectMultiple):
                field.widget.attrs.update({"class": "form-select"})
            elif isinstance(
                field.widget,
                forms.DateInput | forms.DateTimeInput | forms.FileInput,
            ):
                field.widget.attrs.update({"class": "form-control"})
            elif isinstance(field.widget, forms.CheckboxInput | forms.RadioSelect):
                field.widget.attrs.update({"class": "form-check-input"})


class CommunicationCategoryForm(BaseCommunicationForm):
    class Meta:
        model = CommunicationCategory
        fields = ["name", "code", "description", "is_active"]


class CommunicationForm(BaseCommunicationForm):
    class Meta:
        model = Communication
        fields = [
            "title",
            "summary",
            "category",
            "communication_type",
            "body",
            "priority",
            "confidentiality_level",
            "audience",
            "distribution_channel",
            "publication_date",
            "scheduled_date",
            "author",
            "reviewer",
            "approver",
            "is_featured",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "publication_date": forms.DateInput(attrs={"type": "date"}),
            "scheduled_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class AnnouncementForm(BaseCommunicationForm):
    class Meta:
        model = Announcement
        fields = [
            "title",
            "summary",
            "communication_type",
            "body",
            "is_breaking",
            "priority",
            "confidentiality_level",
            "audience",
            "starts_at",
            "ends_at",
            "target_roles",
            "publication_date",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "starts_at": forms.DateInput(attrs={"type": "date"}),
            "ends_at": forms.DateInput(attrs={"type": "date"}),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")
        if starts_at and ends_at and ends_at < starts_at:
            raise ValidationError(_("End date cannot be before the start date."))
        return cleaned_data


class NewsArticleForm(BaseCommunicationForm):
    class Meta:
        model = NewsArticle
        fields = [
            "title",
            "summary",
            "news_category",
            "communication_type",
            "body",
            "is_featured",
            "is_breaking",
            "priority",
            "confidentiality_level",
            "audience",
            "scheduled_publication",
            "publication_date",
            "featured_image",
            "allow_comments",
            "author",
            "reviewer",
            "approver",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "scheduled_publication": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }


class NewsletterForm(BaseCommunicationForm):
    class Meta:
        model = Newsletter
        fields = [
            "title",
            "subject",
            "summary",
            "content",
            "template_name",
            "communication_type",
            "priority",
            "confidentiality_level",
            "audience",
            "scheduled_send",
            "publication_date",
            "subscribers",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "scheduled_send": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }


class NewsletterSubscriberForm(BaseCommunicationForm):
    class Meta:
        model = NewsletterSubscriber
        fields = [
            "email",
            "first_name",
            "last_name",
            "audience_segment",
            "is_active",
        ]


class PressReleaseForm(BaseCommunicationForm):
    class Meta:
        model = PressRelease
        fields = [
            "title",
            "summary",
            "press_release_type",
            "communication_type",
            "body",
            "media_contacts",
            "embargo_date",
            "release_date",
            "publication_date",
            "attachment",
            "priority",
            "confidentiality_level",
            "audience",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "embargo_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "release_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }


class SocialMediaAccountForm(BaseCommunicationForm):
    class Meta:
        model = SocialMediaAccount
        fields = [
            "platform",
            "account_name",
            "handle",
            "account_url",
            "is_active",
            "is_default",
            "notes",
        ]


class SocialMediaPostForm(BaseCommunicationForm):
    class Meta:
        model = SocialMediaPost
        fields = [
            "account",
            "platform",
            "content",
            "media",
            "campaign",
            "scheduled_time",
            "status",
        ]
        widgets = {
            "scheduled_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class CampaignForm(BaseCommunicationForm):
    class Meta:
        model = Campaign
        fields = [
            "title",
            "summary",
            "campaign_type",
            "communication_type",
            "objectives",
            "target_audience",
            "channels",
            "start_date",
            "end_date",
            "priority",
            "confidentiality_level",
            "budget_reference",
            "budget_amount",
            "key_performance_indicators",
            "results",
            "lessons_learned",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }


class CampaignActivityForm(BaseCommunicationForm):
    class Meta:
        model = CampaignActivity
        fields = [
            "campaign",
            "activity_type",
            "title",
            "description",
            "activity_date",
            "channel",
            "is_completed",
        ]
        widgets = {
            "activity_date": forms.DateInput(attrs={"type": "date"}),
        }


class MediaAlbumForm(BaseCommunicationForm):
    class Meta:
        model = MediaAlbum
        fields = ["title", "description", "is_featured"]


class MediaAssetForm(BaseCommunicationForm):
    class Meta:
        model = MediaAsset
        fields = [
            "asset_type",
            "media_category",
            "title",
            "description",
            "file",
            "thumbnail",
            "album",
            "tags",
            "mime_type",
            "version",
            "copyright_info",
            "licensing_info",
            "confidentiality_level",
            "programme",
            "project",
            "status",
        ]


class PhotographForm(BaseCommunicationForm):
    class Meta:
        model = Photograph
        fields = [
            "title",
            "caption",
            "image",
            "photographer",
            "taken_date",
            "programme",
            "project",
            "event_name",
            "media_category",
            "is_featured",
        ]
        widgets = {
            "taken_date": forms.DateInput(attrs={"type": "date"}),
        }


class VideoForm(BaseCommunicationForm):
    class Meta:
        model = Video
        fields = [
            "title",
            "description",
            "video_file",
            "thumbnail",
            "captions",
            "programme",
            "project",
            "duration_seconds",
            "is_streamable",
            "download_allowed",
            "is_published",
            "status",
        ]


class PublicationForm(BaseCommunicationForm):
    class Meta:
        model = Publication
        fields = [
            "title",
            "summary",
            "publication_type",
            "communication_type",
            "file",
            "cover_image",
            "isbn",
            "page_count",
            "version",
            "priority",
            "confidentiality_level",
            "audience",
            "publication_date",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }


class BrandAssetForm(BaseCommunicationForm):
    class Meta:
        model = BrandAsset
        fields = [
            "asset_type",
            "title",
            "description",
            "file",
            "usage_guidelines",
            "is_approved",
            "version",
            "confidentiality_level",
            "status",
        ]


class BrandGuidelineForm(BaseCommunicationForm):
    class Meta:
        model = BrandGuideline
        fields = [
            "title",
            "description",
            "guidelines",
            "file",
            "effective_date",
            "is_current",
        ]
        widgets = {
            "effective_date": forms.DateInput(attrs={"type": "date"}),
        }


class WebsitePageForm(BaseCommunicationForm):
    class Meta:
        model = WebsitePage
        fields = [
            "title",
            "summary",
            "page_type",
            "communication_type",
            "slug",
            "url_path",
            "is_published",
            "priority",
            "confidentiality_level",
            "audience",
            "publication_date",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }


class WebsiteContentForm(BaseCommunicationForm):
    class Meta:
        model = WebsiteContent
        fields = [
            "page",
            "section_key",
            "section_title",
            "content",
            "order",
            "is_published",
        ]


class EventCommunicationForm(BaseCommunicationForm):
    class Meta:
        model = EventCommunication
        fields = [
            "title",
            "summary",
            "event_communication_type",
            "communication_type",
            "event_name",
            "event_date",
            "location",
            "speaker_profiles",
            "programme_schedule",
            "thank_you_message",
            "attendee_count",
            "priority",
            "confidentiality_level",
            "audience",
            "publication_date",
            "programme",
            "project",
            "region",
            "district",
            "community",
            "status",
            "notes",
        ]
        widgets = {
            "event_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }


class CommunicationNotificationForm(BaseCommunicationForm):
    class Meta:
        model = CommunicationNotification
        fields = [
            "notification_type",
            "title",
            "message",
            "recipient",
            "is_read",
        ]
