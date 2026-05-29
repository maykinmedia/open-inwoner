from django.apps import AppConfig
from django.conf import settings


class OpenZaakConfig(AppConfig):
    name = "open_inwoner.openzaak"

    def ready(self):
        if settings.ENABLE_INTERACTIVE_CONFIG_CHECKS:
            from maykin_config_checks.registry import registry

            from .config_checks.fetch_cases import FetchCasesCheck
            from .models import OpenZaakConfig as OpenZaakConfigModel

            registry.register(FetchCasesCheck, model=OpenZaakConfigModel)
