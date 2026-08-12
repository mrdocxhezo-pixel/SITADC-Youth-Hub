"""Managers for Dynamic Report Builder records."""

from __future__ import annotations

from django.db import models

IMMUTABLE_REPORT_HISTORY_MESSAGE = (
    "Report builder history and audit records are immutable."
)


class ActiveReportManager(models.Manager):
    """Default manager excluding soft-deleted and archived records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False, is_archived=False)


class AllReportManager(models.Manager):
    """Manager exposing every record, including archived and soft-deleted rows."""

    def get_queryset(self):
        return super().get_queryset()


class ActiveCategoryManager(models.Manager):
    """Manager excluding deactivated categories."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
