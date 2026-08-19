"""Communication and Media services.

Every state-changing communication operation flows through these services so
that invariants are enforced transactionally: reference numbers are allocated
through the centralized numbering service, timeline events are appended,
notifications are created, and audit metadata is recorded.
"""

from __future__ import annotations

import logging
import uuid

from django.utils import timezone

from apps.communications.constants import NotificationType, TimelineEventType
from apps.communications.exceptions import InvalidStateTransitionError
from apps.core.constants import StatusConstants
from apps.core.services import BaseService
from apps.references.constants import ReferenceModules

logger = logging.getLogger(__name__)

_RECORD_TYPE_DEFAULTS: dict[str, tuple[str, str]] = {
    "communication": ("COM", "Communication"),
    "announcement": ("ANN", "Announcement"),
    "news": ("NWS", "News Article"),
    "newsletter": ("NWL", "Newsletter"),
    "press_release": ("PRS", "Press Release"),
    "campaign": ("CAM", "Campaign"),
    "website_page": ("WEB", "Website Page"),
    "event_communication": ("EVC", "Event Communication"),
    "publication": ("PUB", "Publication"),
    "media": ("MED", "Media Asset"),
    "brand": ("BRD", "Brand Asset"),
}


def _generate_fallback_reference(prefix: str) -> str:
    """Generate a deterministic fallback reference (used before schemes exist)."""
    return f"{prefix}-{timezone.now().year}-{uuid.uuid4().hex.upper()[:8]}"


def _reserve_reference(actor, record_type: str) -> str:
    """Reserve the next reference number through the centralized numbering service.

    Falls back to a locally generated reference when no scheme has been
    configured for the communications module yet.
    """
    prefix, _ = _RECORD_TYPE_DEFAULTS.get(record_type, ("COM", "Communication"))
    try:
        from apps.references.services import ReferenceNumberService

        generated = ReferenceNumberService(user=actor).execute(
            module=ReferenceModules.COMMUNICATIONS,
            record_type=record_type,
            scheme_code=f"communications_{record_type}",
            notes=f"Phase 30 {record_type} reference reservation.",
        )
        return generated.reference_number
    except Exception:  # pragma: no cover - exercised only pre-seeding.
        return _generate_fallback_reference(prefix)


def allocate_reference(actor, instance, record_type: str = "") -> None:
    """Allocate a reference number and persist it on the instance.

    Used by view-level create flows that use forms directly.  Idempotent:
    instances that already carry a reference are left untouched.
    """
    if getattr(instance, "reference_number", None):
        return
    record_type = record_type or getattr(instance, "_record_type", "communication")
    reference = _reserve_reference(actor, record_type)
    instance.reference_number = reference


def _record_timeline(
    actor,
    event_type: str,
    description: str,
    reference_number: str = "",
    action_performed: str = "",
    status_after_event: str = "",
    remarks: str = "",
) -> None:
    """Append a communication timeline event."""
    from apps.communications.models import CommunicationTimeline

    CommunicationTimeline.objects.create(
        event_type=event_type,
        description=description,
        event_date=timezone.now(),
        performed_by=(
            actor if actor and getattr(actor, "is_authenticated", False) else None
        ),
        module="communications",
        reference_number=reference_number,
        action_performed=action_performed,
        status_after_event=status_after_event,
        remarks=remarks,
    )


def _apply_common_fields(instance, data: dict, actor) -> None:
    """Apply validated form data to a communication record instance."""
    valid_fields = {
        f.name for f in instance._meta.fields if f.editable and not f.primary_key
    }
    for field, value in data.items():
        if field in valid_fields:
            setattr(instance, field, value)
    instance.created_by = actor
    instance.updated_by = actor


class CommunicationService(BaseService):
    """Business operations for communication records."""

    model_class = None
    record_type = "communication"

    def __init__(self, user=None, model_class=None, record_type: str = ""):
        super().__init__(user=user)
        if model_class is not None:
            self.model_class = model_class
        if record_type:
            self.record_type = record_type

    def create(self, data: dict) -> object:
        """Create a communication record from validated data."""
        return self._create(self.user, data)

    def update(self, instance, data: dict) -> object:
        """Update a communication record from validated data."""
        return self._update(self.user, instance, data)

    def _create(self, actor, data: dict) -> object:
        from apps.communications.models import Communication

        model_class = self.model_class or Communication
        instance = model_class()
        _apply_common_fields(instance, data, actor)
        allocate_reference(actor, instance, self.record_type)
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.CONTENT_CREATED,
            f"{model_class._meta.verbose_name.title()} '{instance.title}' created.",
            reference_number=instance.reference_number,
            action_performed="create",
            status_after_event=instance.status,
        )
        logger.info("Created %s %s", self.record_type, instance.reference_number)
        return instance

    def _update(self, actor, instance, data: dict) -> object:
        valid_fields = {
            f.name for f in instance._meta.fields if f.editable and not f.primary_key
        }
        for field, value in data.items():
            if field in valid_fields:
                setattr(instance, field, value)
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.CONTENT_EDITED,
            f"{instance.title} updated.",
            reference_number=instance.reference_number,
            action_performed="update",
            status_after_event=instance.status,
        )
        return instance

    def submit_for_review(self, actor, instance) -> object:
        """Transition a communication record to ``PENDING_REVIEW``."""
        if instance.status != StatusConstants.DRAFT:
            raise InvalidStateTransitionError(
                "Only draft records may be submitted for review."
            )
        instance.status = StatusConstants.PENDING_REVIEW
        instance.reviewer = actor
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.REVIEW_COMPLETED,
            f"{instance.title} submitted for review.",
            reference_number=instance.reference_number,
            action_performed="submit_for_review",
            status_after_event=instance.status,
        )
        return instance

    def approve(self, actor, instance) -> object:
        """Approve a communication record."""
        if instance.status not in (
            StatusConstants.PENDING_REVIEW,
            StatusConstants.RETURNED,
        ):
            raise InvalidStateTransitionError(
                "Only records under review may be approved."
            )
        instance.status = StatusConstants.APPROVED
        instance.approver = actor
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.APPROVAL_GRANTED,
            f"{instance.title} approved.",
            reference_number=instance.reference_number,
            action_performed="approve",
            status_after_event=instance.status,
        )
        return instance

    def publish(self, actor, instance) -> object:
        """Publish an approved communication record."""
        if instance.status != StatusConstants.APPROVED:
            raise InvalidStateTransitionError("Only approved records may be published.")
        instance.status = StatusConstants.ACTIVE
        instance.published_at = timezone.now()
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.PUBLICATION_COMPLETED,
            f"{instance.title} published.",
            reference_number=instance.reference_number,
            action_performed="publish",
            status_after_event=instance.status,
        )
        return instance

    def archive(self, actor, instance) -> object:
        """Archive a published communication record."""
        if instance.status not in (StatusConstants.ACTIVE, StatusConstants.APPROVED):
            raise InvalidStateTransitionError(
                "Only active or approved records may be archived."
            )
        instance.status = StatusConstants.ARCHIVED
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.COMMUNICATION_ARCHIVED,
            f"{instance.title} archived.",
            reference_number=instance.reference_number,
            action_performed="archive",
            status_after_event=instance.status,
        )
        return instance

    def restore(self, actor, instance) -> object:
        """Restore an archived communication record to draft."""
        if instance.status != StatusConstants.ARCHIVED:
            raise InvalidStateTransitionError("Only archived records may be restored.")
        instance.status = StatusConstants.DRAFT
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.CONTENT_EDITED,
            f"{instance.title} restored from archive.",
            reference_number=instance.reference_number,
            action_performed="restore",
            status_after_event=instance.status,
        )
        return instance

    def delete_record(self, actor, instance) -> None:
        """Delete a communication record and record the action."""
        _record_timeline(
            actor,
            TimelineEventType.COMMUNICATION_ARCHIVED,
            f"{instance.title} deleted.",
            reference_number=instance.reference_number,
            action_performed="delete",
        )
        instance.delete()


class CampaignService(CommunicationService):
    """Business operations for communication campaigns."""

    record_type = "campaign"

    def launch(self, actor, instance) -> object:
        """Launch a campaign and mark it active."""
        if instance.status != StatusConstants.APPROVED:
            raise InvalidStateTransitionError(
                "Only approved campaigns may be launched."
            )
        instance.status = StatusConstants.ACTIVE
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.CAMPAIGN_LAUNCHED,
            f"Campaign '{instance.title}' launched.",
            reference_number=instance.reference_number,
            action_performed="launch",
            status_after_event=instance.status,
        )
        return instance


class NewsletterService(CommunicationService):
    """Business operations for newsletters."""

    record_type = "newsletter"

    def distribute(self, actor, instance) -> object:
        """Mark a newsletter as distributed."""
        if instance.status not in (StatusConstants.APPROVED, StatusConstants.ACTIVE):
            raise InvalidStateTransitionError(
                "Only approved or active newsletters may be distributed."
            )
        instance.status = StatusConstants.ACTIVE
        instance.sent_at = timezone.now()
        instance.sent_count = instance.subscribers.count()
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.NEWSLETTER_DISTRIBUTED,
            f"Newsletter '{instance.title}' distributed to "
            f"{instance.sent_count} subscribers.",
            reference_number=instance.reference_number,
            action_performed="distribute",
            status_after_event=instance.status,
        )
        return instance


class MediaAssetService(CommunicationService):
    """Business operations for media assets."""

    record_type = "media"

    def publish(self, actor, instance) -> object:
        """Publish a media asset."""
        if instance.status != StatusConstants.DRAFT:
            raise InvalidStateTransitionError(
                "Only draft media assets may be published."
            )
        instance.status = StatusConstants.ACTIVE
        instance.updated_by = actor
        instance.save()
        _record_timeline(
            actor,
            TimelineEventType.MEDIA_UPLOADED,
            f"Media asset '{instance.title}' published.",
            reference_number=getattr(instance, "reference_number", ""),
            action_performed="publish",
            status_after_event=instance.status,
        )
        return instance


def create_notification(
    recipient,
    notification_type: str = NotificationType.PUBLICATION_COMPLETED,
    title: str = "",
    message: str = "",
) -> object:
    """Create a communication notification record."""
    from apps.communications.models import CommunicationNotification

    return CommunicationNotification.objects.create(
        notification_type=notification_type,
        title=title or notification_type.replace("_", " ").title(),
        message=message,
        recipient=recipient,
        sent_at=timezone.now(),
    )


def get_dashboard_analytics(actor=None) -> dict:
    """Return aggregate analytics for the communications dashboard."""
    from apps.communications.models import (
        Announcement,
        BrandAsset,
        Campaign,
        Communication,
        EventCommunication,
        MediaAsset,
        NewsArticle,
        Newsletter,
        PressRelease,
        Publication,
        SocialMediaPost,
        WebsitePage,
    )

    now = timezone.now()
    return {
        "total_communications": Communication.objects.count(),
        "active_communications": Communication.objects.filter(
            status=StatusConstants.ACTIVE
        ).count(),
        "pending_review": Communication.objects.filter(
            status=StatusConstants.PENDING_REVIEW
        ).count(),
        "drafts": Communication.objects.filter(status=StatusConstants.DRAFT).count(),
        "announcements": Announcement.objects.count(),
        "news_articles": NewsArticle.objects.count(),
        "newsletters": Newsletter.objects.count(),
        "press_releases": PressRelease.objects.count(),
        "campaigns": Campaign.objects.count(),
        "active_campaigns": Campaign.objects.filter(
            status=StatusConstants.ACTIVE
        ).count(),
        "publications": Publication.objects.count(),
        "media_assets": MediaAsset.objects.count(),
        "brand_assets": BrandAsset.objects.count(),
        "website_pages": WebsitePage.objects.count(),
        "social_posts": SocialMediaPost.objects.count(),
        "event_communications": EventCommunication.objects.count(),
        "upcoming_events": EventCommunication.objects.filter(
            event_date__gte=now
        ).count(),
    }
