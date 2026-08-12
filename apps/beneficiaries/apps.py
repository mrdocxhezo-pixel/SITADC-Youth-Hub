from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BeneficiariesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.beneficiaries"
    label = "beneficiaries"
    verbose_name = _("Beneficiary Management")
