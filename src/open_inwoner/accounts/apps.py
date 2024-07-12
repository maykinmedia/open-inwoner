from io import StringIO

from django.apps import AppConfig, apps
from django.conf import settings
from django.contrib.contenttypes.management import create_contenttypes
from django.core.management import call_command

# from django.db.models.signals import post_migrate


def update_admin_index(sender=None, **kwargs) -> bool:
    if "django_admin_index" not in settings.INSTALLED_APPS:
        print("django_admin_index not installed, skipping update_admin_index()")
        return False

    from django_admin_index.models import AppGroup

    AppGroup.objects.all().delete()

    # Make sure project models are registered.
    project_name = __name__.split(".")[0]

    for app_config in apps.get_app_configs():
        if app_config.name.startswith(project_name):
            create_contenttypes(app_config, verbosity=0)

    try:
        call_command("loaddata", "django-admin-index", verbosity=0, stdout=StringIO())
    except Exception as exc:
        print(f"Error: Unable to load django-admin-index fixture ({exc})")
        return False
    else:
        print("Loaded django-admin-index fixture")
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

        # FIXME: loading the django-admin-index fixture through the
        # post migrate signal is broken; we now load the fixture
        # in the docker startup script, so this only affects manual
        # installs during development;

        # post_migrate.connect(update_admin_index, sender=self)
