"""
Custom QuerySets and Managers for the volunteer management module.
"""

from __future__ import annotations

from django.db import models

from apps.core.managers import BaseManager, SoftDeleteQuerySet


class VolunteerProfileQuerySet(SoftDeleteQuerySet):
    def active(self):
        from .constants import VolunteerStatus

        return self.filter(
            status=VolunteerStatus.ACTIVE, is_deleted=False, is_archived=False
        )

    def assigned(self):
        from .constants import VolunteerStatus

        return self.filter(
            status=VolunteerStatus.ASSIGNED, is_deleted=False, is_archived=False
        )

    def by_region(self, region: str):
        return self.filter(region__iexact=region)

    def by_category(self, category):
        if hasattr(category, "code"):
            return self.filter(category=category)
        return self.filter(category__code=category)


class VolunteerProfileManager(BaseManager):
    def get_queryset(self):
        return VolunteerProfileQuerySet(self.model, using=self._db).alive()

    def active(self):
        return self.get_queryset().active()

    def assigned(self):
        return self.get_queryset().assigned()


class ImmutableVolunteerQuerySet(models.QuerySet):
    """Application-facing queryset that prevents mutation of audit records."""

    def update(self, **kwargs):
        from django.core.exceptions import ValidationError

        from .models import IMMUTABLE_VOLUNTEER_RECORD_MESSAGE

        raise ValidationError(
            IMMUTABLE_VOLUNTEER_RECORD_MESSAGE,
            code="immutable_volunteer_record",
        )

    def delete(self):
        from django.core.exceptions import ValidationError

        from .models import IMMUTABLE_VOLUNTEER_RECORD_MESSAGE

        raise ValidationError(
            IMMUTABLE_VOLUNTEER_RECORD_MESSAGE,
            code="immutable_volunteer_record",
        )


class ImmutableVolunteerManager(models.Manager):
    def get_queryset(self):
        return ImmutableVolunteerQuerySet(self.model, using=self._db)
