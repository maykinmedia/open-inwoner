import os

from django.conf import settings
from django.core.checks import Tags, Warning, register

from maykin_common.config import DocumentationParams, config


def get_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield from get_subclasses(subclass)
        yield subclass


@register
def check_missing_init_files(app_configs, **kwargs):
    """
    Check that all packages have __init__.py files.

    If they don't, the code will still run, but tests aren't picked up by the
    test runner, for example.
    """
    errors = []

    for dirpath, dirnames, filenames in os.walk(settings.DJANGO_PROJECT_DIR):
        dirname = os.path.split(dirpath)[1]
        if dirname == "__pycache__":
            continue

        if "__init__.py" in filenames:
            continue

        extensions = [os.path.splitext(fn)[1] for fn in filenames]
        if ".py" not in extensions:
            continue

        errors.append(
            Warning(
                "Directory %s does not contain an `__init__.py` file" % dirpath
                + dirname,
                hint="Consider adding this module to make sure tests are picked up",
                id="utils.W001",
            )
        )

    return errors


# Settings of the notification rate limiting cache that can no longer be changed
REMOVED_NOTIFICATION_THROTTLE_SETTINGS = (
    "CACHE_NOTIFICATION_THROTTLE_BACKEND",
    "CACHE_NOTIFICATION_THROTTLE_CLIENT_CLASS",
    "CACHE_NOTIFICATION_THROTTLE_IGNORE_EXCEPTIONS",
)


@register(Tags.caches)
def check_removed_notification_throttle_settings(app_configs, **kwargs):
    """
    Warn about settings of the notification rate limiting cache that are ignored.
    """
    return [
        Warning(
            f"{name} is set, but is no longer used.",
            hint=(
                "The cache used to rate limit notifications is always a Redis cache "
                "with the same settings as the default cache; only its location can "
                "be set, with CACHE_NOTIFICATION_THROTTLE_LOCATION. Remove "
                f"{name} from the configuration."
            ),
            id="utils.W002",
        )
        for name in REMOVED_NOTIFICATION_THROTTLE_SETTINGS
        if config(
            name, default=None, documentation=DocumentationParams(add_to_docs=False)
        )
        is not None
    ]
