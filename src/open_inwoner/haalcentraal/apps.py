from django.apps import AppConfig


class HaalCentraalConfig(AppConfig):
    name = "open_inwoner.haalcentraal"

    def ready(self):
        from .signals import on_bsn_change  # noqa
