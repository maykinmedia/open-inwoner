from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class HaalCentraalConfig(AppConfig):
    name = "open_inwoner.haalcentraal"

    def ready(self):
        from .signals import on_bsn_change
