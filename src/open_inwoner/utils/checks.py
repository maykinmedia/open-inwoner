import os
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import CheckMessage, Tags, Warning, register
from django.db import DatabaseError

from aldryn_apphooks_config.app_base import CMSConfigApp
from cms.apphook_pool import apphook_pool
from cms.models import Page


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


@register(Tags.database)
def check_apphook_configs(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    """
    Check that CMS pages with a configurable apphook are matched to a config.

    aldryn looks up the config of an apphook page by the page's application
    namespace. If no config has that namespace, the views silently run without one
    (hiding sections, or ignoring toggles), and the CMS page settings form hides
    the mismatch by showing the first config as if it were selected.

    Tagged as a database check, so it only runs with ``check --database`` and
    ``migrate``.
    """
    config_apps: dict[str, CMSConfigApp] = {
        name: app
        for name, _ in apphook_pool.get_apphooks()
        if isinstance(app := apphook_pool.get_apphook(name), CMSConfigApp)
    }

    try:
        pages_by_apphook: dict[str, list[Page]] = defaultdict(list)
        for page in Page.objects.filter(application_urls__in=config_apps):
            pages_by_apphook[page.application_urls].append(page)

        namespaces_by_apphook: dict[str, set[str]] = {
            apphook: set(
                config_apps[apphook].get_configs().values_list("namespace", flat=True)
            )
            for apphook in pages_by_apphook
        }
    except DatabaseError:
        # `migrate` runs database checks before migrating, so on a fresh database
        # the tables do not exist yet
        return []

    warnings: list[CheckMessage] = []
    for apphook, pages in sorted(pages_by_apphook.items()):
        namespaces = namespaces_by_apphook[apphook]

        for page in pages:
            if page.application_namespace in namespaces:
                continue
            warnings.append(
                Warning(
                    f"CMS page {page.pk} uses apphook {apphook} with application "
                    f"namespace {page.application_namespace!r}, but no config has "
                    "that namespace. The page's views run without a config.",
                    hint=(
                        f"Existing config namespaces: {sorted(namespaces)}. Select a "
                        "config in the page's advanced settings and save, or change "
                        "the namespace of a config to match the page."
                    ),
                    obj=page,
                    id="utils.W002",
                )
            )

        used_namespaces = {page.application_namespace for page in pages}
        warnings.extend(
            Warning(
                f"Config {namespace!r} for apphook {apphook} is not used by any "
                "CMS page, so its settings have no effect.",
                hint=(
                    "If a page should use this config, select it in that page's "
                    "advanced settings and save. Otherwise, delete the config."
                ),
                id="utils.W003",
            )
            for namespace in sorted(namespaces - used_namespaces)
        )

    return warnings
