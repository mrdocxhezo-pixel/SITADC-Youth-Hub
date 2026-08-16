"""
Central authorization middleware for the SITADC Youth Hub.

The middleware remains lightweight and delegates all access decisions to the
authorization services in :mod:`apps.rbac.authorization`.  It provides:

* A ``request.rbac`` context (roles, permissions, scopes) so views, templates
  and services reuse one consistent authorization snapshot per request.
* Account-status enforcement: authenticated users whose account has been
  suspended, locked, deactivated or archived are logged out immediately,
  even if a stale session already exists.
* Authorisation-failure recording for HTTP 403 responses returned to
  authenticated users.

Templates and navigation are a usability layer only; the middleware never
replaces the server-side checks performed by decorators, mixins and services.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.accounts.constants import AccountStatus

from .authorization import (
    get_effective_permission_codes,
    get_effective_scopes_for_user,
    get_roles_for_user,
    user_has_all_permissions,
    user_has_any_permission,
    user_has_permission,
    user_has_role,
    user_has_scope,
)

logger = logging.getLogger(__name__)

# Account statuses that must never enjoy an authenticated session.
BLOCKED_ACCOUNT_STATUSES = (
    AccountStatus.SUSPENDED,
    AccountStatus.INACTIVE,
    AccountStatus.LOCKED,
    AccountStatus.ARCHIVED,
)

class AuthorizationMiddleware:
    """Attach the RBAC context and enforce active-account access."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            self._attach_rbac_context(request, user)
            blocked = self._blocked_account_response(request, user)
            if blocked is not None:
                return blocked

        response = self.get_response(request)
        self._record_authorization_failure(request, response)
        return response

    # ------------------------------------------------------------------
    # RBAC context
    # ------------------------------------------------------------------
    def _attach_rbac_context(self, request, user) -> None:
        """Attach ``request.rbac`` exposing roles, permissions and scopes.

        The context is a lazy facade over the authorization engine, so the
        middleware itself adds no database queries; values are resolved on
        first use and cached per request instance.
        """

        def permissions():
            return sorted(get_effective_permission_codes(user))

        def roles():
            return list(get_roles_for_user(user))

        def scopes():
            return list(get_effective_scopes_for_user(user))

        request.rbac = SimpleNamespace(
            user=user,
            is_superuser=bool(user.is_superuser),
            roles=roles,
            permissions=permissions,
            scopes=scopes,
            can=user_has_permission,
            can_all=lambda *codes: user_has_all_permissions(user, list(codes)),
            can_any=lambda *codes: user_has_any_permission(user, list(codes)),
            has_role=lambda slug: user_has_role(user, slug),
            has_scope=lambda code: user_has_scope(user, code),
        )

    # ------------------------------------------------------------------
    # Account-status enforcement
    # ------------------------------------------------------------------
    def _blocked_account_response(self, request, user):
        """Force-logout and redirect users with a blocked account status."""
        status = getattr(user, "status", None)
        if status not in BLOCKED_ACCOUNT_STATUSES:
            return None

        path = request.path
        login_path = self._resolve_path(settings.LOGIN_URL)
        if path == login_path:
            return None

        logout(request)
        messages.warning(
            request,
            _(
                "Your account is not active. Please contact the administrator "
                "to restore access."
            ),
        )
        login_url = (
            reverse(settings.LOGIN_URL)
            if not settings.LOGIN_URL.startswith("/")
            else settings.LOGIN_URL
        )
        logger.info(
            "Blocked authenticated session for user %s (status=%s) at %s",
            user,
            status,
            path,
        )
        return redirect(f"{login_url}?next={path}")

    @staticmethod
    def _resolve_path(url_name_or_path: str) -> str:
        """Resolve a URL name to its path, tolerating raw paths."""
        if url_name_or_path.startswith("/"):
            return url_name_or_path
        try:
            return reverse(url_name_or_path)
        except Exception:
            return url_name_or_path

    # ------------------------------------------------------------------
    # Authorization-failure recording
    # ------------------------------------------------------------------
    def _record_authorization_failure(self, request, response) -> None:
        """Log an authorization failure for authenticated users on 403."""
        user = getattr(request, "user", None)
        if response.status_code == 403 and user is not None and user.is_authenticated:
            logger.warning(
                "Authorization denied for user %s at %s",
                user,
                request.path,
            )
