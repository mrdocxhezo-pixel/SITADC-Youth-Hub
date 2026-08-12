"""Permission constants and helpers for the ``meetings`` namespace.

Authorization is enforced on the server.  These helpers centralize the checks
used across views, services, selectors and templates.
"""

from __future__ import annotations

from apps.rbac.authorization import get_active_role_assignments, user_has_permission

# Module permission categories.
_CALENDARS = "calendars"
_EVENTS = "events"
_MEETINGS = "meetings"

# Calendar permissions.
CALENDAR_VIEW = f"{_CALENDARS}.view"
CALENDAR_CREATE = f"{_CALENDARS}.create"
CALENDAR_UPDATE = f"{_CALENDARS}.update"
CALENDAR_DELETE = f"{_CALENDARS}.delete"
CALENDAR_SHARE = f"{_CALENDARS}.share"
CALENDAR_ARCHIVE = f"{_CALENDARS}.archive"
CALENDAR_RESTORE = f"{_CALENDARS}.restore"
CALENDAR_EXPORT = f"{_CALENDARS}.export"
CALENDAR_VIEW_CONFIDENTIAL = f"{_CALENDARS}.view_confidential"
CALENDAR_MANAGE = f"{_CALENDARS}.manage"

# Event permissions.
EVENT_VIEW = f"{_EVENTS}.view"
EVENT_CREATE = f"{_EVENTS}.create"
EVENT_UPDATE = f"{_EVENTS}.update"
EVENT_DELETE = f"{_EVENTS}.delete"
EVENT_SCHEDULE = f"{_EVENTS}.schedule"
EVENT_CONFIRM = f"{_EVENTS}.confirm"
EVENT_COMPLETE = f"{_EVENTS}.complete"
EVENT_CANCEL = f"{_EVENTS}.cancel"
EVENT_ARCHIVE = f"{_EVENTS}.archive"
EVENT_RESTORE = f"{_EVENTS}.restore"
EVENT_EXPORT = f"{_EVENTS}.export"
EVENT_MANAGE_REMINDERS = f"{_EVENTS}.manage_reminders"
EVENT_VIEW_CONFIDENTIAL = f"{_EVENTS}.view_confidential"
EVENT_MANAGE = f"{_EVENTS}.manage"

# Meeting permissions.
MEETING_VIEW = f"{_MEETINGS}.view"
MEETING_CREATE = f"{_MEETINGS}.create"
MEETING_UPDATE = f"{_MEETINGS}.update"
MEETING_DELETE = f"{_MEETINGS}.delete"
MEETING_SCHEDULE = f"{_MEETINGS}.schedule"
MEETING_RESCHEDULE = f"{_MEETINGS}.reschedule"
MEETING_CANCEL = f"{_MEETINGS}.cancel"
MEETING_CONFIRM = f"{_MEETINGS}.confirm"
MEETING_START = f"{_MEETINGS}.start"
MEETING_COMPLETE = f"{_MEETINGS}.complete"
MEETING_ARCHIVE = f"{_MEETINGS}.archive"
MEETING_RESTORE = f"{_MEETINGS}.restore"
MEETING_EXPORT = f"{_MEETINGS}.export"
MEETING_MANAGE_REMINDERS = f"{_MEETINGS}.manage_reminders"
MEETING_MANAGE_AGENDAS = f"{_MEETINGS}.manage_agendas"
MEETING_APPROVE_AGENDAS = f"{_MEETINGS}.approve_agendas"
MEETING_MANAGE_PARTICIPANTS = f"{_MEETINGS}.manage_participants"
MEETING_SEND_INVITATIONS = f"{_MEETINGS}.send_invitations"
MEETING_RECORD_ATTENDANCE = f"{_MEETINGS}.record_attendance"
MEETING_VERIFY_ATTENDANCE = f"{_MEETINGS}.verify_attendance"
MEETING_CHECK_IN = f"{_MEETINGS}.check_in"
MEETING_CHECK_OUT = f"{_MEETINGS}.check_out"
MEETING_MANAGE_QUORUM = f"{_MEETINGS}.manage_quorum"
MEETING_DRAFT_MINUTES = f"{_MEETINGS}.draft_minutes"
MEETING_SUBMIT_MINUTES = f"{_MEETINGS}.submit_minutes"
MEETING_REVIEW_MINUTES = f"{_MEETINGS}.review_minutes"
MEETING_APPROVE_MINUTES = f"{_MEETINGS}.approve_minutes"
MEETING_RECORD_DECISIONS = f"{_MEETINGS}.record_decisions"
MEETING_MANAGE_ACTIONS = f"{_MEETINGS}.manage_actions"
MEETING_VERIFY_ACTIONS = f"{_MEETINGS}.verify_actions"
MEETING_ESCALATE = f"{_MEETINGS}.escalate"
MEETING_MANAGE_TEMPLATES = f"{_MEETINGS}.manage_templates"
MEETING_MANAGE_VENUES = f"{_MEETINGS}.manage_venues"
MEETING_CONFIGURE = f"{_MEETINGS}.configure"
MEETING_VIEW_CONFIDENTIAL = f"{_MEETINGS}.view_confidential"
MEETING_MANAGE = f"{_MEETINGS}.manage"


def _has(user, *codes: str) -> bool:
    return any(user_has_permission(user, code) for code in codes)


def user_can_view_calendars(user) -> bool:
    """Whether the user may browse calendars and events."""
    return _has(user, CALENDAR_VIEW, EVENT_VIEW, MEETING_VIEW, CALENDAR_MANAGE)


def user_can_manage_calendars(user) -> bool:
    """Whether the user may administer calendars."""
    return user_has_permission(user, CALENDAR_MANAGE)


def user_can_view_events(user) -> bool:
    """Whether the user may browse events."""
    return _has(user, EVENT_VIEW, CALENDAR_VIEW, MEETING_VIEW, EVENT_MANAGE)


def user_can_view_meetings(user) -> bool:
    """Whether the user may browse meetings."""
    return _has(user, MEETING_VIEW, CALENDAR_VIEW, EVENT_VIEW, MEETING_MANAGE)


def user_can_view_confidential(user) -> bool:
    """Whether the user may see restricted/confidential meeting records."""
    return _has(
        user,
        MEETING_VIEW_CONFIDENTIAL,
        CALENDAR_VIEW_CONFIDENTIAL,
        EVENT_VIEW_CONFIDENTIAL,
        MEETING_MANAGE,
    )


def user_can_export(user) -> bool:
    """Whether the user may export calendar/meeting data."""
    return _has(
        user,
        MEETING_EXPORT,
        CALENDAR_EXPORT,
        EVENT_EXPORT,
        MEETING_MANAGE,
    )


def user_can_schedule(user) -> bool:
    """Whether the user may schedule or edit meetings and events."""
    return _has(
        user,
        MEETING_SCHEDULE,
        MEETING_CREATE,
        MEETING_UPDATE,
        MEETING_RESCHEDULE,
        EVENT_SCHEDULE,
        EVENT_CREATE,
        EVENT_UPDATE,
        MEETING_MANAGE,
    )


def user_can_manage_attendance(user) -> bool:
    """Whether the user may record or verify attendance."""
    return _has(
        user,
        MEETING_RECORD_ATTENDANCE,
        MEETING_VERIFY_ATTENDANCE,
        MEETING_CHECK_IN,
        MEETING_CHECK_OUT,
        MEETING_MANAGE,
    )


def user_can_manage_minutes(user) -> bool:
    """Whether the user may draft, submit, review or approve minutes."""
    return _has(
        user,
        MEETING_DRAFT_MINUTES,
        MEETING_SUBMIT_MINUTES,
        MEETING_REVIEW_MINUTES,
        MEETING_APPROVE_MINUTES,
        MEETING_MANAGE,
    )


def user_can_manage_actions(user) -> bool:
    """Whether the user may manage or verify action items."""
    return _has(
        user,
        MEETING_MANAGE_ACTIONS,
        MEETING_VERIFY_ACTIONS,
        MEETING_ESCALATE,
        MEETING_MANAGE,
    )


def is_meeting_organizer(user, meeting) -> bool:
    """Whether the user organizes, chairs, secretaries or takes minutes."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return (
        user.pk == meeting.organizer_id
        or user.pk == meeting.chairperson_id
        or user.pk == meeting.secretary_id
        or user.pk == meeting.minute_taker_id
    )


def is_calendar_owner(user, calendar) -> bool:
    """Whether the user owns the calendar."""
    return bool(user and user.is_authenticated and calendar.owner_id == user.pk)


def has_calendar_share(user, calendar, level) -> bool:
    """Whether the user holds at least ``level`` via calendar shares."""
    from django.db.models import Q

    from .constants import CalendarShareLevel

    if not user or not getattr(user, "is_authenticated", False):
        return False
    level_rank = {name: i for i, name in enumerate(CalendarShareLevel.values)}
    min_rank = level_rank.get(level)
    if min_rank is None:
        return False

    scope_ids = [
        assignment.access_scope_id
        for assignment in get_active_role_assignments(user)
        if assignment.access_scope_id
    ]
    share_q = Q(user=user)
    if scope_ids:
        share_q |= Q(access_scope_id__in=scope_ids)

    for share in calendar.shares.filter(share_q):
        if level_rank.get(share.permission_level, -1) >= min_rank:
            return True
    return False
