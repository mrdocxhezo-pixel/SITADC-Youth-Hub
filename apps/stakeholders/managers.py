"""Application-facing querysets for stakeholder records."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.managers import BaseManager, SoftDeleteQuerySet

if TYPE_CHECKING:
    from .models import Stakeholder  # noqa: F401

IMMUTABLE_HISTORY_MESSAGE = _("Historical stakeholder records are immutable.")
FINALIZED_NOTE_VERSION_MESSAGE = _("Finalized note versions are immutable.")


class StakeholderQuerySet(SoftDeleteQuerySet):
    def active(self):
        from .constants import StakeholderStatus

        return self.filter(
            status__in=[StakeholderStatus.ACTIVE, StakeholderStatus.ENGAGED],
            is_archived=False,
            is_deleted=False,
        )

    def directory(self):
        from .constants import ConfidentialityLevel

        return self.filter(
            confidentiality=ConfidentialityLevel.DIRECTORY,
            is_archived=False,
            is_deleted=False,
        )


class StakeholderManager(BaseManager["Stakeholder"]):
    def get_queryset(self):
        return StakeholderQuerySet(self.model, using=self._db).alive()

    def active(self):
        return self.get_queryset().active()


class ImmutableHistoryQuerySet(models.QuerySet):
    """Reject bulk mutation of append-only domain history."""

    def update(self, **kwargs):
        raise ValidationError(IMMUTABLE_HISTORY_MESSAGE, code="immutable_history")

    def delete(self):
        raise ValidationError(IMMUTABLE_HISTORY_MESSAGE, code="immutable_history")


class ImmutableHistoryManager(models.Manager):
    def get_queryset(self):
        return ImmutableHistoryQuerySet(self.model, using=self._db)


class NoteVersionQuerySet(models.QuerySet):
    """Permit draft correction while protecting finalized note versions."""

    def update(self, **kwargs):
        if self.filter(is_finalized=True).exists():
            raise ValidationError(
                FINALIZED_NOTE_VERSION_MESSAGE,
                code="finalized_note_version",
            )
        return super().update(**kwargs)

    def delete(self):
        if self.filter(is_finalized=True).exists():
            raise ValidationError(
                FINALIZED_NOTE_VERSION_MESSAGE,
                code="finalized_note_version",
            )
        return super().delete()


class NoteVersionManager(models.Manager):
    def get_queryset(self):
        return NoteVersionQuerySet(self.model, using=self._db)
