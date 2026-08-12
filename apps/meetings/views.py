"""Views for the Calendar & Meetings module.

Every view is permission checked server side; confidentiality scoping is
applied through the fail-closed selectors.
"""

from __future__ import annotations

import json as _json
import logging

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from .constants import (
    ActionStatus,
    AttendanceMode,
    AttendanceStatus,
    CalendarShareLevel,
    CalendarType,
    EventStatus,
    MeetingStatus,
    MinutesStatus,
)
from .forms import (
    AgendaItemForm,
    CalendarEventForm,
    CalendarForm,
    CalendarShareForm,
    MeetingActionItemForm,
    MeetingAgendaForm,
    MeetingDecisionForm,
    MeetingDocumentForm,
    MeetingForm,
    MeetingMinutesForm,
    MeetingParticipantForm,
    MeetingSearchForm,
    MeetingTemplateForm,
    MeetingVenueForm,
)
from .models import (
    Meeting,
    MeetingActivityRecord,
    MeetingAgenda,
    MeetingMinutes,
    MinuteSection,
)
from .permissions import (
    CALENDAR_CREATE,
    CALENDAR_MANAGE,
    CALENDAR_SHARE,
    CALENDAR_UPDATE,
    EVENT_CREATE,
    EVENT_UPDATE,
    MEETING_APPROVE_AGENDAS,
    MEETING_CANCEL,
    MEETING_CHECK_IN,
    MEETING_CHECK_OUT,
    MEETING_COMPLETE,
    MEETING_CONFIRM,
    MEETING_CREATE,
    MEETING_DRAFT_MINUTES,
    MEETING_MANAGE,
    MEETING_MANAGE_ACTIONS,
    MEETING_MANAGE_AGENDAS,
    MEETING_MANAGE_PARTICIPANTS,
    MEETING_MANAGE_QUORUM,
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
    user_can_export,
    user_can_manage_attendance,
    user_can_manage_minutes,
)
from .selectors import (
    action_queryset,
    calendar_queryset,
    decision_queryset,
    event_queryset,
    meeting_queryset,
    participant_queryset,
    template_queryset,
    upcoming_events,
    upcoming_meetings,
    venue_queryset,
    visible_calendars,
    visible_events,
    visible_meetings,
)
from .services import (
    ActionItemService,
    AgendaService,
    AttendanceService,
    CalendarEventService,
    CalendarService,
    DecisionService,
    MeetingDocumentService,
    MeetingService,
    MinutesService,
    ParticipantService,
    QuorumService,
    TemplateService,
    VenueService,
)

logger = logging.getLogger(__name__)


def _can(user, *permission_codes: str) -> bool:
    from apps.rbac.authorization import user_has_permission

    return bool(
        user_has_permission(user, MEETING_MANAGE)
        or any(user_has_permission(user, code) for code in permission_codes)
    )


def _apply_service_errors(form, exc: ValidationError | PermissionDenied) -> None:
    if isinstance(exc, PermissionDenied):
        form.add_error(None, str(exc))
        return
    if hasattr(exc, "message_dict"):
        for field_name, field_messages in exc.message_dict.items():
            target = field_name if field_name in form.fields else None
            for message in field_messages:
                form.add_error(target, message)
        return
    for message in exc.messages:
        form.add_error(None, message)


def _scoped_calendar(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        calendar_queryset(user, include_archived=include_archived), pk=pk
    )


def _scoped_visible_calendar(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        visible_calendars(user, include_archived=include_archived), pk=pk
    )


def _scoped_event(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        event_queryset(user, include_archived=include_archived), pk=pk
    )


def _scoped_visible_event(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        visible_events(user, include_archived=include_archived), pk=pk
    )


def _scoped_meeting(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        meeting_queryset(user, include_archived=include_archived), pk=pk
    )


def _scoped_visible_meeting(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        visible_meetings(user, include_archived=include_archived), pk=pk
    )


def _scoped_agenda(user, meeting_pk, pk):
    return get_object_or_404(
        MeetingAgenda.objects.filter(
            meeting_id=meeting_pk, meeting__in=visible_meetings(user)
        ),
        pk=pk,
    )


class MeetingPermissionMixin(PermissionRequiredMixin):
    """Allow any listed meetings permission with a module-manager override."""

    request: HttpRequest

    def has_permission(self) -> bool:
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        return _can(self.request.user, *permissions)


# ── Dashboard ────────────────────────────────────────────────────────────


class DashboardView(MeetingPermissionMixin, TemplateView):
    template_name = "meetings/dashboard.html"
    permission_required = "meetings.view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        meetings = visible_meetings(user)
        actions = action_queryset(user)
        now = timezone.now()
        open_statuses = [
            ActionStatus.NOT_STARTED,
            ActionStatus.IN_PROGRESS,
            ActionStatus.ASSIGNED,
        ]
        context.update(
            {
                "total_meetings": meetings.count(),
                "upcoming_count": meetings.filter(
                    start_at__gte=now,
                    status__in=[
                        MeetingStatus.DRAFT,
                        MeetingStatus.SCHEDULED,
                        MeetingStatus.INVITATIONS_SENT,
                        MeetingStatus.CONFIRMED,
                    ],
                ).count(),
                "completed_count": meetings.filter(
                    status=MeetingStatus.COMPLETED
                ).count(),
                "in_progress_count": meetings.filter(
                    status=MeetingStatus.IN_PROGRESS
                ).count(),
                "total_events": visible_events(user).count(),
                "total_calendars": visible_calendars(user).count(),
                "open_actions": actions.filter(status__in=open_statuses).count(),
                "overdue_actions": actions.filter(
                    due_date__lt=now.date(), status__in=open_statuses
                ).count(),
                "minutes_pending_approval": meetings.filter(
                    minutes_status__in=[
                        MinutesStatus.SUBMITTED,
                        MinutesStatus.UNDER_REVIEW,
                    ]
                ).count(),
                "upcoming_meetings": upcoming_meetings(user),
                "upcoming_events": upcoming_events(user),
                "recent_activity": MeetingActivityRecord.objects.filter(
                    meeting__in=meetings
                ).select_related("actor", "meeting")[:12],
                "status_choices": MeetingStatus.choices,
                "can_create_meeting": _can(user, MEETING_CREATE),
                "can_create_calendar": _can(user, CALENDAR_CREATE),
                "can_export": user_can_export(user),
            }
        )
        return context


# ── Calendars ────────────────────────────────────────────────────────────


class CalendarListView(MeetingPermissionMixin, ListView):
    template_name = "meetings/calendar_directory.html"
    context_object_name = "calendars"
    permission_required = "calendars.view"
    paginate_by = 25

    def get_queryset(self):
        queryset = visible_calendars(self.request.user).select_related(
            "owner", "organization_unit", "access_scope"
        )
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )
        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["can_manage"] = _can(user, CALENDAR_MANAGE)
        context["can_create"] = _can(user, CALENDAR_CREATE)
        context["can_export"] = user_can_export(user)
        return context


class CalendarDetailView(MeetingPermissionMixin, DetailView):
    template_name = "meetings/calendar_detail.html"
    context_object_name = "calendar"
    permission_required = "calendars.view"

    def get_queryset(self):
        return visible_calendars(self.request.user).select_related(
            "owner", "organization_unit", "access_scope"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        calendar = self.object
        context["events"] = (
            visible_events(user)
            .filter(calendar=calendar)
            .select_related("venue", "organizer")
            .order_by("-start_at")[:30]
        )
        context["event_count"] = visible_events(user).filter(calendar=calendar).count()
        context["shares"] = calendar.shares.select_related("user", "organization_unit")[
            :20
        ]
        context["can_manage"] = _can(user, CALENDAR_MANAGE)
        context["can_share"] = _can(user, CALENDAR_SHARE)
        context["can_create_event"] = _can(user, EVENT_CREATE)
        context["share_levels"] = CalendarShareLevel.choices
        return context


class CalendarCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/calendar_form.html"
    permission_required = CALENDAR_CREATE
    form_class = CalendarForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        return {"owner": self.request.user.pk, "calendar_type": CalendarType.TEAM}

    def form_valid(self, form):
        data = dict(form.cleaned_data)
        data["owner"] = self.request.user
        try:
            instance = CalendarService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Calendar created."))
        return redirect("meetings:calendar_detail", pk=instance.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class CalendarUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/calendar_form.html"
    permission_required = CALENDAR_UPDATE
    form_class = CalendarForm

    def get_object(self):
        return _scoped_calendar(self.request.user, self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        calendar = self.get_object()
        return {
            "name": calendar.name,
            "calendar_type": calendar.calendar_type,
            "description": calendar.description,
            "visibility": calendar.visibility,
            "organization_unit": calendar.organization_unit_id,
            "access_scope": calendar.access_scope_id,
            "default_timezone": calendar.default_timezone,
            "color": calendar.color,
            "is_default": calendar.is_default,
            "is_confidential": calendar.is_confidential,
            "confidentiality_level": calendar.confidentiality_level,
            "is_active": calendar.is_active,
        }

    def form_valid(self, form):
        calendar = self.get_object()
        data = dict(form.cleaned_data)
        data["owner"] = calendar.owner
        try:
            CalendarService(user=self.request.user).execute(instance=calendar, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Calendar updated."))
        return redirect("meetings:calendar_detail", pk=calendar.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["is_update"] = True
        return context


class CalendarShareCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/calendar_share_form.html"
    permission_required = CALENDAR_SHARE
    form_class = CalendarShareForm

    def get_calendar(self):
        return _scoped_visible_calendar(self.request.user, self.kwargs["calendar_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        calendar = self.get_calendar()
        data = form.cleaned_data
        try:
            CalendarService(user=self.request.user).share(
                calendar=calendar,
                permission_level=data["permission_level"],
                user=data.get("user"),
                organization_unit=data.get("organization_unit"),
                access_scope=data.get("access_scope"),
                expires_at=data.get("expires_at"),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Calendar shared."))
        return redirect("meetings:calendar_detail", pk=calendar.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["calendar"] = self.get_calendar()
        return context


class CalendarShareRevokeView(MeetingPermissionMixin, View):
    permission_required = CALENDAR_SHARE

    def post(self, request, calendar_pk, share_pk):
        calendar = _scoped_visible_calendar(request.user, calendar_pk)
        share = get_object_or_404(calendar.shares, pk=share_pk)
        CalendarService(user=request.user).revoke_share(share=share)
        messages.success(request, _("Calendar share revoked."))
        return redirect("meetings:calendar_detail", pk=calendar.pk)


class CalendarArchiveView(MeetingPermissionMixin, View):
    permission_required = "calendars.archive"

    def post(self, request, pk):
        calendar = _scoped_calendar(request.user, pk)
        CalendarService(user=request.user).archive(instance=calendar)
        messages.success(request, _("Calendar archived."))
        return redirect("meetings:calendar_list")


class CalendarRestoreView(MeetingPermissionMixin, View):
    permission_required = "calendars.restore"

    def post(self, request, pk):
        calendar = _scoped_calendar(request.user, pk, include_archived=True)
        CalendarService(user=request.user).restore(instance=calendar)
        messages.success(request, _("Calendar restored."))
        return redirect("meetings:calendar_detail", pk=calendar.pk)


# ── Events ───────────────────────────────────────────────────────────────


class EventListView(MeetingPermissionMixin, ListView):
    template_name = "meetings/event_directory.html"
    context_object_name = "events"
    permission_required = "events.view"
    paginate_by = 25

    def get_queryset(self):
        queryset = visible_events(self.request.user).select_related(
            "calendar", "venue", "organizer"
        )
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(reference__icontains=q)
                | Q(calendar__name__icontains=q)
            )
        return queryset.order_by("-start_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["status_choices"] = EventStatus.choices
        context["can_create"] = _can(user, EVENT_CREATE)
        context["can_export"] = user_can_export(user)
        return context


class EventDetailView(MeetingPermissionMixin, DetailView):
    template_name = "meetings/event_detail.html"
    context_object_name = "event"
    permission_required = "events.view"

    def get_queryset(self):
        return visible_events(self.request.user).select_related(
            "calendar", "venue", "organizer", "host"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        event = self.object
        context["occurrences"] = event.occurrences.all()[:30]
        context["reminders"] = event.reminders.all()[:20]
        try:
            context["meetings"] = [event.meeting]
        except Meeting.DoesNotExist:
            context["meetings"] = []
        context["can_edit"] = _can(user, EVENT_UPDATE)
        context["can_manage"] = _can(user, "events.manage")
        return context


class EventCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/event_form.html"
    permission_required = EVENT_CREATE
    form_class = CalendarEventForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        calendar_pk = self.kwargs.get("calendar_pk")
        if calendar_pk:
            initial["calendar"] = _scoped_visible_calendar(
                self.request.user, calendar_pk
            ).pk
        initial.setdefault("event_type", "MEETING")
        initial.setdefault("status", EventStatus.DRAFT)
        return initial

    def form_valid(self, form):
        data = dict(form.cleaned_data)
        data["calendar"] = _scoped_visible_calendar(
            self.request.user, data["calendar"].pk
        )
        try:
            instance = CalendarEventService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Event created."))
        return redirect("meetings:event_detail", pk=instance.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class EventUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/event_form.html"
    permission_required = EVENT_UPDATE
    form_class = CalendarEventForm

    def get_object(self):
        return _scoped_visible_event(self.request.user, self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        event = self.get_object()
        return {
            "calendar": event.calendar_id,
            "title": event.title,
            "description": event.description,
            "start_at": event.start_at,
            "end_at": event.end_at,
            "all_day": event.all_day,
            "timezone": event.timezone,
            "venue": event.venue_id,
            "online_meeting_link": event.online_meeting_link,
            "location_details": event.location_details,
            "host": event.host_id,
            "organizer": event.organizer_id,
            "program": event.program_id,
            "project": event.project_id,
            "organization_unit": event.organization_unit_id,
            "access_scope": event.access_scope_id,
            "event_type": event.event_type,
            "priority": event.priority,
            "status": event.status,
            "confidentiality_level": event.confidentiality_level,
            "notes": event.notes,
        }

    def form_valid(self, form):
        event = self.get_object()
        data = dict(form.cleaned_data)
        data["calendar"] = _scoped_visible_calendar(
            self.request.user, data["calendar"].pk
        )
        try:
            CalendarEventService(user=self.request.user).execute(instance=event, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Event updated."))
        return redirect("meetings:event_detail", pk=event.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["is_update"] = True
        return context


class EventTransitionView(MeetingPermissionMixin, View):
    """Apply a simple event status transition via POST."""

    permission_required = "events.update"

    def post(self, request, pk, status):
        event = _scoped_visible_event(request.user, pk)
        try:
            CalendarEventService(user=request.user).transition(
                instance=event, status=status, reason=request.POST.get("reason", "")
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Transition failed: %s") % exc)
            return redirect("meetings:event_detail", pk=event.pk)
        messages.success(request, _("Event status updated."))
        return redirect("meetings:event_detail", pk=event.pk)


class EventArchiveView(MeetingPermissionMixin, View):
    permission_required = "events.archive"

    def post(self, request, pk):
        event = _scoped_event(request.user, pk)
        CalendarEventService(user=request.user).archive(instance=event)
        messages.success(request, _("Event archived."))
        return redirect("meetings:event_list")


class EventRestoreView(MeetingPermissionMixin, View):
    permission_required = "events.restore"

    def post(self, request, pk):
        event = _scoped_event(request.user, pk, include_archived=True)
        CalendarEventService(user=request.user).restore(instance=event)
        messages.success(request, _("Event restored."))
        return redirect("meetings:event_detail", pk=event.pk)


# ── Meetings ─────────────────────────────────────────────────────────────


class MeetingListView(MeetingPermissionMixin, ListView):
    template_name = "meetings/meeting_directory.html"
    context_object_name = "meetings"
    permission_required = "meetings.view"
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        queryset = visible_meetings(user).select_related(
            "venue", "organizer", "program", "project", "organization_unit"
        )
        form = MeetingSearchForm(self.request.GET, user=user)
        if form.is_valid():
            queryset = form.apply_filters(queryset)
        return queryset.order_by("-start_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["search_form"] = MeetingSearchForm(self.request.GET, user=user)
        context["can_create"] = _can(user, MEETING_CREATE)
        context["can_export"] = user_can_export(user)
        context["status_choices"] = MeetingStatus.choices
        return context


class MeetingDetailView(MeetingPermissionMixin, DetailView):
    template_name = "meetings/meeting_detail.html"
    context_object_name = "meeting"
    permission_required = "meetings.view"

    def get_queryset(self):
        return visible_meetings(self.request.user).select_related(
            "venue", "organizer", "chairperson", "secretary", "minute_taker"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        meeting = self.object
        context["participants"] = meeting.participants.select_related("user")[:50]
        context["agendas"] = meeting.agendas.select_related("prepared_by").order_by(
            "-version"
        )[:10]
        context["minutes"] = meeting.minutes_versions.select_related(
            "prepared_by"
        ).order_by("-version")[:10]
        context["attendance"] = meeting.attendance_records.select_related(
            "participant"
        )[:50]
        context["decisions"] = decision_queryset(user).filter(meeting=meeting)[:30]
        context["actions"] = action_queryset(user).filter(meeting=meeting)[:30]
        context["documents"] = meeting.documents.select_related("document")[:30]
        context["schedule_history"] = meeting.schedule_history.all()[:10]
        context["activity"] = meeting.activity_records.select_related("actor")[:20]
        context["can_edit"] = _can(user, MEETING_UPDATE)
        context["can_manage"] = _can(user, MEETING_MANAGE)
        context["can_confirm"] = _can(user, MEETING_CONFIRM)
        context["can_start"] = _can(user, MEETING_START)
        context["can_complete"] = _can(user, MEETING_COMPLETE)
        context["can_cancel"] = _can(user, MEETING_CANCEL)
        context["can_reschedule"] = _can(user, MEETING_RESCHEDULE)
        context["can_manage_participants"] = _can(user, MEETING_MANAGE_PARTICIPANTS)
        context["can_manage_agendas"] = _can(user, MEETING_MANAGE_AGENDAS)
        context["can_manage_actions"] = _can(user, MEETING_MANAGE_ACTIONS)
        context["can_manage_attendance"] = user_can_manage_attendance(user)
        context["can_manage_minutes"] = user_can_manage_minutes(user)
        context["can_record_decisions"] = _can(user, MEETING_RECORD_DECISIONS)
        return context


class MeetingCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/meeting_form.html"
    permission_required = MEETING_CREATE
    form_class = MeetingForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial.setdefault("meeting_type", "TEAM")
        event_pk = self.kwargs.get("event_pk")
        if event_pk:
            event = _scoped_visible_event(self.request.user, event_pk)
            initial["event"] = event.pk
            initial["title"] = event.title
            initial["start_at"] = event.start_at
            initial["end_at"] = event.end_at
        return initial

    def form_valid(self, form):
        data = dict(form.cleaned_data)
        try:
            instance = MeetingService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Meeting scheduled."))
        return redirect("meetings:meeting_detail", pk=instance.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class MeetingUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/meeting_form.html"
    permission_required = MEETING_UPDATE
    form_class = MeetingForm

    def get_object(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        meeting = self.get_object()
        return {
            "title": meeting.title,
            "meeting_type": meeting.meeting_type,
            "template": meeting.template_id,
            "purpose": meeting.purpose,
            "objectives": _json.dumps(meeting.objectives or [], indent=2),
            "start_at": meeting.start_at,
            "end_at": meeting.end_at,
            "timezone": meeting.timezone,
            "mode": meeting.mode,
            "venue": meeting.venue_id,
            "venue_reservation_status": meeting.venue_reservation_status,
            "virtual_provider": meeting.virtual_provider,
            "online_meeting_link": meeting.online_meeting_link,
            "meeting_id": meeting.meeting_id,
            "meeting_passcode": meeting.meeting_passcode,
            "organizer": meeting.organizer_id,
            "chairperson": meeting.chairperson_id,
            "secretary": meeting.secretary_id,
            "minute_taker": meeting.minute_taker_id,
            "facilitator": meeting.facilitator_id,
            "program": meeting.program_id,
            "project": meeting.project_id,
            "organization_unit": meeting.organization_unit_id,
            "access_scope": meeting.access_scope_id,
            "expected_attendees": meeting.expected_attendees,
            "required_attendees": meeting.required_attendees,
            "quorum_type": meeting.quorum_type,
            "quorum_value": meeting.quorum_value,
            "quorum_required_roles": _json.dumps(
                meeting.quorum_required_roles or [], indent=2
            ),
            "confidentiality_level": meeting.confidentiality_level,
            "publication_status": meeting.publication_status,
            "notes": meeting.notes,
        }

    def form_valid(self, form):
        meeting = self.get_object()
        data = dict(form.cleaned_data)
        try:
            MeetingService(user=self.request.user).execute(instance=meeting, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Meeting updated."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["is_update"] = True
        return context


class MeetingTransitionView(MeetingPermissionMixin, View):
    """Apply a simple meeting status transition via POST."""

    permission_required = MEETING_UPDATE

    def post(self, request, pk, status):
        meeting = _scoped_visible_meeting(request.user, pk)
        reason = request.POST.get("reason", "")
        try:
            MeetingService(user=request.user).transition(
                instance=meeting, status=status, reason=reason
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Transition failed: %s") % exc)
            return redirect("meetings:meeting_detail", pk=meeting.pk)
        messages.success(request, _("Meeting status updated."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class MeetingConfirmView(MeetingPermissionMixin, View):
    permission_required = MEETING_CONFIRM

    def post(self, request, pk):
        meeting = _scoped_visible_meeting(request.user, pk)
        try:
            MeetingService(user=request.user).confirm(instance=meeting)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Confirmation failed: %s") % exc)
        else:
            messages.success(request, _("Meeting confirmed."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class MeetingStartView(MeetingPermissionMixin, View):
    permission_required = MEETING_START

    def post(self, request, pk):
        meeting = _scoped_visible_meeting(request.user, pk)
        try:
            MeetingService(user=request.user).start(instance=meeting)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not start meeting: %s") % exc)
        else:
            messages.success(request, _("Meeting started."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class MeetingCompleteView(MeetingPermissionMixin, View):
    permission_required = MEETING_COMPLETE

    def post(self, request, pk):
        meeting = _scoped_visible_meeting(request.user, pk)
        notes = request.POST.get("notes", "")
        try:
            MeetingService(user=request.user).complete(instance=meeting, notes=notes)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not complete meeting: %s") % exc)
        else:
            messages.success(request, _("Meeting completed."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class MeetingRescheduleView(MeetingPermissionMixin, FormView):
    template_name = "meetings/meeting_reschedule.html"
    permission_required = MEETING_RESCHEDULE

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["pk"])

    def get_form_class(self):
        class RescheduleForm(forms.Form):
            new_start = forms.DateTimeField(
                label=_("New start"),
                widget=forms.DateTimeInput(
                    attrs={"class": "form-control", "type": "datetime-local"}
                ),
            )
            new_end = forms.DateTimeField(
                label=_("New end"),
                widget=forms.DateTimeInput(
                    attrs={"class": "form-control", "type": "datetime-local"}
                ),
            )
            reason = forms.CharField(
                label=_("Reason"),
                required=False,
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            )

        return RescheduleForm

    def form_valid(self, form):
        meeting = self.get_meeting()
        data = form.cleaned_data
        try:
            MeetingService(user=self.request.user).reschedule(
                instance=meeting,
                new_start=data["new_start"],
                new_end=data["new_end"],
                reason=data.get("reason", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Meeting rescheduled."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        return context


class MeetingPostponeView(MeetingPermissionMixin, View):
    permission_required = MEETING_RESCHEDULE

    def post(self, request, pk):
        meeting = _scoped_visible_meeting(request.user, pk)
        until = request.POST.get("until") or timezone.now()
        reason = request.POST.get("reason", "")
        try:
            parsed = parse_datetime(str(until)) or timezone.now()
            MeetingService(user=request.user).postpone(
                instance=meeting, until=parsed, reason=reason
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not postpone meeting: %s") % exc)
        else:
            messages.success(request, _("Meeting postponed."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class MeetingCancelView(MeetingPermissionMixin, View):
    permission_required = MEETING_CANCEL

    def post(self, request, pk):
        meeting = _scoped_visible_meeting(request.user, pk)
        reason = request.POST.get("reason", "")
        try:
            MeetingService(user=request.user).cancel(instance=meeting, reason=reason)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not cancel meeting: %s") % exc)
        else:
            messages.success(request, _("Meeting cancelled."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class MeetingArchiveView(MeetingPermissionMixin, View):
    permission_required = "meetings.archive"

    def post(self, request, pk):
        meeting = _scoped_meeting(request.user, pk)
        MeetingService(user=request.user).archive(instance=meeting)
        messages.success(request, _("Meeting archived."))
        return redirect("meetings:meeting_list")


class MeetingRestoreView(MeetingPermissionMixin, View):
    permission_required = "meetings.restore"

    def post(self, request, pk):
        meeting = _scoped_meeting(request.user, pk, include_archived=True)
        MeetingService(user=request.user).restore(instance=meeting)
        messages.success(request, _("Meeting restored."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


# ── Participants & invitations ───────────────────────────────────────────


class ParticipantCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/participant_form.html"
    permission_required = MEETING_MANAGE_PARTICIPANTS
    form_class = MeetingParticipantForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        meeting = self.get_meeting()
        data = form.cleaned_data
        data["name"] = data.pop("name_snapshot", "")
        data["email"] = data.pop("email_snapshot", "")
        data["phone"] = data.pop("phone_snapshot", "")
        try:
            ParticipantService(user=self.request.user).execute(meeting=meeting, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Participant added."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        return context


class ParticipantUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/participant_form.html"
    permission_required = MEETING_MANAGE_PARTICIPANTS
    form_class = MeetingParticipantForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_participant(self):
        return get_object_or_404(
            participant_queryset(self.request.user),
            pk=self.kwargs["pk"],
            meeting=self.get_meeting(),
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        participant = self.get_participant()
        return {
            "participant_type": participant.participant_type,
            "user": participant.user_id,
            "name_snapshot": participant.name_snapshot,
            "email_snapshot": participant.email_snapshot,
            "phone_snapshot": participant.phone_snapshot,
            "organization": participant.organization,
            "role_in_meeting": participant.role_in_meeting,
            "is_required": participant.is_required,
            "special_requirements": participant.special_requirements,
            "accessibility_accommodation": participant.accessibility_accommodation,
        }

    def form_valid(self, form):
        meeting = self.get_meeting()
        data = form.cleaned_data
        data["name"] = data.pop("name_snapshot", "")
        data["email"] = data.pop("email_snapshot", "")
        data["phone"] = data.pop("phone_snapshot", "")
        try:
            ParticipantService(user=self.request.user).execute(
                meeting=meeting, instance=self.get_participant(), **data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Participant updated."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        context["is_update"] = True
        return context


class ParticipantInviteView(MeetingPermissionMixin, View):
    permission_required = MEETING_SEND_INVITATIONS

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        participant = get_object_or_404(meeting.participants, pk=pk)
        try:
            ParticipantService(user=request.user).invite(participant=participant)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Invitation failed: %s") % exc)
        else:
            messages.success(request, _("Invitation sent."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class MeetingSendInvitationsView(MeetingPermissionMixin, View):
    permission_required = MEETING_SEND_INVITATIONS

    def post(self, request, pk):
        meeting = _scoped_visible_meeting(request.user, pk)
        try:
            sent = ParticipantService(user=request.user).send_invitations(
                meeting=meeting
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not send invitations: %s") % exc)
        else:
            messages.success(
                request,
                _("%(count)s invitation(s) sent.") % {"count": len(sent)},
            )
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class ParticipantRSVPView(MeetingPermissionMixin, View):
    permission_required = "meetings.view"

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        participant = get_object_or_404(meeting.participants, pk=pk)
        status = request.POST.get("status", "")
        try:
            ParticipantService(user=request.user).rsvp(
                participant=participant,
                status=status,
                comment=request.POST.get("comment", ""),
                accommodation=request.POST.get("accommodation", ""),
                substitute=request.POST.get("substitute", ""),
                preferred_mode=request.POST.get("preferred_mode", ""),
                decline_reason=request.POST.get("decline_reason", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("RSVP failed: %s") % exc)
        else:
            messages.success(request, _("RSVP recorded."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class ParticipantRemoveView(MeetingPermissionMixin, View):
    permission_required = MEETING_MANAGE_PARTICIPANTS

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        participant = get_object_or_404(meeting.participants, pk=pk)
        ParticipantService(user=request.user).remove(participant=participant)
        messages.success(request, _("Participant removed."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


# ── Agendas ──────────────────────────────────────────────────────────────


class AgendaDetailView(MeetingPermissionMixin, DetailView):
    template_name = "meetings/agenda_detail.html"
    context_object_name = "agenda"
    permission_required = "meetings.view"

    def get_queryset(self):
        return MeetingAgenda.objects.filter(
            meeting__in=visible_meetings(self.request.user)
        ).select_related("meeting", "prepared_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        agenda = self.object
        context["items"] = agenda.items
        context["can_manage"] = _can(user, MEETING_MANAGE_AGENDAS)
        context["can_approve"] = _can(user, MEETING_APPROVE_AGENDAS)
        return context


class AgendaCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/agenda_form.html"
    permission_required = MEETING_MANAGE_AGENDAS
    form_class = MeetingAgendaForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        meeting = self.get_meeting()
        data = form.cleaned_data
        data["meeting"] = meeting
        try:
            instance = AgendaService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Agenda created."))
        return redirect("meetings:agenda_detail", meeting_id=meeting.pk, pk=instance.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        context["is_update"] = False
        return context


class AgendaUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/agenda_form.html"
    permission_required = MEETING_MANAGE_AGENDAS
    form_class = MeetingAgendaForm

    def get_agenda(self):
        return _scoped_agenda(
            self.request.user, self.kwargs["meeting_pk"], self.kwargs["pk"]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        agenda = self.get_agenda()
        return {
            "title": agenda.title,
            "prepared_by": agenda.prepared_by_id,
            "confidentiality_level": agenda.confidentiality_level,
            "change_summary": agenda.change_summary,
            "notes": agenda.notes,
        }

    def form_valid(self, form):
        agenda = self.get_agenda()
        data = form.cleaned_data
        data["meeting"] = agenda.meeting
        try:
            AgendaService(user=self.request.user).execute(instance=agenda, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Agenda updated."))
        return redirect(
            "meetings:agenda_detail", meeting_id=agenda.meeting_id, pk=agenda.pk
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_agenda().meeting
        context["is_update"] = True
        return context


class AgendaApproveView(MeetingPermissionMixin, View):
    permission_required = MEETING_APPROVE_AGENDAS

    def post(self, request, meeting_pk, pk):
        agenda = _scoped_agenda(request.user, meeting_pk, pk)
        try:
            AgendaService(user=request.user).approve(agenda=agenda)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not approve agenda: %s") % exc)
        else:
            messages.success(request, _("Agenda approved."))
        return redirect(
            "meetings:agenda_detail", meeting_id=agenda.meeting_id, pk=agenda.pk
        )


class AgendaPublishView(MeetingPermissionMixin, View):
    permission_required = MEETING_APPROVE_AGENDAS

    def post(self, request, meeting_pk, pk):
        agenda = _scoped_agenda(request.user, meeting_pk, pk)
        try:
            AgendaService(user=request.user).publish(agenda=agenda)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not publish agenda: %s") % exc)
        else:
            messages.success(request, _("Agenda published."))
        return redirect(
            "meetings:agenda_detail", meeting_id=agenda.meeting_id, pk=agenda.pk
        )


class AgendaItemCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/agenda_item_form.html"
    permission_required = MEETING_MANAGE_AGENDAS
    form_class = AgendaItemForm

    def get_agenda(self):
        return _scoped_agenda(
            self.request.user, self.kwargs["meeting_pk"], self.kwargs["pk"]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["agenda"] = self.get_agenda()
        return kwargs

    def get_initial(self):
        agenda = self.get_agenda()
        return {
            "item_number": agenda.agenda_items.count() + 1,
            "display_order": agenda.agenda_items.count() + 1,
            "time_allocation_minutes": 10,
        }

    def form_valid(self, form):
        agenda = self.get_agenda()
        data = form.cleaned_data
        try:
            AgendaService(user=self.request.user).add_item(agenda=agenda, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Agenda item added."))
        return redirect(
            "meetings:agenda_detail", meeting_id=agenda.meeting_id, pk=agenda.pk
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agenda"] = self.get_agenda()
        context["is_update"] = False
        return context


class AgendaItemUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/agenda_item_form.html"
    permission_required = MEETING_MANAGE_AGENDAS
    form_class = AgendaItemForm

    def get_agenda(self):
        return _scoped_agenda(
            self.request.user, self.kwargs["meeting_pk"], self.kwargs["pk"]
        )

    def get_item(self):
        return get_object_or_404(
            self.get_agenda().agenda_items, pk=self.kwargs["item_pk"]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["agenda"] = self.get_agenda()
        return kwargs

    def get_initial(self):
        item = self.get_item()
        return {
            "item_number": item.item_number,
            "display_order": item.display_order,
            "title": item.title,
            "description": item.description,
            "item_type": item.item_type,
            "presenter": item.presenter_id,
            "time_allocation_minutes": item.time_allocation_minutes,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "confidentiality_level": item.confidentiality_level,
            "decision_required": item.decision_required,
            "discussion_required": item.discussion_required,
            "information_only": item.information_only,
            "related_document": item.related_document_id,
            "notes": item.notes,
        }

    def form_valid(self, form):
        agenda = self.get_agenda()
        data = form.cleaned_data
        try:
            AgendaService(user=self.request.user).add_item(
                agenda=agenda, instance=self.get_item(), **data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Agenda item updated."))
        return redirect(
            "meetings:agenda_detail", meeting_id=agenda.meeting_id, pk=agenda.pk
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agenda"] = self.get_agenda()
        context["is_update"] = True
        return context


class AgendaItemDeleteView(MeetingPermissionMixin, View):
    permission_required = MEETING_MANAGE_AGENDAS

    def post(self, request, meeting_pk, pk, item_pk):
        agenda = _scoped_agenda(request.user, meeting_pk, pk)
        item = get_object_or_404(agenda.agenda_items, pk=item_pk)
        AgendaService(user=request.user).delete_item(item=item)
        messages.success(request, _("Agenda item deleted."))
        return redirect(
            "meetings:agenda_detail", meeting_id=agenda.meeting_id, pk=agenda.pk
        )


# ── Attendance ───────────────────────────────────────────────────────────


class AttendanceRecordView(MeetingPermissionMixin, FormView):
    template_name = "meetings/attendance_record.html"
    permission_required = MEETING_RECORD_ATTENDANCE

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_participant(self):
        return get_object_or_404(
            self.get_meeting().participants, pk=self.kwargs["participant_pk"]
        )

    def get_form_class(self):
        class AttendanceForm(forms.Form):
            attendance_status = forms.ChoiceField(
                label=_("Status"),
                choices=AttendanceStatus.choices,
                initial=AttendanceStatus.PRESENT,
            )
            attendance_mode = forms.ChoiceField(
                label=_("Mode"),
                choices=AttendanceMode.choices,
                initial=AttendanceMode.IN_PERSON,
            )
            notes = forms.CharField(
                label=_("Notes"),
                required=False,
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            )

        return AttendanceForm

    def form_valid(self, form):
        meeting = self.get_meeting()
        participant = self.get_participant()
        data = form.cleaned_data
        try:
            AttendanceService(user=self.request.user).execute(
                meeting=meeting, participant=participant, **data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Attendance recorded."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_meeting()
        context["meeting"] = meeting
        context["participant"] = self.get_participant()
        context["records"] = meeting.attendance_records.select_related("participant")[
            :50
        ]
        return context


class AttendanceCheckInView(MeetingPermissionMixin, View):
    permission_required = MEETING_CHECK_IN

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        participant = get_object_or_404(meeting.participants, pk=pk)
        mode = request.POST.get("mode", AttendanceMode.IN_PERSON)
        try:
            AttendanceService(user=request.user).check_in(
                participant=participant, attendance_mode=mode
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Check-in failed: %s") % exc)
        else:
            messages.success(request, _("%s checked in.") % participant.name_snapshot)
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class AttendanceCheckOutView(MeetingPermissionMixin, View):
    permission_required = MEETING_CHECK_OUT

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        participant = get_object_or_404(meeting.participants, pk=pk)
        try:
            AttendanceService(user=request.user).check_out(participant=participant)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Check-out failed: %s") % exc)
        else:
            messages.success(request, _("%s checked out.") % participant.name_snapshot)
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class AttendanceVerifyView(MeetingPermissionMixin, View):
    permission_required = MEETING_VERIFY_ATTENDANCE

    def post(self, request, meeting_pk, attendance_pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        record = get_object_or_404(meeting.attendance_records, pk=attendance_pk)
        accept = request.POST.get("accept") == "1"
        try:
            AttendanceService(user=request.user).verify(
                attendance=record, accept=accept
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Verification failed: %s") % exc)
        else:
            messages.success(request, _("Attendance verification updated."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class QuorumEvaluateView(MeetingPermissionMixin, View):
    permission_required = MEETING_MANAGE_QUORUM

    def post(self, request, pk):
        meeting = _scoped_visible_meeting(request.user, pk)
        try:
            QuorumService(user=request.user).evaluate(meeting=meeting)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Quorum evaluation failed: %s") % exc)
        else:
            messages.success(request, _("Quorum evaluated."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


# ── Minutes ──────────────────────────────────────────────────────────────


class MinutesDetailView(MeetingPermissionMixin, DetailView):
    template_name = "meetings/minutes_detail.html"
    context_object_name = "minutes"
    permission_required = "meetings.view"

    def get_queryset(self):
        return MeetingMinutes.objects.filter(
            meeting__in=visible_meetings(self.request.user)
        ).select_related("meeting", "prepared_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        minutes = self.object
        context["sections"] = minutes.sections.all().order_by("display_order")
        context["can_manage"] = user_can_manage_minutes(user)
        return context


class MinutesCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/minutes_form.html"
    permission_required = MEETING_DRAFT_MINUTES
    form_class = MeetingMinutesForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        meeting = self.get_meeting()
        data = form.cleaned_data
        data["meeting"] = meeting
        try:
            instance = MinutesService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Minutes drafted."))
        return redirect(
            "meetings:minutes_detail", meeting_id=meeting.pk, pk=instance.pk
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        context["is_update"] = False
        return context


class MinutesUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/minutes_form.html"
    permission_required = MEETING_DRAFT_MINUTES
    form_class = MeetingMinutesForm

    def get_minutes(self):
        return get_object_or_404(
            MeetingMinutes.objects.filter(
                meeting__in=visible_meetings(self.request.user)
            ),
            meeting_id=self.kwargs["meeting_pk"],
            pk=self.kwargs["pk"],
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        minutes = self.get_minutes()
        return {
            "title": minutes.title,
            "summary": minutes.summary,
            "opening": minutes.opening,
            "closing": minutes.closing,
            "quorum_status": minutes.quorum_status,
            "prepared_by": minutes.prepared_by_id,
            "confidentiality_level": minutes.confidentiality_level,
            "publication_status": minutes.publication_status,
            "change_summary": minutes.change_summary,
            "notes": minutes.notes,
        }

    def form_valid(self, form):
        minutes = self.get_minutes()
        data = form.cleaned_data
        data["meeting"] = minutes.meeting
        try:
            MinutesService(user=self.request.user).execute(instance=minutes, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Minutes updated."))
        return redirect(
            "meetings:minutes_detail", meeting_id=minutes.meeting_id, pk=minutes.pk
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_minutes().meeting
        context["is_update"] = True
        return context


class MinutesSubmitView(MeetingPermissionMixin, View):
    permission_required = MEETING_SUBMIT_MINUTES

    def post(self, request, meeting_pk, pk):
        minutes = get_object_or_404(
            MeetingMinutes.objects.filter(
                meeting_id=meeting_pk, meeting__in=visible_meetings(request.user)
            ),
            pk=pk,
        )
        try:
            MinutesService(user=request.user).submit(minutes=minutes)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not submit minutes: %s") % exc)
        else:
            messages.success(request, _("Minutes submitted for review."))
        return redirect(
            "meetings:minutes_detail", meeting_id=minutes.meeting_id, pk=minutes.pk
        )


class MinutesReviewView(MeetingPermissionMixin, View):
    permission_required = MEETING_REVIEW_MINUTES

    def post(self, request, meeting_pk, pk):
        minutes = get_object_or_404(
            MeetingMinutes.objects.filter(
                meeting_id=meeting_pk, meeting__in=visible_meetings(request.user)
            ),
            pk=pk,
        )
        try:
            MinutesService(user=request.user).review(minutes=minutes)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not start review: %s") % exc)
        else:
            messages.success(request, _("Minutes review started."))
        return redirect(
            "meetings:minutes_detail", meeting_id=minutes.meeting_id, pk=minutes.pk
        )


class MinutesApproveView(MeetingPermissionMixin, View):
    permission_required = "meetings.approve_minutes"

    def post(self, request, meeting_pk, pk):
        minutes = get_object_or_404(
            MeetingMinutes.objects.filter(
                meeting_id=meeting_pk, meeting__in=visible_meetings(request.user)
            ),
            pk=pk,
        )
        try:
            MinutesService(user=request.user).approve(minutes=minutes)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not approve minutes: %s") % exc)
        else:
            messages.success(request, _("Minutes approved."))
        return redirect(
            "meetings:minutes_detail", meeting_id=minutes.meeting_id, pk=minutes.pk
        )


class MinutesReturnView(MeetingPermissionMixin, View):
    permission_required = MEETING_REVIEW_MINUTES

    def post(self, request, meeting_pk, pk):
        minutes = get_object_or_404(
            MeetingMinutes.objects.filter(
                meeting_id=meeting_pk, meeting__in=visible_meetings(request.user)
            ),
            pk=pk,
        )
        reason = request.POST.get("reason", "")
        try:
            MinutesService(user=request.user).return_for_correction(
                minutes=minutes, reason=reason
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not return minutes: %s") % exc)
        else:
            messages.success(request, _("Minutes returned for correction."))
        return redirect(
            "meetings:minutes_detail", meeting_id=minutes.meeting_id, pk=minutes.pk
        )


class MinuteSectionCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/minute_section_form.html"
    permission_required = MEETING_DRAFT_MINUTES

    def get_minutes(self):
        return get_object_or_404(
            MeetingMinutes.objects.filter(
                meeting__in=visible_meetings(self.request.user)
            ),
            meeting_id=self.kwargs["meeting_pk"],
            pk=self.kwargs["pk"],
        )

    def get_form_class(self):
        class SectionForm(forms.Form):
            section_type = forms.ChoiceField(
                label=_("Section type"),
                choices=MinuteSection._meta.get_field("section_type").choices,
            )
            title = forms.CharField(
                label=_("Title"),
                widget=forms.TextInput(attrs={"class": "form-control"}),
            )
            content = forms.CharField(
                label=_("Content"),
                required=False,
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            )

        return SectionForm

    def form_valid(self, form):
        minutes = self.get_minutes()
        data = form.cleaned_data
        try:
            MinutesService(user=self.request.user).add_section(minutes=minutes, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Minutes section added."))
        return redirect(
            "meetings:minutes_detail", meeting_id=minutes.meeting_id, pk=minutes.pk
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["minutes"] = self.get_minutes()
        return context


# ── Decisions ────────────────────────────────────────────────────────────


class DecisionCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/decision_form.html"
    permission_required = MEETING_RECORD_DECISIONS
    form_class = MeetingDecisionForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        meeting = self.get_meeting()
        data = form.cleaned_data
        data["meeting"] = meeting
        try:
            DecisionService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Decision recorded."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        return context


class DecisionUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/decision_form.html"
    permission_required = MEETING_RECORD_DECISIONS
    form_class = MeetingDecisionForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_decision(self):
        return get_object_or_404(
            decision_queryset(self.request.user),
            meeting=self.get_meeting(),
            pk=self.kwargs["pk"],
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        decision = self.get_decision()
        return {
            "meeting": decision.meeting_id,
            "decision_text": decision.decision_text,
            "decision_type": decision.decision_type,
            "agenda_item": decision.agenda_item_id,
            "proposed_by": decision.proposed_by_id,
            "seconded_by": decision.seconded_by_id,
            "voting_method": decision.voting_method,
            "responsible_officer": decision.responsible_officer_id,
            "effective_date": decision.effective_date,
            "review_date": decision.review_date,
            "confidentiality_level": decision.confidentiality_level,
            "notes": decision.notes,
        }

    def form_valid(self, form):
        decision = self.get_decision()
        data = form.cleaned_data
        data["meeting"] = decision.meeting
        try:
            DecisionService(user=self.request.user).execute(instance=decision, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Decision updated."))
        return redirect("meetings:meeting_detail", pk=decision.meeting_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        context["is_update"] = True
        return context


class DecisionApproveView(MeetingPermissionMixin, View):
    permission_required = MEETING_RECORD_DECISIONS

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        decision = get_object_or_404(meeting.decisions, pk=pk)
        try:
            DecisionService(user=request.user).approve(decision=decision)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not approve decision: %s") % exc)
        else:
            messages.success(request, _("Decision approved."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class DecisionImplementView(MeetingPermissionMixin, View):
    permission_required = MEETING_MANAGE_ACTIONS

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        decision = get_object_or_404(meeting.decisions, pk=pk)
        try:
            DecisionService(user=request.user).implement(decision=decision)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not mark decision implemented: %s") % exc)
        else:
            messages.success(request, _("Decision marked implemented."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


# ── Action items ─────────────────────────────────────────────────────────


class ActionItemCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/action_item_form.html"
    permission_required = MEETING_MANAGE_ACTIONS
    form_class = MeetingActionItemForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        meeting = self.get_meeting()
        data = form.cleaned_data
        data["meeting"] = meeting
        try:
            ActionItemService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Action item created."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        return context


class ActionItemUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/action_item_form.html"
    permission_required = MEETING_MANAGE_ACTIONS
    form_class = MeetingActionItemForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_action(self):
        return get_object_or_404(
            action_queryset(self.request.user),
            meeting=self.get_meeting(),
            pk=self.kwargs["pk"],
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        action = self.get_action()
        return {
            "meeting": action.meeting_id,
            "description": action.description,
            "owner": action.owner_id,
            "agenda_item": action.agenda_item_id,
            "decision": action.decision_id,
            "start_date": action.start_date,
            "due_date": action.due_date,
            "priority": action.priority,
            "supporting_team": ", ".join(action.supporting_team or []),
            "evidence": action.evidence,
        }

    def form_valid(self, form):
        action = self.get_action()
        data = form.cleaned_data
        data["meeting"] = action.meeting
        try:
            ActionItemService(user=self.request.user).execute(instance=action, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Action item updated."))
        return redirect("meetings:meeting_detail", pk=action.meeting_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        context["is_update"] = True
        return context


class ActionItemUpdateProgressView(MeetingPermissionMixin, FormView):
    template_name = "meetings/action_progress.html"
    permission_required = MEETING_MANAGE_ACTIONS

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_action(self):
        return get_object_or_404(
            action_queryset(self.request.user),
            meeting=self.get_meeting(),
            pk=self.kwargs["pk"],
        )

    def get_form_class(self):
        class ProgressForm(forms.Form):
            progress = forms.IntegerField(
                label=_("Progress (%)"), min_value=0, max_value=100, required=False
            )
            status = forms.ChoiceField(
                label=_("Status"),
                required=False,
                choices=ActionStatus.choices,
                widget=forms.Select(attrs={"class": "form-select"}),
            )
            comment = forms.CharField(
                label=_("Comment"),
                required=False,
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            )
            evidence = forms.CharField(
                label=_("Evidence"),
                required=False,
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            )

        return ProgressForm

    def get_initial(self):
        action = self.get_action()
        return {
            "progress": action.progress_percentage,
            "status": action.status,
            "evidence": action.evidence,
        }

    def form_valid(self, form):
        action = self.get_action()
        data = form.cleaned_data
        try:
            ActionItemService(user=self.request.user).update_progress(
                action=action,
                progress=data.get("progress"),
                status=data.get("status") or None,
                comment=data.get("comment", ""),
                evidence=data.get("evidence", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Action progress updated."))
        return redirect("meetings:meeting_detail", pk=action.meeting_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        context["action"] = self.get_action()
        return context


class ActionItemCompleteView(MeetingPermissionMixin, View):
    permission_required = MEETING_MANAGE_ACTIONS

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        action = get_object_or_404(meeting.action_items, pk=pk)
        evidence = request.POST.get("evidence", "")
        try:
            ActionItemService(user=request.user).complete(
                action=action, evidence=evidence
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not complete action: %s") % exc)
        else:
            messages.success(request, _("Action item completed."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class ActionItemVerifyView(MeetingPermissionMixin, View):
    permission_required = MEETING_VERIFY_ACTIONS

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        action = get_object_or_404(meeting.action_items, pk=pk)
        accept = request.POST.get("accept") == "1"
        comment = request.POST.get("comment", "")
        try:
            ActionItemService(user=request.user).verify(
                action=action, accept=accept, comment=comment
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Verification failed: %s") % exc)
        else:
            messages.success(request, _("Action verification updated."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


class ActionItemEscalateView(MeetingPermissionMixin, View):
    permission_required = "meetings.escalate"

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        action = get_object_or_404(meeting.action_items, pk=pk)
        reason = request.POST.get("reason", "")
        try:
            ActionItemService(user=request.user).escalate(action=action, reason=reason)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _("Could not escalate action: %s") % exc)
        else:
            messages.success(request, _("Action item escalated."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


# ── Documents ────────────────────────────────────────────────────────────


class MeetingDocumentLinkView(MeetingPermissionMixin, FormView):
    template_name = "meetings/document_link_form.html"
    permission_required = MEETING_MANAGE_AGENDAS
    form_class = MeetingDocumentForm

    def get_meeting(self):
        return _scoped_visible_meeting(self.request.user, self.kwargs["meeting_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        meeting = self.get_meeting()
        data = form.cleaned_data
        try:
            MeetingDocumentService(user=self.request.user).link(
                meeting=meeting,
                document=data["document"],
                document_type=data["document_type"],
                is_public_to_participants=data["is_public_to_participants"],
                notes=data.get("notes", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Document linked to meeting."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting"] = self.get_meeting()
        return context


class MeetingDocumentUnlinkView(MeetingPermissionMixin, View):
    permission_required = MEETING_MANAGE_AGENDAS

    def post(self, request, meeting_pk, pk):
        meeting = _scoped_visible_meeting(request.user, meeting_pk)
        link = get_object_or_404(meeting.documents, pk=pk)
        MeetingDocumentService(user=request.user).unlink(link=link)
        messages.success(request, _("Document unlinked."))
        return redirect("meetings:meeting_detail", pk=meeting.pk)


# ── Templates & venues ───────────────────────────────────────────────────


class TemplateListView(MeetingPermissionMixin, ListView):
    template_name = "meetings/template_directory.html"
    context_object_name = "templates"
    permission_required = MEETING_MANAGE_TEMPLATES
    paginate_by = 25

    def get_queryset(self):
        return template_queryset(self.request.user)


class TemplateCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/template_form.html"
    permission_required = MEETING_MANAGE_TEMPLATES
    form_class = MeetingTemplateForm

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            TemplateService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Meeting template created."))
        return redirect("meetings:template_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class TemplateUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/template_form.html"
    permission_required = MEETING_MANAGE_TEMPLATES
    form_class = MeetingTemplateForm

    def get_template(self):
        return get_object_or_404(
            template_queryset(self.request.user), pk=self.kwargs["pk"]
        )

    def get_initial(self):
        template = self.get_template()
        return {
            "name": template.name,
            "code": template.code,
            "meeting_type": template.meeting_type,
            "description": template.description,
            "default_title": template.default_title,
            "default_purpose": template.default_purpose,
            "default_objectives": _json.dumps(
                template.default_objectives or [], indent=2
            ),
            "standard_duration_minutes": template.standard_duration_minutes,
            "default_confidentiality": template.default_confidentiality,
            "default_quorum_type": template.default_quorum_type,
            "default_quorum_value": template.default_quorum_value,
            "quorum_required_roles": _json.dumps(
                template.quorum_required_roles or [], indent=2
            ),
            "default_participant_roles": _json.dumps(
                template.default_participant_roles or [], indent=2
            ),
            "agenda_template": _json.dumps(template.agenda_template or [], indent=2),
            "minutes_template": _json.dumps(template.minutes_template or [], indent=2),
            "decision_requirements": _json.dumps(
                template.decision_requirements or {}, indent=2
            ),
            "action_requirements": _json.dumps(
                template.action_requirements or {}, indent=2
            ),
            "recurrence_defaults": _json.dumps(
                template.recurrence_defaults or {}, indent=2
            ),
            "approval_required": template.approval_required,
            "default_reminders": _json.dumps(
                template.default_reminders or [], indent=2
            ),
            "is_active": template.is_active,
        }

    def form_valid(self, form):
        template = self.get_template()
        data = form.cleaned_data
        try:
            TemplateService(user=self.request.user).execute(instance=template, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Meeting template updated."))
        return redirect("meetings:template_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context


class VenueListView(MeetingPermissionMixin, ListView):
    template_name = "meetings/venue_directory.html"
    context_object_name = "venues"
    permission_required = MEETING_MANAGE_VENUES
    paginate_by = 25

    def get_queryset(self):
        return venue_queryset(self.request.user).order_by("name")


class VenueCreateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/venue_form.html"
    permission_required = MEETING_MANAGE_VENUES
    form_class = MeetingVenueForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            VenueService(user=self.request.user).execute(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Meeting venue created."))
        return redirect("meetings:venue_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class VenueUpdateView(MeetingPermissionMixin, FormView):
    template_name = "meetings/venue_form.html"
    permission_required = MEETING_MANAGE_VENUES
    form_class = MeetingVenueForm

    def get_venue(self):
        return get_object_or_404(
            venue_queryset(self.request.user), pk=self.kwargs["pk"]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        venue = self.get_venue()
        return {
            "name": venue.name,
            "venue_type": venue.venue_type,
            "description": venue.description,
            "address": venue.address,
            "location_details": venue.location_details,
            "capacity": venue.capacity,
            "accessibility_features": ", ".join(venue.accessibility_features or []),
            "equipment": ", ".join(venue.equipment or []),
            "contact_person": venue.contact_person,
            "contact_phone": venue.contact_phone,
            "contact_email": venue.contact_email,
            "organization_unit": venue.organization_unit_id,
            "access_scope": venue.access_scope_id,
            "is_active": venue.is_active,
            "notes": venue.notes,
        }

    def form_valid(self, form):
        venue = self.get_venue()
        data = form.cleaned_data
        try:
            VenueService(user=self.request.user).execute(instance=venue, **data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Meeting venue updated."))
        return redirect("meetings:venue_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context


class VenueArchiveView(MeetingPermissionMixin, View):
    permission_required = MEETING_MANAGE_VENUES

    def post(self, request, pk):
        venue = get_object_or_404(venue_queryset(self.request.user), pk=pk)
        VenueService(user=request.user).archive(instance=venue)
        messages.success(request, _("Meeting venue archived."))
        return redirect("meetings:venue_list")


# ── Export ───────────────────────────────────────────────────────────────


class MeetingExportView(MeetingPermissionMixin, View):
    permission_required = "meetings.export"

    def get(self, request, fmt: str = "csv", pk: str | None = None):
        from .exports import meetings_export_response

        meeting = None
        if pk:
            meeting = _scoped_visible_meeting(request.user, pk)
        return meetings_export_response(request.user, meeting=meeting, fmt=fmt)
