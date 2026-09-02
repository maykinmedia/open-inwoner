import os
from shutil import which
from subprocess import CalledProcessError, check_output

from django.conf import settings

import structlog
from maykin_common.config import config
from sentry_sdk.integrations import DidNotEnable, django, redis

logger = structlog.stdlib.get_logger(__name__)


def get_sentry_integrations() -> list:
    """
    Determine which Sentry SDK integrations to enable.
    """
    default = [
        django.DjangoIntegration(),
        redis.RedisIntegration(),
        # NOTE: We use a custom SentryStructlogProcessor in structlog to capture
        # exceptions directly from the event dict before any formatting happens. This
        # ensures Sentry receives proper exception objects instead of formatted strings
        # or JSON blobs. The LoggingIntegration is disabled to prevent interference.
    ]
    extra = []

    try:
        from sentry_sdk.integrations import celery
    except DidNotEnable:  # happens if the celery import fails by the integration
        logger.warning(
            "Unable to initialize Sentry with Celery integration due to failing import"
        )
    else:
        extra.append(celery.CeleryIntegration())

    return [*default, *extra]


def _get_version_from_file(base_dir=None):
    """
    Returns a commit hash from the project's .git/ dir if it exists

    ``base_dir`` defaults to ``settings.BASE_DIR``. Pass it explicitly when
    calling this from settings module code itself (e.g. to derive ``GIT_SHA``) -
    touching ``django.conf.settings`` while it's still being constructed for the
    first time causes Django to silently reconstruct it from a half-initialized
    module, permanently losing settings defined after this point.
    """
    if base_dir is None:
        base_dir = settings.BASE_DIR
    heads_dir = os.path.join(base_dir, ".git", "refs", "heads")

    try:
        heads = os.listdir(heads_dir)
    except FileNotFoundError:
        logger.warning("Unable to read commit hash from git files")
        return ""

    for filename in ("master", "main", "develop"):
        if filename in heads:
            try:
                with open(os.path.join(heads_dir, filename)) as file:
                    return file.read().strip()
            except OSError:
                logger.warning("Unable to read commit hash from file")

    return ""


def _get_version_from_git():
    """
    Returns the current tag or commit hash supplied by git
    """
    try:
        tags = check_output(  # noqa: S603
            ["git", "tag", "--points-at", "HEAD"],  # noqa: S607
            universal_newlines=True,
        )
    except CalledProcessError:
        logger.warning("Unable to list tags")
        tags = None

    if tags:
        return next(version for version in tags.splitlines())

    try:
        commit = check_output(  # noqa: S603
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            universal_newlines=True,
        )
    except CalledProcessError:
        logger.warning("Unable to list current commit hash")
        commit = None

    return commit or ""


def get_current_version(base_dir=None):
    version = config("VERSION_TAG", default=None)

    if version:
        return version
    elif which("git"):
        return _get_version_from_git()

    return _get_version_from_file(base_dir)
