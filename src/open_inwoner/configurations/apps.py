from django.apps import AppConfig


class ConfigurationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "open_inwoner.configurations"

    def ready(self):
        from . import checks  # noqa
