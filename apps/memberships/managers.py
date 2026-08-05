"""
Custom QuerySets and Managers for the membership management module.
"""

from __future__ import annotations

from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.core.managers import BaseManager, SoftDeleteQuerySet


class MemberProfileQuerySet(SoftDeleteQuerySet):
    """QuerySet scoped to member profiles with status helpers."""

    def active(self):
        return self.filter(status__code="ACTIVE", is_deleted=False, is_archived=False)

    def suspended(self):
        return self.filter(
            status__code="SUSPENDED", is_deleted=False, is_archived=False
        )

    def pending(self):
        return self.filter(status__code="PENDING", is_deleted=False, is_archived=False)

    def expired(self):
        return self.filter(status__code="EXPIRED", is_deleted=False, is_archived=False)

    def terminated(self):
        return self.filter(
            status__code="TERMINATED", is_deleted=False, is_archived=False
        )

    def by_category(self, category):
        return self.filter(category=category, is_deleted=False, is_archived=False)

    def by_district(self, district: str):
        return self.filter(district__iexact=district)

    def expiring_within(self, days: int):
        today = timezone.now().date()
        cutoff = today + timedelta(days=days)
        return self.filter(expiry_date__range=(today, cutoff))


class MemberProfileManager(BaseManager):
    """Manager for MemberProfile using MemberProfileQuerySet."""

    def get_queryset(self):
        return MemberProfileQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def suspended(self):
        return self.get_queryset().suspended()

    def pending(self):
        return self.get_queryset().pending()

    def expired(self):
        return self.get_queryset().expired()

    def expiring_within(self, days: int):
        return self.get_queryset().expiring_within(days)


class MembershipApplicationQuerySet(models.QuerySet):
    """QuerySet scoped to membership applications."""

    def submitted(self):
        return self.filter(status="SUBMITTED")

    def pending_review(self):
        return self.filter(status__in=["SUBMITTED", "UNDER_REVIEW"])

    def approved(self):
        return self.filter(status="APPROVED")

    def returned(self):
        return self.filter(status="RETURNED")


class MembershipApplicationManager(models.Manager):
    """Manager for MembershipApplication using its custom QuerySet."""

    def get_queryset(self):
        return MembershipApplicationQuerySet(self.model, using=self._db)

    def submitted(self):
        return self.get_queryset().submitted()

    def pending_review(self):
        return self.get_queryset().pending_review()
