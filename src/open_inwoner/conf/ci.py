import os
import warnings

# Enable traceback pickling for parallel test runner
# This must be done early before any exceptions are raised
import tblib.pickling_support

tblib.pickling_support.install()

os.environ.setdefault("DEBUG", "no")
os.environ.setdefault("ENVIRONMENT", "ci")
os.environ.setdefault("SECRET_KEY", "for-testing-purposes-only")
os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("ALLOWED_HOSTS", "")
# Disable request logging to avoid structlog middleware issues with parallel tests
os.environ.setdefault("LOG_REQUESTS", "no")

from .base import *  # noqa isort:skip

import structlog  # noqa: E402

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

#
# Structlog configuration for parallel tests
#
# Disable logger caching to prevent MaybeEncodingError when running tests in
# parallel with multiprocessing. Cached loggers can contain unpicklable state
# that fails to serialize when sending test results between processes.
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=False,  # Prevent caching issues with multiprocessing
)
