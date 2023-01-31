import tempfile
from typing import Any, Dict, List

from django.core.cache import caches
from django.test import override_settings


def temp_media_root():
    # Convenience decorator/context manager to use a temporary directory as
    # PRIVATE_MEDIA_ROOT.
    tmpdir = tempfile.mkdtemp()
    return override_settings(MEDIA_ROOT=tmpdir)


def paginated_response(results: List[dict]) -> Dict[str, Any]:
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
