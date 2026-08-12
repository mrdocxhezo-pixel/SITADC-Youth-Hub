"""Models for the Enterprise Search module.

Persists user search history (recent searches), reusable saved searches and
an immutable audit trail of every executed query.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import CreatedByModel, TimeStampedModel, UUIDModel

from .constants import ENTITY_TYPE_KEYS
from .validators import validate_entity_type_keys


class RecentSearch(UUIDModel, TimeStampedModel):
    """A search the actor recently executed, deduplicated per user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recent_searches",
        db_index=True,
    )
    query = models.CharField(_("Query"), max_length=200, db_index=True)
    entity_types = models.JSONField(
        _("Entity types"),
        default=list,
        validators=[validate_entity_type_keys],
        help_text=_("Entity type keys targeted by the search."),
    )
    result_count = models.PositiveIntegerField(_("Result count"), default=0)

    class Meta:
        verbose_name = _("Recent Search")
        verbose_name_plural = _("Recent Searches")
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["user", "query"],
                name="uniq_recent_search_user_query",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.query}"


class SavedSearch(UUIDModel, TimeStampedModel, CreatedByModel):
    """A named, reusable search the actor can run again."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_searches",
        db_index=True,
    )
    name = models.CharField(_("Name"), max_length=120)
    query = models.CharField(_("Query"), max_length=200)
    entity_types = models.JSONField(
        _("Entity types"),
        default=list,
        validators=[validate_entity_type_keys],
        help_text=_("Entity type keys targeted by the saved search."),
    )
    result_count = models.PositiveIntegerField(_("Result count"), default=0)

    class Meta:
        verbose_name = _("Saved Search")
        verbose_name_plural = _("Saved Searches")
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="uniq_saved_search_user_name",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.user})"


class SearchQueryLog(UUIDModel, TimeStampedModel):
    """Immutable audit record of an executed search query.

    Records who searched, what they searched for, the entity types targeted
    and the outcome (result count and duration).  Rows are append-only.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="search_query_logs",
    )
    query = models.CharField(_("Query"), max_length=200, db_index=True)
    entity_types = models.JSONField(
        _("Entity types"),
        default=list,
        help_text=_("Entity type keys targeted by the query."),
    )
    result_count = models.PositiveIntegerField(_("Result count"), default=0)
    duration_ms = models.PositiveIntegerField(_("Duration (ms)"), default=0)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)

    class Meta:
        verbose_name = _("Search Query Log")
        verbose_name_plural = _("Search Query Logs")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["-created_at", "user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.query}"

    @classmethod
    def _reject_mutation(cls, instance) -> None:
        if instance._state.adding is False:
            raise ValidationError(_("Search query log rows are immutable."))

    def save(self, *args, **kwargs) -> None:
        if self._state.adding is False:
            raise ValidationError(_("Search query log rows are immutable."))
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_("Search query log rows cannot be deleted."))

    def validate_entity_keys(self) -> None:
        unknown = [key for key in self.entity_types if key not in ENTITY_TYPE_KEYS]
        if unknown:
            validate_entity_type_keys(unknown)
