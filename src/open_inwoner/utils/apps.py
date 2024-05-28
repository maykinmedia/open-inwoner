from django.apps import AppConfig


class UtilsConfig(AppConfig):
    name = "open_inwoner.utils"

    def ready(self):
        from django.apps import registry

        # force the task autodiscovery
        from ..celery import app
        from . import checks  # noqa
        from .signals import copy_log_entry_to_timeline_logger  # noqa

        installed_apps = [
            app_config.name for app_config in registry.apps.app_configs.values()
        ] + ["open_inwoner.openzaak"]
        app.autodiscover_tasks(installed_apps, force=True)
