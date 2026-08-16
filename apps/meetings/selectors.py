"""Fail-closed, permission-aware selectors for Calendar & Meetings data.

Selectors are the only way views and exports read calendar/meeting data.  They
always enforce authentication, module view permissions and confidentiality
scoping so restricted records are never leaked.
"""

from __future__ import annotations

from django.db.models import QuerySet
from django.utils import timezone

from apps.rbac.authorization import get_active_role_assignments, user_has_permission

from .constants import (
    NON_SENSITIVE_LEVELS,
    ActionStatus,
    CalendarVisibility,
    EventStatus,
    MeetingStatus,
)
from .models import (
    AgendaItem,
    Calendar,
    CalendarEvent,
    Meeting,
    MeetingActionItem,
    MeetingDecision,
    MeetingMinutes,
    MeetingParticipant,
    MeetingTemplate,
    MeetingVenue,
)
from .permissions import (
    CALENDAR_MANAGE,
    CALENDAR_VIEW,
    MEETING_MANAGE,
    MEETING_VIEW,
    user_can_view_confidential,
)

_NON_SENSITIVE_LEVELS = tuple(NON_SENSITIVE_LEVELS)


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def _can_view_meetings(user) -> bool:
    return bool(
        user.is_superuser
        or user_has_permission(user, MEETING_VIEW)
        or user_has_permission(user, MEETING_MANAGE)
    )


def _can_view_calendars(user) -> bool:
    return bool(
        user.is_superuser
        or user_has_permission(user, CALENDAR_VIEW)
        or user_has_permission(user, CALENDAR_MANAGE)
    )


def _scope_ids(user) -> list:
    """Access scope ids available to the user via active role assignments."""
    if not _authenticated(user):
        return []
    return [
        assignment.access_scope_id
        for assignment in get_active_role_assignments(user)
        if assignment.access_scope_id
    ]


def calendar_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Calendars the actor may know exist."""
    manager = Calendar.all_objects if include_archived else Calendar.objects
    queryset = manager.all()
    if not include_archived:
        queryset = queryset.filter(is_deleted=False)
    if not _authenticated(user) or not _can_view_calendars(user):
        return queryset.none()
    return queryset


def visible_calendars(user, *, include_archived: bool = False) -> QuerySet:
    """Calendars scoped by confidentiality and visibility for the actor."""
    queryset = calendar_queryset(user, include_archived=include_archived)
    if not _authenticated(user):
        return queryset
    if not user_can_view_confidential(user):
        queryset = queryset.filter(confidentiality_level__in=_NON_SENSITIVE_LEVELS)

    # CALENDAR_MANAGE and superusers bypass visibility scoping
    if user.is_superuser or user_has_permission(user, CALENDAR_MANAGE):
        return queryset

    scope_ids = _scope_ids(user)
    queryset = queryset.filter(Q_calendar_visible_to(user, scope_ids))
    return queryset


def owned_or_shared_calendars(user, *, include_archived: bool = False) -> QuerySet:
    """Calendars the actor owns or has an explicit share on."""
    queryset = visible_calendars(user, include_archived=include_archived)
    if not _authenticated(user):
        return queryset.none()
    from django.db.models import Q

    scope_ids = _scope_ids(user)
    share_q = Q(shares__user=user)
    if scope_ids:
        share_q |= Q(shares__access_scope_id__in=scope_ids)
    return queryset.filter(Q(owner=user) | share_q).distinct()


def event_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Events the actor may know exist."""
    manager = CalendarEvent.all_objects if include_archived else CalendarEvent.objects
    queryset = manager.all()
    if not include_archived:
        queryset = queryset.filter(is_deleted=False)
    if not _authenticated(user):
        return queryset.none()
    if not (user.is_superuser or _can_view_meetings(user) or _can_view_calendars(user)):
        return queryset.none()
    return queryset


def visible_events(user, *, include_archived: bool = False) -> QuerySet:
    """Events scoped by calendar visibility and confidentiality."""
    queryset = event_queryset(user, include_archived=include_archived)
    if not _authenticated(user):
        return queryset
    scope_ids = _scope_ids(user)
    queryset = queryset.filter(
        Q_calendar_visible_to(user, scope_ids, prefix="calendar")
    )
    if not user_can_view_confidential(user):
        queryset = queryset.filter(confidentiality_level__in=_NON_SENSITIVE_LEVELS)
    queryset = queryset.exclude(status=EventStatus.CANCELLED)
    return queryset


def meeting_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Meetings the actor may know exist."""
    manager = Meeting.all_objects if include_archived else Meeting.objects
    queryset = manager.all()
    if not include_archived:
        queryset = queryset.filter(is_deleted=False)
    if not _authenticated(user) or not _can_view_meetings(user):
        return queryset.none()
    return queryset


def visible_meetings(user, *, include_archived: bool = False) -> QuerySet:
    """Meetings scoped by confidentiality for the actor."""
    queryset = meeting_queryset(user, include_archived=include_archived)
    if not _authenticated(user):
        return queryset
    if not user_can_view_confidential(user):
        queryset = queryset.filter(confidentiality_level__in=_NON_SENSITIVE_LEVELS)
    queryset = queryset.exclude(status=MeetingStatus.COMPLETED)
    return queryset


def participant_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Participants linked to meetings the actor may view."""
    meetings = visible_meetings(user, include_archived=include_archived)
    return MeetingParticipant.objects.filter(meeting__in=meetings)


def minutes_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Minutes linked to meetings the actor may view."""
    meetings = visible_meetings(user, include_archived=include_archived)
    return MeetingMinutes.objects.filter(meeting__in=meetings)


def decision_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Decisions linked to meetings the actor may view."""
    meetings = visible_meetings(user, include_archived=include_archived)
    return MeetingDecision.objects.filter(meeting__in=meetings)


def action_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Action items linked to meetings the actor may view."""
    meetings = visible_meetings(user, include_archived=include_archived)
    return MeetingActionItem.objects.filter(meeting__in=meetings)


def venue_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Venues the actor may browse."""
    manager = MeetingVenue.all_objects if include_archived else MeetingVenue.objects
    queryset = manager.all()
    if not include_archived:
        queryset = queryset.filter(is_deleted=False)
    if not _authenticated(user) or not _can_view_meetings(user):
        return queryset.none()
    return queryset


def upcoming_meetings(user, *, limit: int = 10) -> QuerySet:
    """Upcoming non-terminal meetings visible to the actor."""
    return (
        visible_meetings(user)
        .filter(
            start_at__gte=timezone.now(),
            status__in=[
                MeetingStatus.DRAFT,
                MeetingStatus.SCHEDULED,
                MeetingStatus.INVITATIONS_SENT,
                MeetingStatus.CONFIRMED,
            ],
        )
        .select_related("venue", "organizer", "template")
        .order_by("start_at")[:limit]
    )


def upcoming_events(user, *, limit: int = 10) -> QuerySet:
    """Upcoming non-terminal events visible to the actor."""
    return (
        visible_events(user)
        .filter(
            start_at__gte=timezone.now(),
            status__in=[
                EventStatus.DRAFT,
                EventStatus.SCHEDULED,
                EventStatus.CONFIRMED,
            ],
        )
        .select_related("calendar", "venue")
        .order_by("start_at")[:limit]
    )


def overdue_actions(user, *, limit: int = 20) -> QuerySet:
    """Overdue action items visible to the actor."""
    return (
        action_queryset(user)
        .filter(due_date__lt=timezone.localdate())
        .exclude(
            status__in=[
                ActionStatus.COMPLETED,
                ActionStatus.VERIFIED,
                ActionStatus.CANCELLED,
            ]
        )
        .select_related("meeting", "owner")
        .order_by("due_date")[:limit]
    )


def Q_calendar_visible_to(user, scope_ids: list, *, prefix: str = ""):
    """Q filter restricting a queryset to calendars the actor may see.

    Applies to ``Calendar`` querysets with no prefix and to
    ``CalendarEvent``/related querysets with ``prefix="calendar"`` so the
    ``calendar__`` relation is traversed correctly.

    Public and organizational calendars are visible to authenticated users;
    team/unit/directorate scoped calendars require the matching access scope
    or an explicit share.
    """
    from django.db.models import Q

    if not _authenticated(user):
        return Q(pk__in=[])
    field = f"{prefix}__" if prefix else ""
    q = Q(
        **{
            f"{field}visibility__in": [
                CalendarVisibility.PUBLIC,
                CalendarVisibility.ORGANIZATIONAL,
            ]
        }
    )
    q |= Q(**{f"{field}owner": user})
    if scope_ids:
        q |= Q(**{f"{field}access_scope_id__in": scope_ids})
    q |= Q(**{f"{field}shares__user": user})
    if scope_ids:
        q |= Q(**{f"{field}shares__access_scope_id__in": scope_ids})
    return q


def calendar_detail_qs(user, scope_ids: list):
    """Q filter for a single calendar restricted to the actor's visibility."""
    from django.db.models import Q

    if not _authenticated(user):
        return Q(pk__in=[])
    q = Q(visibility__in=[CalendarVisibility.PUBLIC, CalendarVisibility.ORGANIZATIONAL])
    q |= Q(owner=user)
    if scope_ids:
        q |= Q(access_scope_id__in=scope_ids)
    q |= Q(shares__user=user)
    if scope_ids:
        q |= Q(shares__access_scope_id__in=scope_ids)
    return q


def user_queryset(user) -> QuerySet:
    """Active platform users the actor may pick in forms."""
    from apps.accounts.constants import AccountStatus
    from apps.accounts.models import User

    if not _authenticated(user) or not (
        user.is_superuser or _can_view_meetings(user) or _can_view_calendars(user)
    ):
        return User.objects.none()
    return User.objects.filter(status=AccountStatus.ACTIVE, is_active=True)


def organization_unit_queryset(user) -> QuerySet:
    """Active organization units the actor may pick in forms."""
    from apps.organizations.constants import UnitStatus
    from apps.organizations.models import OrganizationUnit

    if not _authenticated(user) or not (
        user.is_superuser or _can_view_meetings(user) or _can_view_calendars(user)
    ):
        return OrganizationUnit.objects.none()
    return OrganizationUnit.objects.filter(
        is_deleted=False, is_archived=False, status=UnitStatus.ACTIVE
    )


def access_scope_queryset(user) -> QuerySet:
    """Active access scopes the actor may pick in forms."""
    from apps.rbac.models import AccessScope

    if not _authenticated(user) or not (
        user.is_superuser or _can_view_meetings(user) or _can_view_calendars(user)
    ):
        return AccessScope.objects.none()
    return AccessScope.objects.filter(is_active=True)


def program_queryset(user) -> QuerySet:
    """Active programs the actor may pick in forms."""
    from apps.programs.models import Program

    if not _authenticated(user) or not _can_view_meetings(user):
        return Program.objects.none()
    return Program.objects.filter(is_deleted=False, is_archived=False)


def project_queryset(user) -> QuerySet:
    """Active projects the actor may pick in forms."""
    from apps.programs.models import Project

    if not _authenticated(user) or not _can_view_meetings(user):
        return Project.objects.none()
    return Project.objects.filter(is_deleted=False, is_archived=False)


def template_queryset(user) -> QuerySet:
    """Active meeting templates the actor may pick in forms."""
    if not _authenticated(user) or not _can_view_meetings(user):
        return MeetingTemplate.objects.none()
    return MeetingTemplate.objects.filter(is_active=True)


def presenter_queryset(user) -> QuerySet:
    """Users who may be listed as agenda presenters."""
    return user_queryset(user)


def related_document_queryset(user) -> QuerySet:
    """Documents the actor may reference in agendas, decisions and actions."""
    from apps.documents.models import Document

    if not _authenticated(user) or not _can_view_meetings(user):
        return Document.objects.none()
    return Document.objects.filter(is_deleted=False, is_archived=False)


def document_queryset(user) -> QuerySet:
    """Documents the actor may link to a meeting."""
    return related_document_queryset(user)


def agenda_queryset_for_meeting(user, meeting) -> QuerySet:
    """Current agenda items for a meeting, scoped to the actor's visibility."""
    if not meeting or not _authenticated(user) or not _can_view_meetings(user):
        return AgendaItem.objects.none()
    base = AgendaItem.objects.filter(agenda__meeting=meeting)
    if not user_can_view_confidential(user):
        base = base.filter(confidentiality_level__in=_NON_SENSITIVE_LEVELS)
    return base


def decision_queryset_for_meeting(user, meeting) -> QuerySet:
    """Decisions for a meeting, scoped to the actor's visibility."""
    if not meeting or not _authenticated(user) or not _can_view_meetings(user):
        return MeetingDecision.objects.none()
    base = MeetingDecision.objects.filter(meeting=meeting)
    if not user_can_view_confidential(user):
        base = base.filter(confidentiality_level__in=_NON_SENSITIVE_LEVELS)
    return base
