from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusConstants(models.TextChoices):
    """
    Standardized status values for business entities across the system.
    """

    DRAFT = "DRAFT", _("Draft")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")
    RETURNED = "RETURNED", _("Returned")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    ARCHIVED = "ARCHIVED", _("Archived")
    ACTIVE = "ACTIVE", _("Active")
