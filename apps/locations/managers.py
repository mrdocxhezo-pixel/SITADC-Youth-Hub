"""Custom managers / querysets for the geographic locations models."""

from django.db import models


class LocationQuerySet(models.QuerySet):
    """QuerySet with geographic-specific filters."""

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class LocationManager(models.Manager):
    """Default manager for geographic models, hiding archived/deleted rows."""

    def get_queryset(self):
        return LocationQuerySet(self.model, using=self._db).filter(
            is_archived=False
        )

    def active(self):
        return self.get_queryset().active()

    def all_including_archived(self):
        return LocationQuerySet(self.model, using=self._db)

    def archived(self):
        return LocationQuerySet(self.model, using=self._db).filter(
            is_archived=True
        )
