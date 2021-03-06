from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "open_inwoner.accounts"

    def ready(self):
        from .signals import log_user_login, log_user_logout  # register the signals
