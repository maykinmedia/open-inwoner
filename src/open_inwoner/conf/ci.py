import os
import warnings

os.environ.setdefault("DEBUG", "no")
os.environ.setdefault("ENVIRONMENT", "ci")
os.environ.setdefault("SECRET_KEY", "for-testing-purposes-only")
os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("ALLOWED_HOSTS", "")

from .base import *  # noqa isort:skip

# Disable all logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
    "loggers": {
        "": {
            "handlers": ["null"],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}

CACHES.update(
    {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        # See: https://github.com/jazzband/django-axes/blob/master/docs/configuration.rst#cache-problems
        "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    }
)

# Allow logging in with both username+password and email+password
AUTHENTICATION_BACKENDS = [
    "open_inwoner.accounts.backends.CustomAxesBackend",
    "open_inwoner.accounts.backends.UserModelEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    # mock login like dev.py
    "digid_eherkenning.mock.backends.DigiDBackend",
    "eherkenning.mock.backends.eHerkenningBackend",
    "open_inwoner.accounts.backends.DigiDOIDCBackend",
    "open_inwoner.accounts.backends.EHerkenningOIDCBackend",
    "open_inwoner.accounts.backends.EIDASOIDCBackend",
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

# Sip the auto-loading of the django-admin-index fixture on startup.
# It doesn't add anything in CI, and just adds time to the run.
SKIP_ADMIN_INDEX_FIXTURE = True


class InvalidVarException(str):
    """Raise when a template references an undefined variable, to catch typos in CI."""

    def __mod__(self, missing):
        raise AssertionError(f"Template used undefined variable: {missing!r}")

    def __contains__(self, search):
        return True  # Django checks `if "%s" in string_if_invalid` before substituting


TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = InvalidVarException()
