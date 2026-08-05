"""
Mixins for server-side authorization on class-based views.

These mixins enforce the same fail-closed behaviour as the function
decorators but are intended for ``View`` subclasses.
"""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import redirect

from .authorization import (
    user_has_all_permissions,
    user_has_any_permission,
    user_has_role,
    user_has_scope,
)


class PermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Require the user to hold every listed permission.

    Set ``permission_required`` to a list/tuple of ``module.action`` codes.
    When ``raise_exception`` is True a 403 is raised; otherwise the user is
    redirected to the friendly access-denied page.
    """

    request: HttpRequest
    permission_required: tuple[str, ...] | str = ()
    any_permission: bool = False
    raise_exception: bool = False

    def test_func(self) -> bool:
        if not self.permission_required:
            return True

        required = self.permission_required
        perms = [required] if isinstance(required, str) else list(required)

        if self.any_permission:
            return user_has_any_permission(self.request.user, perms)
        return user_has_all_permissions(self.request.user, perms)

    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Require the user to hold at least one of the listed role slugs."""

    role_required: tuple[str, ...] = ()
    request: HttpRequest
    raise_exception = False

    def test_func(self) -> bool:
        return any(
            user_has_role(self.request.user, slug) for slug in self.role_required
        )

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied
        return redirect("core:access_denied")


class ScopeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Require the user to have access to at least one of the listed scopes."""

    scope_required: tuple[str, ...] = ()
    request: HttpRequest
    raise_exception = False

    def test_func(self) -> bool:
        return any(
            user_has_scope(self.request.user, code) for code in self.scope_required
        )

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied
        return redirect("core:access_denied")
