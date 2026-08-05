"""Custom managers and querysets for the organizational structure module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from apps.core.managers import SoftDeleteManager

if TYPE_CHECKING:
    from .models import OrganizationUnit, Position  # noqa: F401

from .constants import PositionStatus, UnitStatus


class OrganizationUnitQuerySet(models.QuerySet):
    """QuerySet helpers for organizational units."""

    def active(self) -> OrganizationUnitQuerySet:
        """Return units that are currently active."""
        return self.filter(status=UnitStatus.ACTIVE)

    def roots(self) -> OrganizationUnitQuerySet:
        """Return top-level units (no parent)."""
        return self.filter(parent__isnull=True)

    def of_type(self, unit_type: str) -> OrganizationUnitQuerySet:
        """Return units of the given ``UnitType`` value."""
        return self.filter(unit_type=unit_type)

    def with_parent(self) -> OrganizationUnitQuerySet:
        """Eager-load the parent and level for hierarchy rendering."""
        return self.select_related("parent", "level", "unit_head")


class OrganizationUnitManager(SoftDeleteManager["OrganizationUnit"]):
    """Default manager for ``OrganizationUnit``."""

    def get_queryset(self) -> OrganizationUnitQuerySet:
        return OrganizationUnitQuerySet(self.model, using=self._db)

    def active(self) -> OrganizationUnitQuerySet:
        return self.get_queryset().active()

    def roots(self) -> OrganizationUnitQuerySet:
        return self.get_queryset().roots()

    def of_type(self, unit_type: str) -> OrganizationUnitQuerySet:
        return self.get_queryset().of_type(unit_type)

    def with_parent(self) -> OrganizationUnitQuerySet:
        return self.get_queryset().with_parent()


class PositionQuerySet(models.QuerySet):
    """QuerySet helpers for positions."""

    def active(self) -> PositionQuerySet:
        return self.filter(status=PositionStatus.ACTIVE)

    def with_unit(self) -> PositionQuerySet:
        return self.select_related("organizational_unit", "classification")


class PositionManager(SoftDeleteManager["Position"]):
    """Default manager for ``Position``."""

    def get_queryset(self) -> PositionQuerySet:
        return PositionQuerySet(self.model, using=self._db)

    def active(self) -> PositionQuerySet:
        return self.get_queryset().active()

    def with_unit(self) -> PositionQuerySet:
        return self.get_queryset().with_unit()
