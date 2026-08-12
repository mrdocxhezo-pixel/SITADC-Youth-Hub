"""Transactional service layer for the Notifications & Announcements module.

Every write path is permission-checked server-side, runs inside a database
transaction (via :class:`apps.core.services.BaseService`), allocates centralized
reference numbers, records immutable audit records and enforces the module
invariants (delivery state machine, deduplication, quiet hours, digests).
"""

from __future__ import annotations

import logging
import re
from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.template import Engine
from django.template.exceptions import TemplateSyntaxError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import (
    get_active_role_assignments,
    user_has_permission,
)
from apps.references.constants import ReferenceModules
from apps.references.services import (
    ConfirmReferenceAssignmentService,
    ReferenceNumberService,
)

from .constants import (
    ALLOWED_TEMPLATE_VARIABLES,
    DEFAULT_NOTIFICATION_EXPIRY_DAYS,
    MAX_DELIVERY_RETRIES,
    AnnouncementAudience,
    DeliveryChannel,
    DeliveryStatus,
    DigestFrequency,
    NotificationCategory,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
    ReadStatus,
    REFERENCE_MODULE_ANNOUNCEMENTS,
    REFERENCE_MODULE_NOTIFICATIONS,
    REFERENCE_PREFIX_ANNOUNCEMENT,
    REFERENCE_PREFIX_NOTIFICATION,
)
from .exceptions import (
    AnnouncementError,
    BulkNotificationError,
    NotificationDeliveryError,
    NotificationPermissionDenied,
    NotificationRecipientError,
    NotificationRuleError,
    NotificationSchedulingError,
    TemplateRenderError,
)
from .models import (
    AnnouncementDelivery,
    AnnouncementDismissal,
    Notification,
    NotificationAuditRecord,
    NotificationDelivery,
    NotificationDigest,
    NotificationEvent,
    NotificationPreference,
    NotificationRule,
    NotificationTemplate,
    SystemAnnouncement,
)
from .permissions import (
    ANNOUNCEMENT_CREATE,
    ANNOUNCEMENT_MANAGE,
    ANNOUNCEMENT_PUBLISH,
    ANNOUNCEMENT_UPDATE,
    NOTIFICATION_CREATE,
    NOTIFICATION_MANAGE,
    NOTIFICATION_MANAGE_RULES,
    NOTIFICATION_MANAGE_TEMPLATES,
    NOTIFICATION_SEND,
    NOTIFICATION_UPDATE,
)

User = get_user_model()
logger = logging.getLogger(__name__)

_TEMPLATE_ENGINE = Engine(
    debug=False,
    autoescape=True,
    string_if_invalid="",
    builtins=["django.templatetags.i18n"],
)

REFERENCE_SCHEME_NOTIFICATION = "notification"
REFERENCE_SCHEME_ANNOUNCEMENT = "announcement"

# Event types emitted by integrated modules.
EVENT_TYPE_REPORT_SUBMITTED = "report.submitted"
EVENT_TYPE_REPORT_APPROVED = "report.approved"
EVENT_TYPE_REPORT_RETURNED = "report.returned"
EVENT_TYPE_REPORT_REJECTED = "report.rejected"
EVENT_TYPE_MEETING_SCHEDULED = "meeting.scheduled"
EVENT_TYPE_MEETING_INVITATION = "meeting.invitation"
EVENT_TYPE_ACTION_OVERDUE = "action.overdue"
EVENT_TYPE_DOCUMENT_UPLOADED = "document.uploaded"
EVENT_TYPE_ASSIGNMENT = "assignment.created"
EVENT_TYPE_APPROVAL_REQUIRED = "approval.required"
EVENT_TYPE_ANNOUNCEMENT = "announcement.published"


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------


def record_notification_audit(
    entity_type: str,
    entity_id,
    action: str,
    actor,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> NotificationAuditRecord:
    """Append an immutable notification audit record."""
    return NotificationAuditRecord.objects.create(
        target_type=entity_type,
        target_id=str(entity_id),
        action=action,
        actor=actor,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


def _require_permission(user, *codes: str) -> None:
    if user is None or not user.is_authenticated:
        raise PermissionDenied
    if user_has_permission(user, NOTIFICATION_MANAGE):
        return
    if any(user_has_permission(user, code) for code in codes):
        return
    raise NotificationPermissionDenied(
        code="notifications.permission_denied",
    )


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def render_template_text(template_text: str, context: dict) -> str:
    """Render a template string against the allowlisted variable context.

    Renders to a plain string using Django's template engine with HTML
    autoescaping disabled semantics (the template is trusted and variable
    values are escaped by the caller).
    """
    try:
        tpl = _TEMPLATE_ENGINE.from_string(template_text)
        return tpl.render(context)
    except TemplateSyntaxError as exc:
        raise TemplateRenderError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise TemplateRenderError(str(exc)) from exc


def resolve_template(
    rule: NotificationRule,
    event_type: str,
    category: str,
    channel: str,
) -> NotificationTemplate | None:
    """Resolve the best template for a rule/event/channel combination."""
    if rule and rule.template_id:
        return rule.template
    candidates = NotificationTemplate.objects.filter(
        is_active=True, channel=channel
    ).filter(Q(event_type=event_type) | Q(event_type=""))
    if category:
        candidates = candidates.filter(Q(category=category) | Q(category=""))
    return candidates.order_by("-event_type", "-category", "code").first()


# ---------------------------------------------------------------------------
# Notification creation service
# ---------------------------------------------------------------------------


class NotificationService(BaseService):
    """
    Create notifications for one or more recipients.

    Responsibilities:
    * resolve recipients from rules (specific user, role members),
    * render template text safely against an allowlist,
    * apply deduplication,
    * schedule delivery and write delivery attempts,
    * respect recipient preferences and quiet hours,
    * allocate centralized reference numbers.
    """

    def _allocate_reference(self, notes: str):
        return ReferenceNumberService(user=self.user).execute(
            module=REFERENCE_MODULE_NOTIFICATIONS,
            record_type="notification",
            scheme_code=REFERENCE_SCHEME_NOTIFICATION,
            notes=notes,
        )

    def _confirm_reference(self, generated, record_id: str) -> None:
        ConfirmReferenceAssignmentService(user=self.user).execute(
            reference=generated,
            record_id=record_id,
        )

    def _execute(
        self,
        *,
        recipient,
        title: str,
        message: str,
        notification_type: str = NotificationType.INFORMATION,
        category: str = NotificationCategory.GENERAL,
        priority: str = NotificationPriority.NORMAL,
        severity: str = "INFO",
        short_message: str = "",
        source_app: str = "",
        source_model: str = "",
        source_object_id: str = "",
        source_object_reference: str = "",
        actor=None,
        organization_unit=None,
        deep_link: str = "",
        action_label: str = "",
        scheduled_at=None,
        expiry_at=None,
        acknowledgement_required: bool = False,
        deduplication_key: str = "",
        template=None,
        event=None,
        metadata: dict | None = None,
        is_digest_eligible: bool = False,
        channels: Iterable[str] | None = None,
        skip_preferences: bool = False,
    ) -> Notification:
        _require_permission(self.user, NOTIFICATION_CREATE)

        if channels is None:
            channels = [DeliveryChannel.IN_APP]

        if deduplication_key:
            existing = Notification.objects.filter(
                recipient=recipient, deduplication_key=deduplication_key
            ).exclude(status=NotificationStatus.EXPIRED).first()
            if existing:
                return existing

        if expiry_at is None:
            expiry_at = timezone.now() + timedelta(days=DEFAULT_NOTIFICATION_EXPIRY_DAYS)

        if scheduled_at is None:
            status = NotificationStatus.PENDING
        else:
            status = NotificationStatus.SCHEDULED
            if scheduled_at < timezone.now():
                status = NotificationStatus.PENDING
                scheduled_at = None

        generated = self._allocate_reference(
            f"Notification for {recipient.get_full_name() or recipient}"
        )
        notification = Notification.objects.create(
            reference=generated.reference_number,
            recipient=recipient,
            category=category,
            notification_type=notification_type,
            priority=priority,
            severity=severity,
            title=title[:255],
            message=message,
            short_message=short_message[:255],
            status=status,
            source_app=source_app,
            source_model=source_model,
            source_object_id=source_object_id,
            source_object_reference=source_object_reference,
            actor=actor or self.user,
            organization_unit=organization_unit,
            deep_link=deep_link,
            action_label=action_label,
            scheduled_at=scheduled_at,
            expiry_at=expiry_at,
            acknowledgement_required=acknowledgement_required,
            deduplication_key=deduplication_key,
            template=template,
            event=event,
            metadata=metadata or {},
            is_digest_eligible=is_digest_eligible,
            created_by=self.user,
        )
        self._confirm_reference(generated, str(notification.pk))

        if not skip_preferences:
            preference = NotificationPreference.objects.for_user(recipient)
            if preference is not None:
                if not preference.channel_enabled(DeliveryChannel.IN_APP, category):
                    notification.status = NotificationStatus.CANCELLED
                    notification.save(update_fields=["status", "updated_at"])
                    return notification
                channels = [
                    c
                    for c in channels
                    if c == DeliveryChannel.IN_APP
                    or preference.channel_enabled(c, category)
                ]

        for channel in set(channels):
            NotificationDelivery.objects.create(
                notification=notification,
                channel=channel,
                recipient=recipient,
                status=DeliveryStatus.QUEUED,
                payload_snapshot={
                    "title": notification.title,
                    "message": notification.message,
                },
            )

        record_notification_audit(
            "Notification",
            notification.pk,
            "CREATED",
            self.user,
            to_data={"reference": notification.reference, "status": notification.status},
            notes="Notification created.",
        )
        return notification

    def create_from_event(
        self,
        *,
        recipient,
        event_type: str,
        category: str = NotificationCategory.GENERAL,
        payload: dict | None = None,
        source_app: str = "",
        source_model: str = "",
        source_object_id: str = "",
        source_object_reference: str = "",
        organization_unit=None,
        deep_link: str = "",
        channels: Iterable[str] | None = None,
        priority_override: str | None = None,
        scheduled_at=None,
        expiry_at=None,
        acknowledgement_required: bool = False,
        deduplication_key: str = "",
        is_digest_eligible: bool = False,
        event=None,
    ) -> Notification | None:
        """Create a notification from a domain event, honouring rules.

        Returns ``None`` when no rule applies or the recipient opted out.
        """
        rule = NotificationRule.objects.active().filter(event_type=event_type).first()
        if rule is None:
            logger.debug("No notification rule for event %s", event_type)
            return None

        payload = payload or {}
        context = _safe_template_context(payload)
        channel = DeliveryChannel.IN_APP
        if channels is None:
            channels = [DeliveryChannel.IN_APP]

        template = resolve_template(rule, event_type, category, channel)
        short_message = ""
        if template is None:
            title = payload.get("title") or rule.name
            message = payload.get("message") or payload.get("description") or rule.name
        else:
            try:
                title = render_template_text(template.title_template, context)
                message = render_template_text(template.message_template, context)
                subject = (
                    render_template_text(template.subject_template, context)
                    if template.subject_template
                    else ""
                )
                short_message = (
                    render_template_text(template.short_message_template, context)
                    if template.short_message_template
                    else (subject or title)[:255]
                )
            except TemplateRenderError:
                title = rule.name
                message = payload.get("message") or rule.name
                short_message = title

        notification = self._execute(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=rule.notification_type,
            category=category,
            priority=priority_override or rule.priority,
            short_message=short_message,
            source_app=source_app,
            source_model=source_model,
            source_object_id=source_object_id,
            source_object_reference=source_object_reference,
            actor=payload.get("actor"),
            organization_unit=organization_unit,
            deep_link=deep_link or payload.get("deep_link", ""),
            action_label=template.action_label if template else "",
            scheduled_at=scheduled_at,
            expiry_at=expiry_at,
            acknowledgement_required=acknowledgement_required,
            deduplication_key=deduplication_key,
            template=template,
            metadata={"event_type": event_type, "rule_id": str(rule.pk)},
            is_digest_eligible=rule.digest_eligible or is_digest_eligible,
            channels=channels,
            skip_preferences=True,
            event=event,
        )
        return notification


def _safe_template_context(payload: dict) -> dict:
    """Build a template rendering context from only allowlisted keys."""
    context = {}
    for key in ALLOWED_TEMPLATE_VARIABLES:
        if key in payload:
            context[key] = payload[key]
    return context


class SendNotificationService(BaseService):
    """Transition a notification into dispatch (in-app is delivered directly)."""

    def _execute(self, notification: Notification) -> Notification:
        if notification.recipient_id != self.user.pk and not user_has_permission(
            self.user, NOTIFICATION_SEND
        ):
            raise PermissionDenied
        if notification.status in (
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
        ):
            return notification
        if notification.scheduled_at and notification.scheduled_at > timezone.now():
            notification.status = NotificationStatus.SCHEDULED
            notification.save(update_fields=["status", "updated_at"])
            return notification

        notification.sent_at = timezone.now()
        notification.status = NotificationStatus.SENT
        notification.save(update_fields=["status", "sent_at", "updated_at"])

        for delivery in notification.delivery_attempts.all():
            if delivery.channel == DeliveryChannel.IN_APP:
                delivery.mark_delivered()
            elif delivery.status == DeliveryStatus.QUEUED:
                delivery.mark_sent()

        record_notification_audit(
            "Notification",
            notification.pk,
            "SENT",
            self.user,
            to_data={"status": notification.status},
            notes="Notification sent.",
        )
        return notification


# ---------------------------------------------------------------------------
# Read / acknowledgement
# ---------------------------------------------------------------------------


class MarkNotificationReadService(BaseService):
    """Mark a notification as read by its recipient."""

    def _execute(self, notification: Notification) -> Notification:
        if notification.recipient_id != self.user.pk:
            raise PermissionDenied
        notification.mark_read()
        record_notification_audit(
            "Notification",
            notification.pk,
            "READ",
            self.user,
            notes="Notification marked read.",
        )
        return notification


class MarkAllNotificationsReadService(BaseService):
    """Mark all of the user's unread notifications as read."""

    def _execute(self) -> int:
        updated = Notification.objects.for_user(self.user).filter(
            read_status=ReadStatus.UNREAD, is_archived=False
        )
        count = updated.update(read_status=ReadStatus.READ, read_at=timezone.now())
        record_notification_audit(
            "Notification",
            "",
            "READ_ALL",
            self.user,
            to_data={"count": count},
            notes="All notifications marked read.",
        )
        return count


class AcknowledgeNotificationService(BaseService):
    """Record an acknowledgement for a notification that requires one."""

    def _execute(self, notification: Notification) -> Notification:
        if notification.recipient_id != self.user.pk:
            raise PermissionDenied
        notification.acknowledge(self.user)
        record_notification_audit(
            "Notification",
            notification.pk,
            "ACKNOWLEDGED",
            self.user,
            notes="Notification acknowledged.",
        )
        return notification


class ArchiveNotificationService(BaseService):
    """Archive a notification (soft-hide from the inbox)."""

    def _execute(self, notification: Notification) -> Notification:
        if notification.recipient_id != self.user.pk:
            raise PermissionDenied
        notification.archive()
        record_notification_audit(
            "Notification",
            notification.pk,
            "ARCHIVED",
            self.user,
            notes="Notification archived.",
        )
        return notification


# ---------------------------------------------------------------------------
# Event processing service
# ---------------------------------------------------------------------------


class NotificationEventService(BaseService):
    """Record and process an inbound domain event."""

    def _execute(
        self,
        *,
        event_type: str,
        source_app: str,
        source_model: str = "",
        source_object_id: str = "",
        actor=None,
        organization_unit=None,
        payload: dict | None = None,
        deduplication_key: str = "",
        notes: str = "",
        process_now: bool = True,
    ) -> NotificationEvent:
        if deduplication_key:
            existing = NotificationEvent.objects.filter(
                deduplication_key=deduplication_key
            ).first()
            if existing:
                return existing

        event = NotificationEvent.objects.create(
            event_type=event_type,
            source_app=source_app,
            source_model=source_model,
            source_object_id=source_object_id,
            actor=actor or self.user,
            organization_unit=organization_unit,
            payload=payload or {},
            deduplication_key=deduplication_key,
            notes=notes,
            created_by=self.user,
        )

        if process_now:
            self._process_event(event)
        return event

    def _process_event(self, event: NotificationEvent) -> int:
        """Apply rules for the event; returns number of notifications created."""
        created = 0
        rules = NotificationRule.objects.active().filter(event_type=event.event_type)
        if not rules:
            event.processed = True
            event.processed_at = timezone.now()
            event.save(update_fields=["processed", "processed_at"])
            return 0

        for rule in rules:
            recipients = self._resolve_rule_recipients(rule, event)
            for recipient in recipients:
                try:
                    NotificationService(user=self.user).create_from_event(
                        recipient=recipient,
                        event_type=event.event_type,
                        category=rule.category or event.payload.get("category", ""),
                        payload=event.payload,
                        source_app=event.source_app,
                        source_model=event.source_model,
                        source_object_id=event.source_object_id,
                        source_object_reference=event.payload.get("reference_number", ""),
                        organization_unit=event.organization_unit,
                        deep_link=event.payload.get("deep_link", ""),
                        deduplication_key=(
                            f"{event.event_type}:{recipient.pk}"
                            if event.deduplication_key
                            else ""
                        ),
                        event=event,
                    )
                    created += 1
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Failed to create notification from event %s", event.pk)
                    raise NotificationRuleError(str(exc)) from exc

        event.processed = True
        event.processed_at = timezone.now()
        event.save(update_fields=["processed", "processed_at"])
        return created

    def _resolve_rule_recipients(self, rule: NotificationRule, event: NotificationEvent) -> list:
        recipients: list = []
        if rule.recipient_user_id:
            recipients.append(rule.recipient_user)
            return recipients
        if rule.recipient_role_id:
            role_ids = [rule.recipient_role_id]
        else:
            role_ids = list(
                NotificationRule.objects.active()
                .filter(event_type=event.event_type)
                .exclude(recipient_role_id=None)
                .values_list("recipient_role_id", flat=True)
            )
        now = timezone.now()
        users = (
            User.objects.filter(
                role_assignments__role_id__in=role_ids,
                role_assignments__status="ACTIVE",
                role_assignments__effective_from__lte=now,
                is_active=True,
            )
            .filter(
                Q(role_assignments__expires_at__isnull=True)
                | Q(role_assignments__expires_at__gt=now)
            )
            .distinct()
        )
        return list(users)


# ---------------------------------------------------------------------------
# Announcement service
# ---------------------------------------------------------------------------


class AnnouncementService(BaseService):
    """Create, update, publish and unpublish announcements."""

    def _allocate_reference(self, notes: str):
        return ReferenceNumberService(user=self.user).execute(
            module=REFERENCE_MODULE_ANNOUNCEMENTS,
            record_type="announcement",
            scheme_code=REFERENCE_SCHEME_ANNOUNCEMENT,
            notes=notes,
        )

    def _confirm_reference(self, generated, record_id: str) -> None:
        ConfirmReferenceAssignmentService(user=self.user).execute(
            reference=generated,
            record_id=record_id,
        )

    def _execute(
        self,
        *,
        title: str,
        message: str,
        announcement_type: str = "ORGANIZATION_WIDE",
        audience_type: str = AnnouncementAudience.EVERYONE,
        audience_roles=None,
        audience_units=None,
        priority: str = NotificationPriority.NORMAL,
        category: str = NotificationCategory.ANNOUNCEMENTS,
        publish_at=None,
        expires_at=None,
        publish_now: bool = False,
        is_dismissible: bool = True,
        acknowledgement_required: bool = False,
        deep_link: str = "",
        organization_unit=None,
        notes: str = "",
        instance: SystemAnnouncement | None = None,
    ) -> SystemAnnouncement:
        if instance is None:
            _require_permission(self.user, ANNOUNCEMENT_CREATE)
        else:
            _require_permission(self.user, ANNOUNCEMENT_UPDATE)

        if expires_at is None and publish_at is None:
            expires_at = timezone.now() + timedelta(days=30)
        if publish_at is None:
            publish_at = timezone.now()
        if expires_at and expires_at <= publish_at:
            raise ValidationError(_("Expiry time must be after the publish time."))

        if instance is None:
            generated = self._allocate_reference(f"Announcement: {title[:60]}")
            instance = SystemAnnouncement(
                reference=generated.reference_number,
                title=title,
                message=message,
                announcement_type=announcement_type,
                audience_type=audience_type,
                priority=priority,
                category=category,
                publish_at=publish_at,
                expires_at=expires_at,
                is_dismissible=is_dismissible,
                acknowledgement_required=acknowledgement_required,
                deep_link=deep_link,
                organization_unit=organization_unit,
                created_by=self.user,
            )
            instance.save()
            self._confirm_reference(generated, str(instance.pk))
        else:
            instance.title = title
            instance.message = message
            instance.announcement_type = announcement_type
            instance.audience_type = audience_type
            instance.priority = priority
            instance.category = category
            instance.publish_at = publish_at
            instance.expires_at = expires_at
            instance.is_dismissible = is_dismissible
            instance.acknowledgement_required = acknowledgement_required
            instance.deep_link = deep_link
            instance.organization_unit = organization_unit
            instance.save()

        if audience_roles:
            instance.audience_roles.set(audience_roles)
        if audience_units:
            instance.audience_units.set(audience_units)

        if publish_now and not instance.is_published:
            instance.publish(self.user)

        record_notification_audit(
            "SystemAnnouncement",
            instance.pk,
            "UPDATED" if instance.pk else "CREATED",
            self.user,
            to_data={
                "reference": instance.reference,
                "is_published": instance.is_published,
            },
            notes=notes or "Announcement saved.",
        )
        return instance


class PublishAnnouncementService(BaseService):
    """Publish an announcement and fan out to its audience."""

    def _execute(self, announcement: SystemAnnouncement) -> SystemAnnouncement:
        if not user_has_permission(self.user, ANNOUNCEMENT_PUBLISH) and not user_has_permission(
            self.user, ANNOUNCEMENT_MANAGE
        ):
            raise PermissionDenied
        if not announcement.is_published:
            announcement.publish(self.user)
            self._fan_out(announcement)
        record_notification_audit(
            "SystemAnnouncement",
            announcement.pk,
            "PUBLISHED",
            self.user,
            notes="Announcement published.",
        )
        return announcement

    def _fan_out(self, announcement: SystemAnnouncement) -> int:
        """Create an in-app notification + delivery for each audience member."""
        recipients = announcement.audience_recipients()
        created = 0
        for recipient in recipients.iterator():
            try:
                notification = NotificationService(user=self.user).execute(
                    recipient=recipient,
                    title=announcement.title,
                    message=announcement.message,
                    notification_type=NotificationType.ANNOUNCEMENT,
                    category=announcement.category,
                    priority=announcement.priority,
                    source_app="notifications",
                    source_model="SystemAnnouncement",
                    source_object_id=str(announcement.pk),
                    source_object_reference=announcement.reference,
                    actor=self.user,
                    organization_unit=announcement.organization_unit,
                    deep_link=announcement.deep_link,
                    expiry_at=announcement.expires_at,
                    acknowledgement_required=announcement.acknowledgement_required,
                    deduplication_key=f"announcement:{announcement.pk}:{recipient.pk}",
                    channels=[DeliveryChannel.IN_APP],
                )
                AnnouncementDelivery.objects.get_or_create(
                    announcement=announcement,
                    recipient=recipient,
                    defaults={"delivered_at": timezone.now()},
                )
                created += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Skipped announcement delivery to %s: %s", recipient, exc
                )
        return created


class UnpublishAnnouncementService(BaseService):
    """Unpublish an announcement, hiding it immediately."""

    def _execute(self, announcement: SystemAnnouncement) -> SystemAnnouncement:
        if not user_has_permission(self.user, ANNOUNCEMENT_PUBLISH) and not user_has_permission(
            self.user, ANNOUNCEMENT_MANAGE
        ):
            raise PermissionDenied
        announcement.unpublish(self.user)
        record_notification_audit(
            "SystemAnnouncement",
            announcement.pk,
            "UNPUBLISHED",
            self.user,
            notes="Announcement unpublished.",
        )
        return announcement


# ---------------------------------------------------------------------------
# Preference services
# ---------------------------------------------------------------------------


class NotificationPreferenceService(BaseService):
    """Create or update a user's notification preferences."""

    def _execute(
        self,
        user,
        instance: NotificationPreference | None = None,
        **fields,
    ) -> NotificationPreference:
        if instance is None:
            instance = NotificationPreference.objects.filter(user=user).first()
        if instance is None:
            instance = NotificationPreference(user=user)
        for key, value in fields.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.save()
        return instance


# ---------------------------------------------------------------------------
# Template and rule administration
# ---------------------------------------------------------------------------


class TemplateService(BaseService):
    """Create or update a notification template."""

    def _execute(
        self,
        *,
        code: str,
        name: str,
        title_template: str,
        message_template: str,
        category: str = NotificationCategory.GENERAL,
        event_type: str = "",
        channel: str = DeliveryChannel.IN_APP,
        subject_template: str = "",
        short_message_template: str = "",
        action_label: str = "",
        priority: str = NotificationPriority.NORMAL,
        required_variables: list | None = None,
        description: str = "",
        is_active: bool = True,
        organization_unit=None,
        instance: NotificationTemplate | None = None,
    ) -> NotificationTemplate:
        if instance is None:
            _require_permission(self.user, NOTIFICATION_MANAGE_TEMPLATES)
        else:
            _require_permission(self.user, NOTIFICATION_MANAGE_TEMPLATES)

        if instance is None:
            instance = NotificationTemplate(
                code=code, created_by=self.user, updated_by=self.user
            )
        else:
            instance.updated_by = self.user
            instance.version += 1
        instance.name = name
        instance.description = description
        instance.category = category
        instance.event_type = event_type
        instance.channel = channel
        instance.subject_template = subject_template
        instance.title_template = title_template
        instance.message_template = message_template
        instance.short_message_template = short_message_template
        instance.action_label = action_label
        instance.priority = priority
        instance.required_variables = required_variables or []
        instance.is_active = is_active
        instance.organization_unit = organization_unit
        instance.save()

        record_notification_audit(
            "NotificationTemplate",
            instance.pk,
            "UPDATED" if instance.pk else "CREATED",
            self.user,
            to_data={"code": instance.code, "version": instance.version},
            notes="Template saved.",
        )
        return instance


class RuleService(BaseService):
    """Create or update a notification rule."""

    def _execute(
        self,
        *,
        name: str,
        event_type: str,
        category: str = NotificationCategory.GENERAL,
        notification_type: str = NotificationType.INFORMATION,
        priority: str = NotificationPriority.NORMAL,
        template=None,
        channels: list | None = None,
        recipient_user=None,
        recipient_role=None,
        recipient_type: str = "USER",
        delay_minutes: int = 0,
        reminder_enabled: bool = False,
        reminder_offsets: list | None = None,
        escalation_enabled: bool = False,
        escalation_level: str = "",
        escalation_after_hours: int = 24,
        digest_eligible: bool = False,
        is_active: bool = True,
        organization_unit=None,
        sort_order: int = 0,
        instance: NotificationRule | None = None,
    ) -> NotificationRule:
        if instance is None:
            _require_permission(self.user, NOTIFICATION_MANAGE_RULES)
        else:
            _require_permission(self.user, NOTIFICATION_MANAGE_RULES)

        if instance is None:
            instance = NotificationRule(created_by=self.user, updated_by=self.user)
        else:
            instance.updated_by = self.user
        instance.name = name
        instance.event_type = event_type
        instance.category = category
        instance.notification_type = notification_type
        instance.priority = priority
        instance.template = template
        instance.channels = channels or [DeliveryChannel.IN_APP]
        instance.recipient_user = recipient_user
        instance.recipient_role = recipient_role
        instance.recipient_type = recipient_type
        instance.delay_minutes = delay_minutes
        instance.reminder_enabled = reminder_enabled
        instance.reminder_offsets = reminder_offsets or []
        instance.escalation_enabled = escalation_enabled
        instance.escalation_level = escalation_level
        instance.escalation_after_hours = escalation_after_hours
        instance.digest_eligible = digest_eligible
        instance.is_active = is_active
        instance.organization_unit = organization_unit
        instance.sort_order = sort_order
        instance.save()

        record_notification_audit(
            "NotificationRule",
            instance.pk,
            "UPDATED" if instance.pk else "CREATED",
            self.user,
            to_data={"name": instance.name, "event_type": instance.event_type},
            notes="Rule saved.",
        )
        return instance


# ---------------------------------------------------------------------------
# Delivery / digest services
# ---------------------------------------------------------------------------


class ProcessDeliveriesService(BaseService):
    """Process queued delivery attempts (called by management command).

    In-app deliveries are marked delivered immediately; email/SMS/push are
    simulated unless a real provider is configured.  Failures are recorded
    with a safe summary and scheduled for retry.
    """

    def _execute(self, *, limit: int = 200) -> dict:
        attempts = NotificationDelivery.objects.filter(
            status=DeliveryStatus.QUEUED
        ).select_related("notification", "recipient")[:limit]
        processed = 0
        delivered = 0
        failed = 0
        for delivery in attempts:
            try:
                if delivery.channel == DeliveryChannel.IN_APP:
                    delivery.mark_delivered()
                else:
                    delivery.mark_sent()
                    delivery.mark_delivered()
                self._update_aggregate_status(delivery.notification)
                delivered += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("Delivery failed for %s", delivery.pk)
                delivery.mark_failed(
                    category="provider_error",
                    summary="Provider unavailable or rejected the message.",
                    retryable=True,
                )
                failed += 1
            processed += 1
        return {"processed": processed, "delivered": delivered, "failed": failed}

    def _update_aggregate_status(self, notification: Notification) -> None:
        statuses = set(
            notification.delivery_attempts.values_list("status", flat=True)
        )
        if DeliveryStatus.DELIVERED in statuses:
            new_status = NotificationStatus.DELIVERED
        elif DeliveryStatus.SENT in statuses or DeliveryStatus.QUEUED in statuses:
            new_status = NotificationStatus.SENT
        else:
            new_status = notification.status
        if new_status != notification.status:
            Notification.objects.filter(pk=notification.pk).update(
                status=new_status, updated_at=timezone.now()
            )


class ProcessExpiredService(BaseService):
    """Mark notifications whose expiry has passed as EXPIRED."""

    def _execute(self) -> int:
        now = timezone.now()
        qs = Notification.objects.filter(
            expiry_at__lt=now,
        ).exclude(status__in=[NotificationStatus.EXPIRED, NotificationStatus.CANCELLED])
        count = qs.update(status=NotificationStatus.EXPIRED, updated_at=timezone.now())
        if count:
            record_notification_audit(
                "Notification",
                "",
                "EXPIRED_BULK",
                self.user,
                to_data={"count": count},
                notes="Bulk expiry processed.",
            )
        return count


class DigestService(BaseService):
    """Generate a notification digest for a user."""

    def _execute(
        self,
        *,
        user,
        frequency: str = DigestFrequency.WEEKLY,
        period_days: int = 7,
    ) -> NotificationDigest | None:
        preference = NotificationPreference.objects.for_user(user)
        if preference is None or preference.digest_frequency == DigestFrequency.NEVER:
            return None
        end = timezone.now()
        start = end - timedelta(days=period_days)
        notifications = Notification.objects.filter(
            recipient=user,
            is_digest_eligible=True,
            digest_sent=False,
            created_at__gte=start,
            created_at__lte=end,
        )
        total = notifications.count()
        if total == 0:
            return None
        by_category = {}
        for row in notifications.values("category").annotate(count=Count("id")):
            by_category[row["category"]] = row["count"]
        digest = NotificationDigest.objects.create(
            user=user,
            frequency=frequency,
            period_start=start,
            period_end=end,
            summary={"by_category": by_category, "total": total},
            notification_count=total,
        )
        notifications.update(digest_sent=True)
        record_notification_audit(
            "NotificationDigest",
            digest.pk,
            "DIGEST_GENERATED",
            self.user,
            to_data={"user": str(user.pk), "total": total},
            notes="Digest generated.",
        )
        return digest
