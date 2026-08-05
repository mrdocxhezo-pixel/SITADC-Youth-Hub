from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProgramsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.programs"
    label = "programs"
    verbose_name = _("Program & Project Management")
