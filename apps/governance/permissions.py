"""Governance, Risk, Compliance and Safeguarding permissions.

The ``governance.*`` catalogue supplements Django model-level permissions.
Every governance view must satisfy the relevant governance permission before
data is exposed, and confidential records additionally require the
``governance.view_confidential`` permission.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.http import HttpRequest

from apps.rbac.authorization import user_has_permission

User = get_user_model()

GOVERNANCE_VIEW = "governance.view"
GOVERNANCE_CREATE = "governance.create"
GOVERNANCE_UPDATE = "governance.update"
GOVERNANCE_DELETE = "governance.delete"
GOVERNANCE_APPROVE = "governance.approve"
GOVERNANCE_ARCHIVE = "governance.archive"
GOVERNANCE_RESTORE = "governance.restore"
GOVERNANCE_EXPORT = "governance.export"
GOVERNANCE_MANAGE = "governance.manage"
GOVERNANCE_VIEW_CONFIDENTIAL = "governance.view_confidential"


def _has(user: Any, *codes: str) -> bool:
    """Fail-closed check for any of the given permission codes."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return any(user_has_permission(user, code) for code in codes)


def user_can_access_governance(user) -> bool:
    """Whether the actor may open the governance workspace."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_governance(user) -> bool:
    """Whether the actor holds the master governance-management permission."""
    return _has(user, GOVERNANCE_MANAGE)


def user_can_view_confidential_governance(user) -> bool:
    """Whether the actor may view highly confidential governance records."""
    return _has(user, GOVERNANCE_VIEW_CONFIDENTIAL, GOVERNANCE_MANAGE)


def user_can_view_policies(user) -> bool:
    """Whether the actor may view policy records."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_policies(user) -> bool:
    """Whether the actor may create or update policy records."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_risks(user) -> bool:
    """Whether the actor may view the enterprise risk register."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_risks(user) -> bool:
    """Whether the actor may create or update risk records."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_compliance(user) -> bool:
    """Whether the actor may view compliance records."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_compliance(user) -> bool:
    """Whether the actor may create or update compliance records."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_controls(user) -> bool:
    """Whether the actor may view internal controls."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_controls(user) -> bool:
    """Whether the actor may create or update internal controls."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_ethics(user) -> bool:
    """Whether the actor may view ethics cases."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_ethics(user) -> bool:
    """Whether the actor may create or update ethics cases."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_safeguarding(user) -> bool:
    """Whether the actor may view safeguarding cases."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_VIEW_CONFIDENTIAL, GOVERNANCE_MANAGE)


def user_can_manage_safeguarding(user) -> bool:
    """Whether the actor may create or update safeguarding cases."""
    return _has(
        user,
        GOVERNANCE_CREATE,
        GOVERNANCE_UPDATE,
        GOVERNANCE_VIEW_CONFIDENTIAL,
        GOVERNANCE_MANAGE,
    )


def user_can_view_incidents(user) -> bool:
    """Whether the actor may view incident reports."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_incidents(user) -> bool:
    """Whether the actor may create or update incident reports."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_complaints(user) -> bool:
    """Whether the actor may view complaints."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_complaints(user) -> bool:
    """Whether the actor may create or update complaints."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_whistleblower(user) -> bool:
    """Whether the actor may view whistleblower reports."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_VIEW_CONFIDENTIAL, GOVERNANCE_MANAGE)


def user_can_manage_whistleblower(user) -> bool:
    """Whether the actor may create or update whistleblower reports."""
    return _has(
        user,
        GOVERNANCE_CREATE,
        GOVERNANCE_UPDATE,
        GOVERNANCE_VIEW_CONFIDENTIAL,
        GOVERNANCE_MANAGE,
    )


def user_can_view_capas(user) -> bool:
    """Whether the actor may view corrective & preventive actions."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_capas(user) -> bool:
    """Whether the actor may create or update corrective & preventive actions."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_documents(user) -> bool:
    """Whether the actor may view governance documents."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_documents(user) -> bool:
    """Whether the actor may create or update governance documents."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_view_meetings(user) -> bool:
    """Whether the actor may view governance meetings."""
    return _has(user, GOVERNANCE_VIEW, GOVERNANCE_MANAGE)


def user_can_manage_meetings(user) -> bool:
    """Whether the actor may create or update governance meetings."""
    return _has(user, GOVERNANCE_CREATE, GOVERNANCE_UPDATE, GOVERNANCE_MANAGE)


def user_can_export_governance(user) -> bool:
    """Whether the actor may export governance data."""
    return _has(user, GOVERNANCE_EXPORT, GOVERNANCE_MANAGE)


def user_can_approve_governance(user) -> bool:
    """Whether the actor may approve governance records."""
    return _has(user, GOVERNANCE_APPROVE, GOVERNANCE_MANAGE)


def get_accessible_policies(user):
    """Policies the actor may view (module-level scope)."""
    from apps.governance.models import Policy

    if not user_can_view_policies(user):
        return Policy.objects.none()
    return Policy.objects.all()


def get_accessible_risks(user):
    """Risks the actor may view."""
    from apps.governance.models import RiskRegister

    if not user_can_view_risks(user):
        return RiskRegister.objects.none()
    return RiskRegister.objects.all()


def get_accessible_safeguarding_cases(user):
    """Safeguarding cases the actor may view."""
    from apps.governance.models import SafeguardingCase

    if not user_can_view_safeguarding(user):
        return SafeguardingCase.objects.none()
    return SafeguardingCase.objects.all()


def get_accessible_whistleblower_reports(user):
    """Whistleblower reports the actor may view."""
    from apps.governance.models import WhistleblowerReport

    if not user_can_view_whistleblower(user):
        return WhistleblowerReport.objects.none()
    return WhistleblowerReport.objects.all()


class GovernancePermissionMixin:
    """Mixin to add governance permission checks to class-based views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        if not user_can_access_governance(request.user):
            raise PermissionDenied(
                "You do not have permission to access the governance module."
            )
        return super().dispatch(request, *args, **kwargs)


class SafeguardingPermissionMixin:
    """Mixin to restrict safeguarding views to authorized actors."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        if not user_can_view_safeguarding(request.user):
            raise PermissionDenied(
                "You do not have permission to access safeguarding records."
            )
        return super().dispatch(request, *args, **kwargs)


class WhistleblowerPermissionMixin:
    """Mixin to restrict whistleblower views to authorized actors."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        if not user_can_view_whistleblower(request.user):
            raise PermissionDenied(
                "You do not have permission to access whistleblower records."
            )
        return super().dispatch(request, *args, **kwargs)
