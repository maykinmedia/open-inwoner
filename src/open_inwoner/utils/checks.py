import os

from django.conf import settings
from django.core.checks import Warning, register


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
