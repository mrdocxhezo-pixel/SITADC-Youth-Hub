"""Constants and enums for the geographic locations module."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class LocationStatus(models.TextChoices):
    """Status for geographic entities (used for soft lifecycle management)."""

    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    ARCHIVED = "ARCHIVED", _("Archived")


class EntityLevel(models.TextChoices):
    """The level of a geographic entity in the hierarchy."""

    COUNTRY = "COUNTRY", _("Country")
    PROVINCE = "PROVINCE", _("Province")
    DISTRICT = "DISTRICT", _("District")
    CONSTITUENCY = "CONSTITUENCY", _("Constituency")
    WARD = "WARD", _("Ward")
