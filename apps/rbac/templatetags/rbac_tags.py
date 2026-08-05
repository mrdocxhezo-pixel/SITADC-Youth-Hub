"""
Template tags that surface authorization state to templates.

Templates are a usability layer only; they never enforce security.  All
authorization decisions remain server-side.
"""

from django import template
from django.contrib.auth.models import AnonymousUser

from ..authorization import (
    get_effective_permission_codes,
    get_roles_for_user,
    user_has_permission,
    user_has_role,
    user_has_scope,
)

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Look up a key in a dict-like mapping from a template."""
    try:
        return mapping[key]
    except (KeyError, TypeError):
        return None


@register.simple_tag(takes_context=True)
def has_permission(context, permission_code: str) -> bool:
    """Whether the request user holds the given permission code."""
    user = context.request.user
    return user_has_permission(user, permission_code)


@register.filter
def has_perm(user, permission_code: str) -> bool:
    """Whether the given user holds the permission code (usable in ``{% if %}``)."""
    return user_has_permission(user, permission_code)


@register.simple_tag(takes_context=True)
def has_role(context, role_slug: str) -> bool:
    """Whether the request user holds the given role slug."""
    user = context.request.user
    return user_has_role(user, role_slug)


@register.simple_tag(takes_context=True)
def has_scope(context, scope_code: str) -> bool:
    """Whether the request user's scopes cover the given scope code."""
    user = context.request.user
    return user_has_scope(user, scope_code)


@register.simple_tag(takes_context=True)
def get_user_roles(context) -> list:
    """List of roles held by the request user (usable in templates)."""
    user = context.request.user
    if not user or isinstance(user, AnonymousUser):
        return []
    return list(get_roles_for_user(user))


@register.simple_tag(takes_context=True)
def get_user_permissions(context) -> list[str]:
    """List of effective permission codes for the request user."""
    user = context.request.user
    if not user or isinstance(user, AnonymousUser):
        return []
    return sorted(get_effective_permission_codes(user))
