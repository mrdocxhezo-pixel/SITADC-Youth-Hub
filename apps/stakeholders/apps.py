from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StakeholdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stakeholders"
    label = "stakeholders"
    verbose_name = _("Stakeholder Management")
