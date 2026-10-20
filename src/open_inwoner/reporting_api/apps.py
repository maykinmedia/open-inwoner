from django.apps import AppConfig


class ReportingApiConfig(AppConfig):
    name = "open_inwoner.reporting_api"

    def ready(self):
        from . import checks  # noqa
