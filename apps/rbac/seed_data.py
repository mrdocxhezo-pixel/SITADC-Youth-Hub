"""
Seed data for the Role-Based Access Control (RBAC) framework.

This module is the single source of truth for:

* The permission catalogue (functional categories and their actions).
* The hierarchical organizational access scopes.
* The default organizational roles and their permission grants.

Both the initial data migration and the ``seed_default_roles`` management
command consume this module so the seeded state never drifts between
environments.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Permission catalogue
# ---------------------------------------------------------------------------
# Permission codes follow the ``module.action`` convention required by the
# NAMING_CONVENTIONS.md document (e.g. ``reports.submit``).


def _actions(*names: str) -> frozenset[str]:
    """Build an immutable set of permission action names."""
    return frozenset(names)


# The full catalogue maps a functional category code to a tuple of
# (human-readable label, tuple of supported actions).
PERMISSION_CATEGORIES: dict[str, tuple[str, frozenset[str]]] = {
    "accounts": (
        "Accounts",
        _actions("view", "create", "update", "delete", "assign", "export", "manage"),
    ),
    "dashboard": ("Dashboard", _actions("view", "export")),
    "leadership": (
        "Leadership",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        ),
    ),
    "membership": (
        "Membership",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "archive",
            "restore",
            "export",
            "assign",
            "verify",
            "review",
            "approve",
            "reject",
            "renew",
            "suspend",
            "terminate",
            "transfer",
            "waive",
            "record_payment",
            "verify_payment",
            "issue_card",
            "view_confidential",
            "manage_attendance",
            "manage_participation",
            "manage_leave",
            "manage_exit",
            "configure",
            "manage",
        ),
    ),
    "volunteers": (
        "Volunteers",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "archive",
            "restore",
            "export",
            "assign",
            "manage_attendance",
            "manage_training",
            "manage_performance",
            "manage_leave",
            "manage_exit",
            "manage_activity",
            "manage_disciplinary",
            "manage_communications",
            "manage_documents",
            "configure",
            "view_confidential",
            "manage",
        ),
    ),
    "beneficiaries": (
        "Beneficiaries",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "archive",
            "restore",
            "export",
            "manage",
        ),
    ),
    "partners": (
        "Stakeholders and Partnerships",
        _actions(
            "view",
            "view_directory",
            "view_profile",
            "view_private_contacts",
            "view_due_diligence",
            "view_financial",
            "view_confidential",
            "create",
            "update",
            "delete",
            "archive",
            "restore",
            "export",
            "assign",
            "manage_categories",
            "manage_contacts",
            "assess",
            "manage_engagements",
            "manage_communications",
            "manage_commitments",
            "manage_contributions",
            "manage_agreements",
            "review_agreements",
            "approve_agreements",
            "manage_due_diligence",
            "manage_risk",
            "manage_performance",
            "review_performance",
            "manage_actions",
            "manage_notes",
            "manage_documents",
            "manage_access",
            "analytics",
            "manage",
        ),
    ),
    "programmes": (
        "Programmes",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        ),
    ),
    "projects": (
        "Projects",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        ),
    ),
    "meal": (
        "MEAL",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "archive",
            "restore",
            "export",
            "manage",
        ),
    ),
    "reports": (
        "Reports",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "approve",
            "reject",
            "return",
            "archive",
            "restore",
            "export",
            "manage",
        ),
    ),
    "approvals": (
        "Approvals",
        _actions("view", "approve", "reject", "return", "assign", "manage"),
    ),
    "documents": (
        "Documents",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "download",
            "upload",
            "approve",
            "archive",
            "restore",
            "export",
            "manage",
        ),
    ),
    "registers": (
        "Registers",
        _actions("view", "create", "update", "delete", "export", "manage"),
    ),
    "meetings": (
        "Meetings",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "archive",
            "restore",
            "export",
            "manage",
        ),
    ),
    "notifications": (
        "Notifications",
        _actions("view", "create", "send", "archive", "manage"),
    ),
    "finance": (
        "Finance",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "approve",
            "archive",
            "restore",
            "export",
            "manage",
        ),
    ),
    "communications": (
        "Communications",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "publish",
            "archive",
            "export",
            "manage",
        ),
    ),
    "audit": ("Audit", _actions("view", "export", "manage")),
    "settings": ("Settings", _actions("view", "update", "manage")),
    "administration": ("Administration", _actions("view", "manage", "assign")),
    "governance": (
        "Governance",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "approve",
            "archive",
            "restore",
            "export",
            "manage",
        ),
    ),
    "organizations": (
        "Organizations",
        _actions(
            "view",
            "create",
            "update",
            "delete",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        ),
    ),
    "reference_numbers": (
        "Reference Numbers",
        _actions(
            "view",
            "create",
            "update",
            "activate",
            "archive",
            "preview",
            "reset",
            "view_registry",
            "correct",
        ),
    ),
}

ALL_PERMISSION_CODES: frozenset[str] = frozenset(
    f"{category}.{action}"
    for category, (_, actions) in PERMISSION_CATEGORIES.items()
    for action in actions
)

# ---------------------------------------------------------------------------
# Access scopes
# ---------------------------------------------------------------------------
# Level values must match ``AccessScopeLevel`` in constants.py.  Phase 08
# (Organizational Structure) will attach real organizational units to these
# scopes; they are seeded now so authorization can reference them.
ACCESS_SCOPES: tuple[tuple[str, str, int, str], ...] = (
    ("national", "National", 10, "Access across the entire organization."),
    ("regional", "Regional", 20, "Access limited to an assigned region."),
    ("district", "District", 30, "Access limited to an assigned district."),
    ("community", "Community", 40, "Access limited to an assigned community."),
    ("team", "Team", 50, "Access limited to an assigned team."),
    ("programme", "Programme", 60, "Access limited to an assigned programme."),
    ("project", "Project", 70, "Access limited to an assigned project."),
)

DEFAULT_SCOPE_CODE = "national"

# ---------------------------------------------------------------------------
# Reusable action groups
# ---------------------------------------------------------------------------
VIEW = _actions("view")
OPERATE = _actions("view", "create", "update")
SUBMIT = _actions("view", "create", "update", "submit", "export")
MANAGE = _actions(
    "view",
    "create",
    "update",
    "delete",
    "submit",
    "approve",
    "reject",
    "return",
    "archive",
    "restore",
    "export",
    "assign",
    "manage",
    "manage_attendance",
    "manage_training",
    "manage_performance",
    "manage_leave",
    "manage_exit",
    "view_confidential",
)


def _operational_base() -> dict[str, frozenset[str]]:
    """Common modules every operational officer may work with."""
    return {
        "dashboard": VIEW,
        "reports": _actions("view", "create", "update", "submit", "export"),
        "approvals": _actions("view"),
        "registers": _actions("view", "create", "update", "export"),
        "meetings": _actions("view", "create", "update", "export"),
        "documents": _actions(
            "view", "create", "update", "upload", "download", "export"
        ),
        "notifications": _actions("view", "create", "send"),
        "communications": _actions("view", "create", "update", "export"),
    }


def _officer_base() -> dict[str, frozenset[str]]:
    """Shared module grants for specialist officer roles."""
    return {
        "dashboard": VIEW,
        "reports": _actions("view", "create", "update", "submit", "export"),
        "registers": _actions("view", "create", "update", "export"),
        "meetings": _actions("view", "create", "update", "export"),
        "documents": _actions(
            "view", "create", "update", "upload", "download", "export"
        ),
        "notifications": _actions("view", "create", "send"),
    }


# ---------------------------------------------------------------------------
# Default roles (Super Administrator ... Guest)
# ---------------------------------------------------------------------------
# Each role carries a permission spec: a mapping of category code (or "*" for
# every category) to the set of actions granted.  ``expand_role_permissions``
# resolves the spec against the catalogue below.
ROLE_PERMISSION_SPECS: dict[str, dict[str, frozenset[str]]] = {
    "super-administrator": {"*": MANAGE},
    "system-administrator": {"*": MANAGE},
    "board-chairperson": {
        "*": _actions("view", "approve", "reject", "export", "manage")
    },
    "board-secretary": {
        "*": _actions("view", "create", "update", "approve", "export", "manage")
    },
    "board-member": {"*": _actions("view", "approve", "reject", "export")},
    "president": {
        "*": _actions(
            "view",
            "create",
            "update",
            "submit",
            "approve",
            "reject",
            "export",
            "assign",
            "manage",
        )
    },
    "vice-president": {
        "*": _actions(
            "view",
            "create",
            "update",
            "submit",
            "approve",
            "reject",
            "export",
            "assign",
            "manage",
        )
    },
    "executive-director": {
        "*": _actions(
            "view",
            "create",
            "update",
            "submit",
            "approve",
            "reject",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        )
    },
    "executive-secretary": {
        "*": _actions(
            "view",
            "create",
            "update",
            "submit",
            "approve",
            "reject",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        )
    },
    "secretary-general": {
        "*": _actions(
            "view",
            "create",
            "update",
            "submit",
            "approve",
            "reject",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        )
    },
    "nec-member": {"*": _actions("view", "approve", "reject", "export")},
    "director": {
        "*": _actions(
            "view",
            "create",
            "update",
            "submit",
            "approve",
            "reject",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        )
    },
    "deputy-director": {
        "*": _actions(
            "view",
            "create",
            "update",
            "submit",
            "approve",
            "reject",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        )
    },
    "regional-coordinator": {
        "leadership": _actions("view", "create", "update", "export"),
        "membership": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "volunteers": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "beneficiaries": _actions("view", "create", "update", "submit", "export"),
        "partners": _actions("view", "create", "update", "submit", "export", "assign"),
        "programmes": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "projects": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "meal": _actions("view", "create", "update", "submit", "export"),
        "reports": _actions("view", "create", "update", "submit", "approve", "export"),
        "approvals": _actions("view", "approve", "reject", "assign"),
        "finance": _actions("view", "export"),
        "governance": VIEW,
        **_operational_base(),
    },
    "district-coordinator": {
        "membership": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "volunteers": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "beneficiaries": _actions("view", "create", "update", "submit", "export"),
        "partners": _actions("view", "create", "update", "submit", "export", "assign"),
        "programmes": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "projects": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "meal": _actions("view", "create", "update", "submit", "export"),
        "reports": _actions("view", "create", "update", "submit", "approve", "export"),
        "approvals": _actions("view", "approve", "reject", "assign"),
        "leadership": VIEW,
        **_operational_base(),
    },
    "community-coordinator": {
        "membership": _actions("view", "create", "update", "submit", "export"),
        "volunteers": _actions(
            "view", "create", "update", "submit", "export", "assign"
        ),
        "beneficiaries": _actions("view", "create", "update", "submit", "export"),
        "partners": _actions("view", "create", "update", "submit", "export"),
        "programmes": _actions("view", "create", "update", "submit", "export"),
        "projects": _actions("view", "create", "update", "submit", "export"),
        "meal": _actions("view", "create", "update", "submit", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "approvals": _actions("view"),
        "leadership": VIEW,
        **_operational_base(),
    },
    "team-leader": {
        "membership": _actions("view", "create", "update", "submit", "export"),
        "volunteers": _actions("view", "create", "update", "submit", "export"),
        "beneficiaries": _actions("view", "create", "update", "submit", "export"),
        "programmes": _actions("view", "create", "update", "submit", "export"),
        "projects": _actions("view", "create", "update", "submit", "export"),
        "meal": _actions("view", "create", "update", "submit", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "approvals": VIEW,
        **_operational_base(),
    },
    "programme-manager": {
        "programmes": _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        ),
        "projects": _actions(
            "view", "create", "update", "submit", "archive", "export", "assign"
        ),
        "meal": _actions("view", "create", "update", "submit", "archive", "export"),
        "beneficiaries": _actions("view", "create", "update", "submit", "export"),
        "partners": _actions("view", "create", "update", "submit", "export", "assign"),
        "membership": _actions("view", "create", "update", "submit", "export"),
        "volunteers": _actions("view", "create", "update", "submit", "export"),
        "reports": _actions("view", "create", "update", "submit", "approve", "export"),
        "approvals": _actions("view", "approve", "reject", "assign"),
        "governance": VIEW,
        **_operational_base(),
    },
    "project-manager": {
        "projects": _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        ),
        "programmes": _actions("view", "create", "update", "submit", "export"),
        "meal": _actions("view", "create", "update", "submit", "export"),
        "beneficiaries": _actions("view", "create", "update", "submit", "export"),
        "reports": _actions("view", "create", "update", "submit", "approve", "export"),
        "approvals": _actions("view", "approve", "reject", "assign"),
        "governance": VIEW,
        **_operational_base(),
    },
    "project-officer": {
        "projects": _actions("view", "create", "update", "submit", "export"),
        "programmes": _actions("view", "create", "update", "submit", "export"),
        "meal": _actions("view", "create", "update", "submit", "export"),
        "beneficiaries": _actions("view", "create", "update", "submit", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        **_officer_base(),
    },
    "meal-officer": {
        "meal": _actions(
            "view", "create", "update", "submit", "archive", "restore", "export"
        ),
        "programmes": _actions("view", "create", "update", "submit", "export"),
        "projects": _actions("view", "create", "update", "submit", "export"),
        "beneficiaries": _actions("view", "create", "update", "submit", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        **_officer_base(),
    },
    "finance-officer": {
        "finance": _actions(
            "view", "create", "update", "submit", "approve", "archive", "export"
        ),
        "partners": _actions("view", "create", "update", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "registers": _actions("view", "create", "update", "export"),
        "approvals": _actions("view"),
        **_officer_base(),
    },
    "membership-officer": {
        "membership": _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "archive",
            "restore",
            "export",
            "assign",
            "verify",
            "review",
            "approve",
            "reject",
            "renew",
            "suspend",
            "terminate",
            "transfer",
            "waive",
            "record_payment",
            "verify_payment",
            "issue_card",
            "view_confidential",
            "manage_attendance",
            "manage_participation",
            "manage_leave",
            "manage_exit",
            "configure",
            "manage",
        ),
        "volunteers": _actions("view", "create", "update", "submit", "export"),
        "registers": _actions("view", "create", "update", "delete", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "approvals": _actions("view", "assign"),
        **_officer_base(),
    },
    "volunteer-officer": {
        "volunteers": _actions(
            "view",
            "create",
            "update",
            "delete",
            "archive",
            "restore",
            "export",
            "assign",
            "manage_attendance",
            "manage_training",
            "manage_performance",
            "manage_leave",
            "manage_exit",
            "manage_activity",
            "manage_disciplinary",
            "manage_communications",
            "manage_documents",
            "manage",
        ),
        "membership": _actions("view", "create", "update", "submit", "export"),
        "registers": _actions("view", "create", "update", "delete", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "approvals": _actions("view", "assign"),
        **_officer_base(),
    },
    "communications-officer": {
        "communications": _actions(
            "view",
            "create",
            "update",
            "delete",
            "publish",
            "archive",
            "export",
            "manage",
        ),
        "documents": _actions(
            "view", "create", "update", "upload", "download", "archive", "export"
        ),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "meetings": _actions("view", "create", "update", "export"),
        **_officer_base(),
    },
    "training-officer": {
        "membership": _actions("view", "create", "update", "submit", "export"),
        "volunteers": _actions("view", "create", "update", "submit", "export"),
        "leadership": _actions("view", "create", "update", "export"),
        "registers": _actions("view", "create", "update", "delete", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        **_officer_base(),
    },
    "research-officer": {
        "meal": _actions("view", "create", "update", "submit", "export"),
        "programmes": _actions("view", "create", "update", "export"),
        "projects": _actions("view", "create", "update", "export"),
        "registers": _actions("view", "create", "update", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "documents": _actions(
            "view", "create", "update", "upload", "download", "export"
        ),
        **_officer_base(),
    },
    "partnerships-officer": {
        "partners": _actions(
            "view",
            "create",
            "update",
            "delete",
            "submit",
            "archive",
            "restore",
            "export",
            "assign",
            "manage",
        ),
        "finance": _actions("view", "export"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "registers": _actions("view", "create", "update", "delete", "export"),
        "approvals": _actions("view", "assign"),
        "communications": _actions("view", "create", "update", "export"),
        **_officer_base(),
    },
    "resource-mobilization-officer": {
        "finance": _actions("view", "create", "update", "submit", "export"),
        "partners": _actions("view", "create", "update", "submit", "export", "assign"),
        "reports": _actions("view", "create", "update", "submit", "export"),
        "registers": _actions("view", "create", "update", "export"),
        "approvals": _actions("view"),
        **_officer_base(),
    },
    "guest": {
        "dashboard": VIEW,
        "notifications": _actions("view"),
    },
}


class RoleSeed:
    """Plain-data description of a default role."""

    def __init__(
        self,
        slug: str,
        name: str,
        description: str,
        priority: int,
        is_system: bool,
    ) -> None:
        self.slug = slug
        self.name = name
        self.description = description
        self.priority = priority
        self.is_system = is_system


DEFAULT_ROLES: tuple[RoleSeed, ...] = (
    RoleSeed(
        "super-administrator",
        "Super Administrator",
        "Unrestricted platform administration and configuration.",
        10,
        True,
    ),
    RoleSeed(
        "system-administrator",
        "System Administrator",
        "Technical administration of the platform.",
        20,
        True,
    ),
    RoleSeed(
        "board-chairperson",
        "Board Chairperson",
        "Chairs the Board of Trustees and leads governance oversight.",
        30,
        False,
    ),
    RoleSeed(
        "board-secretary",
        "Board Secretary",
        "Records and administers board meetings and governance records.",
        40,
        False,
    ),
    RoleSeed(
        "board-member",
        "Board Member",
        "Provides governance oversight and decision-making.",
        50,
        False,
    ),
    RoleSeed(
        "president",
        "President",
        "Overall organizational leadership and representation.",
        60,
        False,
    ),
    RoleSeed(
        "vice-president",
        "Vice President",
        "Supports the President and acts in their absence.",
        70,
        False,
    ),
    RoleSeed(
        "executive-director",
        "Executive Director",
        "Chief executive responsible for day-to-day operations.",
        80,
        False,
    ),
    RoleSeed(
        "executive-secretary",
        "Executive Secretary",
        "Administrative head supporting executive governance.",
        90,
        False,
    ),
    RoleSeed(
        "secretary-general",
        "Secretary General",
        "Coordinates the National Executive Committee and secretariat.",
        100,
        False,
    ),
    RoleSeed(
        "nec-member",
        "National Executive Committee Member",
        "Member of the National Executive Committee.",
        110,
        False,
    ),
    RoleSeed(
        "director",
        "Director",
        "Leads a directorate and reports to the Executive Director.",
        120,
        False,
    ),
    RoleSeed(
        "deputy-director",
        "Deputy Director",
        "Deputises for a Director and oversees programmes.",
        130,
        False,
    ),
    RoleSeed(
        "regional-coordinator",
        "Regional Coordinator",
        "Coordinates implementation within an assigned region.",
        140,
        False,
    ),
    RoleSeed(
        "district-coordinator",
        "District Coordinator",
        "Coordinates implementation within an assigned district.",
        150,
        False,
    ),
    RoleSeed(
        "community-coordinator",
        "Community Coordinator",
        "Coordinates implementation within an assigned community.",
        160,
        False,
    ),
    RoleSeed(
        "team-leader",
        "Team Leader",
        "Leads a delivery team within a community.",
        170,
        False,
    ),
    RoleSeed(
        "programme-manager",
        "Programme Manager",
        "Manages the delivery of one or more programmes.",
        180,
        False,
    ),
    RoleSeed(
        "project-manager",
        "Project Manager",
        "Manages the delivery of one or more projects.",
        190,
        False,
    ),
    RoleSeed(
        "project-officer",
        "Project Officer",
        "Implements project activities and reports on progress.",
        200,
        False,
    ),
    RoleSeed(
        "meal-officer",
        "MEAL Officer",
        "Manages monitoring, evaluation, accountability and learning.",
        210,
        False,
    ),
    RoleSeed(
        "finance-officer",
        "Finance Officer",
        "Manages financial records, budgets and reporting.",
        220,
        False,
    ),
    RoleSeed(
        "membership-officer",
        "Membership Officer",
        "Manages membership registration and administration.",
        230,
        False,
    ),
    RoleSeed(
        "volunteer-officer",
        "Volunteer Officer",
        "Manages volunteer recruitment, deployment and records.",
        240,
        False,
    ),
    RoleSeed(
        "communications-officer",
        "Communications Officer",
        "Manages communications, media and public relations.",
        250,
        False,
    ),
    RoleSeed(
        "training-officer",
        "Training Officer",
        "Manages training and capacity development.",
        260,
        False,
    ),
    RoleSeed(
        "research-officer",
        "Research Officer",
        "Supports research, innovation and knowledge management.",
        270,
        False,
    ),
    RoleSeed(
        "partnerships-officer",
        "Partnerships Officer",
        "Manages partners, sponsors, donors and stakeholders.",
        280,
        False,
    ),
    RoleSeed(
        "resource-mobilization-officer",
        "Resource Mobilization Officer",
        "Mobilizes financial and non-financial resources.",
        290,
        False,
    ),
    RoleSeed(
        "guest",
        "Guest",
        "Limited read-only access for guests and external stakeholders.",
        300,
        True,
    ),
)


def expand_role_permissions(spec: dict[str, frozenset[str]]) -> tuple[str, ...]:
    """
    Resolve a role permission spec into the sorted tuple of permission codes.

    A category key of ``"*"`` expands to every category in the catalogue.
    Requested actions that do not exist in the catalogue are ignored, which
    keeps the seed resilient to catalogue refinements.
    """
    codes: set[str] = set()
    for category, actions in spec.items():
        categories = PERMISSION_CATEGORIES.keys() if category == "*" else (category,)
        for current_category in categories:
            available = PERMISSION_CATEGORIES[current_category][1]
            for action in actions:
                if action in available:
                    codes.add(f"{current_category}.{action}")
    return tuple(sorted(codes))


def permission_name(category_label: str, action: str) -> str:
    """Human-readable permission name derived from the catalogue."""
    return f"{category_label} · {action.replace('_', ' ').title()}"
