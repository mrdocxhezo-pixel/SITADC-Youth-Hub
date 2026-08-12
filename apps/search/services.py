"""Service functions for the Enterprise Search module.

Handles search execution across registered providers, persistence of recent
and saved searches, and the immutable audit trail.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from .constants import (
    DEFAULT_RESULTS_PER_TYPE,
    MAX_RESULTS_PER_TYPE,
    RECENT_SEARCH_LIMIT,
)
from .exceptions import SearchPermissionDenied, SearchValidationError
from .models import RecentSearch, SavedSearch, SearchQueryLog
from .permissions import user_can_export, user_can_search
from .providers import registry
from .selectors import recent_search_by_query
from .validators import validate_entity_type_keys, validate_query


@dataclass
class SearchResults:
    """Grouped results for a single executed search."""

    query: str
    groups: list = field(default_factory=list)
    total: int = 0
    duration_ms: int = 0
    executed: bool = False
    error: str | None = None

    def counts_by_score(self) -> int:
        return self.total


@dataclass
class ResultGroup:
    """Hits produced by a single provider (one entity type)."""

    key: str
    label: str
    hits: list
    total: int


def _scope_entity_types(user, requested: list[str] | None) -> list[str]:
    """Restrict requested entity types to those the actor may search."""
    allowed = {provider.key for provider in registry.available(user)}
    if requested is None:
        return list(allowed)
    keys = validate_entity_type_keys(requested)
    return [key for key in keys if key in allowed]


def run_search(
    user,
    query: str,
    entity_types: list[str] | None = None,
    *,
    results_per_type: int = DEFAULT_RESULTS_PER_TYPE,
    persist: bool = True,
    ip_address: str | None = None,
) -> SearchResults:
    """Execute a search across the permitted providers.

    Anonymous or unauthorized actors never discover results: providers are
    filtered by their own permission gates and scoped querysets.
    """
    if not user_can_search(user):
        raise SearchPermissionDenied(_("You do not have permission to search."))

    cleaned = validate_query(query)
    limit = min(max(results_per_type, 1), MAX_RESULTS_PER_TYPE)
    keys = _scope_entity_types(user, entity_types)
    providers = registry.subsets(keys)

    started = time.perf_counter()
    results = SearchResults(query=cleaned, executed=True)
    total = 0

    for provider in providers:
        hits = provider.search(user, cleaned, limit=limit)
        total += len(hits)
        results.groups.append(
            ResultGroup(
                key=provider.key,
                label=str(provider.label),
                hits=hits,
                total=len(hits),
            )
        )

    results.duration_ms = int((time.perf_counter() - started) * 1000)
    results.total = total

    if persist:
        record_search(
            user,
            cleaned,
            [group.key for group in results.groups],
            total,
            duration_ms=results.duration_ms,
            ip_address=ip_address,
        )
    return results


def record_search(
    user,
    query: str,
    entity_types: list[str],
    result_count: int,
    *,
    duration_ms: int = 0,
    ip_address: str | None = None,
) -> None:
    """Persist the recent-search history entry and the immutable audit row.

    Recent entries are deduplicated per (user, query) and pruned to the
    configured limit.  Audit rows are append-only.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return

    existing = recent_search_by_query(user, query)
    if existing is not None:
        for key in entity_types:
            if key not in existing.entity_types:
                existing.entity_types.append(key)
        existing.result_count = result_count
        existing.save(update_fields=["entity_types", "result_count", "updated_at"])
        # Re-save not required; update timestamps via save.
    else:
        RecentSearch.objects.create(
            user=user,
            query=query,
            entity_types=entity_types,
            result_count=result_count,
        )
        # Prune to the configured cap.
        overflow = list(
            RecentSearch.objects.filter(user=user)
            .order_by("-created_at")
            .values_list("id", flat=True)[RECENT_SEARCH_LIMIT:]
        )
        if overflow:
            RecentSearch.objects.filter(id__in=overflow).delete()

    SearchQueryLog.objects.create(
        user=user,
        query=query,
        entity_types=entity_types,
        result_count=result_count,
        duration_ms=duration_ms,
        ip_address=ip_address or None,
    )


def create_saved_search(
    user,
    name: str,
    query: str,
    entity_types: list[str] | None = None,
) -> SavedSearch:
    """Save a named, reusable search owned by the actor."""
    if not user_can_search(user):
        raise SearchPermissionDenied(_("You do not have permission to save searches."))
    cleaned = validate_query(query)
    keys = _scope_entity_types(user, entity_types)
    name = name.strip()
    if not name:
        raise SearchValidationError(_("Provide a name for the saved search."))
    saved, _created = SavedSearch.objects.update_or_create(
        user=user,
        name=name,
        defaults={
            "query": cleaned,
            "entity_types": keys,
            "created_by": user,
        },
    )
    return saved


def delete_saved_search(user, saved: SavedSearch) -> None:
    """Delete a saved search owned by the actor."""
    if saved.user_id != getattr(user, "id", None):
        raise SearchPermissionDenied(_("You may only delete your own saved searches."))
    saved.delete()


def run_saved_search(user, saved: SavedSearch) -> SearchResults:
    """Re-execute a saved search."""
    return run_search(
        user,
        saved.query,
        saved.entity_types,
    )


def exportable_search(user) -> bool:
    return user_can_export(user)
