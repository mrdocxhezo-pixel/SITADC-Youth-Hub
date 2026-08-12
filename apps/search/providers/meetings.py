"""Providers indexing meetings and calendar events."""

from __future__ import annotations

from apps.meetings.models import CalendarEvent, Meeting
from apps.meetings.selectors import visible_events, visible_meetings

from .base import SearchProvider, register


class MeetingProvider(SearchProvider):
    key = "meetings.meeting"
    label = "Meetings"
    model = Meeting
    detail_url_name = "meetings:meeting_detail"
    view_permissions = ("meetings.view", "meetings.manage")
    search_fields = (
        "reference",
        "title",
        "purpose",
    )[:3]
    title_field = "title"
    subtitle_fields = ("reference", "start_at")
    reference_field = "reference"
    status_field = "status"

    def queryset(self, user):
        return visible_meetings(user).select_related("organizer", "venue")


class CalendarEventProvider(SearchProvider):
    key = "meetings.event"
    label = "Calendar Events"
    model = CalendarEvent
    detail_url_name = "meetings:event_detail"
    view_permissions = (
        "meetings.view",
        "meetings.manage",
        "calendars.view",
        "calendars.manage",
    )
    search_fields = (
        "reference",
        "title",
        "description",
        "location_details",
    )[:4]
    title_field = "title"
    subtitle_fields = ("reference", "start_at")
    reference_field = "reference"
    status_field = "status"

    def queryset(self, user):
        return visible_events(user).select_related("calendar", "organizer")


register(MeetingProvider())
register(CalendarEventProvider())
