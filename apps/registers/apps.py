from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RegistersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.registers"
    label = "registers"
    verbose_name = _("Organizational Registers")
