from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MealConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.meal"
    label = "meal"
    verbose_name = _("Monitoring, Evaluation, Accountability & Learning (MEAL)")
