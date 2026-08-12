"""Provider for meeting records (source type MEETING)."""

from __future__ import annotations

from apps.meetings.models import Meeting
from apps.meetings.permissions import MEETING_MANAGE, MEETING_VIEW
from apps.meetings.selectors import visible_meetings

from ..constants import ExportSourceType
from ..renderers.base import ExportColumn
from .base import BaseProvider, register


class MeetingProvider(BaseProvider):
    """Export the organizational meeting register."""

    key = "meetings.meeting"
    source_type = ExportSourceType.MEETING
    label = "Meetings"
    model = Meeting
    view_permissions = (MEETING_VIEW,)
    manage_permissions = (MEETING_MANAGE,)
    reference_field = "reference"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference", "Reference"),
        ExportColumn("title", "Meeting Title"),
        ExportColumn("meeting_type", "Meeting Type"),
        ExportColumn("mode", "Mode"),
        ExportColumn(
            "venue",
            "Venue",
            accessor=lambda obj: obj.venue.name if obj.venue_id else "",
        ),
        ExportColumn("start_at", "Start"),
        ExportColumn("end_at", "End"),
        ExportColumn(
            "organizer",
            "Organizer",
            accessor=lambda obj: (
                obj.organizer.get_full_name() or obj.organizer.email
                if obj.organizer_id
                else ""
            ),
        ),
        ExportColumn("status", "Status"),
        ExportColumn("quorum_met", "Quorum Met"),
        ExportColumn("confidentiality_level", "Confidentiality"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return visible_meetings(user).select_related("venue", "organizer")


register(MeetingProvider())
