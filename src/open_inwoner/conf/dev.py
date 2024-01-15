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

os.environ.setdefault("DB_NAME", "open_inwoner"),
os.environ.setdefault("DB_USER", "open_inwoner"),
os.environ.setdefault("DB_PASSWORD", "open_inwoner"),

os.environ.setdefault("ENVIRONMENT", "development")

from .base import *  # noqa isort:skip

# Feel free to switch dev to sqlite3 for simple projects,
# os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")

#
# Standard Django settings.
#
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

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

# in memory cache and django-axes don't get along.
# https://django-axes.readthedocs.io/en/latest/configuration.html#known-configuration-problems
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "oidc": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
}

#
# Library settings
#

# Allow logging in with both username+password and email+password
AUTHENTICATION_BACKENDS = [
    "open_inwoner.accounts.backends.CustomAxesBackend",
    "open_inwoner.accounts.backends.UserModelEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    "digid_eherkenning.mock.backends.DigiDBackend",
    "eherkenning.mock.backends.eHerkenningBackend",
    "digid_eherkenning_oidc_generics.backends.OIDCAuthenticationDigiDBackend",
    "digid_eherkenning_oidc_generics.backends.OIDCAuthenticationEHerkenningBackend",
    "open_inwoner.accounts.backends.CustomOIDCBackend",
]

ELASTIC_APM["DEBUG"] = True

if "test" in sys.argv:
    ELASTICSEARCH_DSL_AUTO_REFRESH = False
    ELASTICSEARCH_DSL_AUTOSYNC = False
    ES_INDEX_PRODUCTS = "products_test"

# Django debug toolbar
INSTALLED_APPS += ["ddt_api_calls", "django_extensions"]
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
    "ddt_api_calls.panels.APICallsPanel",
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

# playwright multi browser
PLAYWRIGHT_MULTI_ONLY_DEFAULT = True

if config("PROFILE", default=False):
    INSTALLED_APPS += ["silk"]
    MIDDLEWARE = ["silk.middleware.SilkyMiddleware"] + MIDDLEWARE
    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True
    SILKY_DYNAMIC_PROFILING = [
        {
            "module": "open_inwoner.cms.cases.views.status",
            "function": "InnerCaseDetailView.dispatch",
            "name": "InnerCaseDetailView",
        }
    ]

# Override settings with local settings.
try:
    from .local import *  # noqa
except ImportError:
    pass
