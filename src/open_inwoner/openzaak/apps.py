from django.apps import AppConfig


class OpenZaakAppConfig(AppConfig):
    name = "open_inwoner.openzaak"

    def ready(self):
        # Import to register the config check with the maykin_config_checks registry
        from .config_checks import fetch_cases  # noqa
