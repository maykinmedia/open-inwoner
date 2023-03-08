from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "open_inwoner.external_api_logging"

    def ready(self):
        from .log_requests import log_session_requests

        log_session_requests()
