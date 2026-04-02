from django.apps import AppConfig


class ConfigChecksConfig(AppConfig):
    name = "open_inwoner.config_checks"
    verbose_name = "Configuration Checks"

    def ready(self):
        import open_inwoner.config_checks.receivers  # noqa
