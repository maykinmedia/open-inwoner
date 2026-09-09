import contextlib
import os
import sys
import warnings

os.environ.setdefault("DEBUG", "yes")
os.environ.setdefault("ALLOWED_HOSTS", "*")
os.environ.setdefault(
    "SECRET_KEY", "7bk)w=_%lnm#68rc!c)h@gy&5+%^f$=okq17bv!)yv!l0udu2y"
)
os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("VERSION_TAG", "dev")

os.environ.setdefault("DB_NAME", "open_inwoner")
os.environ.setdefault("DB_USER", "open_inwoner")
os.environ.setdefault("DB_PASSWORD", "open_inwoner")
# `bin/stack.sh up --localhost` (see docs/installation/docker-compose.rst) is the
# standard way to run OIP outside Docker: it publishes Postgres/Redis/Elasticsearch
# on 5433/6380/9202 rather than the defaults 5432/6379/9200, so they don't collide
# with a native install. These are only defaults -- conf.docker (used inside Docker
# containers, see conf/docker.py) doesn't import this module, so full-Docker mode is
# unaffected. Override in conf/local.py if you're not using `up --localhost` (e.g. a
# native Postgres/Redis/Elasticsearch install).
os.environ.setdefault("DB_PORT", "5433")
os.environ.setdefault("CACHE_DEFAULT", "localhost:6380/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6380/0")
os.environ.setdefault("ES_HOST", "http://localhost:9202")

# Mailpit's SMTP port, so mail sent by the app ends up there.
os.environ.setdefault("EMAIL_PORT", "1025")

os.environ.setdefault("ES_USERNAME", "elastic")
os.environ.setdefault("ES_PASSWORD", "elastic")

os.environ.setdefault("ENVIRONMENT", "development")

from .base import *  # noqa isort:skip

# Feel free to switch dev to sqlite3 for simple projects,
# os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")

#
# Standard Django settings.
#
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# This is commented out because it causes tests in the CI to fail. It can be enabled in the local.py settings.
# SESSION_COOKIE_DOMAIN = ".localhost"

ADMIN_SESSION_COOKIE_AGE = (
    86400  # Avoid having to relogin when in the admin in dev-environments
)

LOGGING["loggers"].update(
    {
        "open_inwoner": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["django"],
            "level": "DEBUG",
            "propagate": False,
        },
        "performance": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        #
        # See: https://code.djangoproject.com/ticket/30554
        # Autoreload logs excessively, turn it down a bit.
        #
        "django.utils.autoreload": {
            "handlers": ["django"],
            "level": "INFO",
            "propagate": False,
        },
    }
)

# No CACHES override: Redis-backed caches (conf.base) apply as-is. Redis is a
# required service for host mode (see docs/installation/docker-compose.rst) --
# an in-memory cache here would make a host-run Celery worker's results
# invisible to `runserver`.

_MOCK_AUTHENTICATION_BACKENDS = {
    "digid_eherkenning.backends.DigiDBackend": "digid_eherkenning.mock.backends.DigiDBackend",
    "eherkenning.backends.eHerkenningBackend": "eherkenning.mock.backends.eHerkenningBackend",
}

AUTHENTICATION_BACKENDS = [
    _MOCK_AUTHENTICATION_BACKENDS.get(backend, backend)
    for backend in AUTHENTICATION_BACKENDS
]


#
# Library settings
#
ELASTIC_APM["DEBUG"] = True

if "test" in sys.argv:
    ES_INDEX_PRODUCTS = "products_test"

# Django debug toolbar
INSTALLED_APPS += ["django_extensions"]
# MIDDLEWARE += [
#     "debug_toolbar.middleware.DebugToolbarMiddleware",
# ]
INTERNAL_IPS = ("127.0.0.1",)
DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False}
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
]

# THOU SHALT NOT USE NAIVE DATETIMES
warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)

# django-filer
FILER_DEBUG = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:3000",
]

# Django solo caching (disabled for CI)
SOLO_CACHE = None

TWO_FACTOR_PATCH_ADMIN = False

# Disable two-factor authentication by default for development
if config("DISABLE_2FA", default=True):
    MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS = AUTHENTICATION_BACKENDS

# playwright multi browser
PLAYWRIGHT_MULTI_ONLY_DEFAULT = True

if config("PROFILE", default=False):
    INSTALLED_APPS += ["silk"]
    MIDDLEWARE = ["silk.middleware.SilkyMiddleware"] + MIDDLEWARE
    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True

# Override settings with local settings.


with contextlib.suppress(ImportError):
    from .local import *  # noqa
