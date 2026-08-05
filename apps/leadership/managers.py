"""Custom managers and querysets for the leadership management module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from apps.core.managers import SoftDeleteManager

if TYPE_CHECKING:
    from .models import LeadershipAppointment, LeadershipProfile  # noqa: F401


class LeadershipProfileQuerySet(models.QuerySet):
    """Queryset helpers for leadership profiles."""

    def active(self):
        """Return profiles currently in active or acting service."""
        from .constants import LeadershipStatus

        return self.filter(
            status__in=(LeadershipStatus.ACTIVE, LeadershipStatus.ACTING)
        )

    def by_leadership_level(self, level: str):
        """Return profiles at a given organizational leadership level."""
        return self.filter(leadership_level=level)

    def with_supervisor(self):
        """Eager-load the supervisor relationship."""
        return self.select_related("supervisor", "position", "organizational_unit")


class LeadershipProfileManager(SoftDeleteManager["LeadershipProfile"]):
    """Default manager for leadership profiles."""

    def get_queryset(self) -> LeadershipProfileQuerySet:
        return LeadershipProfileQuerySet(self.model, using=self._db)

    def active(self) -> LeadershipProfileQuerySet:
        return self.get_queryset().active()

    def by_leadership_level(self, level: str) -> LeadershipProfileQuerySet:
        return self.get_queryset().by_leadership_level(level)

    def with_supervisor(self) -> LeadershipProfileQuerySet:
        return self.get_queryset().with_supervisor()


class LeadershipAppointmentQuerySet(models.QuerySet):
    """Queryset helpers for leadership appointments."""

    def active(self):
        """Return appointments currently in active service."""
        from .constants import AppointmentStatus

        return self.filter(status=AppointmentStatus.ACTIVE)

    def expiring_between(self, start_date, end_date):
        """Return active appointments whose term ends within a window."""
        from .constants import AppointmentStatus

        return self.filter(
            status=AppointmentStatus.ACTIVE,
            term_end__gte=start_date,
            term_end__lte=end_date,
        )

    def expiring_before(self, end_date):
        """Return active appointments whose term ends before a date."""
        from .constants import AppointmentStatus

        return self.filter(status=AppointmentStatus.ACTIVE, term_end__lt=end_date)


class LeadershipAppointmentManager(SoftDeleteManager["LeadershipAppointment"]):
    """Default manager for leadership appointments."""

    def get_queryset(self) -> LeadershipAppointmentQuerySet:
        return LeadershipAppointmentQuerySet(self.model, using=self._db)

    def active(self) -> LeadershipAppointmentQuerySet:
        return self.get_queryset().active()

    def expiring_between(self, start_date, end_date) -> LeadershipAppointmentQuerySet:
        return self.get_queryset().expiring_between(start_date, end_date)

    def expiring_before(self, end_date) -> LeadershipAppointmentQuerySet:
        return self.get_queryset().expiring_before(end_date)
