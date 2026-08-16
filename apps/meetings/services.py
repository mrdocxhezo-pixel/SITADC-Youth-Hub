"""Permission-checked transactional services for the Calendar & Meetings module.

Every write flows through these services so that RBAC checks, workflow
transitions, reference-number allocation, validation and the immutable
activity timeline are enforced consistently.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission
from apps.references.services import (
    ConfirmReferenceAssignmentService,
    ReferenceNumberService,
)

from .constants import (
    REFERENCE_MODULE_CALENDARS,
    REFERENCE_MODULE_EVENTS,
    REFERENCE_MODULE_MEETINGS,
    SENSITIVE_LEVELS,
    ActionPriority,
    ActionStatus,
    AgendaStatus,
    AttendanceStatus,
    AttendanceVerificationStatus,
    ConfidentialityLevel,
    DecisionStatus,
    EscalationStatus,
    EventStatus,
    FollowUpType,
    InvitationStatus,
    MatterStatus,
    MeetingDocumentType,
    MeetingStatus,
    MinutesStatus,
    ParticipantStatus,
    ParticipantType,
    PublicationStatus,
    QuorumType,
    ReminderChannel,
    ReminderRecipientType,
    ReminderStatus,
    ReminderType,
    RSVPStatus,
)
from .exceptions import (
    EventConflictError,
    EventValidationError,
    InvalidTransitionError,
    InvitationError,
    MeetingSchedulingError,
    MinutesWorkflowError,
    QuorumError,
)
from .models import (
    ActionFollowUpRecord,
    AgendaItem,
    AttendanceCorrectionRecord,
    Calendar,
    CalendarEvent,
    CalendarShare,
    ConfidentialAccessLog,
    DecisionVote,
    EventOccurrence,
    EventReminder,
    MattersArising,
    Meeting,
    MeetingActionItem,
    MeetingActivityRecord,
    MeetingAgenda,
    MeetingAttendance,
    MeetingDecision,
    MeetingDocument,
    MeetingInvitation,
    MeetingMinutes,
    MeetingParticipant,
    MeetingScheduleHistory,
    MeetingTemplate,
    MeetingVenue,
    MinuteSection,
)
from .permissions import (
    CALENDAR_CREATE,
    CALENDAR_DELETE,
    CALENDAR_MANAGE,
    CALENDAR_SHARE,
    CALENDAR_UPDATE,
    EVENT_CREATE,
    EVENT_UPDATE,
    MEETING_APPROVE_AGENDAS,
    MEETING_APPROVE_MINUTES,
    MEETING_CANCEL,
    MEETING_CHECK_IN,
    MEETING_CHECK_OUT,
    MEETING_COMPLETE,
    MEETING_CONFIRM,
    MEETING_CREATE,
    MEETING_DELETE,
    MEETING_DRAFT_MINUTES,
    MEETING_ESCALATE,
    MEETING_MANAGE,
    MEETING_MANAGE_ACTIONS,
    MEETING_MANAGE_AGENDAS,
    MEETING_MANAGE_PARTICIPANTS,
    MEETING_MANAGE_QUORUM,
    MEETING_MANAGE_REMINDERS,
    MEETING_MANAGE_TEMPLATES,
    MEETING_MANAGE_VENUES,
    MEETING_RECORD_ATTENDANCE,
    MEETING_RECORD_DECISIONS,
    MEETING_RESCHEDULE,
    MEETING_REVIEW_MINUTES,
    MEETING_SEND_INVITATIONS,
    MEETING_START,
    MEETING_SUBMIT_MINUTES,
    MEETING_UPDATE,
    MEETING_VERIFY_ACTIONS,
    MEETING_VERIFY_ATTENDANCE,
    MEETING_VIEW_CONFIDENTIAL,
    is_calendar_owner,
)
from .recurrence import expand_occurrences
from .validators import require_transition, validate_recurrence_rule

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared guards and helpers
# ---------------------------------------------------------------------------


class _MeetingServiceMixin:
    """Shared guards, audit and reference helpers for meeting services."""

    user: Any

    def _require_permission(self, permission_code: str) -> None:
        if not self.user or not getattr(self.user, "is_authenticated", False):
            raise PermissionDenied(_("An authenticated actor is required."))
        if not (
            user_has_permission(self.user, permission_code)
            or user_has_permission(self.user, MEETING_MANAGE)
        ):
            raise PermissionDenied(_("Permission denied for this meetings action."))

    def _require_view(self) -> None:
        if not self.user or not getattr(self.user, "is_authenticated", False):
            raise PermissionDenied(_("An authenticated actor is required."))
        if not (
            user_has_permission(self.user, "meetings.view")
            or user_has_permission(self.user, "calendars.view")
            or user_has_permission(self.user, "events.view")
            or user_has_permission(self.user, MEETING_MANAGE)
        ):
            raise PermissionDenied(_("Permission denied for this meetings action."))

    def _require_confidentiality(self, instance) -> None:
        sensitive = (
            getattr(instance, "is_confidential", False)
            or getattr(instance, "confidentiality_level", ConfidentialityLevel.INTERNAL)
            in SENSITIVE_LEVELS
        )
        if sensitive and not (
            user_has_permission(self.user, MEETING_VIEW_CONFIDENTIAL)
            or user_has_permission(self.user, MEETING_MANAGE)
        ):
            raise PermissionDenied(
                _("This meeting record is confidential and outside your access.")
            )

    def _require_calendar_owner_or_manage(self, calendar: Calendar) -> None:
        if self.user.is_superuser or user_has_permission(self.user, CALENDAR_MANAGE):
            return
        if not is_calendar_owner(self.user, calendar):
            raise PermissionDenied(
                _("Only the calendar owner may perform this action.")
            )

    def _activity(
        self, meeting: Meeting, action: str, details: str = "", **metadata
    ) -> None:
        MeetingActivityRecord.objects.create(
            meeting=meeting,
            action=action,
            actor=self.user,
            details=details[:255],
            metadata=metadata or {},
        )
        logger.info(
            "meeting_activity",
            extra={
                "meeting_event": {
                    "action": action,
                    "meeting_id": str(meeting.pk),
                    "actor_id": str(getattr(self.user, "pk", "")),
                }
            },
        )

    def _allocate_reference(
        self, module: str, record_type: str, scheme_code: str, notes: str
    ):
        return ReferenceNumberService(user=self.user).execute(
            module=module,
            record_type=record_type,
            scheme_code=scheme_code,
            notes=notes,
        )

    def _allocate_reference_if_configured(
        self, module: str, record_type: str, scheme_code: str, notes: str
    ):
        """Allocate a reference only when a scheme exists.

        Sub-record types (agenda, minutes, decisions, actions, documents) do
        not have a dedicated numbering scheme in every deployment, so their
        reference allocation is best-effort.
        """
        from apps.references.exceptions import (
            InactiveNumberingSchemeError,
            MissingNumberingContextError,
        )

        try:
            return self._allocate_reference(
                module=module,
                record_type=record_type,
                scheme_code=scheme_code,
                notes=notes,
            )
        except (MissingNumberingContextError, InactiveNumberingSchemeError):
            logger.warning(
                "reference_allocation_skipped",
                extra={
                    "meeting_event": {
                        "module": module,
                        "record_type": record_type,
                        "scheme_code": scheme_code,
                    }
                },
            )
            return None

    def _default_from_instance(self, kwargs: dict, instance, *fields: str) -> dict:
        """Fill missing kwargs from the instance for partial updates."""
        for field in fields:
            if field not in kwargs:
                kwargs[field] = getattr(instance, field)
        return kwargs

    def _confirm_reference(self, generated, record_id: str) -> None:
        ConfirmReferenceAssignmentService(user=self.user).execute(
            reference=generated,
            record_id=record_id,
        )


# ---------------------------------------------------------------------------
# Calendars
# ---------------------------------------------------------------------------


class CalendarService(BaseService, _MeetingServiceMixin):
    """Create and maintain organizational calendars."""

    def _execute(
        self,
        *,
        name: str,
        owner,
        calendar_type: str = "TEAM",
        description: str = "",
        visibility: str = "TEAM",
        organization_unit=None,
        access_scope=None,
        default_timezone: str = "UTC",
        color: str = "#0d6efd",
        is_default: bool = False,
        is_confidential: bool | None = None,
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        is_active: bool = True,
        notes: str = "",
        instance: Calendar | None = None,
    ) -> Calendar:
        if instance is None:
            self._require_permission(CALENDAR_CREATE)
        else:
            self._require_permission(CALENDAR_UPDATE)
            self._require_calendar_owner_or_manage(instance)

        data = {
            "name": name,
            "calendar_type": calendar_type,
            "description": description,
            "visibility": visibility,
            "owner": owner,
            "organization_unit": organization_unit,
            "access_scope": access_scope,
            "default_timezone": default_timezone,
            "color": color,
            "is_default": is_default,
            "confidentiality_level": confidentiality_level,
            "is_confidential": (
                is_confidential
                if is_confidential is not None
                else confidentiality_level in SENSITIVE_LEVELS
            ),
            "is_active": is_active,
            "notes": notes,
        }
        if instance is None:
            instance = Calendar.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()

        if instance.reference:
            return instance

        generated = self._allocate_reference(
            REFERENCE_MODULE_CALENDARS,
            "calendar",
            "calendar",
            f"Calendar for {instance.name}.",
        )
        instance.reference = generated.reference_number
        instance.save(update_fields=["reference"])
        self._confirm_reference(generated, str(instance.pk))
        return instance

    def create(self, *, owner=None, **kwargs) -> Calendar:
        return self.execute(owner=owner or self.user, **kwargs)

    def update(self, instance: Calendar, **kwargs) -> Calendar:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(kwargs, instance, "owner")
        return self.execute(**kwargs)

    def soft_delete(self, instance: Calendar, *, notes: str = "") -> Calendar:
        self._require_permission(CALENDAR_DELETE)
        self._require_calendar_owner_or_manage(instance)
        instance.delete(deleted_by=self.user)
        return instance

    def archive(self, instance: Calendar, *, notes: str = "") -> Calendar:
        self._require_permission(CALENDAR_DELETE)
        self._require_calendar_owner_or_manage(instance)
        instance.archive(archived_by=self.user)
        return instance

    def restore(self, instance: Calendar) -> Calendar:
        self._require_permission(CALENDAR_MANAGE)
        instance.unarchive()
        return instance

    def share(
        self,
        *,
        calendar: Calendar,
        permission_level: str,
        user=None,
        organization_unit=None,
        access_scope=None,
        expires_at=None,
    ) -> CalendarShare:
        self._require_permission(CALENDAR_SHARE)
        self._require_calendar_owner_or_manage(calendar)
        if not any((user, organization_unit, access_scope)):
            raise ValidationError(
                _("Choose a user, unit, or access scope to share with.")
            )
        share, _created = CalendarShare.objects.update_or_create(
            calendar=calendar,
            user=user,
            organization_unit=organization_unit,
            access_scope=access_scope,
            defaults={
                "permission_level": permission_level,
                "expires_at": expires_at,
                "created_by": self.user,
                "updated_by": self.user,
            },
        )
        return share

    def revoke_share(self, *, share: CalendarShare) -> None:
        self._require_permission(CALENDAR_SHARE)
        self._require_calendar_owner_or_manage(share.calendar)
        share.delete()


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class CalendarEventService(BaseService, _MeetingServiceMixin):
    """Create, schedule and maintain calendar events."""

    def _execute(
        self,
        *,
        calendar: Calendar,
        title: str,
        start_at,
        end_at,
        event_type: str = "MEETING",
        description: str = "",
        all_day: bool = False,
        timezone: str = "UTC",
        venue=None,
        online_meeting_link: str = "",
        location_details: str = "",
        host=None,
        organizer=None,
        program=None,
        project=None,
        organization_unit=None,
        access_scope=None,
        priority: str = "NORMAL",
        status: str = EventStatus.DRAFT,
        is_confidential: bool | None = None,
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        recurrence_rule: dict | None = None,
        reminder_config: list | None = None,
        maximum_attendance: int | None = None,
        registration_required: bool = False,
        approval_required: bool = False,
        notes: str = "",
        instance: CalendarEvent | None = None,
    ) -> CalendarEvent:
        if instance is None:
            self._require_permission(EVENT_CREATE)
        else:
            self._require_permission(EVENT_UPDATE)
        self._require_confidentiality(instance if instance else calendar)

        recurrence_rule = recurrence_rule or {}
        try:
            validate_recurrence_rule(recurrence_rule or None)
        except ValidationError as exc:
            raise EventValidationError(str(exc)) from exc

        if end_at <= start_at:
            raise ValidationError(_("End time must be after the start time."))
        self._check_conflict(
            calendar, start_at, end_at, exclude_pk=getattr(instance, "pk", None)
        )

        data = {
            "calendar": calendar,
            "title": title,
            "description": description,
            "start_at": start_at,
            "end_at": end_at,
            "all_day": all_day,
            "timezone": timezone,
            "venue": venue,
            "online_meeting_link": online_meeting_link,
            "location_details": location_details,
            "host": host,
            "organizer": organizer,
            "program": program,
            "project": project,
            "organization_unit": organization_unit,
            "access_scope": access_scope,
            "event_type": event_type,
            "priority": priority,
            "status": status,
            "confidentiality_level": confidentiality_level,
            "is_confidential": (
                is_confidential
                if is_confidential is not None
                else confidentiality_level in SENSITIVE_LEVELS
            ),
            "recurrence_rule": recurrence_rule,
            "is_recurring": bool(recurrence_rule and recurrence_rule.get("frequency")),
            "reminder_config": reminder_config or [],
            "maximum_attendance": maximum_attendance,
            "registration_required": registration_required,
            "approval_required": approval_required,
            "notes": notes,
        }
        if instance is None:
            instance = CalendarEvent.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()

        if not instance.reference:
            generated = self._allocate_reference(
                REFERENCE_MODULE_EVENTS, "event", "event", f"Event {instance.title}."
            )
            instance.reference = generated.reference_number
            instance.save(update_fields=["reference"])
            self._confirm_reference(generated, str(instance.pk))

        self._ensure_occurrences(instance)
        return instance

    def create(self, **kwargs) -> CalendarEvent:
        return self.execute(**kwargs)

    def update(self, instance: CalendarEvent, **kwargs) -> CalendarEvent:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(
            kwargs, instance, "calendar", "title", "start_at", "end_at"
        )
        return self.execute(**kwargs)

    def _check_conflict(self, calendar, start_at, end_at, exclude_pk=None) -> None:
        overlapping = CalendarEvent.objects.filter(
            calendar=calendar,
            start_at__lt=end_at,
            end_at__gt=start_at,
            status__in=[
                EventStatus.SCHEDULED,
                EventStatus.CONFIRMED,
                EventStatus.DRAFT,
            ],
        )
        if exclude_pk:
            overlapping = overlapping.exclude(pk=exclude_pk)
        if overlapping.exists():
            first = overlapping.first()
            raise EventConflictError(
                "Conflicts with event "
                f"'{first.title}' scheduled {first.start_at:%Y-%m-%d %H:%M}."
            )

    def _ensure_occurrences(self, event: CalendarEvent) -> None:
        if not event.is_recurring:
            return
        rule = event.recurrence_rule or {}
        try:
            from .constants import RecurrenceFrequency

            RecurrenceFrequency(rule.get("frequency", ""))
        except ValueError:
            return
        now = timezone.now()
        range_end = now + timedelta(days=365)
        for occ in expand_occurrences(
            start=event.start_at,
            end=event.end_at,
            rule=rule,
            range_start=now,
            range_end=range_end,
            timezone_name=event.timezone,
        ):
            EventOccurrence.objects.update_or_create(
                event=event,
                original_start=occ["start"],
                defaults={
                    "sequence": occ.get("sequence", 0),
                    "occurrence_start": occ["start"],
                    "occurrence_end": occ["end"],
                },
            )

    def transition(
        self, *, instance: CalendarEvent, status: str, reason: str = ""
    ) -> CalendarEvent:
        allowed = {
            EventStatus.DRAFT: {EventStatus.SCHEDULED, EventStatus.CANCELLED},
            EventStatus.SCHEDULED: {
                EventStatus.CONFIRMED,
                EventStatus.POSTPONED,
                EventStatus.CANCELLED,
            },
            EventStatus.CONFIRMED: {
                EventStatus.COMPLETED,
                EventStatus.POSTPONED,
                EventStatus.CANCELLED,
            },
            EventStatus.POSTPONED: {EventStatus.SCHEDULED, EventStatus.CANCELLED},
            EventStatus.RESCHEDULED: {EventStatus.CONFIRMED, EventStatus.CANCELLED},
            EventStatus.COMPLETED: {EventStatus.ARCHIVED},
            EventStatus.CANCELLED: set(),
            EventStatus.ARCHIVED: set(),
        }
        require_transition(instance.status, status, allowed[instance.status], "event")
        previous = instance.status
        instance.status = status
        if status == EventStatus.CANCELLED:
            instance.cancelled_at = timezone.now()
            instance.cancellation_reason = reason
        instance.updated_by = self.user
        instance.save()
        logger.info(
            "event_status_change",
            extra={
                "event_event": {
                    "event_id": str(instance.pk),
                    "from": previous,
                    "to": status,
                    "actor_id": str(getattr(self.user, "pk", "")),
                }
            },
        )
        return instance

    def archive(self, *, instance: CalendarEvent) -> CalendarEvent:
        self._require_permission("events.archive")
        instance.archive(archived_by=self.user)
        return instance

    def restore(self, *, instance: CalendarEvent) -> CalendarEvent:
        self._require_permission("events.restore")
        instance.unarchive()
        return instance


# ---------------------------------------------------------------------------
# Meetings
# ---------------------------------------------------------------------------


class MeetingService(BaseService, _MeetingServiceMixin):
    """Schedule and manage the meeting lifecycle."""

    def _execute(
        self,
        *,
        title: str,
        start_at,
        end_at,
        meeting_type: str = "TEAM",
        template: MeetingTemplate | None = None,
        purpose: str = "",
        objectives: list | None = None,
        timezone: str = "UTC",
        mode: str = "IN_PERSON",
        venue=None,
        venue_reservation_status: str = "REQUESTED",
        virtual_provider: str = "",
        online_meeting_link: str = "",
        meeting_id: str = "",
        meeting_passcode: str = "",
        organizer=None,
        chairperson=None,
        secretary=None,
        minute_taker=None,
        facilitator=None,
        program=None,
        project=None,
        organization_unit=None,
        access_scope=None,
        expected_attendees: int = 0,
        required_attendees: int = 0,
        quorum_type: str = QuorumType.FIXED_NUMBER,
        quorum_value: int | None = None,
        quorum_required_roles: list | None = None,
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        publication_status: str = PublicationStatus.PRIVATE,
        notes: str = "",
        event: CalendarEvent | None = None,
        instance: Meeting | None = None,
    ) -> Meeting:
        if instance is None:
            self._require_permission(MEETING_CREATE)
        else:
            self._require_permission(MEETING_UPDATE)
            if not (
                self.user.is_superuser
                or user_has_permission(self.user, MEETING_MANAGE)
                or self.user.pk
                in (
                    instance.organizer_id,
                    instance.chairperson_id,
                    instance.secretary_id,
                    instance.minute_taker_id,
                )
                or instance.created_by_id == self.user.pk
            ):
                raise PermissionDenied(
                    _("Only the meeting organizer may update this meeting.")
                )

        if end_at <= start_at:
            raise MeetingSchedulingError(_("End time must be after the start time."))

        if template is not None:
            meeting_type = meeting_type or template.meeting_type
            confidentiality_level = (
                confidentiality_level or template.default_confidentiality
            )
            quorum_type = quorum_type or template.default_quorum_type
            quorum_value = (
                quorum_value if quorum_value else template.default_quorum_value
            )

        data = {
            "title": title,
            "start_at": start_at,
            "end_at": end_at,
            "meeting_type": meeting_type,
            "template": template,
            "purpose": purpose,
            "objectives": objectives or [],
            "timezone": timezone,
            "mode": mode,
            "venue": venue,
            "venue_reservation_status": venue_reservation_status,
            "virtual_provider": virtual_provider,
            "online_meeting_link": online_meeting_link,
            "meeting_id": meeting_id,
            "meeting_passcode": meeting_passcode,
            "organizer": organizer or self.user,
            "chairperson": chairperson,
            "secretary": secretary,
            "minute_taker": minute_taker,
            "facilitator": facilitator,
            "program": program,
            "project": project,
            "organization_unit": organization_unit,
            "access_scope": access_scope,
            "expected_attendees": expected_attendees,
            "required_attendees": required_attendees,
            "quorum_type": quorum_type,
            "quorum_value": quorum_value,
            "quorum_required_roles": quorum_required_roles or [],
            "confidentiality_level": confidentiality_level,
            "is_confidential": confidentiality_level in SENSITIVE_LEVELS,
            "publication_status": publication_status,
            "notes": notes,
            "event": event,
        }
        if instance is None:
            instance = Meeting.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
            if event is not None and event.status in (
                EventStatus.DRAFT,
                EventStatus.SCHEDULED,
            ):
                event.status = EventStatus.SCHEDULED
                event.save(update_fields=["status"])
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()

        if not instance.reference:
            generated = self._allocate_reference(
                REFERENCE_MODULE_MEETINGS,
                "meeting",
                "meeting",
                f"Meeting {instance.title}.",
            )
            instance.reference = generated.reference_number
            instance.save(update_fields=["reference"])
            self._confirm_reference(generated, str(instance.pk))

        if instance.status == MeetingStatus.DRAFT:
            instance.status = MeetingStatus.SCHEDULED
            instance.save(update_fields=["status"])

        self._activity(
            instance, "MEETING_CREATED", f"Meeting {instance.reference} scheduled."
        )
        return instance

    def create(self, **kwargs) -> Meeting:
        meeting = self.execute(**kwargs)
        if meeting.status == MeetingStatus.SCHEDULED:
            meeting.status = MeetingStatus.DRAFT
            meeting.save(update_fields=["status", "updated_at"])
        return meeting

    def update(self, instance: Meeting, **kwargs) -> Meeting:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(kwargs, instance, "title", "start_at", "end_at")
        return self.execute(**kwargs)

    def transition(
        self, *, instance: Meeting, status: str, reason: str = ""
    ) -> Meeting:
        self._require_permission(MEETING_UPDATE)
        allowed = {
            MeetingStatus.DRAFT: {
                MeetingStatus.SCHEDULED,
                MeetingStatus.CONFIRMED,
                MeetingStatus.CANCELLED,
            },
            MeetingStatus.SCHEDULED: {
                MeetingStatus.INVITATIONS_SENT,
                MeetingStatus.CONFIRMED,
                MeetingStatus.POSTPONED,
                MeetingStatus.CANCELLED,
            },
            MeetingStatus.INVITATIONS_SENT: {
                MeetingStatus.CONFIRMED,
                MeetingStatus.POSTPONED,
                MeetingStatus.CANCELLED,
            },
            MeetingStatus.CONFIRMED: {
                MeetingStatus.IN_PROGRESS,
                MeetingStatus.COMPLETED,
                MeetingStatus.POSTPONED,
                MeetingStatus.CANCELLED,
            },
            MeetingStatus.IN_PROGRESS: {
                MeetingStatus.COMPLETED,
                MeetingStatus.CANCELLED,
            },
            MeetingStatus.COMPLETED: {
                MeetingStatus.MINUTES_DRAFTED,
                MeetingStatus.MINUTES_UNDER_REVIEW,
                MeetingStatus.MINUTES_APPROVED,
                MeetingStatus.CLOSED,
            },
            MeetingStatus.MINUTES_DRAFTED: {
                MeetingStatus.MINUTES_UNDER_REVIEW,
                MeetingStatus.COMPLETED,
            },
            MeetingStatus.MINUTES_UNDER_REVIEW: {
                MeetingStatus.MINUTES_APPROVED,
                MeetingStatus.COMPLETED,
            },
            MeetingStatus.MINUTES_APPROVED: {MeetingStatus.CLOSED},
            MeetingStatus.POSTPONED: {MeetingStatus.SCHEDULED, MeetingStatus.CANCELLED},
            MeetingStatus.RESCHEDULED: {
                MeetingStatus.SCHEDULED,
                MeetingStatus.CONFIRMED,
                MeetingStatus.CANCELLED,
            },
            MeetingStatus.CLOSED: {MeetingStatus.ARCHIVED},
            MeetingStatus.CANCELLED: set(),
            MeetingStatus.ARCHIVED: set(),
        }
        require_transition(instance.status, status, allowed[instance.status], "meeting")
        previous = instance.status
        instance.status = status
        if status == MeetingStatus.CANCELLED:
            instance.cancelled_at = timezone.now()
            instance.cancellation_reason = reason
        if status == MeetingStatus.COMPLETED:
            instance.completed_at = timezone.now()
            instance.completion_notes = reason
        if status == MeetingStatus.CLOSED:
            instance.closed_at = timezone.now()
        instance.updated_by = self.user
        instance.save()
        self._activity(instance, f"MEETING_{status}", reason)
        logger.info(
            "meeting_status_change",
            extra={
                "meeting_event": {
                    "meeting_id": str(instance.pk),
                    "from": previous,
                    "to": status,
                    "actor_id": str(getattr(self.user, "pk", "")),
                }
            },
        )
        return instance

    def confirm(self, instance: Meeting) -> Meeting:
        self._require_permission(MEETING_CONFIRM)
        return self.transition(instance=instance, status=MeetingStatus.CONFIRMED)

    def start(self, *, instance: Meeting) -> Meeting:
        self._require_permission(MEETING_START)
        meeting = self.transition(instance=instance, status=MeetingStatus.IN_PROGRESS)
        QuorumService(user=self.user).evaluate(meeting=meeting)
        return meeting

    def complete(self, instance: Meeting, *, notes: str = "") -> Meeting:
        self._require_permission(MEETING_COMPLETE)
        return self.transition(
            instance=instance, status=MeetingStatus.COMPLETED, reason=notes
        )

    def reschedule(
        self,
        *,
        instance: Meeting,
        new_start,
        new_end,
        new_venue=None,
        reason: str = "",
    ) -> Meeting:
        self._require_permission(MEETING_RESCHEDULE)
        if new_end <= new_start:
            raise MeetingSchedulingError(_("End time must be after the start time."))

        MeetingScheduleHistory.objects.create(
            meeting=instance,
            previous_start=instance.start_at,
            previous_end=instance.end_at,
            new_start=new_start,
            new_end=new_end,
            previous_venue=instance.venue,
            new_venue=new_venue or instance.venue,
            reason=reason,
            changed_by=self.user,
        )
        instance.original_start_at = instance.start_at
        instance.original_end_at = instance.end_at
        instance.start_at = new_start
        instance.end_at = new_end
        if new_venue is not None:
            instance.venue = new_venue
        instance.is_rescheduled = True
        instance.reschedule_reason = reason
        instance.status = MeetingStatus.RESCHEDULED
        instance.updated_by = self.user
        instance.save()
        self._activity(
            instance, "MEETING_RESCHEDULED", reason or "Meeting rescheduled."
        )
        return instance

    def postpone(self, *, instance: Meeting, until, reason: str = "") -> Meeting:
        self._require_permission(MEETING_RESCHEDULE)
        instance.postponement_until = until
        instance.status = MeetingStatus.POSTPONED
        instance.reschedule_reason = reason
        instance.updated_by = self.user
        instance.save()
        self._activity(instance, "MEETING_POSTPONED", reason or "Meeting postponed.")
        return instance

    def cancel(self, instance: Meeting, *, reason: str = "") -> Meeting:
        self._require_permission(MEETING_CANCEL)
        if instance.status in (
            MeetingStatus.CLOSED,
            MeetingStatus.ARCHIVED,
            MeetingStatus.CANCELLED,
        ):
            raise InvalidTransitionError(
                f"Cannot cancel a {instance.get_status_display()} meeting."
            )
        return self.transition(
            instance=instance, status=MeetingStatus.CANCELLED, reason=reason
        )

    def archive(self, *, instance: Meeting) -> Meeting:
        self._require_permission("meetings.archive")
        instance.archive(archived_by=self.user)
        self._activity(instance, "MEETING_ARCHIVED")
        return instance

    def restore(self, *, instance: Meeting) -> Meeting:
        self._require_permission("meetings.restore")
        instance.unarchive()
        self._activity(instance, "MEETING_RESTORED")
        return instance

    def delete(self, *, instance: Meeting) -> None:
        self._require_permission(MEETING_DELETE)
        instance.delete(deleted_by=self.user)
        self._activity(instance, "MEETING_DELETED")


# ---------------------------------------------------------------------------
# Participants & invitations
# ---------------------------------------------------------------------------


class ParticipantService(BaseService, _MeetingServiceMixin):
    """Manage meeting participants and invitations."""

    def _execute(
        self,
        *,
        meeting: Meeting,
        participant_type: str = "USER",
        user=None,
        name: str = "",
        email: str = "",
        phone: str = "",
        organization: str = "",
        role_in_meeting: str = "ATTENDEE",
        is_required: bool = False,
        special_requirements: str = "",
        accessibility_accommodation: str = "",
        instance: MeetingParticipant | None = None,
    ) -> MeetingParticipant:
        self._require_permission(MEETING_MANAGE_PARTICIPANTS)
        self._require_confidentiality(meeting)

        data = {
            "meeting": meeting,
            "participant_type": participant_type,
            "user": user,
            "name_snapshot": name or (user.get_full_name() if user else ""),
            "email_snapshot": email or (user.email if user else ""),
            "phone_snapshot": phone,
            "organization": organization,
            "role_in_meeting": role_in_meeting,
            "is_required": is_required,
            "special_requirements": special_requirements,
            "accessibility_accommodation": accessibility_accommodation,
        }
        if instance is None:
            instance = MeetingParticipant.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()
        return instance

    def add_participant(self, meeting, **kwargs) -> MeetingParticipant:
        return self.execute(meeting=meeting, **kwargs)

    def update_status(
        self,
        participant: MeetingParticipant,
        *,
        participant_status: str,
        rsvp_status: str | None = None,
    ) -> MeetingParticipant:
        participant.participant_status = participant_status
        if rsvp_status is not None:
            participant.rsvp_status = rsvp_status
        participant.save(
            update_fields=["participant_status", "rsvp_status", "updated_at"]
        )
        return participant

    def invite(
        self,
        *,
        participant: MeetingParticipant,
        delivery_channel: str = ReminderChannel.EMAIL,
    ) -> MeetingInvitation:
        self._require_permission(MEETING_SEND_INVITATIONS)
        if not participant.email_snapshot:
            raise InvitationError(
                _("An email address is required to send an invitation.")
            )
        invitation, created = MeetingInvitation.objects.get_or_create(
            meeting=participant.meeting,
            defaults={
                "status": InvitationStatus.PENDING,
                "delivery_channel": delivery_channel,
                "created_by": self.user,
            },
        )
        participant.invitation = invitation
        participant.participant_status = ParticipantStatus.INVITED
        participant.save(update_fields=["invitation", "participant_status"])
        return invitation

    def send_invitations(
        self,
        *,
        meeting: Meeting,
        delivery_channel: str = ReminderChannel.EMAIL,
    ) -> list[MeetingInvitation]:
        self._require_permission(MEETING_SEND_INVITATIONS)
        if meeting.status not in (
            MeetingStatus.SCHEDULED,
            MeetingStatus.INVITATIONS_SENT,
            MeetingStatus.CONFIRMED,
        ):
            raise InvitationError(
                _("Invitations can only be sent to scheduled meetings.")
            )
        sent = []
        for participant in meeting.participants.exclude(email_snapshot=""):
            invitation = self.invite(
                participant=participant, delivery_channel=delivery_channel
            )
            invitation.status = InvitationStatus.SENT
            invitation.sent_at = timezone.now()
            invitation.save(update_fields=["status", "sent_at", "updated_at"])
            sent.append(invitation)
        if meeting.status == MeetingStatus.SCHEDULED:
            meeting.status = MeetingStatus.INVITATIONS_SENT
            meeting.save(update_fields=["status"])
        self._activity(meeting, "INVITATIONS_SENT", f"{len(sent)} invitation(s) sent.")
        return sent

    def rsvp(
        self,
        *,
        participant: MeetingParticipant,
        status: str,
        comment: str = "",
        accommodation: str = "",
        substitute: str = "",
        preferred_mode: str = "",
        decline_reason: str = "",
    ) -> MeetingParticipant:
        if status not in RSVPStatus.values:
            raise ValidationError(_("Invalid RSVP status."))
        participant.rsvp_status = status
        participant.participant_status = {
            RSVPStatus.ACCEPTED: ParticipantStatus.ACCEPTED,
            RSVPStatus.TENTATIVE: ParticipantStatus.PROVISIONAL,
            RSVPStatus.DECLINED: ParticipantStatus.DECLINED,
        }.get(status, participant.participant_status)
        participant.save(
            update_fields=["rsvp_status", "participant_status", "updated_at"]
        )

        if participant.invitation_id:
            inv = participant.invitation
            inv.rsvp_status = status
            inv.rsvp_at = timezone.now()
            inv.rsvp_comment = comment
            inv.rsvp_accommodation = accommodation
            inv.substitute_attendee = substitute
            inv.preferred_mode = preferred_mode
            inv.decline_reason = decline_reason
            inv.save()
        return participant

    def remove(self, *, participant: MeetingParticipant) -> None:
        self._require_permission(MEETING_MANAGE_PARTICIPANTS)
        participant.participant_status = ParticipantStatus.REMOVED
        participant.save(update_fields=["participant_status", "updated_at"])


# ---------------------------------------------------------------------------
# Agendas
# ---------------------------------------------------------------------------


class AgendaService(BaseService, _MeetingServiceMixin):
    """Create, version and approve meeting agendas."""

    def _execute(
        self,
        *,
        meeting: Meeting,
        title: str = "",
        prepared_by=None,
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        change_summary: str = "",
        notes: str = "",
        instance: MeetingAgenda | None = None,
    ) -> MeetingAgenda:
        self._require_permission(MEETING_MANAGE_AGENDAS)
        self._require_confidentiality(meeting)

        if instance is None:
            version = 1
            latest = meeting.agendas.order_by("-version").first()
            if latest:
                version = latest.version + 1
                latest.is_current_version = False
                latest.save(update_fields=["is_current_version", "updated_at"])
            instance = MeetingAgenda.objects.create(
                meeting=meeting,
                title=title or f"{meeting.title} Agenda",
                version=version,
                status=AgendaStatus.DRAFT,
                prepared_by=prepared_by or self.user,
                confidentiality_level=confidentiality_level,
                is_current_version=True,
                change_summary=change_summary,
                notes=notes,
                created_by=self.user,
                updated_by=self.user,
            )
        else:
            instance.title = title or instance.title
            if change_summary:
                instance.change_summary = change_summary
            instance.updated_by = self.user
            instance.save()
        meeting.agenda_status = AgendaStatus.DRAFT
        meeting.save(update_fields=["agenda_status", "updated_at"])
        return instance

    def create(
        self, *, meeting: Meeting, title: str = "", prepared_by=None, **kwargs
    ) -> MeetingAgenda:
        return self.execute(
            meeting=meeting, title=title, prepared_by=prepared_by or self.user, **kwargs
        )

    def update(self, instance: MeetingAgenda, **kwargs) -> MeetingAgenda:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(kwargs, instance, "meeting", "prepared_by")
        return self.execute(**kwargs)

    def add_item(
        self,
        *,
        agenda: MeetingAgenda,
        item_number: int,
        title: str,
        item_type: str = "INFORMATION",
        description: str = "",
        presenter=None,
        time_allocation_minutes: int = 10,
        start_time=None,
        end_time=None,
        decision_required: bool = False,
        discussion_required: bool = False,
        information_only: bool = False,
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        related_document=None,
        display_order: int | None = None,
        notes: str = "",
        instance: AgendaItem | None = None,
    ) -> AgendaItem:
        self._require_permission(MEETING_MANAGE_AGENDAS)
        display_order = display_order if display_order is not None else item_number
        if instance is None:
            instance = AgendaItem.objects.create(
                agenda=agenda,
                item_number=item_number,
                display_order=display_order,
                title=title,
                description=description,
                item_type=item_type,
                presenter=presenter,
                time_allocation_minutes=time_allocation_minutes,
                start_time=start_time,
                end_time=end_time,
                decision_required=decision_required,
                discussion_required=discussion_required,
                information_only=information_only,
                confidentiality_level=confidentiality_level,
                related_document=related_document,
                notes=notes,
                created_by=self.user,
                updated_by=self.user,
            )
        else:
            for key, value in {
                "item_number": item_number,
                "display_order": display_order,
                "title": title,
                "description": description,
                "item_type": item_type,
                "presenter": presenter,
                "time_allocation_minutes": time_allocation_minutes,
                "start_time": start_time,
                "end_time": end_time,
                "decision_required": decision_required,
                "discussion_required": discussion_required,
                "information_only": information_only,
                "confidentiality_level": confidentiality_level,
                "related_document": related_document,
                "notes": notes,
            }.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()
        return instance

    def reorder_items(self, *, agenda: MeetingAgenda, ordered_ids: list) -> None:
        self._require_permission(MEETING_MANAGE_AGENDAS)
        for index, pk in enumerate(ordered_ids, start=1):
            AgendaItem.objects.filter(pk=pk, agenda=agenda).update(
                display_order=index, item_number=index
            )

    def approve(self, agenda: MeetingAgenda, *, approved_by=None) -> MeetingAgenda:
        self._require_permission(MEETING_APPROVE_AGENDAS)
        if agenda.status not in (AgendaStatus.DRAFT, AgendaStatus.UNDER_REVIEW):
            raise InvalidTransitionError(
                f"Cannot approve an agenda in status {agenda.get_status_display()}."
            )
        agenda.status = AgendaStatus.APPROVED
        agenda.approved_by = approved_by or self.user
        agenda.approved_at = timezone.now()
        agenda.updated_by = self.user
        agenda.save()
        agenda.meeting.agenda_status = AgendaStatus.APPROVED
        agenda.meeting.save(update_fields=["agenda_status", "updated_at"])
        self._activity(
            agenda.meeting, "AGENDA_APPROVED", f"Agenda v{agenda.version} approved."
        )
        return agenda

    def publish(self, *, agenda: MeetingAgenda) -> MeetingAgenda:
        self._require_permission(MEETING_APPROVE_AGENDAS)
        agenda.status = AgendaStatus.PUBLISHED
        agenda.publication_date = timezone.now()
        agenda.updated_by = self.user
        agenda.save()
        agenda.meeting.agenda_status = AgendaStatus.PUBLISHED
        agenda.meeting.save(update_fields=["agenda_status", "updated_at"])
        return agenda

    def delete_item(self, *, item: AgendaItem) -> None:
        self._require_permission(MEETING_MANAGE_AGENDAS)
        item.delete()


# ---------------------------------------------------------------------------
# Attendance & quorum
# ---------------------------------------------------------------------------


class AttendanceService(BaseService, _MeetingServiceMixin):
    """Record, correct and verify meeting attendance."""

    def _execute(
        self,
        *,
        meeting: Meeting,
        participant: MeetingParticipant,
        attendance_status: str = AttendanceStatus.PRESENT,
        attendance_mode: str = "IN_PERSON",
        check_in_at=None,
        check_out_at=None,
        signature_reference: str = "",
        notes: str = "",
        instance: MeetingAttendance | None = None,
    ) -> MeetingAttendance:
        self._require_permission(MEETING_RECORD_ATTENDANCE)
        self._require_confidentiality(meeting)
        if not check_in_at:
            check_in_at = timezone.now()
        data = {
            "meeting": meeting,
            "participant": participant,
            "attendance_status": attendance_status,
            "attendance_mode": attendance_mode,
            "check_in_at": check_in_at,
            "check_out_at": check_out_at,
            "signature_reference": signature_reference,
            "recorded_by": self.user,
            "notes": notes,
        }
        if instance is None:
            instance = MeetingAttendance.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()
        return instance

    def check_in(
        self, *, participant: MeetingParticipant, attendance_mode: str = "IN_PERSON"
    ) -> MeetingAttendance:
        self._require_permission(MEETING_CHECK_IN)
        meeting = participant.meeting
        self._require_confidentiality(meeting)
        record, created = MeetingAttendance.objects.get_or_create(
            meeting=meeting,
            participant=participant,
            defaults={
                "attendance_status": AttendanceStatus.PRESENT,
                "attendance_mode": attendance_mode,
                "check_in_at": timezone.now(),
                "recorded_by": self.user,
                "created_by": self.user,
                "updated_by": self.user,
            },
        )
        if not created and not record.check_in_at:
            record.check_in_at = timezone.now()
            record.attendance_status = AttendanceStatus.PRESENT
            record.save(
                update_fields=["check_in_at", "attendance_status", "updated_at"]
            )
        return record

    def check_out(self, *, participant: MeetingParticipant) -> MeetingAttendance:
        self._require_permission(MEETING_CHECK_OUT)
        record = MeetingAttendance.objects.filter(
            meeting=participant.meeting, participant=participant
        ).first()
        if not record:
            raise ValidationError(
                _("The participant has no attendance record to check out.")
            )
        record.check_out_at = timezone.now()
        record.attendance_status = AttendanceStatus.LEFT_EARLY
        record.save(update_fields=["check_out_at", "attendance_status", "updated_at"])
        return record

    def correct(
        self,
        *,
        attendance: MeetingAttendance,
        attendance_status: str,
        check_in_at=None,
        check_out_at=None,
        reason: str = "",
    ) -> MeetingAttendance:
        self._require_permission(MEETING_RECORD_ATTENDANCE)
        AttendanceCorrectionRecord.objects.create(
            attendance=attendance,
            previous_status=attendance.attendance_status,
            previous_check_in=attendance.check_in_at,
            previous_check_out=attendance.check_out_at,
            new_status=attendance_status,
            new_check_in=check_in_at,
            new_check_out=check_out_at,
            reason=reason,
            corrected_by=self.user,
        )
        attendance.attendance_status = attendance_status
        attendance.check_in_at = (
            check_in_at if check_in_at is not None else attendance.check_in_at
        )
        attendance.check_out_at = (
            check_out_at if check_out_at is not None else attendance.check_out_at
        )
        attendance.verification_status = AttendanceVerificationStatus.UNVERIFIED
        attendance.save(
            update_fields=[
                "attendance_status",
                "check_in_at",
                "check_out_at",
                "verification_status",
                "updated_at",
            ]
        )
        return attendance

    def verify(
        self, *, attendance: MeetingAttendance, accept: bool = True
    ) -> MeetingAttendance:
        self._require_permission(MEETING_VERIFY_ATTENDANCE)
        attendance.verification_status = (
            AttendanceVerificationStatus.VERIFIED
            if accept
            else AttendanceVerificationStatus.REJECTED
        )
        attendance.verified_by = self.user
        attendance.verified_at = timezone.now()
        attendance.save(
            update_fields=[
                "verification_status",
                "verified_by",
                "verified_at",
                "updated_at",
            ]
        )
        return attendance


class QuorumService(BaseService, _MeetingServiceMixin):
    """Evaluate and record meeting quorum."""

    def evaluate(self, *, meeting: Meeting) -> Meeting:
        self._require_permission(MEETING_MANAGE_QUORUM)
        present = meeting.attendance_records.filter(
            attendance_status__in=[
                AttendanceStatus.PRESENT,
                AttendanceStatus.LATE,
                AttendanceStatus.REMOTE,
                AttendanceStatus.PROXY,
            ]
        ).count()

        met, required = self._calculate(meeting, present)
        meeting.quorum_met = met
        if met and not meeting.quorum_met_at:
            meeting.quorum_met_at = timezone.now()
        meeting.save(update_fields=["quorum_met", "quorum_met_at", "updated_at"])
        self._activity(
            meeting,
            "QUORUM_EVALUATED",
            f"{present} present of {required} required.",
            present=present,
            required=required,
            met=met,
        )
        if not met:
            raise QuorumError(
                f"Quorum not met: {present} present of {required} required."
            )
        return meeting

    def _calculate(self, meeting: Meeting, present: int) -> tuple[bool, int]:
        required = 0
        if meeting.quorum_type == QuorumType.FIXED_NUMBER:
            required = meeting.quorum_value or meeting.required_attendees or 0
        elif meeting.quorum_type == QuorumType.PERCENTAGE:
            base = meeting.expected_attendees or meeting.required_attendees or 0
            pct = meeting.quorum_value or 50
            required = max(1, int(round(base * pct / 100)))
        elif meeting.quorum_type == QuorumType.ROLE_BASED:
            required_roles = set(meeting.quorum_required_roles or [])
            if required_roles:
                roles_present = set(
                    meeting.attendance_records.filter(
                        attendance_status__in=[
                            AttendanceStatus.PRESENT,
                            AttendanceStatus.LATE,
                            AttendanceStatus.REMOTE,
                            AttendanceStatus.PROXY,
                        ]
                    ).values_list("participant__role_in_meeting", flat=True)
                )
                return roles_present.issuperset(required_roles), len(required_roles)
            required = meeting.required_attendees or 0
        else:
            required = meeting.required_attendees or 0
        return present >= required, required


# ---------------------------------------------------------------------------
# Minutes
# ---------------------------------------------------------------------------


class MinutesService(BaseService, _MeetingServiceMixin):
    """Draft, submit, review and approve meeting minutes."""

    def _execute(
        self,
        *,
        meeting: Meeting,
        title: str = "",
        summary: str = "",
        opening: str = "",
        closing: str = "",
        quorum_status: str = "",
        prepared_by=None,
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        publication_status: str = PublicationStatus.PARTICIPANTS_ONLY,
        change_summary: str = "",
        notes: str = "",
        instance: MeetingMinutes | None = None,
    ) -> MeetingMinutes:
        self._require_permission(MEETING_DRAFT_MINUTES)
        self._require_confidentiality(meeting)

        if instance is None:
            version = 1
            latest = meeting.minutes_versions.order_by("-version").first()
            if latest:
                version = latest.version + 1
                latest.is_current_version = False
                latest.save(update_fields=["is_current_version", "updated_at"])
            instance = MeetingMinutes.objects.create(
                meeting=meeting,
                title=title or f"{meeting.title} Minutes",
                version=version,
                summary=summary,
                opening=opening,
                closing=closing,
                quorum_status=quorum_status,
                status=MinutesStatus.DRAFT,
                prepared_by=prepared_by or self.user,
                confidentiality_level=confidentiality_level,
                publication_status=publication_status,
                is_current_version=True,
                change_summary=change_summary,
                notes=notes,
                created_by=self.user,
                updated_by=self.user,
            )
            if not instance.reference:
                generated = self._allocate_reference_if_configured(
                    REFERENCE_MODULE_MEETINGS,
                    "minutes",
                    "meeting_minutes",
                    f"Minutes {instance.title}.",
                )
                if generated is not None:
                    instance.reference = generated.reference_number
                    instance.save(update_fields=["reference"])
                    self._confirm_reference(generated, str(instance.pk))
        else:
            instance.title = title or instance.title
            instance.summary = summary
            instance.opening = opening
            instance.closing = closing
            instance.quorum_status = quorum_status
            if change_summary:
                instance.change_summary = change_summary
            instance.updated_by = self.user
            instance.save()

        meeting.minutes_status = MinutesStatus.DRAFT
        if meeting.status == MeetingStatus.COMPLETED:
            meeting.status = MeetingStatus.MINUTES_DRAFTED
            meeting.save(update_fields=["minutes_status", "status", "updated_at"])
        else:
            meeting.save(update_fields=["minutes_status", "updated_at"])
        return instance

    def add_section(
        self,
        *,
        minutes: MeetingMinutes,
        section_type: str,
        title: str,
        content: str = "",
        agenda_item=None,
        display_order: int = 0,
        instance: MinuteSection | None = None,
    ) -> MinuteSection:
        self._require_permission(MEETING_DRAFT_MINUTES)
        if instance is None:
            instance = MinuteSection.objects.create(
                minutes=minutes,
                section_type=section_type,
                title=title,
                content=content,
                agenda_item=agenda_item,
                display_order=display_order,
                created_by=self.user,
                updated_by=self.user,
            )
        else:
            for key, value in {
                "section_type": section_type,
                "title": title,
                "content": content,
                "agenda_item": agenda_item,
                "display_order": display_order,
            }.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()
        return instance

    def create(
        self, *, meeting: Meeting, title: str = "", prepared_by=None, **kwargs
    ) -> MeetingMinutes:
        return self.execute(
            meeting=meeting, title=title, prepared_by=prepared_by or self.user, **kwargs
        )

    def update(self, instance: MeetingMinutes, **kwargs) -> MeetingMinutes:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(kwargs, instance, "meeting", "prepared_by")
        return self.execute(**kwargs)

    def submit(self, minutes: MeetingMinutes) -> MeetingMinutes:
        self._require_permission(MEETING_SUBMIT_MINUTES)
        if minutes.status != MinutesStatus.DRAFT:
            raise MinutesWorkflowError(
                "Only draft minutes can be submitted "
                f"(current: {minutes.get_status_display()})."
            )
        minutes.status = MinutesStatus.SUBMITTED
        minutes.submitted_at = timezone.now()
        minutes.updated_by = self.user
        minutes.save()
        minutes.meeting.minutes_status = MinutesStatus.SUBMITTED
        minutes.meeting.save(update_fields=["minutes_status", "updated_at"])
        self._activity(
            minutes.meeting,
            "MINUTES_SUBMITTED",
            f"Minutes v{minutes.version} submitted.",
        )
        return minutes

    def review(self, *, minutes: MeetingMinutes, reviewed_by=None) -> MeetingMinutes:
        self._require_permission(MEETING_REVIEW_MINUTES)
        minutes.status = MinutesStatus.UNDER_REVIEW
        minutes.reviewed_by = reviewed_by or self.user
        minutes.updated_by = self.user
        minutes.save()
        minutes.meeting.minutes_status = MinutesStatus.UNDER_REVIEW
        minutes.meeting.save(update_fields=["minutes_status", "updated_at"])
        return minutes

    def approve(self, *, minutes: MeetingMinutes, approved_by=None) -> MeetingMinutes:
        self._require_permission(MEETING_APPROVE_MINUTES)
        minutes.status = MinutesStatus.APPROVED
        minutes.approved_by = approved_by or self.user
        minutes.approved_at = timezone.now()
        minutes.updated_by = self.user
        minutes.save()
        meeting = minutes.meeting
        meeting.minutes_status = MinutesStatus.APPROVED
        meeting.status = MeetingStatus.MINUTES_APPROVED
        meeting.save(update_fields=["minutes_status", "status", "updated_at"])
        self._activity(
            meeting, "MINUTES_APPROVED", f"Minutes v{minutes.version} approved."
        )
        return minutes

    def return_for_correction(
        self, *, minutes: MeetingMinutes, reason: str = ""
    ) -> MeetingMinutes:
        self._require_permission(MEETING_REVIEW_MINUTES)
        minutes.status = MinutesStatus.RETURNED
        minutes.notes = reason or minutes.notes
        minutes.updated_by = self.user
        minutes.save()
        minutes.meeting.minutes_status = MinutesStatus.RETURNED
        minutes.meeting.save(update_fields=["minutes_status", "updated_at"])
        return minutes


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


class DecisionService(BaseService, _MeetingServiceMixin):
    """Record, approve and track meeting decisions."""

    def _execute(
        self,
        *,
        meeting: Meeting,
        decision_text: str,
        decision_type: str = "RESOLUTION",
        agenda_item=None,
        proposed_by=None,
        seconded_by=None,
        voting_method: str = "VOICE",
        votes_for: int = 0,
        votes_against: int = 0,
        votes_abstain: int = 0,
        responsible_officer=None,
        effective_date=None,
        review_date=None,
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        notes: str = "",
        instance: MeetingDecision | None = None,
    ) -> MeetingDecision:
        self._require_permission(MEETING_RECORD_DECISIONS)
        self._require_confidentiality(meeting)

        data = {
            "meeting": meeting,
            "decision_text": decision_text,
            "decision_type": decision_type,
            "agenda_item": agenda_item,
            "proposed_by": proposed_by,
            "seconded_by": seconded_by,
            "voting_method": voting_method,
            "quorum_at_vote": "MET" if meeting.quorum_met else "NOT MET",
            "votes_for": votes_for,
            "votes_against": votes_against,
            "votes_abstain": votes_abstain,
            "outcome": DecisionStatus.RECORDED,
            "status": DecisionStatus.RECORDED,
            "responsible_officer": responsible_officer,
            "effective_date": effective_date,
            "review_date": review_date,
            "confidentiality_level": confidentiality_level,
            "is_confidential": confidentiality_level in SENSITIVE_LEVELS,
            "decision_date": timezone.localdate(),
            "notes": notes,
        }
        if instance is None:
            instance = MeetingDecision.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()

        if not instance.reference:
            generated = self._allocate_reference_if_configured(
                REFERENCE_MODULE_MEETINGS,
                "decision",
                "meeting_decision",
                f"Decision for {meeting.title}.",
            )
            if generated is not None:
                instance.reference = generated.reference_number
                instance.save(update_fields=["reference"])
                self._confirm_reference(generated, str(instance.pk))
        meeting.decisions_recorded = True
        meeting.save(update_fields=["decisions_recorded", "updated_at"])
        return instance

    def create(
        self, *, meeting: Meeting, decision_text: str, **kwargs
    ) -> MeetingDecision:
        return self.execute(meeting=meeting, decision_text=decision_text, **kwargs)

    def update(self, instance: MeetingDecision, **kwargs) -> MeetingDecision:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(kwargs, instance, "meeting", "decision_text")
        return self.execute(**kwargs)

    def record_vote(
        self,
        *,
        decision: MeetingDecision,
        participant: MeetingParticipant | get_user_model(),
        vote_type: str,
        comment: str = "",
    ) -> DecisionVote:
        self._require_permission(MEETING_RECORD_DECISIONS)
        from apps.accounts.models import User

        if isinstance(participant, User):
            participant, _ = MeetingParticipant.objects.get_or_create(
                meeting=decision.meeting,
                user=participant,
                defaults={
                    "participant_type": ParticipantType.USER,
                    "role_in_meeting": "ATTENDEE",
                    "name_snapshot": participant.get_full_name()
                    or participant.username,
                    "email_snapshot": participant.email,
                    "created_by": self.user,
                    "updated_by": self.user,
                },
            )
        vote, _ = DecisionVote.objects.update_or_create(
            decision=decision,
            participant=participant,
            defaults={
                "vote_type": vote_type,
                "comment": comment,
                "created_by": self.user,
                "updated_by": self.user,
            },
        )
        self._recount_votes(decision)
        return vote

    def _recount_votes(self, decision: MeetingDecision) -> None:
        from django.db.models import Count

        counts = (
            DecisionVote.objects.filter(decision=decision)
            .values("vote_type")
            .annotate(total=Count("id"))
        )
        tally = {item["vote_type"]: item["total"] for item in counts}
        decision.votes_for = tally.get("FOR", 0)
        decision.votes_against = tally.get("AGAINST", 0)
        decision.votes_abstain = tally.get("ABSTAIN", 0)
        decision.save(
            update_fields=["votes_for", "votes_against", "votes_abstain", "updated_at"]
        )

    def approve(self, *, decision: MeetingDecision) -> MeetingDecision:
        self._require_permission(MEETING_RECORD_DECISIONS)
        decision.status = DecisionStatus.APPROVED
        decision.outcome = DecisionStatus.APPROVED
        decision.updated_by = self.user
        decision.save(update_fields=["status", "outcome", "updated_at"])
        return decision

    def implement(self, *, decision: MeetingDecision) -> MeetingDecision:
        self._require_permission(MEETING_MANAGE_ACTIONS)
        decision.status = DecisionStatus.IMPLEMENTED
        decision.outcome = DecisionStatus.IMPLEMENTED
        decision.updated_by = self.user
        decision.save(update_fields=["status", "outcome", "updated_at"])
        return decision


# ---------------------------------------------------------------------------
# Action items
# ---------------------------------------------------------------------------


class ActionItemService(BaseService, _MeetingServiceMixin):
    """Create, update, escalate and close meeting action items."""

    def _execute(
        self,
        *,
        meeting: Meeting,
        description: str,
        owner=None,
        agenda_item=None,
        decision=None,
        due_date=None,
        start_date=None,
        priority: str = ActionPriority.MEDIUM,
        supporting_team: list | None = None,
        notes: str = "",
        instance: MeetingActionItem | None = None,
    ) -> MeetingActionItem:
        self._require_permission(MEETING_MANAGE_ACTIONS)
        self._require_confidentiality(meeting)

        data = {
            "meeting": meeting,
            "description": description,
            "owner": owner,
            "agenda_item": agenda_item,
            "decision": decision,
            "start_date": start_date,
            "due_date": due_date,
            "priority": priority,
            "supporting_team": supporting_team or [],
            "notes": notes,
            "status": ActionStatus.ASSIGNED if owner else ActionStatus.NOT_STARTED,
        }
        if instance is None:
            instance = MeetingActionItem.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()

        if not instance.reference:
            generated = self._allocate_reference_if_configured(
                REFERENCE_MODULE_MEETINGS,
                "action",
                "meeting_action",
                f"Action for {meeting.title}.",
            )
            if generated is not None:
                instance.reference = generated.reference_number
                instance.save(update_fields=["reference"])
                self._confirm_reference(generated, str(instance.pk))
        meeting.actions_recorded = True
        meeting.save(update_fields=["actions_recorded", "updated_at"])
        return instance

    def create(
        self, *, meeting: Meeting, description: str, owner=None, **kwargs
    ) -> MeetingActionItem:
        return self.execute(
            meeting=meeting, description=description, owner=owner, **kwargs
        )

    def update(self, instance: MeetingActionItem, **kwargs) -> MeetingActionItem:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(kwargs, instance, "meeting", "description")
        return self.execute(**kwargs)

    def update_progress(
        self,
        action: MeetingActionItem,
        *,
        progress: int | None = None,
        progress_percentage: int | None = None,
        status: str | None = None,
        comment: str = "",
        evidence: str = "",
    ) -> MeetingActionItem:
        self._require_permission(MEETING_MANAGE_ACTIONS)
        progress = progress if progress is not None else progress_percentage
        if progress is not None and not 0 <= progress <= 100:
            raise ValidationError(_("Progress must be between 0 and 100."))
        previous_status = action.status

        action.progress_percentage = (
            progress if progress is not None else action.progress_percentage
        )
        if status:
            action.status = status
        if action.status in (ActionStatus.COMPLETED, ActionStatus.VERIFIED):
            action.progress_percentage = 100
            if action.status == ActionStatus.COMPLETED and not action.completion_date:
                action.completion_date = timezone.localdate()
        if action.progress_percentage == 100 and action.status not in (
            ActionStatus.COMPLETED,
            ActionStatus.VERIFIED,
            ActionStatus.CANCELLED,
        ):
            action.status = ActionStatus.COMPLETED
            if not action.completion_date:
                action.completion_date = timezone.localdate()
        if evidence:
            action.evidence = evidence
        action.save()

        ActionFollowUpRecord.objects.create(
            action_item=action,
            update_type=FollowUpType.PROGRESS if not status else FollowUpType.COMMENT,
            comment=comment,
            evidence=evidence,
            previous_status=previous_status,
            new_status=action.status,
            acted_by=self.user,
        )
        return action

    def reassign(
        self,
        *,
        action: MeetingActionItem,
        new_owner,
        reason: str = "",
    ) -> MeetingActionItem:
        self._require_permission(MEETING_MANAGE_ACTIONS)
        previous_owner = action.owner
        action.owner = new_owner
        action.status = ActionStatus.ASSIGNED
        action.save(update_fields=["owner", "status", "updated_at"])
        ActionFollowUpRecord.objects.create(
            action_item=action,
            update_type=FollowUpType.REASSIGN,
            comment=reason,
            previous_owner=previous_owner,
            new_owner=new_owner,
            acted_by=self.user,
        )
        return action

    def extend_deadline(
        self,
        *,
        action: MeetingActionItem,
        new_due_date,
        reason: str = "",
    ) -> MeetingActionItem:
        self._require_permission(MEETING_MANAGE_ACTIONS)
        previous = action.due_date
        action.due_date = new_due_date
        action.save(update_fields=["due_date", "updated_at"])
        ActionFollowUpRecord.objects.create(
            action_item=action,
            update_type=FollowUpType.EXTENSION,
            comment=reason,
            previous_due_date=previous,
            new_due_date=new_due_date,
            acted_by=self.user,
        )
        return action

    def escalate(
        self,
        *,
        action: MeetingActionItem,
        reason: str = "",
    ) -> MeetingActionItem:
        self._require_permission(MEETING_ESCALATE)
        action.escalation_status = EscalationStatus.ESCALATED
        action.escalated_at = timezone.now()
        action.escalation_reason = reason
        action.save(
            update_fields=[
                "escalation_status",
                "escalated_at",
                "escalation_reason",
                "updated_at",
            ]
        )
        ActionFollowUpRecord.objects.create(
            action_item=action,
            update_type=FollowUpType.ESCALATION,
            comment=reason,
            acted_by=self.user,
        )
        return action

    def complete(
        self, action: MeetingActionItem, *, evidence: str = ""
    ) -> MeetingActionItem:
        self._require_permission(MEETING_MANAGE_ACTIONS)
        return self.update_progress(
            action=action,
            progress=100,
            status=ActionStatus.COMPLETED,
            evidence=evidence,
        )

    def verify(
        self, *, action: MeetingActionItem, accept: bool = True, comment: str = ""
    ) -> MeetingActionItem:
        self._require_permission(MEETING_VERIFY_ACTIONS)
        action.verification_status = (
            AttendanceVerificationStatus.VERIFIED
            if accept
            else AttendanceVerificationStatus.REJECTED
        )
        action.verified_by = self.user
        action.verified_at = timezone.now()
        if accept:
            action.status = ActionStatus.VERIFIED
        action.save(
            update_fields=[
                "verification_status",
                "verified_by",
                "verified_at",
                "status",
                "updated_at",
            ]
        )
        ActionFollowUpRecord.objects.create(
            action_item=action,
            update_type=FollowUpType.VERIFICATION,
            comment=comment,
            new_status=action.status,
            acted_by=self.user,
        )
        return action


class MattersArisingService(BaseService, _MeetingServiceMixin):
    """Track matters arising from previous minutes."""

    def _execute(
        self,
        *,
        source_meeting: Meeting,
        update: str,
        source_action=None,
        source_decision=None,
        current_meeting=None,
        responsible_officer=None,
        follow_up_required: bool = False,
    ) -> MattersArising:
        self._require_permission(MEETING_MANAGE_ACTIONS)
        return MattersArising.objects.create(
            source_meeting=source_meeting,
            source_action=source_action,
            source_decision=source_decision,
            current_meeting=current_meeting,
            update=update,
            status=MatterStatus.OPEN,
            responsible_officer=responsible_officer,
            follow_up_required=follow_up_required,
            created_by=self.user,
            updated_by=self.user,
        )

    def close(self, *, matter: MattersArising, notes: str = "") -> MattersArising:
        self._require_permission(MEETING_MANAGE_ACTIONS)
        matter.status = MatterStatus.CLOSED
        matter.closure_notes = notes
        matter.closed_at = timezone.now()
        matter.updated_by = self.user
        matter.save()
        return matter


# ---------------------------------------------------------------------------
# Reminders & documents
# ---------------------------------------------------------------------------


class ReminderService(BaseService, _MeetingServiceMixin):
    """Create reminders for events, meetings and action deadlines."""

    def _execute(
        self,
        *,
        target,
        reminder_type: str = ReminderType.MEETING_START,
        recipient_type: str = ReminderRecipientType.PARTICIPANTS,
        lead_minutes: int = 30,
        channel: str = ReminderChannel.EMAIL,
        instance: EventReminder | None = None,
    ) -> EventReminder:
        self._require_permission(MEETING_MANAGE_REMINDERS)
        meeting = target if isinstance(target, Meeting) else None
        event = target if isinstance(target, CalendarEvent) else None
        anchor = (meeting or event).start_at
        due_at = anchor - timedelta(minutes=lead_minutes)
        data = {
            "event": event,
            "meeting": meeting,
            "reminder_type": reminder_type,
            "recipient_type": recipient_type,
            "lead_minutes": lead_minutes,
            "channel": channel,
            "status": ReminderStatus.PENDING,
            "due_at": due_at,
        }
        if instance is None:
            instance = EventReminder.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()
        return instance

    def mark_due(self, *, reminder: EventReminder) -> EventReminder:
        """Mark a reminder as due for dispatch (outbound channel hook)."""
        reminder.status = ReminderStatus.SENT
        reminder.sent_at = timezone.now()
        reminder.save(update_fields=["status", "sent_at", "updated_at"])
        return reminder

    def mark_failed(self, *, reminder: EventReminder, error: str = "") -> EventReminder:
        reminder.retry_count += 1
        if reminder.retry_count >= reminder.max_retries:
            reminder.status = ReminderStatus.FAILED
        reminder.error_message = error
        reminder.save(
            update_fields=["retry_count", "status", "error_message", "updated_at"]
        )
        return reminder


class MeetingDocumentService(BaseService, _MeetingServiceMixin):
    """Link documents to meetings through the central document engine."""

    def link(
        self,
        *,
        meeting: Meeting,
        document,
        document_type: str = MeetingDocumentType.REPORT,
        is_public_to_participants: bool = True,
        notes: str = "",
    ) -> MeetingDocument:
        self._require_permission(MEETING_MANAGE_AGENDAS)
        link, created = MeetingDocument.objects.get_or_create(
            meeting=meeting,
            document=document,
            defaults={
                "document_type": document_type,
                "is_public_to_participants": is_public_to_participants,
                "published_at": timezone.now(),
                "notes": notes,
                "created_by": self.user,
                "updated_by": self.user,
            },
        )
        if not created:
            link.document_type = document_type
            link.is_public_to_participants = is_public_to_participants
            link.notes = notes
            link.updated_by = self.user
            link.save()
        return link

    def unlink(self, *, link: MeetingDocument) -> None:
        self._require_permission(MEETING_MANAGE_AGENDAS)
        link.delete()


# ---------------------------------------------------------------------------
# Template & venue administration
# ---------------------------------------------------------------------------


class TemplateService(BaseService, _MeetingServiceMixin):
    """Create and maintain meeting templates."""

    def _execute(
        self,
        *,
        name: str,
        code: str,
        meeting_type: str = "TEAM",
        description: str = "",
        default_title: str = "",
        default_purpose: str = "",
        default_objectives: list | None = None,
        standard_duration_minutes: int = 60,
        default_confidentiality: str = ConfidentialityLevel.INTERNAL,
        default_quorum_type: str = QuorumType.FIXED_NUMBER,
        default_quorum_value: int | None = None,
        quorum_required_roles: list | None = None,
        default_participant_roles: list | None = None,
        agenda_template: list | None = None,
        minutes_template: list | None = None,
        decision_requirements: dict | None = None,
        action_requirements: dict | None = None,
        recurrence_defaults: dict | None = None,
        approval_required: bool = False,
        default_reminders: list | None = None,
        is_active: bool = True,
        instance: MeetingTemplate | None = None,
    ) -> MeetingTemplate:
        self._require_permission(MEETING_MANAGE_TEMPLATES)
        data = {
            "name": name,
            "code": code,
            "meeting_type": meeting_type,
            "description": description,
            "default_title": default_title,
            "default_purpose": default_purpose,
            "default_objectives": default_objectives or [],
            "standard_duration_minutes": standard_duration_minutes,
            "default_confidentiality": default_confidentiality,
            "default_quorum_type": default_quorum_type,
            "default_quorum_value": default_quorum_value,
            "quorum_required_roles": quorum_required_roles or [],
            "default_participant_roles": default_participant_roles or [],
            "agenda_template": agenda_template or [],
            "minutes_template": minutes_template or [],
            "decision_requirements": decision_requirements or {},
            "action_requirements": action_requirements or {},
            "recurrence_defaults": recurrence_defaults or {},
            "approval_required": approval_required,
            "default_reminders": default_reminders or [],
            "is_active": is_active,
        }
        if instance is None:
            instance = MeetingTemplate.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()
        return instance

    def create(self, *, name: str, code: str, **kwargs) -> MeetingTemplate:
        return self.execute(name=name, code=code, **kwargs)

    def update(self, instance: MeetingTemplate, **kwargs) -> MeetingTemplate:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(kwargs, instance, "name", "code")
        return self.execute(**kwargs)

    def activate(self, instance: MeetingTemplate) -> MeetingTemplate:
        self._require_permission(MEETING_MANAGE_TEMPLATES)
        instance.is_active = True
        instance.save(update_fields=["is_active", "updated_at"])
        return instance

    def deactivate(self, instance: MeetingTemplate) -> MeetingTemplate:
        self._require_permission(MEETING_MANAGE_TEMPLATES)
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        return instance


class VenueService(BaseService, _MeetingServiceMixin):
    """Create and maintain meeting venues."""

    def _execute(
        self,
        *,
        name: str,
        venue_type: str = "BOARDROOM",
        description: str = "",
        address: str = "",
        location_details: str = "",
        capacity: int | None = None,
        accessibility_features: list | None = None,
        equipment: list | None = None,
        contact_person: str = "",
        contact_phone: str = "",
        contact_email: str = "",
        organization_unit=None,
        access_scope=None,
        is_active: bool = True,
        notes: str = "",
        instance: MeetingVenue | None = None,
    ) -> MeetingVenue:
        self._require_permission(MEETING_MANAGE_VENUES)
        data = {
            "name": name,
            "venue_type": venue_type,
            "description": description,
            "address": address,
            "location_details": location_details,
            "capacity": capacity,
            "accessibility_features": accessibility_features or [],
            "equipment": equipment or [],
            "contact_person": contact_person,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "organization_unit": organization_unit,
            "access_scope": access_scope,
            "is_active": is_active,
            "notes": notes,
        }
        if instance is None:
            instance = MeetingVenue.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.updated_by = self.user
            instance.save()
        return instance

    def create(self, *, name: str, **kwargs) -> MeetingVenue:
        return self.execute(name=name, **kwargs)

    def update(self, instance: MeetingVenue, **kwargs) -> MeetingVenue:
        kwargs.setdefault("instance", instance)
        self._default_from_instance(kwargs, instance, "name")
        return self.execute(**kwargs)

    def archive(self, instance: MeetingVenue) -> MeetingVenue:
        self._require_permission(MEETING_MANAGE_VENUES)
        instance.archive(archived_by=self.user)
        return instance


class ConfidentialAccessService(BaseService, _MeetingServiceMixin):
    """Log access to confidential meeting records."""

    def log_access(
        self,
        *,
        meeting: Meeting,
        access_type: str,
        target_model: str = "",
        target_reference: str = "",
        reason: str = "",
        ip_address=None,
    ) -> ConfidentialAccessLog:
        self._require_confidentiality(meeting)
        return ConfidentialAccessLog.objects.create(
            meeting=meeting,
            actor=self.user,
            access_type=access_type,
            target_model=target_model,
            target_reference=target_reference,
            reason=reason,
            ip_address=ip_address,
        )
