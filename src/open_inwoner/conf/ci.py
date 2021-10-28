import os

os.environ.setdefault("DEBUG", "no")
os.environ.setdefault("ENVIRONMENT", "ci")
os.environ.setdefault("SECRET_KEY", "for-testing-purposes-only")
os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("ALLOWED_HOSTS", "")

from .base import *  # noqa isort:skip


LOGGING["loggers"].update(
    {
        "django": {
            "handlers": ["django"],
            "level": "WARNING",
            "propagate": True,
        },
    }
)


# in memory cache and django-axes don't get along.
# https://django-axes.readthedocs.io/en/latest/configuration.html#known-configuration-problems
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
}

ELASTIC_APM["DEBUG"] = True

# Directory for testing media files
TEST_PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, "test_private_media")
