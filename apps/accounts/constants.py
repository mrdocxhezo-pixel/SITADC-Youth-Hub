from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountStatus(models.TextChoices):
    PENDING_INVITATION = "PENDING_INVITATION", _("Pending Invitation")
    PENDING_REGISTRATION = "PENDING_REGISTRATION", _("Pending Registration")
    PENDING_VERIFICATION = "PENDING_VERIFICATION", _("Pending Email Verification")
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    SUSPENDED = "SUSPENDED", _("Suspended")
    LOCKED = "LOCKED", _("Locked")
    ARCHIVED = "ARCHIVED", _("Archived")
