from django.apps import AppConfig


class KvKConfig(AppConfig):
    name = "open_inwoner.kvk"

    def ready(self):
        from .signals import on_kvk_change  # noqa
