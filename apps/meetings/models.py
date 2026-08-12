"""Data models for the Phase 24 Calendar & Meetings module.

The module provides centralized organizational scheduling: calendars, events,
meetings, participants, invitations, agendas, attendance, quorum, minutes,
decisions, action items, reminders, venues, templates and the immutable
activity timeline.  All state changes flow through the service layer.
"""

# ruff: noqa: RUF012 - Django Meta options are declarative class attributes.

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    IsActiveModel,
    NotesModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)
from apps.organizations.models import OrganizationUnit
from apps.rbac.models import AccessScope

from .constants import (
    ActionPriority,
    ActionStatus,
    AgendaItemType,
    AgendaStatus,
    AttendanceMode,
    AttendanceStatus,
    AttendanceVerificationStatus,
    CalendarShareLevel,
    CalendarType,
    CalendarVisibility,
    ConfidentialityLevel,
    DecisionStatus,
    DecisionType,
    EscalationStatus,
    EventPriority,
    EventStatus,
    EventType,
    FollowUpType,
    InvitationStatus,
    MatterStatus,
    MeetingDocumentType,
    MeetingMode,
    MeetingStatus,
    MeetingType,
    MinuteSectionType,
    MinutesStatus,
    ParticipantRole,
    ParticipantStatus,
    ParticipantType,
    PublicationStatus,
    QuorumType,
    ReminderChannel,
    ReminderRecipientType,
    ReminderStatus,
    ReminderType,
    RSVPStatus,
    VenueReservationStatus,
    VenueType,
    VirtualMeetingProvider,
    VoteType,
    VotingMethod,
)
from .validators import (
    validate_recurrence_rule,
    validate_time_range,
)


class MeetingRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Common actor and timestamp metadata for meeting domain rows."""

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Configurable reference data
# ---------------------------------------------------------------------------


class CalendarTypeConfig(MeetingRecord, IsActiveModel):
    """A configurable calendar type used across the organization."""

    code = models.SlugField(_("Code"), max_length=60, unique=True)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    default_visibility = models.CharField(
        _("Default visibility"),
        max_length=30,
        choices=CalendarVisibility.choices,
        default=CalendarVisibility.TEAM,
    )
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Calendar Type")
        verbose_name_plural = _("Calendar Types")
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class MeetingVenue(
    MeetingRecord, SoftDeleteModel, ArchivableModel, IsActiveModel, NotesModel
):
    """A physical or virtual meeting venue."""

    name = models.CharField(_("Name"), max_length=200)
    venue_type = models.CharField(
        _("Venue type"),
        max_length=30,
        choices=VenueType.choices,
        default=VenueType.BOARDROOM,
    )
    description = models.TextField(_("Description"), blank=True)
    address = models.CharField(_("Address"), max_length=300, blank=True)
    location_details = models.CharField(
        _("Location details"), max_length=300, blank=True
    )
    capacity = models.PositiveIntegerField(_("Capacity"), null=True, blank=True)
    accessibility_features = models.JSONField(
        _("Accessibility features"), default=list, blank=True
    )
    equipment = models.JSONField(_("Equipment"), default=list, blank=True)
    contact_person = models.CharField(_("Contact person"), max_length=160, blank=True)
    contact_phone = models.CharField(_("Contact phone"), max_length=30, blank=True)
    contact_email = models.EmailField(_("Contact email"), blank=True)
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meeting_venues",
        verbose_name=_("Organization unit"),
    )
    access_scope = models.ForeignKey(
        AccessScope,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meeting_venues",
        verbose_name=_("Access scope"),
    )

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting Venue")
        verbose_name_plural = _("Meeting Venues")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class MeetingTemplate(MeetingRecord, SoftDeleteModel, IsActiveModel, NotesModel):
    """A reusable template for standard meetings."""

    name = models.CharField(_("Name"), max_length=200)
    code = models.SlugField(_("Code"), max_length=60, unique=True)
    description = models.TextField(_("Description"), blank=True)
    meeting_type = models.CharField(
        _("Meeting type"),
        max_length=40,
        choices=MeetingType.choices,
        default=MeetingType.TEAM,
    )
    default_title = models.CharField(_("Default title"), max_length=255, blank=True)
    default_purpose = models.TextField(_("Default purpose"), blank=True)
    default_objectives = models.JSONField(
        _("Default objectives"), default=list, blank=True
    )
    standard_duration_minutes = models.PositiveIntegerField(
        _("Standard duration (minutes)"), default=60
    )
    default_confidentiality = models.CharField(
        _("Default confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    default_quorum_type = models.CharField(
        _("Default quorum type"),
        max_length=30,
        choices=QuorumType.choices,
        default=QuorumType.FIXED_NUMBER,
    )
    default_quorum_value = models.PositiveIntegerField(
        _("Default quorum value"), null=True, blank=True
    )
    quorum_required_roles = models.JSONField(
        _("Quorum required roles"), default=list, blank=True
    )
    default_participant_roles = models.JSONField(
        _("Default participant roles"), default=list, blank=True
    )
    agenda_template = models.JSONField(_("Agenda template"), default=list, blank=True)
    minutes_template = models.JSONField(_("Minutes template"), default=list, blank=True)
    decision_requirements = models.JSONField(
        _("Decision requirements"), default=dict, blank=True
    )
    action_requirements = models.JSONField(
        _("Action requirements"), default=dict, blank=True
    )
    recurrence_defaults = models.JSONField(
        _("Recurrence defaults"), default=dict, blank=True
    )
    approval_required = models.BooleanField(
        _("Approval required for minutes"), default=False
    )
    default_reminders = models.JSONField(
        _("Default reminders"), default=list, blank=True
    )

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting Template")
        verbose_name_plural = _("Meeting Templates")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Calendars
# ---------------------------------------------------------------------------


class Calendar(
    MeetingRecord, SoftDeleteModel, ArchivableModel, IsActiveModel, NotesModel
):
    """An organizational calendar to which events belong."""

    reference = models.CharField(_("Reference"), max_length=80, unique=True, blank=True)
    name = models.CharField(_("Name"), max_length=200)
    calendar_type = models.CharField(
        _("Calendar type"),
        max_length=40,
        choices=CalendarType.choices,
        default=CalendarType.TEAM,
    )
    description = models.TextField(_("Description"), blank=True)
    visibility = models.CharField(
        _("Visibility"),
        max_length=30,
        choices=CalendarVisibility.choices,
        default=CalendarVisibility.TEAM,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_calendars",
        verbose_name=_("Owner"),
    )
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calendars",
        verbose_name=_("Organization unit"),
    )
    access_scope = models.ForeignKey(
        AccessScope,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calendars",
        verbose_name=_("Access scope"),
    )
    default_timezone = models.CharField(
        _("Default timezone"), max_length=64, default="UTC"
    )
    color = models.CharField(_("Color"), max_length=9, default="#0d6efd")
    is_default = models.BooleanField(_("Is default"), default=False)
    is_confidential = models.BooleanField(_("Is confidential"), default=False)
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Calendar")
        verbose_name_plural = _("Calendars")
        ordering = ("name",)
        indexes = [
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["visibility", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("meetings:calendar_detail", args=[self.pk])


class CalendarShare(MeetingRecord):
    """A permission grant on a calendar to a user or scope."""

    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        related_name="shares",
        verbose_name=_("Calendar"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calendar_shares",
        verbose_name=_("User"),
    )
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calendar_shares",
        verbose_name=_("Organization unit"),
    )
    access_scope = models.ForeignKey(
        AccessScope,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calendar_shares",
        verbose_name=_("Access scope"),
    )
    permission_level = models.CharField(
        _("Permission level"),
        max_length=30,
        choices=CalendarShareLevel.choices,
        default=CalendarShareLevel.VIEW_EVENTS,
    )
    expires_at = models.DateTimeField(_("Expires at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Calendar Share")
        verbose_name_plural = _("Calendar Shares")
        constraints = [
            models.UniqueConstraint(
                fields=["calendar", "user"],
                name="uq_meetings_calendarshare_calendar_user",
                condition=models.Q(user__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["calendar", "organization_unit"],
                name="uq_meetings_calendarshare_calendar_unit",
                condition=models.Q(organization_unit__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["calendar", "access_scope"],
                name="uq_meetings_calendarshare_calendar_scope",
                condition=models.Q(access_scope__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        target = self.user or self.organization_unit or self.access_scope
        return f"{self.calendar.name} -> {target}"


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class CalendarEvent(MeetingRecord, SoftDeleteModel, ArchivableModel, NotesModel):
    """A single event on an organizational calendar."""

    reference = models.CharField(_("Reference"), max_length=80, unique=True, blank=True)
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Calendar"),
    )
    event_type = models.CharField(
        _("Event type"),
        max_length=40,
        choices=EventType.choices,
        default=EventType.MEETING,
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    start_at = models.DateTimeField(_("Start"), db_index=True)
    end_at = models.DateTimeField(_("End"))
    all_day = models.BooleanField(_("All day"), default=False)
    timezone = models.CharField(_("Timezone"), max_length=64, default="UTC")

    venue = models.ForeignKey(
        MeetingVenue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name=_("Venue"),
    )
    online_meeting_link = models.URLField(_("Online meeting link"), blank=True)
    location_details = models.CharField(
        _("Location details"), max_length=300, blank=True
    )

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hosted_events",
        verbose_name=_("Host"),
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organized_events",
        verbose_name=_("Organizer"),
    )

    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name=_("Program"),
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name=_("Project"),
    )
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name=_("Organization unit"),
    )
    access_scope = models.ForeignKey(
        AccessScope,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name=_("Access scope"),
    )

    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=EventStatus.choices,
        default=EventStatus.DRAFT,
        db_index=True,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=EventPriority.choices,
        default=EventPriority.NORMAL,
    )
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    is_confidential = models.BooleanField(_("Is confidential"), default=False)

    recurrence_rule = models.JSONField(_("Recurrence rule"), default=dict, blank=True)
    is_recurring = models.BooleanField(_("Is recurring"), default=False, db_index=True)
    reminder_config = models.JSONField(
        _("Reminder configuration"), default=list, blank=True
    )
    maximum_attendance = models.PositiveIntegerField(
        _("Maximum attendance"), null=True, blank=True
    )
    registration_required = models.BooleanField(
        _("Registration required"), default=False
    )
    approval_required = models.BooleanField(_("Approval required"), default=False)

    cancelled_at = models.DateTimeField(_("Cancelled at"), null=True, blank=True)
    cancellation_reason = models.TextField(_("Cancellation reason"), blank=True)

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Calendar Event")
        verbose_name_plural = _("Calendar Events")
        ordering = ("start_at",)
        indexes = [
            models.Index(fields=["calendar", "start_at"]),
            models.Index(fields=["status", "start_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.start_at:%Y-%m-%d %H:%M})"

    def get_absolute_url(self) -> str:
        return reverse("meetings:event_detail", args=[self.pk])

    def clean(self) -> None:
        super().clean()
        validate_time_range(self.start_at, self.end_at)
        try:
            validate_recurrence_rule(self.recurrence_rule or None)
        except ValidationError as exc:
            raise ValidationError({"recurrence_rule": exc}) from exc
        if self.recurrence_rule and self.recurrence_rule.get("frequency"):
            self.is_recurring = True

    @property
    def duration(self) -> timedelta:
        return self.end_at - self.start_at


class EventOccurrence(MeetingRecord):
    """An explicit occurrence (override or cancellation) of a recurring event."""

    event = models.ForeignKey(
        CalendarEvent,
        on_delete=models.CASCADE,
        related_name="occurrences",
        verbose_name=_("Event"),
    )
    sequence = models.PositiveIntegerField(_("Sequence"), default=0)
    original_start = models.DateTimeField(_("Original start"))
    occurrence_start = models.DateTimeField(_("Occurrence start"))
    occurrence_end = models.DateTimeField(_("Occurrence end"))
    is_rescheduled = models.BooleanField(_("Is rescheduled"), default=False)
    is_cancelled = models.BooleanField(_("Is cancelled"), default=False)
    exception_reason = models.TextField(_("Exception reason"), blank=True)
    venue_override = models.ForeignKey(
        MeetingVenue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_occurrences",
        verbose_name=_("Venue override"),
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Event Occurrence")
        verbose_name_plural = _("Event Occurrences")
        ordering = ("original_start",)
        constraints = [
            models.UniqueConstraint(
                fields=["event", "original_start"],
                name="uq_meetings_eventoccurrence_event_start",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event.title} @ {self.occurrence_start:%Y-%m-%d %H:%M}"


class EventReminder(MeetingRecord):
    """A configured reminder for an event or meeting."""

    event = models.ForeignKey(
        CalendarEvent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reminders",
        verbose_name=_("Event"),
    )
    meeting = models.ForeignKey(
        "Meeting",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reminders",
        verbose_name=_("Meeting"),
    )
    reminder_type = models.CharField(
        _("Reminder type"),
        max_length=40,
        choices=ReminderType.choices,
        default=ReminderType.MEETING_START,
    )
    recipient_type = models.CharField(
        _("Recipient type"),
        max_length=30,
        choices=ReminderRecipientType.choices,
        default=ReminderRecipientType.PARTICIPANTS,
    )
    lead_minutes = models.PositiveIntegerField(_("Lead time (minutes)"), default=30)
    channel = models.CharField(
        _("Channel"),
        max_length=20,
        choices=ReminderChannel.choices,
        default=ReminderChannel.EMAIL,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ReminderStatus.choices,
        default=ReminderStatus.PENDING,
    )
    due_at = models.DateTimeField(_("Due at"), null=True, blank=True)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    error_message = models.TextField(_("Error message"), blank=True)
    retry_count = models.PositiveIntegerField(_("Retry count"), default=0)
    max_retries = models.PositiveIntegerField(_("Max retries"), default=3)

    class Meta:
        verbose_name = _("Event Reminder")
        verbose_name_plural = _("Event Reminders")
        indexes = [
            models.Index(fields=["status", "due_at"]),
        ]

    def __str__(self) -> str:
        target = self.event or self.meeting
        return f"{self.get_reminder_type_display()} ({self.lead_minutes}m) -> {target}"


# ---------------------------------------------------------------------------
# Meetings
# ---------------------------------------------------------------------------


class Meeting(MeetingRecord, SoftDeleteModel, ArchivableModel, NotesModel):
    """A scheduled organizational meeting."""

    reference = models.CharField(_("Reference"), max_length=80, unique=True, blank=True)
    event = models.OneToOneField(
        CalendarEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meeting",
        verbose_name=_("Calendar event"),
    )
    meeting_type = models.CharField(
        _("Meeting type"),
        max_length=40,
        choices=MeetingType.choices,
        default=MeetingType.TEAM,
    )
    template = models.ForeignKey(
        MeetingTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        verbose_name=_("Template"),
    )
    title = models.CharField(_("Title"), max_length=255)
    purpose = models.TextField(_("Purpose"), blank=True)
    objectives = models.JSONField(_("Objectives"), default=list, blank=True)

    start_at = models.DateTimeField(_("Start"), db_index=True)
    end_at = models.DateTimeField(_("End"))
    timezone = models.CharField(_("Timezone"), max_length=64, default="UTC")
    mode = models.CharField(
        _("Mode"),
        max_length=20,
        choices=MeetingMode.choices,
        default=MeetingMode.IN_PERSON,
    )

    venue = models.ForeignKey(
        MeetingVenue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        verbose_name=_("Venue"),
    )
    venue_reservation_status = models.CharField(
        _("Venue reservation status"),
        max_length=20,
        choices=VenueReservationStatus.choices,
        default=VenueReservationStatus.REQUESTED,
    )

    virtual_provider = models.CharField(
        _("Virtual provider"),
        max_length=30,
        choices=VirtualMeetingProvider.choices,
        blank=True,
    )
    online_meeting_link = models.URLField(_("Online meeting link"), blank=True)
    meeting_id = models.CharField(_("Meeting ID"), max_length=100, blank=True)
    meeting_passcode = models.CharField(
        _("Meeting passcode"), max_length=100, blank=True
    )
    provider_settings = models.JSONField(
        _("Provider settings"), default=dict, blank=True
    )
    virtual_consent_required = models.BooleanField(
        _("Recording consent required"), default=False
    )
    recording_allowed = models.BooleanField(_("Recording allowed"), default=False)

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organized_meetings",
        verbose_name=_("Organizer"),
    )
    chairperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chaired_meetings",
        verbose_name=_("Chairperson"),
    )
    secretary = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secretaried_meetings",
        verbose_name=_("Secretary"),
    )
    minute_taker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="minuted_meetings",
        verbose_name=_("Minute taker"),
    )
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="facilitated_meetings",
        verbose_name=_("Facilitator"),
    )

    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        verbose_name=_("Program"),
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        verbose_name=_("Project"),
    )
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        verbose_name=_("Organization unit"),
    )
    access_scope = models.ForeignKey(
        AccessScope,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        verbose_name=_("Access scope"),
    )

    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=MeetingStatus.choices,
        default=MeetingStatus.DRAFT,
        db_index=True,
    )
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    is_confidential = models.BooleanField(_("Is confidential"), default=False)
    publication_status = models.CharField(
        _("Publication status"),
        max_length=30,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PRIVATE,
    )

    expected_attendees = models.PositiveIntegerField(_("Expected attendees"), default=0)
    required_attendees = models.PositiveIntegerField(_("Required attendees"), default=0)
    quorum_type = models.CharField(
        _("Quorum type"),
        max_length=30,
        choices=QuorumType.choices,
        default=QuorumType.FIXED_NUMBER,
    )
    quorum_value = models.PositiveIntegerField(_("Quorum value"), null=True, blank=True)
    quorum_required_roles = models.JSONField(
        _("Quorum required roles"), default=list, blank=True
    )
    quorum_met = models.BooleanField(_("Quorum met"), default=False)
    quorum_met_at = models.DateTimeField(_("Quorum met at"), null=True, blank=True)

    agenda_status = models.CharField(
        _("Agenda status"),
        max_length=30,
        choices=AgendaStatus.choices,
        default=AgendaStatus.DRAFT,
    )
    attendance_status = models.CharField(
        _("Attendance status"), max_length=30, default="NOT_OPEN"
    )
    minutes_status = models.CharField(
        _("Minutes status"),
        max_length=30,
        choices=MinutesStatus.choices,
        default=MinutesStatus.DRAFT,
    )
    decisions_recorded = models.BooleanField(_("Decisions recorded"), default=False)
    actions_recorded = models.BooleanField(_("Actions recorded"), default=False)

    original_start_at = models.DateTimeField(_("Original start"), null=True, blank=True)
    original_end_at = models.DateTimeField(_("Original end"), null=True, blank=True)
    is_rescheduled = models.BooleanField(_("Is rescheduled"), default=False)
    reschedule_reason = models.TextField(_("Reschedule reason"), blank=True)
    postponement_until = models.DateTimeField(
        _("Postponed until"), null=True, blank=True
    )
    cancelled_at = models.DateTimeField(_("Cancelled at"), null=True, blank=True)
    cancellation_reason = models.TextField(_("Cancellation reason"), blank=True)
    completion_notes = models.TextField(_("Completion notes"), blank=True)
    completed_at = models.DateTimeField(_("Completed at"), null=True, blank=True)
    closed_at = models.DateTimeField(_("Closed at"), null=True, blank=True)

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        ordering = ("start_at",)
        indexes = [
            models.Index(fields=["status", "start_at"]),
            models.Index(fields=["meeting_type", "start_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.start_at:%Y-%m-%d %H:%M})"

    def get_absolute_url(self) -> str:
        return reverse("meetings:meeting_detail", args=[self.pk])

    def clean(self) -> None:
        super().clean()
        validate_time_range(self.start_at, self.end_at)
        if self.is_confidential:
            self.confidentiality_level = ConfidentialityLevel.CONFIDENTIAL

    def save(self, *args, **kwargs) -> None:
        if self.is_confidential and not self.confidentiality_level:
            self.confidentiality_level = ConfidentialityLevel.CONFIDENTIAL
        super().save(*args, **kwargs)


class MeetingParticipant(MeetingRecord, NotesModel):
    """A person invited to or attending a meeting."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="participants",
        verbose_name=_("Meeting"),
    )
    participant_type = models.CharField(
        _("Participant type"),
        max_length=30,
        choices=ParticipantType.choices,
        default=ParticipantType.USER,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="meeting_participations",
        verbose_name=_("User"),
    )
    name_snapshot = models.CharField(_("Name"), max_length=200, blank=True)
    email_snapshot = models.EmailField(_("Email"), blank=True)
    phone_snapshot = models.CharField(_("Phone"), max_length=30, blank=True)
    organization = models.CharField(_("Organization"), max_length=200, blank=True)
    role_in_meeting = models.CharField(
        _("Role in meeting"),
        max_length=30,
        choices=ParticipantRole.choices,
        default=ParticipantRole.ATTENDEE,
    )
    is_required = models.BooleanField(_("Required attendee"), default=False)
    participant_status = models.CharField(
        _("Participant status"),
        max_length=20,
        choices=ParticipantStatus.choices,
        default=ParticipantStatus.PROPOSED,
        db_index=True,
    )
    rsvp_status = models.CharField(
        _("RSVP status"),
        max_length=20,
        choices=RSVPStatus.choices,
        default=RSVPStatus.NO_RESPONSE,
    )
    special_requirements = models.TextField(_("Special requirements"), blank=True)
    accessibility_accommodation = models.TextField(
        _("Accessibility accommodation"), blank=True
    )
    invitation = models.OneToOneField(
        "MeetingInvitation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="participant",
        verbose_name=_("Invitation"),
    )

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting Participant")
        verbose_name_plural = _("Meeting Participants")
        ordering = ("role_in_meeting", "name_snapshot")
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "user"],
                name="uq_meetings_participant_meeting_user",
                condition=models.Q(user__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["meeting", "email_snapshot"],
                name="uq_meetings_participant_meeting_email",
                condition=~models.Q(email_snapshot=""),
            ),
        ]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        if self.user:
            return self.user.get_full_name() or self.user.email
        return self.name_snapshot or self.email_snapshot or "Unnamed"

    def clean(self) -> None:
        super().clean()
        if not self.user and not self.name_snapshot and not self.email_snapshot:
            raise ValidationError(
                _("Provide a user, name, or email address for the participant."),
                code="participant_identity_required",
            )


class MeetingInvitation(MeetingRecord):
    """Delivery and RSVP tracking for a participant invitation."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("Meeting"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    delivery_channel = models.CharField(
        _("Delivery channel"),
        max_length=20,
        choices=ReminderChannel.choices,
        default=ReminderChannel.EMAIL,
    )
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("Delivered at"), null=True, blank=True)
    delivered_confirmed_by_provider = models.BooleanField(
        _("Delivery confirmed by provider"), default=False
    )
    rsvp_status = models.CharField(
        _("RSVP status"),
        max_length=20,
        choices=RSVPStatus.choices,
        default=RSVPStatus.NO_RESPONSE,
    )
    rsvp_at = models.DateTimeField(_("RSVP at"), null=True, blank=True)
    rsvp_comment = models.TextField(_("RSVP comment"), blank=True)
    rsvp_accommodation = models.TextField(_("RSVP accommodation"), blank=True)
    substitute_attendee = models.CharField(
        _("Substitute attendee"), max_length=200, blank=True
    )
    preferred_mode = models.CharField(
        _("Preferred mode"), max_length=20, choices=MeetingMode.choices, blank=True
    )
    decline_reason = models.TextField(_("Decline reason"), blank=True)
    error_message = models.TextField(_("Error message"), blank=True)

    class Meta:
        verbose_name = _("Meeting Invitation")
        verbose_name_plural = _("Meeting Invitations")

    def __str__(self) -> str:
        return f"Invitation to {self.meeting.title}"


# ---------------------------------------------------------------------------
# Agendas
# ---------------------------------------------------------------------------


class MeetingAgenda(MeetingRecord, NotesModel):
    """A versioned agenda for a meeting."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="agendas",
        verbose_name=_("Meeting"),
    )
    version = models.PositiveIntegerField(_("Version"), default=1)
    title = models.CharField(_("Title"), max_length=255, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=AgendaStatus.choices,
        default=AgendaStatus.DRAFT,
    )
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prepared_agendas",
        verbose_name=_("Prepared by"),
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_agendas",
        verbose_name=_("Reviewed by"),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_agendas",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    publication_date = models.DateTimeField(
        _("Publication date"), null=True, blank=True
    )
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    is_current_version = models.BooleanField(_("Is current version"), default=True)
    change_summary = models.TextField(_("Change summary"), blank=True)

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting Agenda")
        verbose_name_plural = _("Meeting Agendas")
        ordering = ("-version",)
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "version"],
                name="uq_meetings_agenda_meeting_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.meeting.title} (v{self.version})"

    def get_absolute_url(self) -> str:
        return reverse("meetings:agenda_detail", args=[self.meeting_id, self.pk])

    @property
    def items(self):
        return self.agenda_items.order_by("display_order", "item_number")


class AgendaItem(MeetingRecord, NotesModel):
    """A single item on a meeting agenda."""

    agenda = models.ForeignKey(
        MeetingAgenda,
        on_delete=models.CASCADE,
        related_name="agenda_items",
        verbose_name=_("Agenda"),
    )
    item_number = models.PositiveIntegerField(_("Item number"), default=1)
    display_order = models.PositiveIntegerField(_("Display order"), default=0)
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    item_type = models.CharField(
        _("Item type"),
        max_length=30,
        choices=AgendaItemType.choices,
        default=AgendaItemType.INFORMATION,
    )
    presenter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="presented_agenda_items",
        verbose_name=_("Presenter"),
    )
    time_allocation_minutes = models.PositiveIntegerField(
        _("Time allocation (minutes)"), default=10
    )
    start_time = models.TimeField(_("Start time"), null=True, blank=True)
    end_time = models.TimeField(_("End time"), null=True, blank=True)
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    decision_required = models.BooleanField(_("Decision required"), default=False)
    discussion_required = models.BooleanField(_("Discussion required"), default=False)
    information_only = models.BooleanField(_("Information only"), default=False)
    related_document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agenda_items",
        verbose_name=_("Related document"),
    )

    class Meta:
        verbose_name = _("Agenda Item")
        verbose_name_plural = _("Agenda Items")
        ordering = ("display_order", "item_number")
        constraints = [
            models.UniqueConstraint(
                fields=["agenda", "item_number"],
                name="uq_meetings_agendaitem_agenda_number",
            ),
            models.UniqueConstraint(
                fields=["agenda", "display_order"],
                name="uq_meetings_agendaitem_agenda_order",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.item_number}. {self.title}"


# ---------------------------------------------------------------------------
# Attendance & Quorum
# ---------------------------------------------------------------------------


class MeetingAttendance(MeetingRecord, NotesModel):
    """A recorded attendance for a meeting participant."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("Meeting"),
    )
    participant = models.ForeignKey(
        MeetingParticipant,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("Participant"),
    )
    attendance_status = models.CharField(
        _("Attendance status"),
        max_length=30,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
        db_index=True,
    )
    attendance_mode = models.CharField(
        _("Attendance mode"),
        max_length=20,
        choices=AttendanceMode.choices,
        default=AttendanceMode.IN_PERSON,
    )
    check_in_at = models.DateTimeField(_("Checked in at"), null=True, blank=True)
    check_out_at = models.DateTimeField(_("Checked out at"), null=True, blank=True)
    signature_reference = models.CharField(
        _("Signature reference"), max_length=100, blank=True
    )
    verification_status = models.CharField(
        _("Verification status"),
        max_length=20,
        choices=AttendanceVerificationStatus.choices,
        default=AttendanceVerificationStatus.UNVERIFIED,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_attendance_records",
        verbose_name=_("Verified by"),
    )
    verified_at = models.DateTimeField(_("Verified at"), null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_attendance",
        verbose_name=_("Recorded by"),
    )
    reason = models.TextField(_("Reason"), blank=True)

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting Attendance")
        verbose_name_plural = _("Meeting Attendance")
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "participant"],
                name="uq_meetings_attendance_meeting_participant",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.participant} -> {self.get_attendance_status_display()}"


class AttendanceCorrectionRecord(MeetingRecord):
    """An immutable record of a correction to an attendance record."""

    attendance = models.ForeignKey(
        MeetingAttendance,
        on_delete=models.CASCADE,
        related_name="corrections",
        verbose_name=_("Attendance"),
    )
    previous_status = models.CharField(
        _("Previous status"), max_length=30, choices=AttendanceStatus.choices
    )
    previous_check_in = models.DateTimeField(
        _("Previous check in"), null=True, blank=True
    )
    previous_check_out = models.DateTimeField(
        _("Previous check out"), null=True, blank=True
    )
    new_status = models.CharField(
        _("New status"), max_length=30, choices=AttendanceStatus.choices
    )
    new_check_in = models.DateTimeField(_("New check in"), null=True, blank=True)
    new_check_out = models.DateTimeField(_("New check out"), null=True, blank=True)
    reason = models.TextField(_("Reason"), blank=True)
    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="attendance_corrections",
        verbose_name=_("Corrected by"),
    )
    corrected_at = models.DateTimeField(_("Corrected at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Attendance Correction")
        verbose_name_plural = _("Attendance Corrections")
        ordering = ("-corrected_at",)

    def __str__(self) -> str:
        return f"Correction {self.previous_status} -> {self.new_status}"


# ---------------------------------------------------------------------------
# Minutes
# ---------------------------------------------------------------------------


class MeetingMinutes(MeetingRecord, NotesModel):
    """A versioned record of meeting minutes."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="minutes_versions",
        verbose_name=_("Meeting"),
    )
    reference = models.CharField(_("Reference"), max_length=80, unique=True, blank=True)
    version = models.PositiveIntegerField(_("Version"), default=1)
    title = models.CharField(_("Title"), max_length=255)
    summary = models.TextField(_("Summary"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=MinutesStatus.choices,
        default=MinutesStatus.DRAFT,
    )
    opening = models.TextField(_("Opening"), blank=True)
    closing = models.TextField(_("Closing"), blank=True)
    quorum_status = models.CharField(_("Quorum status"), max_length=100, blank=True)
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prepared_minutes",
        verbose_name=_("Prepared by"),
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_minutes",
        verbose_name=_("Reviewed by"),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_minutes",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    submitted_at = models.DateTimeField(_("Submitted at"), null=True, blank=True)
    publication_status = models.CharField(
        _("Publication status"),
        max_length=30,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PARTICIPANTS_ONLY,
    )
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    is_current_version = models.BooleanField(_("Is current version"), default=True)
    change_summary = models.TextField(_("Change summary"), blank=True)

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting Minutes")
        verbose_name_plural = _("Meeting Minutes")
        ordering = ("-version",)
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "version"],
                name="uq_meetings_minutes_meeting_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} (v{self.version})"

    def get_absolute_url(self) -> str:
        return reverse("meetings:minutes_detail", args=[self.meeting_id, self.pk])

    @property
    def sections(self):
        return self.sections.all().order_by("display_order")


class MinuteSection(MeetingRecord):
    """A structured section within meeting minutes."""

    minutes = models.ForeignKey(
        MeetingMinutes,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name=_("Minutes"),
    )
    section_type = models.CharField(
        _("Section type"),
        max_length=30,
        choices=MinuteSectionType.choices,
        default=MinuteSectionType.AGENDA_ITEM,
    )
    title = models.CharField(_("Title"), max_length=255)
    content = models.TextField(_("Content"), blank=True)
    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="minute_sections",
        verbose_name=_("Agenda item"),
    )
    display_order = models.PositiveIntegerField(_("Display order"), default=0)

    class Meta:
        verbose_name = _("Minute Section")
        verbose_name_plural = _("Minute Sections")
        ordering = ("display_order",)

    def __str__(self) -> str:
        return f"{self.title} ({self.get_section_type_display()})"


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


class MeetingDecision(MeetingRecord, NotesModel):
    """A formal decision recorded from a meeting."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="decisions",
        verbose_name=_("Meeting"),
    )
    reference = models.CharField(_("Reference"), max_length=80, unique=True, blank=True)
    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decisions",
        verbose_name=_("Agenda item"),
    )
    decision_text = models.TextField(_("Decision text"))
    decision_type = models.CharField(
        _("Decision type"),
        max_length=30,
        choices=DecisionType.choices,
        default=DecisionType.RESOLUTION,
    )
    decision_date = models.DateField(_("Decision date"), null=True, blank=True)
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="proposed_decisions",
        verbose_name=_("Proposed by"),
    )
    seconded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seconded_decisions",
        verbose_name=_("Seconded by"),
    )
    voting_method = models.CharField(
        _("Voting method"),
        max_length=20,
        choices=VotingMethod.choices,
        default=VotingMethod.VOICE,
    )
    quorum_at_vote = models.CharField(
        _("Quorum status at vote"), max_length=100, blank=True
    )
    votes_for = models.PositiveIntegerField(_("Votes for"), default=0)
    votes_against = models.PositiveIntegerField(_("Votes against"), default=0)
    votes_abstain = models.PositiveIntegerField(_("Votes abstain"), default=0)
    outcome = models.CharField(
        _("Outcome"),
        max_length=30,
        choices=DecisionStatus.choices,
        default=DecisionStatus.RECORDED,
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsible_decisions",
        verbose_name=_("Responsible officer"),
    )
    effective_date = models.DateField(_("Effective date"), null=True, blank=True)
    review_date = models.DateField(_("Review date"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=DecisionStatus.choices,
        default=DecisionStatus.RECORDED,
        db_index=True,
    )
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    is_confidential = models.BooleanField(_("Is confidential"), default=False)
    supporting_document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meeting_decisions",
        verbose_name=_("Supporting document"),
    )

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting Decision")
        verbose_name_plural = _("Meeting Decisions")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.reference or 'Decision'} - {self.decision_text[:60]}"


class DecisionVote(MeetingRecord):
    """An individual recorded vote on a meeting decision."""

    decision = models.ForeignKey(
        MeetingDecision,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name=_("Decision"),
    )
    participant = models.ForeignKey(
        MeetingParticipant,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name=_("Participant"),
    )
    vote_type = models.CharField(_("Vote"), max_length=10, choices=VoteType.choices)
    comment = models.TextField(_("Comment"), blank=True)
    voted_at = models.DateTimeField(_("Voted at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Decision Vote")
        verbose_name_plural = _("Decision Votes")
        constraints = [
            models.UniqueConstraint(
                fields=["decision", "participant"],
                name="uq_meetings_decisionvote_decision_participant",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.participant} -> {self.get_vote_type_display()}"


# ---------------------------------------------------------------------------
# Action items
# ---------------------------------------------------------------------------


class MeetingActionItem(MeetingRecord, NotesModel):
    """An action item assigned from a meeting."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="action_items",
        verbose_name=_("Meeting"),
    )
    reference = models.CharField(_("Reference"), max_length=80, unique=True, blank=True)
    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_items",
        verbose_name=_("Agenda item"),
    )
    decision = models.ForeignKey(
        MeetingDecision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_items",
        verbose_name=_("Decision"),
    )
    description = models.TextField(_("Description"))
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_meeting_actions",
        verbose_name=_("Owner"),
    )
    supporting_team = models.JSONField(_("Supporting team"), default=list, blank=True)
    start_date = models.DateField(_("Start date"), null=True, blank=True)
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=ActionPriority.choices,
        default=ActionPriority.MEDIUM,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ActionStatus.choices,
        default=ActionStatus.NOT_STARTED,
        db_index=True,
    )
    progress_percentage = models.PositiveIntegerField(_("Progress (%)"), default=0)
    completion_date = models.DateField(_("Completion date"), null=True, blank=True)
    evidence = models.TextField(_("Evidence"), blank=True)
    verification_status = models.CharField(
        _("Verification status"),
        max_length=20,
        choices=AttendanceVerificationStatus.choices,
        default=AttendanceVerificationStatus.UNVERIFIED,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_meeting_actions",
        verbose_name=_("Verified by"),
    )
    verified_at = models.DateTimeField(_("Verified at"), null=True, blank=True)
    escalation_status = models.CharField(
        _("Escalation status"),
        max_length=20,
        choices=EscalationStatus.choices,
        default=EscalationStatus.NOT_ESCALATED,
    )
    escalated_at = models.DateTimeField(_("Escalated at"), null=True, blank=True)
    escalation_reason = models.TextField(_("Escalation reason"), blank=True)

    objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Meeting Action Item")
        verbose_name_plural = _("Meeting Action Items")
        ordering = ("due_date", "priority")

    def __str__(self) -> str:
        return f"{self.reference or 'Action'} - {self.description[:60]}"

    @property
    def is_overdue(self) -> bool:
        if not self.due_date or self.status in (
            ActionStatus.COMPLETED,
            ActionStatus.VERIFIED,
            ActionStatus.CANCELLED,
        ):
            return False
        return self.due_date < timezone.localdate()


class ActionFollowUpRecord(MeetingRecord):
    """An immutable follow-up event on an action item."""

    action_item = models.ForeignKey(
        MeetingActionItem,
        on_delete=models.CASCADE,
        related_name="follow_ups",
        verbose_name=_("Action item"),
    )
    update_type = models.CharField(
        _("Update type"),
        max_length=20,
        choices=FollowUpType.choices,
        default=FollowUpType.COMMENT,
    )
    comment = models.TextField(_("Comment"), blank=True)
    evidence = models.TextField(_("Evidence"), blank=True)
    previous_status = models.CharField(
        _("Previous status"), max_length=20, choices=ActionStatus.choices, blank=True
    )
    new_status = models.CharField(
        _("New status"), max_length=20, choices=ActionStatus.choices, blank=True
    )
    previous_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_followup_previous_owner",
        verbose_name=_("Previous owner"),
    )
    new_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_followup_new_owner",
        verbose_name=_("New owner"),
    )
    previous_due_date = models.DateField(_("Previous due date"), null=True, blank=True)
    new_due_date = models.DateField(_("New due date"), null=True, blank=True)
    reason = models.TextField(_("Reason"), blank=True)
    acted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="action_follow_ups",
        verbose_name=_("Acted by"),
    )
    acted_at = models.DateTimeField(_("Acted at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Action Follow-Up Record")
        verbose_name_plural = _("Action Follow-Up Records")
        ordering = ("-acted_at",)

    def __str__(self) -> str:
        return f"{self.get_update_type_display()} on {self.action_item.reference}"


class MattersArising(MeetingRecord):
    """A matter arising from previous minutes brought to the current meeting."""

    source_meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="matters_raised",
        verbose_name=_("Source meeting"),
    )
    source_action = models.ForeignKey(
        MeetingActionItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matters_arising",
        verbose_name=_("Source action"),
    )
    source_decision = models.ForeignKey(
        MeetingDecision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matters_arising",
        verbose_name=_("Source decision"),
    )
    current_meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="matters_presented",
        verbose_name=_("Current meeting"),
    )
    update = models.TextField(_("Update"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=MatterStatus.choices,
        default=MatterStatus.OPEN,
        db_index=True,
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsible_matters",
        verbose_name=_("Responsible officer"),
    )
    follow_up_required = models.BooleanField(_("Follow-up required"), default=False)
    new_action = models.ForeignKey(
        MeetingActionItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matter_links",
        verbose_name=_("New action"),
    )
    closure_notes = models.TextField(_("Closure notes"), blank=True)
    closed_at = models.DateTimeField(_("Closed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Matter Arising")
        verbose_name_plural = _("Matters Arising")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Matter from {self.source_meeting.title}"


# ---------------------------------------------------------------------------
# Scheduling history & documents
# ---------------------------------------------------------------------------


class MeetingScheduleHistory(MeetingRecord):
    """An immutable record of a meeting reschedule."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="schedule_history",
        verbose_name=_("Meeting"),
    )
    previous_start = models.DateTimeField(_("Previous start"))
    previous_end = models.DateTimeField(_("Previous end"))
    new_start = models.DateTimeField(_("New start"))
    new_end = models.DateTimeField(_("New end"))
    previous_venue = models.ForeignKey(
        MeetingVenue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Previous venue"),
    )
    new_venue = models.ForeignKey(
        MeetingVenue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("New venue"),
    )
    reason = models.TextField(_("Reason"), blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="meeting_reschedules",
        verbose_name=_("Changed by"),
    )
    changed_at = models.DateTimeField(_("Changed at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Meeting Schedule History")
        verbose_name_plural = _("Meeting Schedule History")
        ordering = ("-changed_at",)

    def __str__(self) -> str:
        return (
            f"Reschedule {self.previous_start:%Y-%m-%d %H:%M} -> "
            f"{self.new_start:%Y-%m-%d %H:%M}"
        )


class MeetingDocument(MeetingRecord):
    """A document linked to a meeting through the central document engine."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Meeting"),
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.PROTECT,
        related_name="meeting_links",
        verbose_name=_("Document"),
    )
    document_type = models.CharField(
        _("Document type"),
        max_length=30,
        choices=MeetingDocumentType.choices,
        default=MeetingDocumentType.REPORT,
    )
    is_public_to_participants = models.BooleanField(
        _("Visible to participants"), default=True
    )
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Meeting Document")
        verbose_name_plural = _("Meeting Documents")
        ordering = ("document_type", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "document"],
                name="uq_meetings_meetingdocument_meeting_document",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.document.title} -> {self.meeting.title}"


# ---------------------------------------------------------------------------
# Immutable activity timeline
# ---------------------------------------------------------------------------


class MeetingActivityRecord(MeetingRecord):
    """An immutable activity entry on a meeting's timeline."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="activity_records",
        verbose_name=_("Meeting"),
    )
    action = models.CharField(_("Action"), max_length=100, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="meeting_activities",
        verbose_name=_("Actor"),
    )
    details = models.CharField(_("Details"), max_length=255, blank=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Meeting Activity Record")
        verbose_name_plural = _("Meeting Activity Records")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.action} on {self.meeting.title}"


class ConfidentialAccessLog(MeetingRecord):
    """An immutable log of access to confidential meeting records."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="confidential_access_logs",
        verbose_name=_("Meeting"),
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="confidential_meeting_access",
        verbose_name=_("Actor"),
    )
    access_type = models.CharField(_("Access type"), max_length=50)
    target_model = models.CharField(_("Target model"), max_length=80, blank=True)
    target_reference = models.CharField(
        _("Target reference"), max_length=80, blank=True
    )
    reason = models.TextField(_("Reason"), blank=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    accessed_at = models.DateTimeField(_("Accessed at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Confidential Access Log")
        verbose_name_plural = _("Confidential Access Logs")
        ordering = ("-accessed_at",)

    def __str__(self) -> str:
        return f"{self.access_type} on {self.meeting.title} by {self.actor}"
