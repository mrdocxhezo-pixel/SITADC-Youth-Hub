"""Finance Engine permissions.

The ``finance.*`` catalogue supplements Django model-level permissions.
Every finance view must satisfy the finance permission before data is exposed.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.http import HttpRequest

from apps.rbac.authorization import user_has_permission

User = get_user_model()

FINANCE_VIEW = "finance.view"
FINANCE_CREATE = "finance.create"
FINANCE_UPDATE = "finance.update"
FINANCE_DELETE = "finance.delete"
FINANCE_APPROVE = "finance.approve"
FINANCE_ARCHIVE = "finance.archive"
FINANCE_RESTORE = "finance.restore"
FINANCE_EXPORT = "finance.export"
FINANCE_MANAGE = "finance.manage"


def _has(user: Any, *codes: str) -> bool:
    """Fail-closed check for any of the given permission codes."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return any(user_has_permission(user, code) for code in codes)


def user_can_access_finance(user) -> bool:
    """Whether the actor may open the finance workspace."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


def user_can_manage_finance(user) -> bool:
    """Whether the actor holds the master finance-management permission."""
    return _has(user, FINANCE_MANAGE)


def user_can_view_financial_reports(user) -> bool:
    """Whether the actor may view financial reports."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


def user_can_manage_budgets(user) -> bool:
    """Whether the actor may create or update budgets."""
    return _has(user, FINANCE_CREATE, FINANCE_UPDATE, FINANCE_MANAGE)


def user_can_view_budgets(user) -> bool:
    """Whether the actor may view budgets."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


def user_can_manage_transactions(user) -> bool:
    """Whether the actor may create or update transactions."""
    return _has(user, FINANCE_CREATE, FINANCE_UPDATE, FINANCE_MANAGE)


def user_can_view_transactions(user) -> bool:
    """Whether the actor may view transactions."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


def user_can_manage_grants(user) -> bool:
    """Whether the actor may create or update grants."""
    return _has(user, FINANCE_CREATE, FINANCE_UPDATE, FINANCE_MANAGE)


def user_can_view_grants(user) -> bool:
    """Whether the actor may view grants."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


def user_can_manage_donors(user) -> bool:
    """Whether the actor may create or update donors."""
    return _has(user, FINANCE_CREATE, FINANCE_UPDATE, FINANCE_MANAGE)


def user_can_view_donors(user) -> bool:
    """Whether the actor may view donors."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


def user_can_manage_sponsors(user) -> bool:
    """Whether the actor may create or update sponsors."""
    return _has(user, FINANCE_CREATE, FINANCE_UPDATE, FINANCE_MANAGE)


def user_can_view_sponsors(user) -> bool:
    """Whether the actor may view sponsors."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


def user_can_manage_fundraising(user) -> bool:
    """Whether the actor may create or update fundraising campaigns."""
    return _has(user, FINANCE_CREATE, FINANCE_UPDATE, FINANCE_MANAGE)


def user_can_view_fundraising(user) -> bool:
    """Whether the actor may view fundraising campaigns."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


def user_can_export_finance(user) -> bool:
    """Whether the actor may export finance data."""
    return _has(user, FINANCE_EXPORT, FINANCE_MANAGE)


def user_can_approve_finance(user) -> bool:
    """Whether the actor may approve financial transactions."""
    return _has(user, FINANCE_APPROVE, FINANCE_MANAGE)


def get_accessible_financial_accounts(user):
    """Financial accounts the actor may view (module-level scope)."""
    from apps.finance.models import FinancialAccount

    if not user_can_view_finance_data(user):
        return FinancialAccount.objects.none()
    return FinancialAccount.objects.all()


def get_accessible_bank_accounts(user):
    """Bank accounts the actor may view."""
    from apps.finance.models import BankAccount

    if not user_can_view_finance_data(user):
        return BankAccount.objects.none()
    return BankAccount.objects.all()


def get_accessible_petty_cash_accounts(user):
    """Petty cash accounts the actor may view."""
    from apps.finance.models import PettyCash

    if not user_can_view_finance_data(user):
        return PettyCash.objects.none()
    return PettyCash.objects.all()


def get_accessible_budgets(user):
    """Budgets the actor may view."""
    from apps.finance.models import Budget

    if not user_can_view_budgets(user):
        return Budget.objects.none()
    return Budget.objects.all()


def get_accessible_transactions(user):
    """Transactions the actor may view."""
    from apps.finance.models import Transaction

    if not user_can_view_transactions(user):
        return Transaction.objects.none()
    return Transaction.objects.all()


def get_accessible_grants(user):
    """Grants the actor may view."""
    from apps.finance.models import Grant

    if not user_can_view_grants(user):
        return Grant.objects.none()
    return Grant.objects.all()


def get_accessible_donors(user):
    """Donors the actor may view."""
    from apps.finance.models import Donor

    if not user_can_view_donors(user):
        return Donor.objects.none()
    return Donor.objects.all()


def get_accessible_sponsors(user):
    """Sponsors the actor may view."""
    from apps.finance.models import Sponsor

    if not user_can_view_sponsors(user):
        return Sponsor.objects.none()
    return Sponsor.objects.all()


def get_accessible_fundraising_campaigns(user):
    """Fundraising campaigns the actor may view."""
    from apps.finance.models import FundraisingCampaign

    if not user_can_view_fundraising(user):
        return FundraisingCampaign.objects.none()
    return FundraisingCampaign.objects.all()


def user_can_view_finance_data(user) -> bool:
    """Whether the actor may view core finance records (accounts, ledgers)."""
    return _has(user, FINANCE_VIEW, FINANCE_MANAGE)


class FinancePermissionMixin:
    """Mixin to add finance permission checks to class-based views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        if not user_can_access_finance(request.user):
            raise PermissionDenied(
                "You do not have permission to access the finance module."
            )
        return super().dispatch(request, *args, **kwargs)


class FinancialAccountPermissionMixin:
    """Mixin to add financial account permission checks to class-based views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        if not user_can_access_finance(request.user):
            raise PermissionDenied(
                "You do not have permission to access financial accounts."
            )
        return super().dispatch(request, *args, **kwargs)


class BudgetPermissionMixin:
    """Mixin to add budget permission checks to class-based views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        if not user_can_view_budgets(request.user):
            raise PermissionDenied("You do not have permission to access budgets.")
        return super().dispatch(request, *args, **kwargs)


class TransactionPermissionMixin:
    """Mixin to add transaction permission checks to class-based views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        if not user_can_view_transactions(request.user):
            raise PermissionDenied("You do not have permission to access transactions.")
        return super().dispatch(request, *args, **kwargs)
