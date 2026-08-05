from django.db import models
from django.utils.translation import gettext_lazy as _


class RoleStatus(models.TextChoices):
    """Lifecycle status for a role."""

    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")


class AssignmentStatus(models.TextChoices):
    """Lifecycle status for a user-role assignment."""

    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    REVOKED = "REVOKED", _("Revoked")


class RoleHistoryAction(models.TextChoices):
    """Audited actions that may be recorded against a role."""

    CREATED = "CREATED", _("Created")
    UPDATED = "UPDATED", _("Updated")
    ACTIVATED = "ACTIVATED", _("Activated")
    DEACTIVATED = "DEACTIVATED", _("Deactivated")
    ARCHIVED = "ARCHIVED", _("Archived")
    RESTORED = "RESTORED", _("Restored")
    CLONED = "CLONED", _("Cloned")
    DELETED = "DELETED", _("Deleted")
    PERMISSIONS_CHANGED = "PERMISSIONS_CHANGED", _("Permissions Changed")
    ROLE_ASSIGNED = "ROLE_ASSIGNED", _("Role Assigned")
    ROLE_REVOKED = "ROLE_REVOKED", _("Role Revoked")


class AccessScopeLevel(models.IntegerChoices):
    """
    Hierarchical organizational access scopes.

    Lower numeric values represent broader (higher authority) scopes and
    therefore cover every scope with a greater value.
    """

    NATIONAL = 10, _("National")
    REGIONAL = 20, _("Regional")
    DISTRICT = 30, _("District")
    COMMUNITY = 40, _("Community")
    TEAM = 50, _("Team")
    PROGRAMME = 60, _("Programme")
    PROJECT = 70, _("Project")
