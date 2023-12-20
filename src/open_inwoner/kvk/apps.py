from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class KvKConfig(AppConfig):
    name = "open_inwoner.kvk"

    def ready(self):
        from .signals import on_kvk_change
