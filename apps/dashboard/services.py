"""Dashboard services: single source of truth for home-page data.

Every widget rendered on the dashboard is resolved here so views, the
AJAX widget endpoint and templates all share one data path.  All counts
are permission-aware and scope-aware where selectors exist.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.core.cache import cache
from django.db.models import Avg, Count, Q, QuerySet
from django.utils import timezone

from apps.accounts.models import User
from apps.beneficiaries.constants import BeneficiaryStatus
from apps.beneficiaries.models import Beneficiary
from apps.documents.constants import ApprovalStatus as DocumentApprovalStatus
from apps.documents.models import Document
from apps.leadership.constants import LeadershipStatus
from apps.leadership.models import LeadershipProfile
from apps.meetings.constants import MeetingStatus
from apps.meetings.models import CalendarEvent, Meeting
from apps.notifications.models import SystemAnnouncement
from apps.notifications.selectors import (
    action_required_notifications,
    unread_count,
)
from apps.programs.constants import ProgramStatus, ProjectStatus
from apps.programs.models import Program, Project
from apps.rbac.authorization import (
    get_active_role_assignments,
    get_roles_for_user,
    user_has_any_permission,
)
from apps.report_instances.models import Report
from apps.report_instances.selectors import (
    get_overdue_reports,
    get_reports_pending_review,
)
from apps.reports.constants import ReportStatus
from apps.stakeholders.constants import StakeholderStatus
from apps.stakeholders.models import Stakeholder
from apps.volunteers.constants import VolunteerStatus

from .models import DashboardWidgetConfiguration

if TYPE_CHECKING:
    from .models import DashboardConfiguration

DEFAULT_REFRESH_INTERVAL = 300
CACHE_TTL_SECONDS = 60
DASHBOARD_ACTIVITY_PREVIEW_LIMIT = 5
ACTIVITY_LOG_PAGE_SIZE = 20
ACTIVITY_LOG_WINDOW = 200

# ---------------------------------------------------------------------------
# Stat cards
# ---------------------------------------------------------------------------

MEMBERSHIPS_VIEW_PERMS = ["memberships.view", "memberships.manage"]
PROGRAMMES_VIEW_PERMS = ["programmes.view", "programmes.manage"]
PROJECTS_VIEW_PERMS = ["projects.view", "projects.manage"]
BENEFICIARIES_VIEW_PERMS = ["beneficiaries.view", "beneficiaries.manage"]
PARTNERS_VIEW_PERMS = ["partners.view", "partners.view_directory", "partners.manage"]
REVIEWS_VIEW_PERMS = ["reviews.view", "reviews.manage"]
MEETINGS_VIEW_PERMS = ["meetings.view", "calendars.view", "meetings.manage"]
DOCUMENTS_VIEW_PERMS = ["documents.view", "documents.manage"]


def _active_members_count(period_start_date=None) -> int:
    from apps.memberships.models import MemberProfile
    
    queryset = MemberProfile.objects.filter(status__code="ACTIVE")
    if period_start_date:
        queryset = queryset.filter(created_at__gte=period_start_date)
    return queryset.count()


def _active_volunteers_count(user: User, period_start_date=None) -> int:
    from apps.volunteers.selectors import visible_volunteer_profiles

    queryset = (
        visible_volunteer_profiles(user)
        .filter(status__in=[VolunteerStatus.ACTIVE, VolunteerStatus.ASSIGNED])
    )
    if period_start_date:
        queryset = queryset.filter(created_at__gte=period_start_date)
    return queryset.count()


def _stat_definitions(period_start_date=None) -> list[dict[str, Any]]:
    """Ordered stat-card definitions shared by seeding and rendering."""
    return [
        {
            "key": "active_members",
            "title": "Active Members",
            "icon": "bi-person-badge",
            "url_name": "memberships:dashboard",
            "permissions": [],
            "resolver": lambda user: _active_members_count(period_start_date),
        },
        {
            "key": "active_volunteers",
            "title": "Active Volunteers",
            "icon": "bi-heart",
            "url_name": "volunteers:dashboard",
            "permissions": [],
            "resolver": lambda user: _active_volunteers_count(user, period_start_date),
        },
        {
            "key": "active_programs",
            "title": "Active Programs",
            "icon": "bi-kanban",
            "url_name": "programs:dashboard",
            "permissions": PROGRAMMES_VIEW_PERMS,
            "resolver": lambda user: Program.objects.filter(
                status=ProgramStatus.ACTIVE,
                created_at__gte=period_start_date
            ).count() if period_start_date else Program.objects.filter(
                status=ProgramStatus.ACTIVE
            ).count(),
        },
        {
            "key": "active_projects",
            "title": "Active Projects",
            "icon": "bi-diagram-3",
            "url_name": "programs:dashboard",
            "permissions": PROJECTS_VIEW_PERMS + PROGRAMMES_VIEW_PERMS,
            "resolver": lambda user: Project.objects.filter(
                status__in=[
                    ProjectStatus.INITIATION,
                    ProjectStatus.EXECUTION,
                    ProjectStatus.MONITORING,
                ],
                created_at__gte=period_start_date
            ).count() if period_start_date else Project.objects.filter(
                status__in=[
                    ProjectStatus.INITIATION,
                    ProjectStatus.EXECUTION,
                    ProjectStatus.MONITORING,
                ]
            ).count(),
        },
        {
            "key": "beneficiaries",
            "title": "Beneficiaries",
            "icon": "bi-people",
            "url_name": "beneficiaries:dashboard",
            "permissions": BENEFICIARIES_VIEW_PERMS,
            "resolver": lambda user: Beneficiary.objects.filter(
                status=BeneficiaryStatus.ACTIVE,
                created_at__gte=period_start_date
            ).count() if period_start_date else Beneficiary.objects.filter(
                status=BeneficiaryStatus.ACTIVE
            ).count(),
        },
        {
            "key": "stakeholders",
            "title": "Stakeholders",
            "icon": "bi-building-gear",
            "url_name": "stakeholders:dashboard",
            "permissions": PARTNERS_VIEW_PERMS,
            "resolver": lambda user: Stakeholder.objects.filter(
                status=StakeholderStatus.ACTIVE,
                created_at__gte=period_start_date
            ).count() if period_start_date else Stakeholder.objects.filter(
                status=StakeholderStatus.ACTIVE
            ).count(),
        },
        {
            "key": "reports_pending_review",
            "title": "Pending Reviews",
            "icon": "bi-check2-square",
            "url_name": "reviews:dashboard",
            "permissions": REVIEWS_VIEW_PERMS,
            "resolver": lambda user: get_reports_pending_review(user).count(),
        },
        {
            "key": "overdue_reports",
            "title": "Overdue Reports",
            "icon": "bi-exclamation-triangle",
            "url_name": "report_instances:dashboard",
            "permissions": [],
            "resolver": lambda user: get_overdue_reports().count(),
            "alert_when_nonzero": True,
        },
        {
            "key": "upcoming_meetings",
            "title": "Meetings (7 Days)",
            "icon": "bi-calendar3",
            "url_name": "meetings:dashboard",
            "permissions": MEETINGS_VIEW_PERMS,
            "resolver": lambda user: upcoming_meetings().count(),
        },
        {
            "key": "documents",
            "title": "Documents",
            "icon": "bi-folder2-open",
            "url_name": "documents:dashboard",
            "permissions": DOCUMENTS_VIEW_PERMS,
            "resolver": lambda user: Document.objects.filter(
                created_at__gte=period_start_date
            ).count() if period_start_date else Document.objects.count(),
        },
    ]


def upcoming_meetings(days: int = 7) -> QuerySet[Meeting]:
    """Meetings starting within the next ``days`` days that are still on."""
    now = timezone.now()
    horizon = now + timedelta(days=days)
    return Meeting.objects.filter(
        start_at__gte=now,
        start_at__lte=horizon,
    ).exclude(
        status__in=[MeetingStatus.CANCELLED, MeetingStatus.POSTPONED],
    )


def get_stat_cards(user: User, period_start_date=None) -> list[dict[str, Any]]:
    """Permission-filtered statistic cards for the stats row."""
    cards: list[dict[str, Any]] = []
    for definition in _stat_definitions(period_start_date):
        permissions = definition["permissions"]
        if permissions and not user_has_any_permission(user, permissions):
            continue
        value = definition["resolver"](user)
        alert = bool(definition.get("alert_when_nonzero")) and value > 0
        cards.append(
            {
                "key": definition["key"],
                "title": definition["title"],
                "icon": definition["icon"],
                "url_name": definition["url_name"],
                "value": value,
                "is_alert": alert,
            }
        )
    return cards


# ---------------------------------------------------------------------------
# Welcome / profile hero
# ---------------------------------------------------------------------------


def get_welcome_profile(user: User) -> dict[str, Any]:
    """Position/unit context for the welcome card.

    Position and organizational unit live on LeadershipProfile (staff) or
    VolunteerProfile.team (volunteers), not on the auth User model.
    """
    profile_photo_url = None
    user_profile = getattr(user, "profile", None)
    if user_profile is not None and user_profile.profile_photo:
        profile_photo_url = user_profile.profile_photo.url

    position_title = None
    unit_name = None

    leadership = (
        LeadershipProfile.objects.filter(
            user=user,
            status__in=[
                LeadershipStatus.ACTIVE,
                LeadershipStatus.APPOINTED,
                LeadershipStatus.ACTING,
            ],
        )
        .select_related("position", "organizational_unit")
        .first()
    )
    if leadership is not None:
        position_title = getattr(leadership.position, "title", None)
        unit_name = getattr(leadership.organizational_unit, "name", None)

    if position_title is None:
        volunteer = getattr(user, "volunteer_profile", None)
        if volunteer is not None:
            position_title = volunteer.get_status_display()
            unit_name = getattr(volunteer.team, "name", None)

    if position_title is None:
        # Fall back to the user's active RBAC role assignment.
        assignment = (
            get_active_role_assignments(user)
            .select_related("role", "access_scope")
            .first()
        )
        if assignment is not None:
            position_title = getattr(assignment.role, "name", None)
            unit_name = getattr(assignment.access_scope, "name", None)

    return {
        "display_name": user.get_full_name() or user.username,
        "position_title": position_title,
        "unit_name": unit_name,
        "profile_photo_url": profile_photo_url,
    }


# ---------------------------------------------------------------------------
# Quick actions
# ---------------------------------------------------------------------------

_QUICK_ACTIONS: list[dict[str, Any]] = [
    {
        "label": "Create Report",
        "description": "Start a new report from template",
        "icon": "bi-file-earmark-plus",
        "url_name": "report_instances:create",
        "permissions": ["report_templates.view", "report_templates.manage"],
        "color": "primary",
    },
    {
        "label": "Browse Templates",
        "description": "View available report templates",
        "icon": "bi-grid",
        "url_name": "reports:category_browse",
        "permissions": ["report_templates.view", "report_templates.manage"],
        "color": "purple",
    },
    {
        "label": "My Reports",
        "description": "View and manage your reports",
        "icon": "bi-file-earmark-text",
        "url_name": "report_instances:list",
        "permissions": ["report_templates.view", "report_templates.manage"],
        "color": "cyan",
    },
    {
        "label": "Add Member",
        "description": "Register a new member",
        "icon": "bi-person-plus",
        "url_name": "memberships:member_create",
        "permissions": ["memberships.manage", "memberships.view"],
        "color": "success",
    },
    {
        "label": "Add Volunteer",
        "description": "Register a new volunteer",
        "icon": "bi-people",
        "url_name": "volunteers:create",
        "permissions": ["volunteers.manage", "volunteers.view"],
        "color": "warning",
    },
    {
        "label": "Add Leader",
        "description": "Create a leadership profile",
        "icon": "bi-person-badge",
        "url_name": "leadership:profile_create",
        "permissions": ["leadership.manage", "leadership.view"],
        "color": "indigo",
    },
    {
        "label": "Add Beneficiary",
        "description": "Register a new beneficiary",
        "icon": "bi-person-heart",
        "url_name": "beneficiaries:create",
        "permissions": BENEFICIARIES_VIEW_PERMS,
        "color": "danger",
    },
    {
        "label": "Upload Document",
        "description": "Upload a new document",
        "icon": "bi-cloud-arrow-up",
        "url_name": "documents:upload",
        "permissions": DOCUMENTS_VIEW_PERMS,
        "color": "teal",
    },
    {
        "label": "Schedule Meeting",
        "description": "Create a new meeting or event",
        "icon": "bi-calendar-plus",
        "url_name": "meetings:meeting_create",
        "permissions": MEETINGS_VIEW_PERMS,
        "color": "amber",
    },
    {
        "label": "View Notifications",
        "description": "Check your notifications",
        "icon": "bi-bell",
        "url_name": "notifications:inbox",
        "permissions": [],
        "color": "danger",
    },
    {
        "label": "View Approvals",
        "description": "Review pending approvals",
        "icon": "bi-check2-square",
        "url_name": "reviews:dashboard",
        "permissions": REVIEWS_VIEW_PERMS,
        "color": "success",
    },
    {
        "label": "Search",
        "description": "Search across the platform",
        "icon": "bi-search",
        "url_name": "search:home",
        "permissions": [],
        "color": "secondary",
    },
]


def get_quick_actions(user: User) -> list[dict[str, str]]:
    """Permission-gated shortcuts used across the workspace."""
    actions: list[dict[str, str]] = []
    for action in _QUICK_ACTIONS:
        permissions = action["permissions"]
        # Empty permissions list means no permission required (available to all authenticated users)
        if not permissions or user_has_any_permission(user, permissions):
            actions.append(
                {
                    "label": action["label"],
                    "description": action["description"],
                    "icon": action["icon"],
                    "url_name": action["url_name"],
                    "color": action["color"],
                }
            )
    return actions


# ---------------------------------------------------------------------------
# Notifications summary
# ---------------------------------------------------------------------------


def get_notification_summary(user: User) -> dict[str, int]:
    return {
        "unread": unread_count(user),
        "action_required": action_required_notifications(user).count(),
    }


# ---------------------------------------------------------------------------
# Recent activity feed
# ---------------------------------------------------------------------------

_ACTIVITY_SOURCES = [
    ("apps.memberships.models", "MembershipAuditRecord", "Membership"),
    ("apps.volunteers.models", "VolunteerAuditRecord", "Volunteers"),
    ("apps.beneficiaries.models", "BeneficiaryAuditRecord", "Beneficiaries"),
    ("apps.documents.models", "DocumentAuditRecord", "Documents"),
    ("apps.organizations.models", "OrganizationAuditRecord", "Organization"),
    ("apps.leadership.models", "LeadershipAuditRecord", "Leadership"),
]

_ACTION_ICONS = [
    ("CREATE", "bi-plus-circle", "text-success"),
    ("UPDATE", "bi-pencil-square", "text-primary-brand"),
    ("DELETE", "bi-trash3", "text-danger"),
    ("APPROVE", "bi-check2-circle", "text-success"),
    ("REJECT", "bi-x-circle", "text-danger"),
    ("SUBMIT", "bi-send", "text-primary-brand"),
]


def _audit_icon(action: str) -> tuple[str, str]:
    upper = (action or "").upper()
    for keyword, icon, color in _ACTION_ICONS:
        if keyword in upper:
            return icon, color
    return "bi-activity", "text-muted"


def _audit_timestamp_field(model) -> str:
    """Audit models name their timestamp ``changed_at`` or ``created_at``."""
    for candidate in ("changed_at", "created_at"):
        try:
            model._meta.get_field(candidate)
            return candidate
        except Exception:
            continue
    return "pk"


def get_recent_activity(
    user: User, limit: int = 10, per_source: int | None = None
) -> list[dict[str, Any]]:
    """Merge the newest immutable audit records across modules.

    ``limit`` caps the merged feed length; ``per_source`` controls how many
    rows are pulled from each module before merging (defaults to ``limit``).
    """
    from django.apps import apps as django_apps

    source_window = per_source if per_source is not None else limit
    entries: list[dict[str, Any]] = []
    for module_path, model_name, module_label in _ACTIVITY_SOURCES:
        model = django_apps.get_model(module_path.split(".")[1], model_name)
        timestamp_field = _audit_timestamp_field(model)
        rows = model.objects.order_by(f"-{timestamp_field}")[:source_window]
        for row in rows:
            actor = row.changed_by
            icon, color = _audit_icon(row.action)
            entries.append(
                {
                    "module": module_label,
                    "action": str(row.get_action_display())
                    if hasattr(row, "get_action_display")
                    else str(row.action).replace("_", " ").title(),
                    "entity_type": str(row.entity_type).replace("_", " ").title()
                    if row.entity_type
                    else "",
                    "actor": (actor.get_full_name() or actor.username)
                    if actor
                    else "System",
                    "created_at": getattr(row, timestamp_field),
                    "icon": icon,
                    "color": color,
                }
            )

    entries.sort(key=lambda entry: entry["created_at"], reverse=True)
    return entries[:limit]


# ---------------------------------------------------------------------------
# Widget resolution
# ---------------------------------------------------------------------------


def get_default_configuration() -> DashboardConfiguration:
    """Return the default dashboard configuration, creating it if missing."""
    from .models import DashboardConfiguration

    try:
        return DashboardConfiguration.objects.get(is_default=True)
    except DashboardConfiguration.DoesNotExist:
        return DashboardConfiguration.objects.create(
            name="Default Dashboard", is_default=True
        )


def resolve_statistic_card(
    widget_config: DashboardWidgetConfiguration, user: User, period_start_date=None
) -> dict[str, Any] | None:
    """Resolve one statistic widget to a renderable card.

    Returns ``None`` when the widget has no known stat key or the user
    lacks the required permissions.
    """
    configuration = widget_config.widget.configuration or {}
    stat_key = configuration.get("stat_key")

    for definition in _stat_definitions(period_start_date):
        if definition["key"] != stat_key:
            continue
        permissions = definition["permissions"]
        if permissions and not user_has_any_permission(user, permissions):
            return None
        value = definition["resolver"](user)
        return {
            "key": stat_key,
            "title": definition["title"],
            "icon": definition["icon"],
            "url_name": definition["url_name"],
            "value": value,
            "is_alert": bool(definition.get("alert_when_nonzero")) and value > 0,
        }
    return None


def resolve_widget_payload(
    widget_config: DashboardWidgetConfiguration, user: User, period_start_date=None
) -> dict[str, Any]:
    """Resolve renderable data for one configured widget.

    Statistic widgets are resolved by their stable seeded key stored in
    ``configuration['stat_key']``; other types map directly to service calls.
    """
    widget = widget_config.widget

    if widget.widget_type == "statistic":
        card = resolve_statistic_card(widget_config, user, period_start_date)
        if card is None:
            return {"key": (widget.configuration or {}).get("stat_key"), "value": "--"}
        return card

    if widget.widget_type == "quick_actions":
        return {"actions": get_quick_actions(user)}

    if widget.widget_type == "notification":
        return get_notification_summary(user)

    if widget.widget_type == "activity":
        return {
            "entries": get_recent_activity(
                user, limit=DASHBOARD_ACTIVITY_PREVIEW_LIMIT
            )
        }

    if widget.widget_type == "chart":
        # Return chart configuration with user's preferred chart style
        pref = getattr(user, "dashboard_preference", None)
        chart_style = getattr(pref, "preferred_chart_style", "bar")
        return {
            "chart_type": chart_style,
            "configuration": widget.configuration,
        }

    # Hero-type widgets are rendered by the view via get_welcome_profile().
    return {}


# ---------------------------------------------------------------------------
# Settings, caching and period helpers
# ---------------------------------------------------------------------------


def get_refresh_interval() -> int:
    """System-configured dashboard auto-refresh interval (seconds)."""
    cached = cache.get("dashboard:refresh_interval")
    if cached is not None:
        return int(cached)
    interval = DEFAULT_REFRESH_INTERVAL
    try:
        from apps.system_settings.models import SystemConfiguration

        config = SystemConfiguration.objects.first()  # type: ignore[attr-defined]
        if config and config.dashboard_refresh_interval_seconds:
            interval = int(config.dashboard_refresh_interval_seconds)
    except Exception:
        pass
    cache.set("dashboard:refresh_interval", interval, CACHE_TTL_SECONDS)
    return interval


REPORTING_PERIOD_LABELS = {
    "today": "Today",
    "this_week": "This Week",
    "this_month": "This Month",
    "this_quarter": "This Quarter",
    "this_year": "This Year",
}


def period_start(period: str):
    """Start date for a user's reporting-period selection."""
    now = timezone.now()
    mapping = {
        "today": now - timedelta(days=1),
        "this_week": now - timedelta(days=7),
        "this_month": now - timedelta(days=30),
        "this_quarter": now - timedelta(days=90),
        "this_year": now - timedelta(days=365),
    }
    return mapping.get(period, mapping["this_month"])


def _cached_stat_values(user: User, period_start_date=None) -> dict[str, Any]:
    """Compute (and briefly cache) raw stat values for a user."""
    cache_suffix = f":{period_start_date.isoformat()}" if period_start_date else ""
    cache_key = f"dashboard:stats:{user.id}:{int(user.is_superuser)}{cache_suffix}"
    values = cache.get(cache_key)
    if values is not None:
        return values

    values = {}
    for definition in _stat_definitions(period_start_date):
        try:
            values[definition["key"]] = definition["resolver"](user)
        except Exception:
            values[definition["key"]] = None
    cache.set(cache_key, values, CACHE_TTL_SECONDS)
    return values


# ---------------------------------------------------------------------------
# Welcome context (greeting / date / reporting period)
# ---------------------------------------------------------------------------


def get_welcome_context(user: User) -> dict[str, Any]:
    from django.utils.timezone import localtime

    profile = get_welcome_profile(user)
    hour = localtime().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    pref = getattr(user, "dashboard_preference", None)
    period_key = getattr(pref, "default_reporting_period", "this_month")

    return {
        **profile,
        "greeting": greeting,
        "today": localtime(),
        "reporting_period": REPORTING_PERIOD_LABELS.get(period_key, "This Month"),
    }


# ---------------------------------------------------------------------------
# Profile summary and organizational context
# ---------------------------------------------------------------------------


def get_profile_summary(user: User) -> dict[str, Any]:
    """Profile summary card data."""
    roles = [role.name for role in get_roles_for_user(user)[:5]]

    member_status = None
    member_profile = getattr(user, "member_profile", None)
    if member_profile is not None:
        member_status = getattr(member_profile.status, "code", None)

    return {
        "email": user.email,
        "phone_number": user.phone_number,
        "roles": roles,
        "member_status": member_status,
    }


def get_org_context(user: User) -> dict[str, Any]:
    """Organizational information relevant to the user's responsibilities."""
    supervisor = None
    unit_name = None
    team_name = None

    leadership = (
        LeadershipProfile.objects.filter(user=user)
        .select_related("supervisor__user", "organizational_unit")
        .first()
    )
    if leadership is not None:
        unit_name = getattr(leadership.organizational_unit, "name", None)
        supervisor_user = getattr(leadership.supervisor, "user", None)
        if supervisor_user is not None:
            supervisor = supervisor_user.get_full_name() or supervisor_user.username

    volunteer = getattr(user, "volunteer_profile", None)
    if volunteer is not None:
        team_name = getattr(volunteer.team, "name", None)
        if supervisor is None and volunteer.supervisor is not None:
            supervisor_user = volunteer.supervisor.user
            supervisor = supervisor_user.get_full_name() or supervisor_user.username
        if unit_name is None:
            unit_name = team_name

    managed_programs = Program.objects.filter(
        program_manager=user, status=ProgramStatus.ACTIVE
    ).order_by("title")
    managed_projects = Project.objects.filter(
        project_manager=user,
        status__in=[
            ProjectStatus.INITIATION,
            ProjectStatus.EXECUTION,
            ProjectStatus.MONITORING,
        ],
    ).order_by("title")

    return {
        "unit_name": unit_name,
        "team_name": team_name,
        "supervisor": supervisor,
        "programs": list(managed_programs.values("id", "title")[:3]),
        "programs_count": managed_programs.count(),
        "projects": list(managed_projects.values("id", "title")[:3]),
        "projects_count": managed_projects.count(),
    }


# ---------------------------------------------------------------------------
# Report work-queue widgets
# ---------------------------------------------------------------------------

_OPEN_REPORT_STATUSES = [
    ReportStatus.DRAFT,
    ReportStatus.IN_PROGRESS,
    ReportStatus.SUBMITTED,
    ReportStatus.UNDER_REVIEW,
    ReportStatus.RESUBMITTED,
    ReportStatus.RETURNED_FOR_CORRECTION,
]


def _visible_reports(user: User) -> QuerySet[Report]:
    """Reports the user may see: own, reviewed, or all for superusers."""
    queryset = get_all_reports_queryset()
    if user.is_superuser or user_has_any_permission(user, ["report_templates.manage"]):
        return queryset
    return queryset.filter(Q(owner=user) | Q(assigned_reviewer=user))


def get_all_reports_queryset() -> QuerySet[Report]:
    from apps.report_instances.selectors import get_all_reports

    return get_all_reports()


def _report_row(report: Report, today) -> dict[str, Any]:
    return {
        "id": report.id,
        "title": report.title,
        "reference_number": report.reference_number,
        "status_display": report.get_status_display(),
        "owner": report.owner.get_full_name() or str(report.owner)
        if report.owner
        else "-",
        "due_date": report.due_date,
        "days_left": (report.due_date - today).days if report.due_date else None,
    }


def get_reports_due(user: User, days: int = 14, limit: int = 6) -> list[dict[str, Any]]:
    today = timezone.localdate()
    horizon = today + timedelta(days=days)
    rows = (
        _visible_reports(user)
        .filter(
            due_date__gte=today,
            due_date__lte=horizon,
            status__in=_OPEN_REPORT_STATUSES,
        )
        .select_related("owner")
        .order_by("due_date")[:limit]
    )
    return [_report_row(report, today) for report in rows]


def get_my_drafts(user: User, limit: int = 6) -> list[dict[str, Any]]:
    today = timezone.localdate()
    drafts = (
        get_all_reports_queryset()
        .filter(owner=user, status__in=[ReportStatus.DRAFT, ReportStatus.IN_PROGRESS])
        .order_by("-updated_at")[:limit]
    )
    return [_report_row(report, today) for report in drafts]


def get_pending_approvals(user: User, limit: int = 6) -> list[dict[str, Any]]:
    today = timezone.localdate()
    pending = (
        get_reports_pending_review(user)
        .select_related("owner")
        .order_by("-submitted_at")[:limit]
    )
    return [_report_row(report, today) for report in pending]


def get_overdue_list(user: User, limit: int = 6) -> list[dict[str, Any]]:
    today = timezone.localdate()
    overdue = (
        _visible_reports(user)
        .filter(due_date__lt=today, status__in=_OPEN_REPORT_STATUSES)
        .select_related("owner")
        .order_by("due_date")[:limit]
    )
    rows = []
    for report in overdue:
        row = _report_row(report, today)
        row["days_overdue"] = -row["days_left"] if row["days_left"] else 0
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Performance widgets
# ---------------------------------------------------------------------------


def get_program_progress(limit: int = 5) -> list[dict[str, Any]]:
    programs = (
        Program.objects.filter(status=ProgramStatus.ACTIVE)
        .annotate(
            projects_total=Count("projects", distinct=True),
            projects_completed=Count(
                "projects",
                filter=Q(
                    projects__status__in=[
                        ProjectStatus.COMPLETION,
                        ProjectStatus.CLOSURE,
                    ]
                ),
                distinct=True,
            ),
            avg_completion=Avg("projects__completion_percentage"),
        )
        .order_by("title")[:limit]
    )

    rows = []
    for program in programs:
        approved = program.budget_approved or 0
        utilized = program.budget_utilized or 0
        rows.append(
            {
                "id": program.id,
                "title": program.title,
                "projects_total": program.projects_total,
                "projects_completed": program.projects_completed,
                "avg_completion": round(program.avg_completion or 0, 1),
                "budget_utilization": round(utilized / approved * 100, 1)
                if approved > 0
                else 0,
            }
        )
    return rows


def get_project_status_summary() -> dict[str, Any]:
    active_statuses = [
        ProjectStatus.INITIATION,
        ProjectStatus.EXECUTION,
        ProjectStatus.MONITORING,
    ]
    closed_statuses = [
        ProjectStatus.COMPLETION,
        ProjectStatus.CLOSURE,
        ProjectStatus.ARCHIVED,
    ]
    today = timezone.localdate()
    active = Project.objects.filter(status__in=active_statuses)

    delayed = active.filter(end_date__lt=today).count()
    summary = active.aggregate(
        total=Count("id"),
        avg_completion=Avg("completion_percentage"),
        high_risk=Count("id", filter=Q(risk_level__gte=4)),
    )
    upcoming_milestones = 0
    try:
        from apps.programs.models import Milestone

        upcoming_milestones = Milestone.objects.filter(
            target_date__gte=today,
            completion_date__isnull=True,
            project__status__in=active_statuses,
        ).count()
    except Exception:
        pass

    return {
        "active": summary["total"] or 0,
        "delayed": delayed,
        "high_risk": summary["high_risk"] or 0,
        "avg_completion": round(summary["avg_completion"] or 0, 1),
        "upcoming_milestones": upcoming_milestones,
        "completed": Project.objects.filter(status__in=closed_statuses).count(),
    }


# ---------------------------------------------------------------------------
# Document, audit, events, announcements, notifications widgets
# ---------------------------------------------------------------------------


def get_document_activity(user: User, limit: int = 6) -> dict[str, Any]:
    recent = Document.objects.order_by("-updated_at")[:limit]
    soon = timezone.localdate() + timedelta(days=30)
    return {
        "recent": [
            {
                "id": document.id,
                "title": document.title,
                "updated_at": document.updated_at,
                "status_display": document.get_status_display(),
            }
            for document in recent
        ],
        "pending_approval": Document.objects.filter(
            approval_status__in=[
                DocumentApprovalStatus.PENDING_APPROVAL,
                DocumentApprovalStatus.PENDING_REVIEW,
            ]
        ).count(),
        "expiring_soon": Document.objects.filter(
            expiry_date__isnull=False, expiry_date__lte=soon
        ).count(),
    }


def can_view_audit_activity(user: User) -> bool:
    return bool(user.is_superuser or user_has_any_permission(user, ["security.view"]))


def get_audit_activity(limit: int = 6) -> dict[str, Any]:
    from apps.security.models import LoginAttempt

    week_ago = timezone.now() - timedelta(days=7)
    failed = LoginAttempt.objects.exclude(outcome=LoginAttempt.SUCCESS).filter(
        created_at__gte=week_ago
    )

    return {
        "failed_logins_7d": failed.count(),
        "recent_failures": [
            {
                "username": attempt.username_attempted,
                "ip_address": attempt.ip_address,
                "outcome": attempt.get_outcome_display(),
                "created_at": attempt.created_at,
            }
            for attempt in failed.order_by("-created_at")[:limit]
        ],
    }


def get_upcoming_events(user: User, limit: int = 8) -> list[dict[str, Any]]:
    now = timezone.now()
    horizon = now + timedelta(days=30)
    events: list[dict[str, Any]] = []

    for meeting in upcoming_meetings(days=30)[:limit]:
        events.append(
            {
                "kind": "Meeting",
                "icon": "bi-people",
                "title": meeting.title,
                "start_at": meeting.start_at,
                "url": ("meetings:meeting_detail", meeting.id),
            }
        )

    calendar_events = CalendarEvent.objects.filter(
        start_at__gte=now, start_at__lte=horizon
    ).order_by("start_at")[:limit]
    for event in calendar_events:
        events.append(
            {
                "kind": event.get_event_type_display(),
                "icon": "bi-calendar-event",
                "title": event.title,
                "start_at": event.start_at,
                "url": ("meetings:event_detail", event.id),
            }
        )

    events.sort(key=lambda item: item["start_at"])
    trimmed = events[:limit]
    for item in trimmed:
        item["url_name"], item["url_id"] = item.pop("url")
    return trimmed


def get_announcements(limit: int = 4) -> list[dict[str, Any]]:
    now = timezone.now()
    announcements = SystemAnnouncement.objects.filter(
        is_published=True, publish_at__lte=now
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
    return [
        {
            "title": announcement.title,
            "message": announcement.message,
            "priority": announcement.priority,
            "publish_at": announcement.publish_at,
            "deep_link": announcement.deep_link or "",
        }
        for announcement in announcements.order_by("-publish_at")[:limit]
    ]


def get_recent_notifications(user: User, limit: int = 5) -> list[dict[str, Any]]:
    from apps.notifications.selectors import active_notifications

    return [
        {
            "title": notification.title,
            "message": notification.message,
            "category": notification.category,
            "created_at": notification.created_at,
            "read": notification.read_status != "UNREAD",
        }
        for notification in active_notifications(user)[:limit]
    ]


# ---------------------------------------------------------------------------
# Personalization
# ---------------------------------------------------------------------------


def get_personalized_widgets(
    user: User, configs: list[DashboardWidgetConfiguration]
) -> list[DashboardWidgetConfiguration]:
    """Apply per-user visibility/order overrides to default widget layout."""
    states = {state.widget_id: state for state in user.dashboard_widget_states.all()}

    def sort_position(config: DashboardWidgetConfiguration) -> int:
        state = states.get(config.widget_id)
        if state is not None and state.position is not None:
            return state.position
        return config.position if config.position is not None else 9999

    visible = [
        config
        for config in configs
        if not (states.get(config.widget_id) and states[config.widget_id].is_hidden)
    ]
    return sorted(visible, key=sort_position)


def set_widget_state(
    user: User,
    widget_id: int,
    *,
    is_hidden: bool | None = None,
    position: int | None = None,
) -> None:
    from .models import UserWidgetState

    state, _created = UserWidgetState.objects.get_or_create(
        user=user, widget_id=widget_id
    )
    if is_hidden is not None:
        state.is_hidden = is_hidden
    if position is not None:
        state.position = position
    state.save()
