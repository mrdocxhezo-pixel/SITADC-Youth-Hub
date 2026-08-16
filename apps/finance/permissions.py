"""Finance Engine permissions."""

from __future__ import annotations

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.http import HttpRequest
from guardian.shortcuts import get_objects_for_user
from typing import Iterable, TypeVar

from apps.rbac.models import Role
from apps.rbac.utils import get_organization_from_request

User = get_user_model()
T = TypeVar("T", bound=Model)


def user_can_access_finance(user: User) -> bool:
    """
    Check if user can access finance module.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can access finance module, False otherwise.
    """
    return user.has_perm("finance.view_financialaccount")


def user_can_manage_finance(user: User) -> bool:
    """
    Check if user can manage finance module.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can manage finance module, False otherwise.
    """
    return user.has_perm("finance.change_financialaccount")


def user_can_view_financial_reports(user: User) -> bool:
    """
    Check if user can view financial reports.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can view financial reports, False otherwise.
    """
    return user.has_perm("finance.view_financialreport")


def user_can_manage_budgets(user: User) -> bool:
    """
    Check if user can manage budgets.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can manage budgets, False otherwise.
    """
    return user.has_perm("finance.change_budget")


def user_can_view_budgets(user: User) -> bool:
    """
    Check if user can view budgets.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can view budgets, False otherwise.
    """
    return user.has_perm("finance.view_budget")


def user_can_manage_transactions(user: User) -> bool:
    """
    Check if user can manage transactions.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can manage transactions, False otherwise.
    """
    return user.has_perm("finance.change_transaction")


def user_can_view_transactions(user: User) -> bool:
    """
    Check if user can view transactions.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can view transactions, False otherwise.
    """
    return user.has_perm("finance.view_transaction")


def user_can_manage_grants(user: User) -> bool:
    """
    Check if user can manage grants.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can manage grants, False otherwise.
    """
    return user.has_perm("finance.change_grant")


def user_can_view_grants(user: User) -> bool:
    """
    Check if user can view grants.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can view grants, False otherwise.
    """
    return user.has_perm("finance.view_grant")


def user_can_manage_donors(user: User) -> bool:
    """
    Check if user can manage donors.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can manage donors, False otherwise.
    """
    return user.has_perm("finance.change_donor")


def user_can_view_donors(user: User) -> bool:
    """
    Check if user can view donors.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can view donors, False otherwise.
    """
    return user.has_perm("finance.view_donor")


def user_can_manage_sponsors(user: User) -> bool:
    """
    Check if user can manage sponsors.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can manage sponsors, False otherwise.
    """
    return user.has_perm("finance.change_sponsor")


def user_can_view_sponsors(user: User) -> bool:
    """
    Check if user can view sponsors.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can view sponsors, False otherwise.
    """
    return user.has_perm("finance.view_sponsor")


def user_can_manage_fundraising(user: User) -> bool:
    """
    Check if user can manage fundraising campaigns.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can manage fundraising campaigns, False otherwise.
    """
    return user.has_perm("finance.change_fundraisingcampaign")


def user_can_view_fundraising(user: User) -> bool:
    """
    Check if user can view fundraising campaigns.

    Args:
        user: The user to check permissions for.

    Returns:
        bool: True if user can view fundraising campaigns, False otherwise.
    """
    return user.has_perm("finance.view_fundraisingcampaign")


def get_accessible_financial_accounts(user: User) -> Iterable:
    """
    Get financial accounts accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Financial accounts the user can access.
    """
    FinancialAccount = django_apps.get_model("finance", "FinancialAccount")
    return get_objects_for_user(user, "finance.view_financialaccount", FinancialAccount)


def get_accessible_budgets(user: User) -> Iterable:
    """
    Get budgets accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Budgets the user can access.
    """
    Budget = django_apps.get_model("finance", "Budget")
    return get_objects_for_user(user, "finance.view_budget", Budget)


def get_accessible_transactions(user: User) -> Iterable:
    """
    Get transactions accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Transactions the user can access.
    """
    Transaction = django_apps.get_model("finance", "Transaction")
    return get_objects_for_user(user, "finance.view_transaction", Transaction)


def get_accessible_grants(user: User) -> Iterable:
    """
    Get grants accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Grants the user can access.
    """
    Grant = django_apps.get_model("finance", "Grant")
    return get_objects_for_user(user, "finance.view_grant", Grant)


def get_accessible_donors(user: User) -> Iterable:
    """
    Get donors accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Donors the user can access.
    """
    Donor = django_apps.get_model("finance", "Donor")
    return get_objects_for_user(user, "finance.view_donor", Donor)


def get_accessible_sponsors(user: User) -> Iterable:
    """
    Get sponsors accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Sponsors the user can access.
    """
    Sponsor = django_apps.get_model("finance", "Sponsor")
    return get_objects_for_user(user, "finance.view_sponsor", Sponsor)


def get_accessible_fundraising_campaigns(user: User) -> Iterable:
    """
    Get fundraising campaigns accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Fundraising campaigns the user can access.
    """
    FundraisingCampaign = django_apps.get_model("finance", "FundraisingCampaign")
    return get_objects_for_user(user, "finance.view_fundraisingcampaign", FundraisingCampaign)


class FinancePermissionMixin:
    """Mixin to add finance permission checks to views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """
        Dispatch the view with finance permission checks.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: The HTTP response.
        """
        if not user_can_access_finance(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access the finance module.")
        return super().dispatch(request, *args, **kwargs)


class FinancialAccountPermissionMixin:
    """Mixin to add financial account permission checks to views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """
        Dispatch the view with financial account permission checks.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: The HTTP response.
        """
        if not user_can_access_finance(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access financial accounts.")
        return super().dispatch(request, *args, **kwargs)


class BudgetPermissionMixin:
    """Mixin to add budget permission checks to views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """
        Dispatch the view with budget permission checks.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: The HTTP response.
        """
        if not user_can_view_budgets(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access budgets.")
        return super().dispatch(request, *args, **kwargs)


class TransactionPermissionMixin:
    """Mixin to add transaction permission checks to views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """
        Dispatch the view with transaction permission checks.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: The HTTP response.
        """
        if not user_can_view_transactions(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access transactions.")
        return super().dispatch(request, *args, **kwargs)