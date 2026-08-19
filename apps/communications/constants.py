"""Constants for the Communication and Media module (Phase 30)."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class CommunicationType(models.TextChoices):
    """Communication domains supported by the module."""

    INTERNAL = "INTERNAL", _("Internal")
    EXTERNAL = "EXTERNAL", _("External")
    PUBLIC_RELATIONS = "PUBLIC_RELATIONS", _("Public Relations")
    CORPORATE = "CORPORATE", _("Corporate")
    DIGITAL = "DIGITAL", _("Digital")
    ADVOCACY = "ADVOCACY", _("Advocacy & Awareness")
    EVENT = "EVENT", _("Event Communication")
    KNOWLEDGE = "KNOWLEDGE", _("Knowledge Dissemination")


class Priority(models.TextChoices):
    """Priority levels applied to communication records."""

    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class ConfidentialityLevel(models.TextChoices):
    """Confidentiality classifications inherited by communication records."""

    PUBLIC = "PUBLIC", _("Public")
    INTERNAL = "INTERNAL", _("Internal")
    RESTRICTED = "RESTRICTED", _("Restricted")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL", _("Highly Confidential")


class AudienceType(models.TextChoices):
    """Target audiences for communications."""

    GENERAL_PUBLIC = "GENERAL_PUBLIC", _("General Public")
    MEMBERS = "MEMBERS", _("Members")
    VOLUNTEERS = "VOLUNTEERS", _("Volunteers")
    BENEFICIARIES = "BENEFICIARIES", _("Beneficiaries")
    STAFF = "STAFF", _("Staff")
    LEADERSHIP = "LEADERSHIP", _("Leadership")
    PARTNERS = "PARTNERS", _("Partners")
    DONORS = "DONORS", _("Donors")
    SPONSORS = "SPONSORS", _("Sponsors")
    STAKEHOLDERS = "STAKEHOLDERS", _("Stakeholders")
    MEDIA = "MEDIA", _("Media")
    COMMUNITIES = "COMMUNITIES", _("Communities")


class DistributionChannel(models.TextChoices):
    """Distribution channels used for communications."""

    WEBSITE = "WEBSITE", _("Website")
    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    SOCIAL_MEDIA = "SOCIAL_MEDIA", _("Social Media")
    PRESS = "PRESS", _("Press")
    NEWSLETTER = "NEWSLETTER", _("Newsletter")
    PRINT = "PRINT", _("Print")
    COMMUNITY_MEETING = "COMMUNITY_MEETING", _("Community Meeting")
    PUSH_NOTIFICATION = "PUSH_NOTIFICATION", _("Push Notification")


class NewsCategory(models.TextChoices):
    """News article categories."""

    GENERAL = "GENERAL", _("General")
    PROGRAMME = "PROGRAMME", _("Programme")
    PROJECT = "PROJECT", _("Project")
    ORGANIZATION = "ORGANIZATION", _("Organization")
    LEADERSHIP = "LEADERSHIP", _("Leadership")
    SUCCESS_STORY = "SUCCESS_STORY", _("Success Story")
    EVENTS = "EVENTS", _("Events")
    PARTNERSHIP = "PARTNERSHIP", _("Partnership")
    ADVOCACY = "ADVOCACY", _("Advocacy")
    ANNOUNCEMENT = "ANNOUNCEMENT", _("Announcement")


class PressReleaseType(models.TextChoices):
    """Press release categories."""

    NEWS = "NEWS", _("News Release")
    PRODUCT = "PRODUCT", _("Product / Initiative Release")
    CRISIS = "CRISIS", _("Crisis Statement")
    ANNOUNCEMENT = "ANNOUNCEMENT", _("Announcement")
    STATEMENT = "STATEMENT", _("Official Statement")


class SocialPlatform(models.TextChoices):
    """Supported social media platforms."""

    FACEBOOK = "FACEBOOK", _("Facebook")
    X = "X", _("X (Twitter)")
    INSTAGRAM = "INSTAGRAM", _("Instagram")
    LINKEDIN = "LINKEDIN", _("LinkedIn")
    YOUTUBE = "YOUTUBE", _("YouTube")
    TIKTOK = "TIKTOK", _("TikTok")
    WHATSAPP = "WHATSAPP", _("WhatsApp")


class WebsitePageType(models.TextChoices):
    """Website page categories."""

    HOME = "HOME", _("Home")
    NEWS = "NEWS", _("News")
    PROGRAMME = "PROGRAMME", _("Programme")
    PROJECT = "PROJECT", _("Project")
    EVENT = "EVENT", _("Event")
    PUBLICATION = "PUBLICATION", _("Publication")
    SUCCESS_STORY = "SUCCESS_STORY", _("Success Story")
    LEADERSHIP = "LEADERSHIP", _("Leadership")
    PARTNER = "PARTNER", _("Partner")
    CONTACT = "CONTACT", _("Contact")
    OTHER = "OTHER", _("Other")


class CampaignType(models.TextChoices):
    """Communication campaign categories."""

    AWARENESS = "AWARENESS", _("Awareness")
    ADVOCACY = "ADVOCACY", _("Advocacy")
    FUNDRAISING = "FUNDRAISING", _("Fundraising / Resource Mobilization")
    BRAND = "BRAND", _("Brand")
    MEMBERSHIP = "MEMBERSHIP", _("Membership")
    RECOGNITION = "RECOGNITION", _("Recognition")
    BEHAVIOUR_CHANGE = "BEHAVIOUR_CHANGE", _("Behaviour Change")


class MediaCategory(models.TextChoices):
    """Media asset categories."""

    EVENTS = "EVENTS", _("Events")
    PROGRAMME = "PROGRAMME", _("Programme")
    PROJECT = "PROJECT", _("Project")
    COMMUNITY = "COMMUNITY", _("Community Engagement")
    TRAINING = "TRAINING", _("Training")
    LEADERSHIP = "LEADERSHIP", _("Leadership")
    CAMPAIGN = "CAMPAIGN", _("Campaign")
    HISTORICAL = "HISTORICAL", _("Historical Archive")
    BRANDING = "BRANDING", _("Branding")
    OTHER = "OTHER", _("Other")


class MediaAssetType(models.TextChoices):
    """Media asset types."""

    IMAGE = "IMAGE", _("Image")
    PHOTOGRAPH = "PHOTOGRAPH", _("Photograph")
    VIDEO = "VIDEO", _("Video")
    AUDIO = "AUDIO", _("Audio Recording")
    GRAPHIC = "GRAPHIC", _("Graphic")
    POSTER = "POSTER", _("Poster")
    FLYER = "FLYER", _("Flyer")
    INFOGRAPHIC = "INFOGRAPHIC", _("Infographic")
    BANNER = "BANNER", _("Banner")
    LOGO = "LOGO", _("Logo")
    BRAND_TEMPLATE = "BRAND_TEMPLATE", _("Brand Template")
    DOCUMENT = "DOCUMENT", _("Document")


class PublicationType(models.TextChoices):
    """Publication categories."""

    ANNUAL_REPORT = "ANNUAL_REPORT", _("Annual Report")
    QUARTERLY_REPORT = "QUARTERLY_REPORT", _("Quarterly Report")
    RESEARCH_REPORT = "RESEARCH_REPORT", _("Research Report")
    POLICY_BRIEF = "POLICY_BRIEF", _("Policy Brief")
    SUCCESS_STORY = "SUCCESS_STORY", _("Success Story")
    CASE_STUDY = "CASE_STUDY", _("Case Study")
    MANUAL = "MANUAL", _("Manual")
    BROCHURE = "BROCHURE", _("Brochure")
    FACT_SHEET = "FACT_SHEET", _("Fact Sheet")
    BOOKLET = "BOOKLET", _("Information Booklet")


class BrandAssetType(models.TextChoices):
    """Brand asset categories."""

    LOGO = "LOGO", _("Official Logo")
    COLOUR = "COLOUR", _("Brand Colours")
    TYPOGRAPHY = "TYPOGRAPHY", _("Typography")
    ICON = "ICON", _("Icon")
    TEMPLATE = "TEMPLATE", _("Template")
    SOCIAL_GRAPHIC = "SOCIAL_GRAPHIC", _("Social Media Graphic")
    PRESENTATION = "PRESENTATION", _("Presentation Template")
    REPORT_COVER = "REPORT_COVER", _("Report Cover")
    EMAIL_SIGNATURE = "EMAIL_SIGNATURE", _("Email Signature")
    EVENT_BRANDING = "EVENT_BRANDING", _("Event Branding")


class EventCommunicationType(models.TextChoices):
    """Event communication categories."""

    ANNOUNCEMENT = "ANNOUNCEMENT", _("Announcement")
    INVITATION = "INVITATION", _("Invitation")
    REMINDER = "REMINDER", _("Reminder")
    LIVE_UPDATE = "LIVE_UPDATE", _("Live Update")
    POST_EVENT = "POST_EVENT", _("Post-Event Summary")
    THANK_YOU = "THANK_YOU", _("Thank-You")


class NotificationType(models.TextChoices):
    """Communication notification event types."""

    DRAFT_AWAITING_REVIEW = "DRAFT_AWAITING_REVIEW", _("Draft Awaiting Review")
    CONTENT_APPROVED = "CONTENT_APPROVED", _("Content Approved")
    PUBLICATION_SCHEDULED = "PUBLICATION_SCHEDULED", _("Publication Scheduled")
    PUBLICATION_COMPLETED = "PUBLICATION_COMPLETED", _("Publication Completed")
    CAMPAIGN_LAUNCHED = "CAMPAIGN_LAUNCHED", _("Campaign Launched")
    NEWSLETTER_DISTRIBUTED = "NEWSLETTER_DISTRIBUTED", _("Newsletter Distributed")
    MEDIA_UPLOADED = "MEDIA_UPLOADED", _("Media Upload Completed")
    WEBSITE_UPDATED = "WEBSITE_UPDATED", _("Website Content Updated")
    EVENT_COMMUNICATION_DUE = "EVENT_COMMUNICATION_DUE", _("Event Communication Due")
    BRAND_ASSET_UPDATED = "BRAND_ASSET_UPDATED", _("Brand Asset Updated")


class TimelineEventType(models.TextChoices):
    """Communication timeline event types."""

    CONTENT_CREATED = "CONTENT_CREATED", _("Content Created")
    CONTENT_EDITED = "CONTENT_EDITED", _("Content Edited")
    REVIEW_COMPLETED = "REVIEW_COMPLETED", _("Review Completed")
    APPROVAL_GRANTED = "APPROVAL_GRANTED", _("Approval Granted")
    PUBLICATION_COMPLETED = "PUBLICATION_COMPLETED", _("Publication Completed")
    DISTRIBUTION_COMPLETED = "DISTRIBUTION_COMPLETED", _("Distribution Completed")
    MEDIA_UPLOADED = "MEDIA_UPLOADED", _("Media Uploaded")
    CAMPAIGN_LAUNCHED = "CAMPAIGN_LAUNCHED", _("Campaign Launched")
    NEWSLETTER_DISTRIBUTED = "NEWSLETTER_DISTRIBUTED", _("Newsletter Distributed")
    COMMUNICATION_ARCHIVED = "COMMUNICATION_ARCHIVED", _("Communication Archived")
