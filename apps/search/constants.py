"""Constants for the Enterprise Search module.

Defines the search limits, query validation thresholds and the source
entity catalogue that the unified search indexes.  Entity keys use the
``module.model`` dotted convention and mirror the RBAC permission namespaces.
"""

from django.utils.translation import gettext_lazy as _

SEARCH_APP_LABEL = _("Search")

# ---------------------------------------------------------------------------
# Query limits
# ---------------------------------------------------------------------------

MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 200
DEFAULT_RESULTS_PER_TYPE = 5
MAX_RESULTS_PER_TYPE = 25
RECENT_SEARCH_LIMIT = 12
SAVED_SEARCH_LIMIT = 50
AUDIT_LOG_LIMIT = 100

TERM_SEQUENCE_RESERVED = ("~", "!", "(", ")", '"', "+", "-", "&", "|", "^", ":")

# ---------------------------------------------------------------------------
# Entity types (the sources searched by the unified index)
# ---------------------------------------------------------------------------
# The payload returned for each entity type drives the providers registry.
SEARCHABLE_ENTITY_TYPES: tuple[tuple[str, str], ...] = (
    ("leadership.profile", _("Leadership Profiles")),
    ("memberships.profile", _("Members")),
    ("volunteers.profile", _("Volunteers")),
    ("stakeholders.partner", _("Stakeholders & Partners")),
    ("programs.program", _("Programmes")),
    ("programs.project", _("Projects")),
    ("beneficiaries.beneficiary", _("Beneficiaries")),
    ("meal.indicator", _("MEAL Indicators")),
    ("meal.monitoring_visit", _("Monitoring Visits")),
    ("meal.evaluation", _("Evaluations")),
    ("meal.complaint", _("Complaints")),
    ("meal.feedback", _("Feedback")),
    ("meal.lesson", _("Lessons Learned")),
    ("reports.template", _("Report Templates")),
    ("reports.report", _("Reports")),
    ("documents.document", _("Documents")),
    ("registers.register", _("Registers")),
    ("registers.entry", _("Register Entries")),
    ("meetings.meeting", _("Meetings")),
    ("meetings.event", _("Calendar Events")),
    ("notifications.notification", _("Notifications")),
    ("reviews.review", _("Reviews")),
)

ENTITY_TYPE_KEYS: tuple[str, ...] = tuple(
    key for key, _label in SEARCHABLE_ENTITY_TYPES
)

ENTITY_TYPE_LABELS: dict[str, str] = dict(SEARCHABLE_ENTITY_TYPES)
