"""
Data models for the centralized geographic / administrative hierarchy.

The hierarchy is authoritative and database-driven:

    Country
      └── Province
            └── District
                  └── Constituency
                        └── Ward

Every child references its parent with a ForeignKey. Entities support soft
deactivation (is_active) and archiving so that historical records referencing
them are never hard-deleted when administrative boundaries change.
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    IsActiveModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)

from .managers import LocationManager


class Country(UUIDModel, TimeStampedModel, IsActiveModel, ArchivableModel):
    """
    A country at the top of the geographic hierarchy (e.g. Zambia).
    """

    name = models.CharField(_("Name"), max_length=150, unique=True)
    code = models.CharField(_("ISO code"), max_length=3, unique=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    objects: ClassVar[LocationManager] = LocationManager()

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")
        ordering = ("sort_order", "name")
        indexes: ClassVar[list] = [
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def province_count(self) -> int:
        return self.provinces.count()


class Province(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, IsActiveModel, ArchivableModel):
    """
    A province / region within a country (e.g. Lusaka Province).
    """

    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="provinces",
        verbose_name=_("Country"),
    )
    name = models.CharField(_("Name"), max_length=150)
    code = models.CharField(_("Code"), max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    objects: ClassVar[LocationManager] = LocationManager()

    class Meta:
        verbose_name = _("Province")
        verbose_name_plural = _("Provinces")
        ordering = ("sort_order", "name")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["country", "name"],
                name="uniq_province_name_per_country",
            ),
        ]
        indexes: ClassVar[list] = [
            models.Index(fields=["country", "is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def district_count(self) -> int:
        return self.districts.count()


class District(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, IsActiveModel, ArchivableModel):
    """
    A district within a province.
    """

    province = models.ForeignKey(
        Province,
        on_delete=models.PROTECT,
        related_name="districts",
        verbose_name=_("Province"),
    )
    name = models.CharField(_("Name"), max_length=150)
    code = models.CharField(_("Code"), max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    objects: ClassVar[LocationManager] = LocationManager()

    class Meta:
        verbose_name = _("District")
        verbose_name_plural = _("Districts")
        ordering = ("sort_order", "name")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["province", "name"],
                name="uniq_district_name_per_province",
            ),
        ]
        indexes: ClassVar[list] = [
            models.Index(fields=["province", "is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def constituency_count(self) -> int:
        return self.constituencies.count()

    @property
    def province_name(self) -> str:
        return self.province.name


class Constituency(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, IsActiveModel, ArchivableModel):
    """
    A constituency within a district.
    """

    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="constituencies",
        verbose_name=_("District"),
    )
    name = models.CharField(_("Name"), max_length=150)
    code = models.CharField(_("Code"), max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    objects: ClassVar[LocationManager] = LocationManager()

    class Meta:
        verbose_name = _("Constituency")
        verbose_name_plural = _("Constituencies")
        ordering = ("sort_order", "name")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["district", "name"],
                name="uniq_constituency_name_per_district",
            ),
        ]
        indexes: ClassVar[list] = [
            models.Index(fields=["district", "is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def ward_count(self) -> int:
        return self.wards.count()

    @property
    def district_name(self) -> str:
        return self.district.name


class Ward(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, IsActiveModel, ArchivableModel):
    """
    A ward / community within a constituency.
    """

    constituency = models.ForeignKey(
        Constituency,
        on_delete=models.PROTECT,
        related_name="wards",
        verbose_name=_("Constituency"),
    )
    name = models.CharField(_("Name"), max_length=150)
    code = models.CharField(_("Code"), max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    objects: ClassVar[LocationManager] = LocationManager()

    class Meta:
        verbose_name = _("Ward")
        verbose_name_plural = _("Wards")
        ordering = ("sort_order", "name")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["constituency", "name"],
                name="uniq_ward_name_per_constituency",
            ),
        ]
        indexes: ClassVar[list] = [
            models.Index(fields=["constituency", "is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def constituency_name(self) -> str:
        return self.constituency.name
