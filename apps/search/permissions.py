"""Permission constants and helpers for the Enterprise Search module.

Search is additive: ``search.view`` allows the page, ``search.export``
allows result export and ``search.manage`` administers saved searches and
the audit log.  Cross-module visibility is always governed by the source
module selectors, never by the search permission alone.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

SEARCH_VIEW = "search.view"
SEARCH_EXPORT = "search.export"
SEARCH_MANAGE = "search.manage"

VIEW_PERMISSIONS: tuple[str, ...] = (SEARCH_VIEW, SEARCH_MANAGE)
EXPORT_PERMISSIONS: tuple[str, ...] = (SEARCH_EXPORT, SEARCH_MANAGE)
MANAGE_PERMISSIONS: tuple[str, ...] = (SEARCH_MANAGE,)


def user_can_search(user) -> bool:
    return bool(user and user.is_authenticated) and any(
        user_has_permission(user, code) for code in VIEW_PERMISSIONS
    )


def user_can_export(user) -> bool:
    return bool(user and user.is_authenticated) and any(
        user_has_permission(user, code) for code in EXPORT_PERMISSIONS
    )


def user_can_manage(user) -> bool:
    return bool(user and user.is_authenticated) and user_has_permission(
        user, SEARCH_MANAGE
    )
