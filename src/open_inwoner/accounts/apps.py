from io import StringIO

from django.apps import AppConfig, apps
from django.conf import settings
from django.contrib.contenttypes.management import create_contenttypes
from django.core.management import call_command
from django.db.models.signals import post_migrate


def update_admin_index(sender=None, **kwargs) -> bool:
    if "django_admin_index" not in settings.INSTALLED_APPS:
        print("django_admin_index not installed, skipping update_admin_index()")
        return False

    from django_admin_index.models import AppGroup

    AppGroup.objects.all().delete()

    # The django-admin-index fixture depends on the contenttypes having been generated.
    # However, given that the contenttypes framework itself uses the post_migrate hook
    # to accomplish this, it's possible our hook will be run before their hook. Therefore,
    # we have to run the contenttype generation manually here.
    ct_create_exceptions = []
    for app_config in apps.get_app_configs():
        try:
            create_contenttypes(app_config, verbosity=0)
        except Exception as exc:
            # Only an issue if the fixtures actually refer to any contenttypes within this app,
            # which we remind the user of below.
            ct_create_exceptions.append(exc)

    try:
        call_command("loaddata", "django-admin-index", verbosity=0, stdout=StringIO())
    except Exception as exc:
        print(f"Error: Unable to load django-admin-index fixture ({exc})")
        if ct_create_exceptions:
            ct_exc = ExceptionGroup(
                "Unable to create contenttypes", *ct_create_exceptions
            )
            print(
                "NOTE: this may be a consequence of being unable to create the following "
                f"contenttypes: {ct_exc}"
            )
        return False
    else:
        print("Successfully loaded django-admin-index fixture")
        return True


class AccountsConfig(AppConfig):
    name = "open_inwoner.accounts"

    _has_run = False

    def ready(self):
        from .signals import (  # noqa:register the signals
            log_user_login,
            log_user_logout,
        )

        if self._has_run:
            return
        self._has_run = True

        post_migrate.connect(update_admin_index, sender=self)
