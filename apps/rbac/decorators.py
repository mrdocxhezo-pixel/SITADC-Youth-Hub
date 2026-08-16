"""
Decorators for server-side authorization on function-based views.

Authorization is always enforced on the server.  These decorators wrap
``login_required`` and fail closed (deny by default).
"""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .authorization import user_has_all_permissions, user_has_role, user_has_scope


def permission_required(*permission_codes: str, login_url=None, raise_exception=True):
    """
    Require the user to hold every listed permission (AND semantics).

    Example::

        @permission_required("administration.manage")
        def role_create(request): ...

    By default a ``PermissionDenied`` (403) is raised.  Set
    ``raise_exception=False`` to redirect to the friendly access-denied page.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=login_url)
        def _wrapped_view(request, *args, **kwargs):
            if not user_has_all_permissions(request.user, list(permission_codes)):
                if raise_exception:
                    raise PermissionDenied
                return redirect("rbac:access_denied")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def any_permission_required(
    *permission_codes: str, login_url=None, raise_exception=True
):
    """Require the user to hold at least one of the listed permissions."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=login_url)
        def _wrapped_view(request, *args, **kwargs):
            from .authorization import user_has_any_permission

            if not user_has_any_permission(request.user, list(permission_codes)):
                if raise_exception:
                    raise PermissionDenied
                return redirect("rbac:access_denied")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def role_required(*role_slugs: str, login_url=None, raise_exception=True):
    """Require the user to hold at least one of the given roles."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=login_url)
        def _wrapped_view(request, *args, **kwargs):
            if not any(user_has_role(request.user, slug) for slug in role_slugs):
                if raise_exception:
                    raise PermissionDenied
                return redirect("rbac:access_denied")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def scope_required(*scope_codes: str, login_url=None, raise_exception=True):
    """Require the user to have access to at least one of the given scopes."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=login_url)
        def _wrapped_view(request, *args, **kwargs):
            if not any(user_has_scope(request.user, code) for code in scope_codes):
                if raise_exception:
                    raise PermissionDenied
                return redirect("rbac:access_denied")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
