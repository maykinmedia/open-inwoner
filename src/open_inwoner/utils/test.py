import logging
import tempfile
from typing import Any
from uuid import UUID

from django.contrib.sessions.middleware import (
    SessionMiddleware as DefaultSessionMiddleWare,
)
from django.core.cache import caches
from django.test import override_settings

from open_inwoner.kvk.branches import KVK_BRANCH_SESSION_VARIABLE


def temp_media_root():
    # Convenience decorator/context manager to use a temporary directory as
    # PRIVATE_MEDIA_ROOT.
    tmpdir = tempfile.mkdtemp()
    return override_settings(MEDIA_ROOT=tmpdir)


def paginated_response(results: list[dict]) -> dict[str, Any]:
    body = {
        "count": len(results),
        "previous": None,
        "next": None,
        "results": results,
    }
    return body


class ClearCachesMixin:
    def clear_caches(self):
        for cache in caches.all():
            cache.clear()

    def setUp(self):
        super().setUp()

        for cache in caches.all():
            cache.clear()
            self.addCleanup(cache.clear)


class DisableRequestLogMixin:
    def setUp(self):
        logger = logging.getLogger("requests")
        if not logger.disabled:
            logger.disabled = True

            def _reset_requests_logger():
                logger = logging.getLogger("requests")
                logger.disabled = False

            self.addCleanup(_reset_requests_logger)

        super().setUp()


def set_kvk_branch_number_in_session(value="1234"):
    """
    Injects a value for the `KVK_BRANCH_NUMBER` variable into the session, to prevent
    the `KvKLoginMiddleware` from triggering

    NOTE: DOES NOT WORK FOR DJANGO-WEBTEST
    see: https://github.com/django-webtest/django-webtest/issues/68#issuecomment-285131384
    """

    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            session = self.client.session
            session[KVK_BRANCH_SESSION_VARIABLE] = value
            session.save()
            test_func(self, *args, **kwargs)

        return wrapper

    return decorator


class SessionMiddleware(DefaultSessionMiddleWare):
    """
    `SessionMiddleware` __init__ expects a `get_response` argument in Django 4.2
    """

    def __init__(self, *args, **kwargs):
        super().__init__(get_response=lambda x: "dummy")


def uuid_from_url(url: str) -> str:
    """
    Extract UUID string from `url`, raise `ValueError` via UUID lib for invalid uuids
    """
    uuid = url.split("/")[-1]
    return str(UUID(uuid))
