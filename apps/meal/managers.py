"""Managers for MEAL records."""

from __future__ import annotations

from django.db import models

IMMUTABLE_MEAL_HISTORY_MESSAGE = "Historical MEAL records are immutable."


class ActiveMEALManager(models.Manager):
    """Default manager excluding soft-deleted and archived records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False, is_archived=False)


class AllMEALManager(models.Manager):
    """Manager exposing every record, including archived and soft-deleted rows."""

    def get_queryset(self):
        return super().get_queryset()
