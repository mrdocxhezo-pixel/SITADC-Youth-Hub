"""Fail-closed, permission-aware selectors for the Enterprise Search module."""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

from .constants import (
    AUDIT_LOG_LIMIT,
    ENTITY_TYPE_KEYS,
    ENTITY_TYPE_LABELS,
    RECENT_SEARCH_LIMIT,
    SAVED_SEARCH_LIMIT,
)
from .models import RecentSearch, SavedSearch, SearchQueryLog
from .permissions import SEARCH_MANAGE, SEARCH_VIEW
from .providers import registry


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def available_entity_type_keys(user) -> list[str]:
    """Entity type keys the actor may search, in catalogue order."""
    if not _authenticated(user):
        return []
    allowed = {provider.key for provider in registry.available(user)}
    return [key for key in ENTITY_TYPE_KEYS if key in allowed]


def available_entity_type_choices(user) -> list[tuple[str, str]]:
    keys = available_entity_type_keys(user)
    return [(key, ENTITY_TYPE_LABELS.get(key, key)) for key in keys]


def recent_searches_for_user(
    user, *, limit: int = RECENT_SEARCH_LIMIT
) -> list[RecentSearch]:
    """The actor's recent searches, most recent first."""
    if not _authenticated(user):
        return RecentSearch.objects.none()
    return RecentSearch.objects.filter(user=user).order_by("-created_at")[:limit]


def saved_searches_for_user(
    user, *, limit: int = SAVED_SEARCH_LIMIT
) -> list[SavedSearch]:
    """Named searches saved by the actor, alphabetical."""
    if not _authenticated(user):
        return SavedSearch.objects.none()
    return SavedSearch.objects.filter(user=user).order_by("name", "-created_at")[:limit]


def recent_search_by_query(user, query: str) -> RecentSearch | None:
    return (
        RecentSearch.objects.filter(user=user, query=query)
        .order_by("-created_at")
        .first()
    )


def saved_search_for_user(user, pk) -> SavedSearch | None:
    return SavedSearch.objects.filter(user=user, pk=pk).first()


def query_logs(user, *, limit: int = AUDIT_LOG_LIMIT) -> list[SearchQueryLog]:
    """Recent search audit rows.

    Only managers may read the global trail; for others the result is the
    empty queryset (fail-closed).
    """
    if not _authenticated(user):
        return SearchQueryLog.objects.none()
    if not (user.is_superuser or user_has_permission(user, SEARCH_MANAGE)):
        return SearchQueryLog.objects.none()
    return SearchQueryLog.objects.order_by("-created_at")[:limit]


def user_can_access_search(user) -> bool:
    """Whether the actor may open the search page."""
    if not _authenticated(user):
        return False
    if user.is_superuser:
        return True
    return any(user_has_permission(user, code) for code in (SEARCH_VIEW, SEARCH_MANAGE))
