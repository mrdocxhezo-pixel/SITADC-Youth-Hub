"""Managers for immutable and reference-data beneficiary rows."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

from django.db import models
from django.utils.translation import gettext_lazy as _

IMMUTABLE_HISTORY_MESSAGE = _(
    "Beneficiary history records are append-only and cannot be modified."
)


class ImmutableHistoryManager(models.Manager):
    """Manager that blocks updates and deletes on immutable rows."""

    def get_queryset(self):
        return super().get_queryset().select_related("beneficiary")

    def bulk_create(
        self,
        objs: Any,
        batch_size: int | None = None,
        ignore_conflicts: bool = False,
        update_conflicts: bool = False,
        update_fields: Collection[str] | None = None,
        unique_fields: Collection[str] | None = None,
    ):
        return super().bulk_create(
            objs,
            batch_size,
            ignore_conflicts,
            update_conflicts,
            update_fields,
            unique_fields,
        )


class BeneficiaryReferenceDataManager(models.Manager):
    """Manager with kind-scoped helpers for beneficiary reference data."""

    def active(self):
        return self.filter(active=True)

    def of_kind(self, kind):
        return self.filter(kind=kind)
