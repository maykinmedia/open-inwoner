import os
import warnings

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

CACHES.update(
    {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        # See: https://github.com/jazzband/django-axes/blob/master/docs/configuration.rst#cache-problems
        "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "oidc": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
)

# Allow logging in with both username+password and email+password
AUTHENTICATION_BACKENDS = [
    "open_inwoner.accounts.backends.CustomAxesBackend",
    "open_inwoner.accounts.backends.UserModelEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    # mock login like dev.py
    "digid_eherkenning.mock.backends.DigiDBackend",
    "open_inwoner.accounts.backends.CustomOIDCBackend",
]

ELASTIC_APM["DEBUG"] = True

ELASTICSEARCH_DSL_AUTO_REFRESH = False
ELASTICSEARCH_DSL_AUTOSYNC = False
ES_INDEX_PRODUCTS = "products_test"

ENVIRONMENT = "CI"

# Django solo caching (disabled for CI)
SOLO_CACHE = None

#
# Django-axes
#
AXES_BEHIND_REVERSE_PROXY = False

# Django privates
SENDFILE_BACKEND = "django_sendfile.backends.development"

# Two factor auth
TWO_FACTOR_FORCE_OTP_ADMIN = False
TWO_FACTOR_PATCH_ADMIN = False

# THOU SHALT NOT USE NAIVE DATETIMES
warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)

PLAYWRIGHT_MULTI_ONLY_DEFAULT = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
