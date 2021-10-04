from django.apps import AppConfig


class UtilsConfig(AppConfig):
    name = "open_inwoner.utils"

    def ready(self):
        from . import checks  # noqa
