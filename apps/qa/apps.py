from django.apps import AppConfig


class QaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.qa"
    verbose_name = "Quality Assurance"

    def ready(self):
        import apps.qa.signals  # noqa
