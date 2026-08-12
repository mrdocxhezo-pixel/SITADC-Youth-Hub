"""Base class and registry for Enterprise Search providers.

A provider knows how to search exactly one entity type, delegating permission
scoping to the source module's fail-closed selectors.  Providers declare the
fields searched, the fields displayed and a canonical deep link to the source
record.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from django.db.models import Q, QuerySet
from django.urls import reverse
from django.utils.text import capfirst

from apps.rbac.authorization import user_has_permission


@dataclass(frozen=True)
class SearchHit:
    """A single rendered result from one provider."""

    key: str
    label: str
    object_id: str
    title: str
    subtitle: str
    reference: str
    status: str
    url: str | None


class SearchProvider(ABC):
    """Base contract implemented by every source entity provider."""

    key: str = ""
    label: str = ""
    model = None
    detail_url_name: str | None = None
    view_permissions: tuple[str, ...] = ()
    manage_permissions: tuple[str, ...] = ()
    search_fields: tuple[str, ...] = ()
    title_field: str = "title"
    subtitle_fields: tuple[str, ...] = ()
    reference_field: str = "reference_number"
    status_field: str = "status"

    # ------------------------------------------------------------------ #
    # Permission gates
    # ------------------------------------------------------------------ #
    def is_available(self, user) -> bool:
        """Whether this entity can ever be surfaced to the actor."""
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if getattr(user, "is_superuser", False):
            return True
        if any(user_has_permission(user, code) for code in self.manage_permissions):
            return True
        return any(user_has_permission(user, code) for code in self.view_permissions)

    # ------------------------------------------------------------------ #
    # Query scoping (must be fail-closed)
    # ------------------------------------------------------------------ #
    @abstractmethod
    def queryset(self, user) -> QuerySet:
        """Return the permission-scaled queryset for this entity."""

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #
    def _get_value(self, instance: Any, field: str) -> str:
        value = instance
        for part in field.split("__"):
            value = getattr(value, part, None)
            if value is None:
                return ""
        if callable(value):
            value = value()
        return str(value) if value not in (None, "") else ""

    def status_label(self, instance: Any) -> str:
        value = self._get_value(instance, self.status_field)
        if value and hasattr(instance, f"get_{self.status_field}_display"):
            return str(getattr(instance, f"get_{self.status_field}_display")())
        return value

    def title_value(self, instance: Any) -> str:
        """Resolve the hit title; subclasses may override for joined fields."""
        return self._get_value(instance, self.title_field) or str(instance)

    def subtitle(self, instance: Any) -> str:
        parts = [
            self._get_value(instance, field)
            for field in self.subtitle_fields
            if self._get_value(instance, field)
        ]
        return " - ".join(parts) or capfirst(self.label)

    def url_for(self, instance: Any) -> str | None:
        if not self.detail_url_name:
            return None
        obj_id = getattr(instance, "pk", None)
        if obj_id is None:
            return None
        return reverse(self.detail_url_name, args=[obj_id])

    def hit(self, instance: Any) -> SearchHit:
        title = self.title_value(instance) or str(instance)
        return SearchHit(
            key=self.key,
            label=str(self.label),
            object_id=str(getattr(instance, "pk", "")),
            title=title,
            subtitle=self.subtitle(instance),
            reference=self._get_value(instance, self.reference_field),
            status=self.status_label(instance),
            url=self.url_for(instance),
        )

    # ------------------------------------------------------------------ #
    # Search execution
    # ------------------------------------------------------------------ #
    def search(self, user, query: str, *, limit: int = 5) -> list[SearchHit]:
        """Run an icontains search over the scoped queryset."""
        if not query or not self.is_available(user):
            return []
        qs = self.queryset(user)
        if qs is None:
            return []
        combined = Q()
        for field in self.search_fields:
            combined |= Q(**{f"{field}__icontains": query})
        matches = qs.filter(combined).distinct()[:limit]
        return [self.hit(instance) for instance in matches]


class Registry:
    """In-memory catalogue of registered search providers."""

    def __init__(self) -> None:
        self._providers: dict[str, SearchProvider] = {}

    def register(self, provider: SearchProvider) -> SearchProvider:
        """Register a provider under its entity type key."""
        if not provider.key:
            raise ValueError("Provider key is required.")
        if provider.key in self._providers:
            raise ValueError(f"Duplicate provider key: {provider.key}")
        self._providers[provider.key] = provider
        return provider

    def all(self) -> list[SearchProvider]:
        return list(self._providers.values())

    def get(self, key: str) -> SearchProvider | None:
        return self._providers.get(key)

    def keys(self) -> tuple[str, ...]:
        return tuple(self._providers.keys())

    def subsets(self, keys: list[str]) -> list[SearchProvider]:
        """Providers for the given entity type keys (unknown keys ignored)."""
        seen: set[str] = set()
        providers: list[SearchProvider] = []
        for key in keys:
            provider = self._providers.get(key)
            if provider is not None and key not in seen:
                seen.add(key)
                providers.append(provider)
        return providers

    def available(self, user, keys: list[str] | None = None) -> list[SearchProvider]:
        """Providers the actor may search, optionally restricted to keys."""
        providers = self.subsets(keys) if keys else list(self._providers.values())
        return [p for p in providers if p.is_available(user)]


registry = Registry()


def register(provider: SearchProvider) -> SearchProvider:
    """Module-level decorator helper mirroring Django's app registry."""
    return registry.register(provider)
