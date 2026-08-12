"""Provider base class and registry for the Export Engine.

Each provider knows how to collect data from exactly one source module,
delegating permission scoping to the source module's fail-closed selectors.
Providers never decide who may export; the service layer combines the export
permission, the source permission, the format permission and sensitivity
rules before a provider is invoked.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from django.db.models import QuerySet
from django.utils.text import capfirst

from apps.rbac.authorization import user_has_permission

from ..constants import (
    SENSITIVE_SOURCE_TYPES,
    ConfidentialityLevel,
    ExportSourceType,
)
from ..permissions import user_can_export_sensitive
from ..renderers.base import ExportColumn, ExportDataset


class BaseProvider(ABC):
    """Contract implemented by every source-type provider.

    Subclasses declare a unique ``key``, the ``source_type`` they serve and
    the full catalogue of exportable columns.  ``queryset`` must be fail-closed
    (delegate to the source module's permission-scaled selectors).
    """

    key: str = ""
    source_type: str = ExportSourceType.REPORT
    label: str = ""
    model = None
    columns_catalogue: tuple[ExportColumn, ...] = ()
    view_permissions: tuple[str, ...] = ()
    manage_permissions: tuple[str, ...] = ()
    reference_field: str = "reference_number"
    status_field: str = "status"

    # ------------------------------------------------------------------ #
    # Permissions
    # ------------------------------------------------------------------ #
    def is_available(self, user) -> bool:
        """Whether the actor may ever see this provider's data."""
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if getattr(user, "is_superuser", False):
            return True
        if any(user_has_permission(user, code) for code in self.manage_permissions):
            return True
        return any(user_has_permission(user, code) for code in self.view_permissions)

    def can_export_sensitive(self, user) -> bool:
        """Whether the actor may include columns marked sensitive."""
        if getattr(user, "is_superuser", False):
            return True
        return user_can_export_sensitive(user)

    # ------------------------------------------------------------------ #
    # Queryset (must be fail-closed)
    # ------------------------------------------------------------------ #
    @abstractmethod
    def queryset(self, user) -> QuerySet:
        """Return the permission-scaled queryset for this source."""

    # ------------------------------------------------------------------ #
    # Columns
    # ------------------------------------------------------------------ #
    def columns(self, user, *, include_sensitive: bool = False) -> list[ExportColumn]:
        """The columns the actor may include.

        Sensitive columns are dropped unless the actor holds the sensitive
        export permission.
        """
        if include_sensitive or self.can_export_sensitive(user):
            return list(self.columns_catalogue)
        return [column for column in self.columns_catalogue if not column.sensitive]

    def column_keys(self, user, *, include_sensitive: bool = False) -> list[str]:
        return [
            column.key
            for column in self.columns(user, include_sensitive=include_sensitive)
        ]

    # ------------------------------------------------------------------ #
    # Value rendering helpers
    # ------------------------------------------------------------------ #
    def _resolve_value(self, instance: Any, column: ExportColumn):
        return column.value_for(instance)

    def _rows(
        self, user, queryset: QuerySet, columns: list[ExportColumn]
    ) -> list[list]:
        rows = []
        for instance in queryset[: _max_rows()]:
            rows.append(
                [
                    self._render_cell(self._resolve_value(instance, column))
                    for column in columns
                ]
            )
        return rows

    @staticmethod
    def _render_cell(value: Any) -> Any:
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return value

    # ------------------------------------------------------------------ #
    # Dataset assembly
    # ------------------------------------------------------------------ #
    def build_dataset(
        self,
        user,
        *,
        filters: dict | None = None,
        selected_columns: list[str] | None = None,
        include_sensitive: bool = False,
    ) -> ExportDataset:
        """Build the tabular dataset for this source.

        ``selected_columns`` narrows the exported columns (unknown/sensitive
        keys are ignored).  Sensitivity is re-checked here so a malicious
        request can never bypass the caller's include_sensitive flag.
        """
        all_columns = self.columns(user, include_sensitive=include_sensitive)
        if selected_columns:
            keys = set(selected_columns)
            columns = [
                column for column in all_columns if column.key in keys
            ] or all_columns
        else:
            columns = all_columns

        queryset = self.queryset(user)
        if filters:
            queryset = self.apply_filters(queryset, filters)

        rows = self._rows(user, queryset, columns)
        dataset = ExportDataset(
            title=self.dataset_title(user),
            subtitle=self.label,
            columns=columns,
            rows=rows,
            confidentiality=self.confidentiality_for(user, queryset),
            filters=self.clean_filters(filters),
        )
        return dataset

    def apply_filters(self, queryset: QuerySet, filters: dict) -> QuerySet:
        """Apply safe filter keywords (exact matches only)."""
        allowed = set(self.column_keys(None, include_sensitive=True))
        safe = {}
        for key, value in (filters or {}).items():
            if key in allowed and value not in (None, ""):
                safe[key] = value
        if safe:
            return queryset.filter(**safe)
        return queryset

    def clean_filters(self, filters: dict | None) -> dict:
        """Serialize filters for the dataset meta block."""
        return {
            key: str(value)
            for key, value in (filters or {}).items()
            if value not in (None, "")
        }

    def confidentiality_for(self, user, queryset: QuerySet) -> str:
        """Inherit the source confidentiality classification."""
        if self.source_type in SENSITIVE_SOURCE_TYPES:
            return ConfidentialityLevel.CONFIDENTIAL
        if getattr(self.model, "_meta", None) and any(
            field.name in {"confidentiality", "confidentiality_level"}
            for field in self.model._meta.get_fields()
        ):
            return ConfidentialityLevel.INTERNAL
        return ConfidentialityLevel.INTERNAL

    def dataset_title(self, user) -> str:
        return capfirst(self.label or self.source_type)

    def to_display_value(self, instance: Any, column: ExportColumn):
        value = self._resolve_value(instance, column)
        if value is not None and hasattr(instance, f"get_{column.key}_display"):
            try:
                return str(getattr(instance, f"get_{column.key}_display")())
            except (AttributeError, ValueError):
                return value
        return self._render_cell(value)


def _max_rows() -> int:
    """Cap provider rows to the configured synchronous maximum."""
    from ..models import ExportConfiguration

    return ExportConfiguration.load().max_sync_rows


class Registry:
    """Catalogue of registered export providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> BaseProvider:
        if not provider.key:
            raise ValueError("Provider key is required.")
        if provider.key in self._providers:
            raise ValueError(f"Duplicate provider key: {provider.key}")
        self._providers[provider.key] = provider
        return provider

    def all(self) -> list[BaseProvider]:
        return list(self._providers.values())

    def get(self, key: str) -> BaseProvider | None:
        return self._providers.get(key)

    def keys(self) -> tuple[str, ...]:
        return tuple(self._providers.keys())

    def available(
        self, user, source_types: list[str] | None = None
    ) -> list[BaseProvider]:
        """Providers the actor may use, optionally restricted to source types."""
        providers = [
            provider
            for provider in self._providers.values()
            if (not source_types or provider.source_type in source_types)
        ]
        return [provider for provider in providers if provider.is_available(user)]


registry = Registry()


def register(provider: BaseProvider) -> BaseProvider:
    """Module-level decorator helper mirroring Django's app registry."""
    return registry.register(provider)
