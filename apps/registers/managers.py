"""Managers and querysets for the Organizational Registers module."""

from __future__ import annotations

from django.db import models

from apps.core.managers import SoftDeleteManager


class ActiveRegisterManager(SoftDeleteManager):
    """Default manager excluding soft-deleted and archived records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)


class AllRegisterManager(models.Manager):
    """Manager exposing every record, including archived and soft-deleted rows."""

    def get_queryset(self):
        return super().get_queryset()
