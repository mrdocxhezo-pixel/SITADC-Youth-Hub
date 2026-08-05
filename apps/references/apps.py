from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReferencesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.references"
    verbose_name = _("Reference Numbering")
