"""Managers for program and project records."""

from __future__ import annotations

from django.db import models

IMMUTABLE_HISTORY_MESSAGE = "Historical program records are immutable."


class ProgramManager(models.Manager):
    """Default manager excluding soft-deleted and archived records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False, is_archived=False)


class ProjectManager(models.Manager):
    """Default manager excluding soft-deleted and archived records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False, is_archived=False)


class ImmutableHistoryManager(models.Manager):
    """Manager for append-only lifecycle history rows."""

    def get_queryset(self):
        return super().get_queryset()
