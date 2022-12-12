from django.apps import AppConfig
from django.conf import settings


class AccountsConfig(AppConfig):
    name = "open_inwoner.accounts"

    def ready(self):
        from .signals import log_user_login, log_user_logout  # register the signals

        use_signals = getattr(settings, "ENABLE_USER_SIGNALS", True)
        if not use_signals:
            from django.contrib.auth.models import update_last_login
            from django.contrib.auth.signals import user_logged_in, user_logged_out
            from django.db.models.signals import pre_save

            from open_inwoner.accounts.models import User
            from open_inwoner.haalcentraal.signals import on_bsn_change

            user_logged_in.disconnect(update_last_login)
            user_logged_in.disconnect(log_user_login)
            user_logged_out.disconnect(log_user_logout)
            pre_save.disconnect(on_bsn_change, sender=User)
