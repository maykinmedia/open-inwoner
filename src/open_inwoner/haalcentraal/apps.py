from django.apps import AppConfig


class HaalCentraalConfig(AppConfig):
    name = "open_inwoner.haalcentraal"

    def ready(self):
        from .config_checks import fetch_brp  # noqa
