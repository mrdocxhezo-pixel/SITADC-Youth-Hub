from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet that filters out soft-deleted records by default.
    """

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)

    def delete(self):
        """Soft delete the queryset records."""
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently delete the queryset records."""
        return super().delete()


class SoftDeleteManager(models.Manager):
    """
    Manager that uses SoftDeleteQuerySet.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        """Return all records, including soft-deleted ones."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted(self):
        """Return only soft-deleted records."""
        return self.all_with_deleted().dead()


class BaseQuerySet(SoftDeleteQuerySet):
    """
    Base QuerySet extending SoftDeleteQuerySet with active/inactive filtering.
    """

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class BaseManager(SoftDeleteManager):
    """
    Base Manager that uses BaseQuerySet, filtering out soft-deleted records.
    Provides easy access to active/inactive filters.
    """

    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return BaseQuerySet(self.model, using=self._db)
