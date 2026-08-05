"""Custom managers and querysets for the reference numbering module."""

from __future__ import annotations

from django.db import models

from .constants import SchemeStatus


class ReferenceNumberSchemeQuerySet(models.QuerySet):
    """QuerySet helpers for reference number schemes."""

    def active(self) -> ReferenceNumberSchemeQuerySet:
        """Return schemes that are currently usable."""
        return self.filter(status=SchemeStatus.ACTIVE, is_active=True)

    def for_module(self, module: str) -> ReferenceNumberSchemeQuerySet:
        """Return schemes that serve a given business module."""
        return self.filter(module=module)

    def with_sequences(self) -> ReferenceNumberSchemeQuerySet:
        """Eager-load sequence rows for summary display."""
        return self.prefetch_related("sequences")


class ReferenceNumberSchemeManager(models.Manager):
    """Default manager for ``ReferenceNumberScheme``."""

    def get_queryset(self) -> ReferenceNumberSchemeQuerySet:
        return ReferenceNumberSchemeQuerySet(self.model, using=self._db)

    def active(self) -> ReferenceNumberSchemeQuerySet:
        return self.get_queryset().active()

    def for_module(self, module: str) -> ReferenceNumberSchemeQuerySet:
        return self.get_queryset().for_module(module)

    def with_sequences(self) -> ReferenceNumberSchemeQuerySet:
        return self.get_queryset().with_sequences()
