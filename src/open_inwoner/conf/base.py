import datetime
import os

import django.utils.timezone
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

import sentry_sdk
import structlog
from celery.schedules import crontab
from easy_thumbnails.conf import Settings as ThumbnailSettings
from log_outgoing_requests.structlog import ExtractRequestAndResponseDetails
from maykin_common.config import DocumentationParams, config
from maykin_common.health_checks import default_health_check_apps

from .structlog_sentry import SentryStructlogProcessor
from .utils import get_sentry_integrations

# django.utils.timezone.utc was removed in Django 5.0. Restore it as a
# compatibility shim for third-party packages (e.g. zgw-consumers-oas) that
# haven't been updated yet.
django.utils.timezone.utc = datetime.timezone.utc

# Build paths inside the project, so further paths can be defined relative to
# the code root.

DJANGO_PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir)
)
BASE_DIR = os.path.abspath(
    os.path.join(DJANGO_PROJECT_DIR, os.path.pardir, os.path.pardir)
)

#
# Core Django settings
#
SITE_ID = config(
    "SITE_ID",
    default=1,
    documentation=DocumentationParams(
        help_text="Database ID of the Django Site object for this installation.",
        group="Application",
    ),
)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    "SECRET_KEY",
    documentation=DocumentationParams(
        help_text=(
            "A long, random string used for cryptographic signing. "
            "Must be unique per environment and never committed to version control."
        ),
        group="Application",
    ),
)

# To facilitate key rotation and migrations. We currently only allow a single value
# (hence the singular `SECRET_KEY_FALLBACK` config attribute).
if secret_key_fallback := config(
    "SECRET_KEY_FALLBACK",
    default="",
    documentation=DocumentationParams(
        help_text=(
            "A previous SECRET_KEY value to support gradual key rotation. "
            "Sessions and tokens signed with this key remain valid during the transition."
        ),
        group="Security",
    ),
):
    SECRET_KEY_FALLBACKS = [secret_key_fallback]

# NEVER run with DEBUG=True in production-like environments
DEBUG = config(
    "DEBUG",
    default=False,
    documentation=DocumentationParams(
        help_text=(
            "Enables Django debug mode. Must be False in production: "
            "exposes tracebacks and disables security hardening."
        ),
        group="Security",
    ),
)

# = domains we're running on
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default=[],
    split=True,
    documentation=DocumentationParams(
        help_text=(
            "Comma-separated list of domains (without spaces) that serve this installation. "
            "Protects against HTTP Host header attacks. "
            "Example: example.com,www.example.com"
        ),
        group="Application",
    ),
)

IS_HTTPS = config(
    "IS_HTTPS",
    default=not DEBUG,
    documentation=DocumentationParams(
        help_text=(
            "Set to True when the application is served over HTTPS. "
            "Enables secure cookies and HSTS. Defaults to the inverse of DEBUG."
        ),
        group="Security",
    ),
)

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "nl"
LANGUAGES = [
    ("nl", _("Dutch")),
]

# Default (connection timeout, read timeout) for the requests library (in seconds)
DEFAULT_TIMEOUT_REQUESTS = (10, 60)

TIME_ZONE = "Europe/Amsterdam"  # note: this *may* affect the output of DRF datetimes

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

#
# DATABASE and CACHING setup
#
DATABASES = {
    "default": {
        "ENGINE": config(
            "DB_ENGINE",
            default="django.contrib.gis.db.backends.postgis",
            documentation=DocumentationParams(
                help_text="Django database backend to use. The default enables PostGIS (spatial data support).",
                group="Database",
            ),
        ),
        "NAME": config(
            "DB_NAME",
            default="open_inwoner",
            documentation=DocumentationParams(
                help_text="Name of the PostgreSQL database.",
                group="Database",
            ),
        ),
        "USER": config(
            "DB_USER",
            default="open_inwoner",
            documentation=DocumentationParams(
                help_text="PostgreSQL database user.",
                group="Database",
            ),
        ),
        "PASSWORD": config(
            "DB_PASSWORD",
            default="open_inwoner",
            documentation=DocumentationParams(
                help_text="Password for the PostgreSQL database user.",
                group="Database",
            ),
        ),
        "HOST": config(
            "DB_HOST",
            default="localhost",
            documentation=DocumentationParams(
                help_text="Hostname or IP address of the PostgreSQL server.",
                group="Database",
            ),
        ),
        "PORT": config(
            "DB_PORT",
            default=5432,
            documentation=DocumentationParams(
                help_text="Port the PostgreSQL server listens on.",
                group="Database",
            ),
        ),
    }
}

# Geospatial libraries
GEOS_LIBRARY_PATH = config(
    "GEOS_LIBRARY_PATH",
    default=None,
    documentation=DocumentationParams(
        help_text=(
            "Absolute path to the GEOS shared library. "
            "Only required when the library cannot be found automatically."
        ),
        group="Database",
    ),
)
GDAL_LIBRARY_PATH = config(
    "GDAL_LIBRARY_PATH",
    default=None,
    documentation=DocumentationParams(
        help_text=(
            "Absolute path to the GDAL shared library. "
            "Only required when the library cannot be found automatically."
        ),
        group="Database",
    ),
)

# Custom JavaScript feature flag
ALLOW_CUSTOM_JS = config(
    "ALLOW_CUSTOM_JS",
    default=False,
    documentation=DocumentationParams(
        help_text=(
            "Allow administrators to inject custom JavaScript via the admin interface. "
            "Disable in environments where strict CSP is required."
        ),
        group="Application",
    ),
)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_DEFAULT', default='localhost:6379/0', documentation=DocumentationParams(help_text='Redis connection string for the default cache, in host:port/db format.', group='Cache'))}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
    "axes": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_DEFAULT', default='localhost:6379/0', documentation=DocumentationParams(add_to_docs=False))}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
    "local": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

# Django solo caching
SOLO_CACHE_TIMEOUT = 5  # 5 seconds
SOLO_CACHE = "local"  # Avoid Redis overhead

# ZGW API caches
CACHE_ZGW_CATALOGI_TIMEOUT = config(
    "CACHE_ZGW_CATALOGI_TIMEOUT",
    default=60 * 60 * 24,
    documentation=DocumentationParams(
        help_text=(
            "Seconds to cache ZGW catalogus data (zaaktypen, statustypen, etc.). "
            "Catalogue data changes infrequently; a long TTL reduces API load."
        ),
        group="ZGW",
    ),
)
CACHE_ZGW_ZAKEN_TIMEOUT = config(
    "CACHE_ZGW_ZAKEN_TIMEOUT",
    default=60 * 5,
    documentation=DocumentationParams(
        help_text="Seconds to cache individual zaak data fetched from ZGW APIs.",
        group="ZGW",
    ),
)

# Maximum number of pagination requests to follow when fetching zaken from ZGW APIs
ZGW_MAX_REQUESTS = config(
    "ZGW_MAX_REQUESTS",
    default=8,
    documentation=DocumentationParams(
        help_text=(
            "Maximum number of paginated API calls to follow when fetching zaken from ZGW APIs. "
            "Limits the total number of cases loaded per request."
        ),
        group="ZGW",
    ),
)

# Laposta API caching
CACHE_LAPOSTA_API_TIMEOUT = config(
    "CACHE_LAPOSTA_API_TIMEOUT",
    default=60 * 15,
    documentation=DocumentationParams(
        help_text="Seconds to cache responses from the Laposta mailing list API.",
        group="Cache",
    ),
)


#
# APPLICATIONS enabled for this project
#

INSTALLED_APPS = [
    # Note: contenttypes should be first, see Django ticket #10827
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    # NOTE: If enabled, at least one Site object is required and
    # uncomment SITE_ID above.
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.flatpages",
    "django.forms",
    # load user model before CMS
    "open_inwoner.accounts",
    "open_inwoner.openzaak",
    # Django-CMS
    "cms",
    "menus",
    "treebeard",
    "sekizai",
    # "djangocms_admin_style",
    "djangocms_versioning",
    "djangocms_alias",
    "open_inwoner.djangocms_4_migration",
    "djangocms_link",
    "djangocms_picture",
    # 'djangocms_video',
    # 'djangocms_googlemap',
    # "djangocms_snippet",
    # "djangocms_style",
    # Admin auth
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    "two_factor.plugins.webauthn",
    "maykin_2fa",
    # Optional applications.
    "ordered_model",
    "django_admin_index",
    "django.contrib.admin",
    "django.contrib.gis",
    # 'django.contrib.admindocs',
    # 'django.contrib.humanize',
    # 'django.contrib.sitemaps',
    # External applications.
    "corsheaders",
    "ckeditor",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "axes",
    "sniplates",
    "digid_eherkenning",
    "eherkenning",
    "digid_eherkenning.oidc",
    "localflavor",
    "easy_thumbnails",  # used by filer
    "image_cropping",
    "filer",
    "django_elasticsearch_dsl",
    "import_export",
    "solo",
    "colorfield",
    "view_breadcrumbs",
    "django_jsonform",
    "simple_certmanager",
    "zgw_consumers",
    "mail_editor",
    "django_prosemirror",
    "privates",
    "timeline_logger",
    "csp",
    "cspreports",
    "mozilla_django_oidc",
    "mozilla_django_oidc_db",
    "sessionprofile",
    "openformsclient",
    "django_htmx",
    "log_outgoing_requests",
    "formtools",
    "django_setup_configuration",
    "django_yubin",
    "notifications",
    "custom_migrations",
    "objectsapiclient",
    *default_health_check_apps,
    "maykin_common.health_checks.celery",
    "maykin_config_checks",
    # Project applications.
    "open_inwoner.core",
    "open_inwoner.components",
    "open_inwoner.kvk",
    "open_inwoner.laposta",
    "open_inwoner.qmatic",
    "open_inwoner.pdc",
    "open_inwoner.plans",
    "open_inwoner.search",
    "open_inwoner.utils",
    "open_inwoner.configurations",
    "open_inwoner.haalcentraal",
    "open_inwoner.openklant",
    "open_inwoner.soap",
    "open_inwoner.ssd",
    "open_inwoner.questionnaire",
    "open_inwoner.extended_sessions",
    "open_inwoner.custom_csp",
    "open_inwoner.mail",
    "open_inwoner.media",
    "open_inwoner.userfeed",
    "open_inwoner.mijn_afval",
    "open_inwoner.mijn_afval.cms",
    "open_inwoner.cms.profile",
    "open_inwoner.cms.cases",
    "open_inwoner.cms.inbox",
    "open_inwoner.cms.products",
    "open_inwoner.cms.collaborate",
    "open_inwoner.cms.banner",
    "open_inwoner.cms.extensions",
    "open_inwoner.cms.footer",
    "open_inwoner.cms.plugins",
    "open_inwoner.cms.benefits",
    "djchoices",
    "django_celery_beat",
    "django_celery_monitor",
    # Temporary fix: the notifications lib interferes with
    # celery's task loading meachanism, which prevents certain
    # tasks from showing up in the admin when OIP is run with
    # Docker; this needs to be fixed this in the library eventually;
    # for now we load it after all our apps.
    "notifications_api_common",
]

_log_requests_via_middleware = config(
    "LOG_REQUESTS",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Enable structured request logging via django-structlog middleware. "
            "Logs method, path, status code, and duration for every request."
        ),
        group="Logging",
    ),
)
_structlog_middleware = (
    [
        "django_structlog.middlewares.RequestMiddleware",
    ]
    if _log_requests_via_middleware
    else []
)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "sessionprofile.middleware.SessionProfileMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 'django.middleware.locale.LocaleMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    *_structlog_middleware,
    "csp.contrib.rate_limiting.RateLimitedCSPMiddleware",
    "csp.middleware.CSPMiddleware",
    "open_inwoner.custom_csp.middleware.SkipStaffCSPMiddleware",
    "open_inwoner.custom_csp.middleware.UpdateCSPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "maykin_2fa.middleware.OTPMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "cms.middleware.utils.ApphookReloadMiddleware",
    "cms.middleware.user.CurrentUserMiddleware",
    "cms.middleware.page.CurrentPageMiddleware",
    "cms.middleware.toolbar.ToolbarMiddleware",
    "cms.middleware.language.LanguageCookieMiddleware",
    "open_inwoner.cms.utils.middleware.DropToolbarMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "open_inwoner.extended_sessions.middleware.SessionTimeoutMiddleware",
    "open_inwoner.kvk.middleware.KvKLoginMiddleware",
    "open_inwoner.accounts.middleware.NecessaryFieldsMiddleware",
    "open_inwoner.accounts.middleware.EmailVerificationMiddleware",
    "open_inwoner.cms.utils.middleware.AnonymousHomePageRedirectMiddleware",
    "mozilla_django_oidc_db.middleware.SessionRefresh",
]

ROOT_URLCONF = "open_inwoner.urls"

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(DJANGO_PROJECT_DIR, "templates")],
        "APP_DIRS": False,  # conflicts with explicity specifying the loaders
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "open_inwoner.utils.context_processors.settings",
                "open_inwoner.cms.context_processors.active_apphooks",
                "sekizai.context_processors.sekizai",
                "cms.context_processors.cms_settings",
                "django.template.context_processors.i18n",
            ],
            "loaders": TEMPLATE_LOADERS,
        },
    },
]
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

WSGI_APPLICATION = "open_inwoner.wsgi.application"

# Translations
LOCALE_PATHS = (os.path.join(DJANGO_PROJECT_DIR, "conf", "locale"),)

#
# SERVING of static and media files
#

STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Additional locations of static files
STATICFILES_DIRS = [os.path.join(DJANGO_PROJECT_DIR, "static")]

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_SUBFOLDER = config(
    "MEDIA_SUBFOLDER",
    default="",
    documentation=DocumentationParams(
        help_text=(
            "Optional subdirectory appended to MEDIA_ROOT and PRIVATE_MEDIA_ROOT. "
            "Useful for separating media files across deployments sharing the same storage."
        ),
        group="Application",
    ),
)

if MEDIA_SUBFOLDER:
    MEDIA_ROOT = os.path.join(MEDIA_ROOT, MEDIA_SUBFOLDER)

MEDIA_URL = "/media/"

FILE_UPLOAD_PERMISSIONS = 0o644

#
# Sending EMAIL
#
EMAIL_HOST = config(
    "EMAIL_HOST",
    default="localhost",
    documentation=DocumentationParams(
        help_text="Hostname of the SMTP server used to send outgoing email.",
        group="Email",
    ),
)
EMAIL_PORT = config(
    "EMAIL_PORT",
    default=25,
    documentation=DocumentationParams(
        help_text="Port of the SMTP server. Port 25 is blocked on Google Cloud; use 587 instead.",
        group="Email",
    ),
)  # disabled on Google Cloud, use 487 instead
EMAIL_HOST_USER = config(
    "EMAIL_HOST_USER",
    default="",
    documentation=DocumentationParams(
        help_text="Username for SMTP authentication. Leave empty if the server does not require auth.",
        group="Email",
    ),
)
EMAIL_HOST_PASSWORD = config(
    "EMAIL_HOST_PASSWORD",
    default="",
    documentation=DocumentationParams(
        help_text="Password for SMTP authentication.",
        group="Email",
    ),
)
EMAIL_USE_TLS = config(
    "EMAIL_USE_TLS",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable STARTTLS when connecting to the SMTP server.",
        group="Email",
    ),
)
EMAIL_TIMEOUT = 10

DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="openinwoner@maykinmedia.nl",
    documentation=DocumentationParams(
        help_text="Default sender address for outgoing email.",
        group="Email",
    ),
)

EMAIL_BACKEND = "django_yubin.backends.QueuedEmailBackend"
MAILER_USE_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

#
# LOGGING
#
LOG_STDOUT = config(
    "LOG_STDOUT",
    default=False,
    documentation=DocumentationParams(
        help_text=(
            "Write application and request logs to stdout instead of rotating log files. "
            "Enable in containerised deployments where stdout is collected by the platform."
        ),
        group="Logging",
    ),
)
CELERY_LOGLEVEL = config(
    "CELERY_LOGLEVEL",
    default="INFO",
    documentation=DocumentationParams(
        help_text="Log level for Celery workers. One of DEBUG, INFO, WARNING, ERROR, CRITICAL.",
        group="Logging",
    ),
)

LOGGING_DIR = os.path.join(BASE_DIR, "log")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamped": {"format": "%(asctime)s %(levelname)s %(name)s  %(message)s"},
        "simple": {"format": "%(levelname)s  %(message)s"},
        "performance": {
            "format": "%(asctime)s %(process)d | %(thread)d | %(message)s",
        },
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                ExtractRequestAndResponseDetails(),
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.format_exc_info,
            ],
        },
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(pad_level=False),
            "foreign_pre_chain": [
                ExtractRequestAndResponseDetails(),
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.format_exc_info,
            ],
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": config(
                "LOG_FORMAT_CONSOLE",
                default="plain_console",
                documentation=DocumentationParams(
                    help_text=(
                        "Formatter to use for console log output. "
                        "Use 'json' for machine-readable output or 'plain_console' for human-readable output."
                    ),
                    group="Logging",
                ),
            ),
        },
        "django": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGGING_DIR, "django.log"),
            "formatter": "json",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
        },
        "project": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGGING_DIR, "open_inwoner.log"),
            "formatter": "json",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
        },
        "performance": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGGING_DIR, "performance.log"),
            "formatter": "performance",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
        },
        "save_outgoing_requests": {
            "level": "DEBUG",
            "class": "log_outgoing_requests.handlers.DatabaseOutgoingRequestsHandler",
        },
    },
    "loggers": {
        "open_inwoner": {
            "handlers": ["project"] if not LOG_STDOUT else ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["django"] if not LOG_STDOUT else ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.template": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "digid_eherkenning": {
            "handlers": ["django"] if not LOG_STDOUT else ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "log_outgoing_requests": {
            "handlers": (["project"] if not LOG_STDOUT else ["console"])
            + ["save_outgoing_requests"],
            "level": "DEBUG",
            "propagate": True,
        },
        "opentelemetry": {
            "handlers": ["django"] if not LOG_STDOUT else ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "opentelemetry.metrics": {
            "handlers": ["django"] if not LOG_STDOUT else ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "opentelemetry.sdk.metrics": {
            "handlers": ["django"] if not LOG_STDOUT else ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "django_structlog": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        # Capture exceptions for Sentry BEFORE any formatting happens.
        # This ensures Sentry receives raw exception objects with full stack traces
        # and all the context from the event dict.
        SentryStructlogProcessor(),
        # Format exceptions for display in logs. This happens AFTER Sentry has
        # captured the raw exception, so both Sentry (proper exception) and logs
        # (formatted traceback) work correctly.
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

#
# DJANGO-STRUCTLOG
#
DJANGO_STRUCTLOG_IP_LOGGING_ENABLED = False
DJANGO_STRUCTLOG_CELERY_ENABLED = True


#
# LOG OUTGOING REQUESTS
#
LOG_OUTGOING_REQUESTS_DB_SAVE = config(
    "LOG_OUTGOING_REQUESTS_DB_SAVE",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Persist outgoing HTTP request logs to the database so they are "
            "viewable in the admin interface."
        ),
        group="Logging",
    ),
)
LOG_OUTGOING_REQUESTS_RESET_DB_SAVE_AFTER = None  # reset config after $ minutes


#
# AUTH settings - user accounts, passwords, backends...
#
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "open_inwoner.utils.validators.DiversityValidator"},
]


# Allow logging in with email+password
AUTHENTICATION_BACKENDS = [
    "open_inwoner.accounts.backends.CustomAxesBackend",
    "open_inwoner.accounts.backends.UserModelEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    "digid_eherkenning.backends.DigiDBackend",
    "eherkenning.backends.eHerkenningBackend",
    "open_inwoner.accounts.backends.DigiDOIDCBackend",
    "open_inwoner.accounts.backends.EHerkenningOIDCBackend",
    "open_inwoner.accounts.backends.EIDASOIDCBackend",
    "open_inwoner.accounts.backends.CustomOIDCBackend",
]


SESSION_COOKIE_NAME = "open_inwoner_sessionid"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

ADMIN_SESSION_COOKIE_AGE = config(
    "ADMIN_SESSION_COOKIE_AGE",
    default=3600,
    documentation=DocumentationParams(
        help_text=(
            "Maximum admin session duration in seconds. "
            "Sessions older than this are invalidated to reduce the window for session hijacking."
        ),
        group="Security",
    ),
)  # Default 1 hour max session duration for admins
SESSION_WARN_DELTA = 120  # Warn 2 minutes before end of session.
SESSION_COOKIE_AGE = 900  # Set to 15 minutes or less for testing

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

OIDC_FRONTEND_LOGOUT_WITH_HINTS = config(
    "OIDC_FRONTEND_LOGOUT_WITH_HINTS",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Pass login_hint and id_token_hint when redirecting to the IdP logout endpoint. "
            "Enables single-logout for OIDC sessions."
        ),
        group="Security",
    ),
)

#
# SECURITY settings
#
SESSION_COOKIE_SECURE = IS_HTTPS
SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_SECURE = IS_HTTPS
CSRF_USE_SESSIONS = True  # Because cookie csrf makes pen testers uncomfortable
CSRF_FAILURE_VIEW = "open_inwoner.accounts.views.csrf_failure"

if IS_HTTPS:
    SECURE_HSTS_SECONDS = 31536000

# X_FRAME_OPTIONS = "DENY"
X_FRAME_OPTIONS = "SAMEORIGIN"

#
# FIXTURES
#

FIXTURE_DIRS = (os.path.join(DJANGO_PROJECT_DIR, "conf", "fixtures"),)

#
# Custom settings
#
PROJECT_NAME = "open_inwoner"
ENVIRONMENT = config(
    "ENVIRONMENT",
    default="",
    documentation=DocumentationParams(
        help_text=(
            "Name of the deployment environment (e.g. production, staging, review). "
            "Included in Sentry reports and the admin page title."
        ),
        group="Monitoring",
    ),
)
SHOW_ALERT = True

##############################
#                            #
# 3RD PARTY LIBRARY SETTINGS #
#                            #
##############################

#
# Django CMS
#

CMS_PAGE_CACHE = False
CMS_PLACEHOLDER_CACHE = False
CMS_PLUGIN_CACHE = False

# The page creation wizard defaults to creating a TextPlugin pre-filled with
# the wizard's content field. The content field is a plain textarea (we no
# longer use djangocms_text_ckeditor), so the raw string would be stored
# directly as the Prosemirror body field, bypassing JSON serialisation.
# Disabling the body field prevents the wizard from creating a broken plugin.
CMS_PAGE_WIZARD_CONTENT_PLUGIN_BODY = ""

CMS_TEMPLATES = [
    ("cms/fullwidth.html", "Home page template"),
    ("cms/cms_flatpage_template.html", "CMS Flatpage Template"),
    ("cms/contactform/form_outer.html", "CMS Contactformulier Template"),
]
CMS_PLACEHOLDER_CONF = {
    # TODO properly configure this based on actual available plugins
    None: {
        "plugins": ["TextPlugin"],
        "excluded_plugins": ["InheritPlugin"],
    },
    "content": {
        "plugins": [
            "TextPlugin",
            "PicturePlugin",
            "VideoPlayerPlugin",
            "CategoriesPlugin",
            "ActivePlansPlugin",
            "QuestionnairePlugin",
            "ProductFinderPlugin",
            "ProductLocationPlugin",
            "UserFeedPlugin",
            "UserAppointmentsPlugin",
            "TasksPlugin",
            "CMSFlatPagePlugin",
            "CMSLinkPlugin",
            "CMSZakenPlugin",
        ],
        "text_only_plugins": ["LinkPlugin"],
        "name": _("Content"),
        "language_fallback": True,
    },
    "banner_image": {"plugins": ["BannerImagePlugin"], "name": _("Banner Image")},
    "banner_text": {"plugins": ["BannerTextPlugin"], "name": _("Banner Text")},
    "login_banner": {"plugins": ["BannerImagePlugin"], "name": _("Login Banner")},
    "footer_left": {
        "name": _("Footer, Left"),
        "plugins": ["TextPlugin", "LinkPlugin", "FooterPagesPlugin"],
        "child_classes": {
            "TextPlugin": ["LinkPlugin"],
        },
    },
    "footer_center": {
        "name": _("Footer, Center"),
        "plugins": ["TextPlugin", "LinkPlugin", "FooterPagesPlugin"],
        "child_classes": {
            "TextPlugin": ["LinkPlugin"],
        },
    },
    "footer_right": {
        "name": _("Footer, Right"),
        "plugins": ["TextPlugin", "LinkPlugin", "FooterPagesPlugin"],
        "child_classes": {
            "TextPlugin": ["LinkPlugin"],
        },
    },
    "contact_form": {
        "name": _("Contact form plugin"),
        "plugins": ["ContactFormPlugin"],
    },
    "cms_flatpage": {
        "name": _("CMS flatpage plugin"),
        "plugins": ["CMSFlatPagePlugin"],
    },
}

CMS_TOOLBAR_ANONYMOUS_ON = False

# Needed to run the cms4_migration
CMS_CONFIRM_VERSION4 = True

# This project uses email as the User.USERNAME_FIELD (no 'username' column).
# djangocms-versioning defaults to 'username' — override it here.
DJANGOCMS_VERSIONING_USERNAME_FIELD = "email"

DJANGOCMS_LINK_TEMPLATES = [
    ("arrow", _("Arrow")),
]

# Styling for rich text fields
DJANGO_PROSEMIRROR = {"tag_to_classes": {"p": "nl-paragraph"}}

#
# Django-Admin-Index
#
ADMIN_INDEX_SHOW_REMAINING_APPS = False
ADMIN_INDEX_AUTO_CREATE_APP_GROUP = False
ADMIN_INDEX_SHOW_REMAINING_APPS_TO_SUPERUSERS = False
ADMIN_INDEX_SHOW_MENU = True
ADMIN_INDEX_DISPLAY_DROP_DOWN_MENU_CONDITION_FUNCTION = (
    "open_inwoner.utils.django_two_factor_auth.should_display_dropdown_menu"
)


#
# DJANGO-AXES (4.0+)
#
AXES_CACHE = "axes"  # refers to CACHES setting
# The number of login attempts allowed before a record is created for the
# failed logins. Default: 3
AXES_FAILURE_LIMIT = 5
# If set, defines a period of inactivity after which old failed login attempts
# will be forgotten. Can be set to a python timedelta object or an integer. If
# an integer, will be interpreted as a number of hours. Default: None
AXES_COOLOFF_TIME = 1
# If True only locks based on user id and never locks by IP if attempts limit
# exceed, otherwise utilize the existing IP and user locking logic Default:
# False
AXES_ONLY_USER_FAILURES = True
# If set, specifies a template to render when a user is locked out. Template
# receives cooloff_time and failure_limit as context variables. Default: None
AXES_LOCKOUT_TEMPLATE = "account_blocked.html"
AXES_USE_USER_AGENT = True  # Default: False
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # Default: False
AXES_BEHIND_REVERSE_PROXY = IS_HTTPS
# By default, Axes obfuscates values for formfields named "password", but the admin
# interface login formfield name is "auth-password", so we obfuscate that as well
AXES_SENSITIVE_PARAMETERS = ["password", "auth-password"]  # nosec

# The default meta precedence order
IPWARE_META_PRECEDENCE_ORDER = (
    "HTTP_X_FORWARDED_FOR",
    "X_FORWARDED_FOR",  # <client>, <proxy1>, <proxy2>
    "HTTP_CLIENT_IP",
    "HTTP_X_REAL_IP",
    "HTTP_X_FORWARDED",
    "HTTP_X_CLUSTER_CLIENT_IP",
    "HTTP_FORWARDED_FOR",
    "HTTP_FORWARDED",
    "HTTP_VIA",
    "REMOTE_ADDR",
)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

#
# CELERY - async task queue
#
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_TASK_TIME_LIMIT = config(
    "CELERY_TASK_HARD_TIME_LIMIT",
    default=15 * 60,
    documentation=DocumentationParams(
        help_text=(
            "Hard time limit in seconds for Celery tasks. "
            "A task exceeding this limit is forcibly terminated."
        ),
        group="Celery",
    ),
)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
# https://docs.celeryq.dev/en/latest/userguide/periodic-tasks.html#beat-entries
CELERY_BEAT_SCHEDULE = {
    # Note that the keys here will be used to give human-readable names
    # to the periodic task entries, which will be visible to users in the
    # admin interface. Unfortunately, we we cannot use gettext here (even
    # in lazy mode): Django allows it, Celery does not. We could consider
    # doing this registration in one of the Celery hooks, but until this
    # becomes a painpoint, it's cleaner to have the schedule easily accessible
    # here in the settings file.
    "Importeer ZGW data": {
        "task": "open_inwoner.openzaak.tasks.import_zgw_data",
        "schedule": crontab(minute="0", hour="7", day_of_month="*"),
    },
    "Zoekindex opnieuw opbouwen": {
        "task": "open_inwoner.search.tasks.rebuild_search_index",
        "schedule": crontab(minute="0", hour="4", day_of_month="*"),
    },
    "Dagelijkse misluke email samenvatting": {
        "task": "open_inwoner.configurations.tasks.send_failed_mail_digest",
        "schedule": crontab(minute="0", hour="7", day_of_month="*"),
    },
    "Probeer emails opnieuw te sturen": {
        "task": "django_yubin.tasks.retry_emails",
        "schedule": crontab(minute="1", hour="*", day_of_month="*"),
    },
    "Verwijder oude emails": {
        "task": "django_yubin.tasks.delete_old_emails",
        "schedule": crontab(minute="0", hour="6", day_of_month="*"),
    },
    "Verzend emails in het kader van taken": {
        "task": "open_inwoner.accounts.tasks.schedule_user_notifications",
        "schedule": crontab(minute="15", hour="9", day_of_month="*"),
        "kwargs": {
            "notify_about": "actions",
            "channel": "email",
        },
    },
    "Verzend emails in het kader van samenwerkingen": {
        "task": "open_inwoner.accounts.tasks.schedule_user_notifications",
        "schedule": crontab(minute="5", hour="9", day_of_month="*"),
        "kwargs": {
            "notify_about": "plans",
            "channel": "email",
        },
    },
    "Verzend emails in het kader van berichten": {
        "task": "open_inwoner.accounts.tasks.schedule_user_notifications",
        "schedule": crontab(minute="*/15", hour="*", day_of_month="*"),
        "kwargs": {
            "notify_about": "messages",
            "channel": "email",
        },
    },
    "Opschonen uitgaande request-logs": {
        "task": "log_outgoing_requests.tasks.prune_logs",
        "schedule": crontab(hour=0, minute=0),
    },
    "Opschonen notificatieberichten": {
        "task": "notifications.tasks.prune_notification_records",
        "schedule": crontab(hour=3, minute=0),
    },
}

# Only ACK when the task has been executed. This prevents tasks from getting lost, with
# the drawback that tasks should be idempotent (if they execute partially, the mutations
# executed will be executed again!)
# CELERY_TASK_ACKS_LATE = True

# ensure that no tasks are scheduled to a worker that may be running a very long-running
# operation, leading to idle workers and backed-up workers. The `-O fair` option
# *should* have the same effect...
CELERY_WORKER_PREFETCH_MULTIPLIER = 1


#
# SENTRY - error monitoring
#
SENTRY_DSN = config(
    "SENTRY_DSN",
    default=None,
    documentation=DocumentationParams(
        help_text=(
            "Sentry Data Source Name (DSN) for error reporting. "
            "Leave empty to disable Sentry."
        ),
        group="Monitoring",
    ),
)
RELEASE = "v2.4.1"  # get_current_version()

PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, "private_media")
FILER_ROOT = os.path.join(BASE_DIR, "media", "filer")
FILER_THUMBNAIL_ROOT = os.path.join(BASE_DIR, "media", "filer_thumbnails")
if MEDIA_SUBFOLDER:
    PRIVATE_MEDIA_ROOT = os.path.join(PRIVATE_MEDIA_ROOT, MEDIA_SUBFOLDER)
    FILER_ROOT = os.path.join(FILER_ROOT, MEDIA_SUBFOLDER)
    FILER_THUMBNAIL_ROOT = os.path.join(FILER_THUMBNAIL_ROOT, MEDIA_SUBFOLDER)

FILER_STORAGES = {
    "public": {
        "main": {
            "OPTIONS": {
                "location": FILER_ROOT,
                "base_url": "/media/filer/",
            },
        },
        "thumbnails": {
            "OPTIONS": {
                "location": FILER_THUMBNAIL_ROOT,
                "base_url": "/media/filer_thumbnails/",
            },
        },
    },
}


THUMBNAIL_PROCESSORS = (
    "filer.thumbnail_processors.scale_and_crop_with_subject_location",
    "image_cropping.thumbnail_processors.crop_corners",
) + ThumbnailSettings.THUMBNAIL_PROCESSORS

THUMBNAIL_HIGH_RESOLUTION = True

IMAGE_CROPPING_BACKEND = "image_cropping.backends.easy_thumbs.EasyThumbnailsBackend"
IMAGE_CROPPING_JQUERY_URL = "/static/admin/js/vendor/jquery/jquery.min.js"

PRIVATE_MEDIA_URL = "/private_files/"

SENDFILE_ROOT = PRIVATE_MEDIA_ROOT
# django-sendfile2 requires SENDFILE_URL; keep it equal to the privates storage base_url.
SENDFILE_URL = PRIVATE_MEDIA_URL
SENDFILE_BACKEND = "django_sendfile.backends.simple"

# django-privates 4.x dropped its own PRIVATE_MEDIA_* settings and now resolves its
# storage from STORAGES["privates"]. We keep PRIVATE_MEDIA_ROOT/URL as the single
# source of truth (django-sendfile2 still reads SENDFILE_ROOT above) and wire them in
# here. `default` and `staticfiles` are re-declared with Django's defaults because
# defining STORAGES replaces the built-in defaults wholesale.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "privates": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": PRIVATE_MEDIA_ROOT,
            "base_url": PRIVATE_MEDIA_URL,
        },
    },
}

CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = True


CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    split=True,
    default=CORS_ALLOWED_ORIGINS,
    documentation=DocumentationParams(
        help_text=(
            "Comma-separated list of origins trusted for CSRF verification. "
            "Required when the application is accessed via a different domain or through a reverse proxy."
        ),
        group="Security",
    ),
)

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"

REST_FRAMEWORK = {
    # YOUR SETTINGS
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        # Any other renders
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        # Any other parsers
    ),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Open Inwoner API",
    "DESCRIPTION": "Description",
    "VERSION": "1.0.0",
    # OTHER SETTINGS
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "SERVE_INCLUDE_SCHEMA": False,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
    ],
}

if SENTRY_DSN:
    SENTRY_CONFIG = {
        "dsn": SENTRY_DSN,
        "environment": ENVIRONMENT,
        "release": RELEASE,
    }

    sentry_sdk.init(
        **SENTRY_CONFIG,
        traces_sample_rate=0,
        integrations=get_sentry_integrations(),
        send_default_pii=True,
        before_send=SentryStructlogProcessor.before_send,
    )

# Elastic APM
ELASTIC_APM_SERVER_URL = os.getenv("ELASTIC_APM_SERVER_URL", None)
ELASTIC_APM = {
    "SERVICE_NAME": f"open_inwoner {ENVIRONMENT}",
    "SECRET_TOKEN": config(
        "ELASTIC_APM_SECRET_TOKEN",
        default="default",
        documentation=DocumentationParams(
            help_text="Secret token for authenticating with the Elastic APM server.",
            group="Monitoring",
        ),
    ),
    "SERVER_URL": ELASTIC_APM_SERVER_URL,
}
if not ELASTIC_APM_SERVER_URL:
    ELASTIC_APM["ENABLED"] = False
    ELASTIC_APM["SERVER_URL"] = "http://localhost:8200"


# geopy
GEOPY_APP = "Openinwoner"
GEOPY_TIMEOUT = 10  # in seconds
LOCATIESERVER_DOMAIN = "api.pdok.nl/bzk/locatieserver/search/v3_1"
GEOCODER = "open_inwoner.utils.geocode.PdocLocatieserver"


# ELASTICSEARCH CONFIG
_es_username = config(
    "ES_USERNAME",
    default="",
    documentation=DocumentationParams(
        help_text="Username for Elasticsearch basic authentication. Must be set together with ES_PASSWORD.",
        group="Elasticsearch",
    ),
)
_es_password = config(
    "ES_PASSWORD",
    default="",
    documentation=DocumentationParams(
        help_text="Password for Elasticsearch basic authentication. Must be set together with ES_USERNAME.",
        group="Elasticsearch",
    ),
)
if bool(_es_username) ^ bool(_es_password):
    raise ImproperlyConfigured(
        "Both ES_USERNAME and ES_PASSWORD must be set to enable Elasticsearch "
        "authentication. Only one of the two is currently configured."
    )
_es_connection: dict = {
    "hosts": config(
        "ES_HOST",
        default="http://localhost:9200",
        documentation=DocumentationParams(
            help_text="URL of the Elasticsearch node, including scheme and port.",
            group="Elasticsearch",
        ),
    )
}
if _es_username and _es_password:
    _es_connection["basic_auth"] = (_es_username, _es_password)
ELASTICSEARCH_DSL = {"default": _es_connection}
ES_INDEX_PRODUCTS = config(
    "ES_INDEX_PRODUCTS",
    default="products",
    documentation=DocumentationParams(
        help_text="Elasticsearch index name for PDC product records.",
        group="Elasticsearch",
    ),
)
ES_INDEX_CMS_PAGES = config(
    "ES_INDEX_CMS_PAGES",
    default="cms_pages",
    documentation=DocumentationParams(
        help_text="Elasticsearch index name for CMS page records.",
        group="Elasticsearch",
    ),
)
ES_MAX_SIZE = 10000
ES_SUGGEST_SIZE = 5

# Triggers indexing on each model save. Requires Elasticsearch to be available and
# correctly configured, otherwise this can cause 500s on admin operations.
# Set to False to disable autosync and rely on the Celery index rebuild task instead.
ELASTICSEARCH_DSL_AUTO_REFRESH = config("ELASTICSEARCH_DSL_AUTO_REFRESH", default=True)
ELASTICSEARCH_DSL_AUTOSYNC = config("ELASTICSEARCH_DSL_AUTOSYNC", default=True)

# Search page pagination trigger
RESULTS_PER_PAGE = config(
    "RESULTS_PER_PAGE",
    default=9,
    documentation=DocumentationParams(
        help_text="Number of search results shown per page.",
        group="Elasticsearch",
    ),
)

# django import-export
IMPORT_EXPORT_USE_TRANSACTIONS = True

# invite expires in X days after sending
INVITE_EXPIRY_DAYS = config(
    "INVITE_EXPIRY_DAYS",
    default=30,
    documentation=DocumentationParams(
        help_text="Number of days before a user invitation link expires.",
        group="Application",
    ),
)

# zgw-consumers
ZGW_CONSUMERS_TEST_SCHEMA_DIRS = [
    os.path.join(DJANGO_PROJECT_DIR, "openzaak", "tests", "files"),
    os.path.join(DJANGO_PROJECT_DIR, "openklant", "tests", "files"),
]

# The maximum number of workers to use when concurrently fetching and resolving
# cases on the "Mijn Zaken" page
ZGW_CASE_LIST_NUM_WORKERS = (
    config(
        "ZGW_CASE_LIST_NUM_WORKERS",
        default=0,
        documentation=DocumentationParams(
            help_text=(
                "Number of threads used to concurrently fetch cases on the Mijn Zaken page. "
                "Set to 0 to use the library default."
            ),
            group="ZGW",
        ),
    )
    # Because auto config has no clean way to express "int | None", and we want to fall
    # back to the library default
    or None
)

# The aggregate number of seconds workers can concurrently fetch and resolve
# cases on the "Mijn Zaken" page. Should be set to slightly less than the overall
# timeout.
ZGW_CASE_LIST_FETCH_TIMEOUT = config(
    "ZGW_CASE_LIST_FETCH_TIMEOUT",
    default=25,
    documentation=DocumentationParams(
        help_text=(
            "Total seconds the Mijn Zaken worker pool may spend fetching cases. "
            "Should be slightly less than the overall request timeout."
        ),
        group="ZGW",
    ),
)

# Timeout in seconds for the login cache warm-up task per API group.
# Needs to be longer than ZGW_CASE_LIST_FETCH_TIMEOUT because the warm-up fetches
# status history, roles, and documents on top of what the list view resolves.
ZGW_CACHE_WARMUP_TIMEOUT = config(
    "ZGW_CACHE_WARMUP_TIMEOUT",
    default=120,
    documentation=DocumentationParams(
        help_text=(
            "Seconds the login cache warm-up task may run per API group. "
            "Must exceed ZGW_CASE_LIST_FETCH_TIMEOUT because the warm-up fetches "
            "additional data (statuses, roles, documents)."
        ),
        group="ZGW",
    ),
)

# Celery queue to use for cache-seeding tasks (IO-bound, latency-sensitive).
# Operators may dedicate a separate high-priority queue/worker pool for these.
# Defaults to Celery's built-in default queue so no extra infrastructure is
# needed out of the box.
CACHE_SEEDING_QUEUE = config(
    "CACHE_SEEDING_QUEUE",
    default="celery",
    documentation=DocumentationParams(
        help_text=(
            "Celery queue for cache-seeding tasks. "
            "Point this to a dedicated high-priority queue to keep warm-up latency low."
        ),
        group="Celery",
    ),
)

# notifications
ZGW_LIMIT_NOTIFICATIONS_FREQUENCY = config(
    "ZGW_LIMIT_NOTIFICATIONS_FREQUENCY",
    default=60 * 15,
    documentation=DocumentationParams(
        help_text=(
            "Minimum seconds between duplicate ZGW notifications for the same zaak. "
            "Prevents notification storms when the same event is delivered multiple times."
        ),
        group="ZGW",
    ),
)

# recent documents: created/added no longer than n days in the past
DOCUMENT_RECENT_DAYS = config(
    "DOCUMENT_RECENT_DAYS",
    default=1,
    documentation=DocumentationParams(
        help_text="Documents created within this many days are labelled as recent in the UI.",
        group="ZGW",
    ),
)

# recent answers to contactmomenten: no longer than n days in the past
CONTACTMOMENT_NEW_DAYS = config(
    "CONTACTMOMENT_NEW_DAYS",
    default=7,
    documentation=DocumentationParams(
        help_text="Contactmoment answers created within this many days are shown as new in the UI.",
        group="ZGW",
    ),
)

#
# Maykin 2FA
#
TWO_FACTOR_PATCH_ADMIN = False
TWO_FACTOR_WEBAUTHN_RP_NAME = f"OpenInwoner {ENVIRONMENT}"
TWO_FACTOR_WEBAUTHN_AUTHENTICATOR_ATTACHMENT = "cross-platform"
# Allow OIDC admins to bypass 2FA
MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS = [
    "open_inwoner.accounts.backends.CustomOIDCBackend",
]

# file upload limits
MIN_UPLOAD_SIZE = 1  # in bytes
MAX_UPLOAD_SIZE = 1024**2 * 100  # 100MB
UPLOAD_FILE_TYPES = "application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/plain,application/vnd.oasis.opendocument.text,application/vnd.oasis.opendocument.formula,application/vnd.oasis.opendocument.spreadsheet,application/pdf,image/jpeg,image/png"

#
# DIGID
#
DIGID_ENABLED = config(
    "DIGID_ENABLED",
    default=True,
    documentation=DocumentationParams(
        help_text="Enable DigiD authentication. Set to False to hide DigiD login options.",
        group="Authentication",
    ),
)
DIGID_MOCK = config(
    "DIGID_MOCK",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Use the DigiD mock backend instead of the real SAML integration. "
            "Must be False in production."
        ),
        group="Authentication",
    ),
)

#
# EHERKENNING
#
EHERKENNING_MOCK = config(
    "EHERKENNING_MOCK",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Use the eHerkenning mock backend instead of the real SAML integration. "
            "Must be False in production."
        ),
        group="Authentication",
    ),
)

THUMBNAIL_ALIASES = {
    "": {
        "logo": {
            "size": (21600, 60),
            "upscale": False,
        },
        "card-image": {
            "size": (256, 320),
            "crop": True,
        },
        "avatar": {"size": (160, 160), "crop": True, "upscale": False},
    }
}
THUMBNAIL_QUALITY = 100

OIDC_AUTHENTICATE_CLASS = "mozilla_django_oidc_db.views.OIDCAuthenticationRequestView"
OIDC_CALLBACK_CLASS = "mozilla_django_oidc_db.views.OIDCCallbackView"
OIDC_AUTHENTICATION_CALLBACK_URL = "oidc_authentication_callback"
# ID token is required to enable OIDC logout
OIDC_STORE_ID_TOKEN = True

OIDC_USE_LEGACY_ENDPOINTS = config(
    "OIDC_USE_LEGACY_ENDPOINTS",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Deprecated: advertise the legacy per-provider OIDC callback URLs "
            "(e.g. /digid-oidc/callback/) as the redirect_uri sent to the IdP, "
            "instead of the generic /oidc/callback/ endpoint. Kept for backwards "
            "compatibility with identity providers that whitelist the legacy "
            "URLs. Set to False once every IdP whitelist has been updated to "
            "allow the generic callback endpoint; this setting will be removed "
            "in a future release."
        ),
        group="Security",
    ),
)

# Amount of elapsed time before redirecting the user back to the IdP for re-authentication
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = config(
    "OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS",
    default=15 * 60,
    documentation=DocumentationParams(
        help_text=(
            "Seconds before an OIDC session is considered stale and the user is "
            "redirected to the IdP for re-authentication."
        ),
        group="Security",
    ),
)

# In order to support zaaktypeconfig admin screens with many statusses/results
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

#
# 2FA SMS Verification
#

ACCOUNTS_USER_TOKEN_EXPIRE_TIME = 300
ACCOUNTS_SMS_MESSAGE = _("Inlogcode: {token} (deze code is 5 minuten geldig.)")
ACCOUNTS_SMS_GATEWAY = {
    "BACKEND": config(
        "ACCOUNTS_SMS_GATEWAY_BACKEND",
        default="open_inwoner.accounts.gateways.Dummy",
        documentation=DocumentationParams(
            help_text=(
                "Python dotted path to the SMS gateway backend class. "
                "Use the Dummy backend for local development."
            ),
            group="Authentication",
        ),
    ),
    "API_KEY": config(
        "ACCOUNTS_SMS_GATEWAY_API_KEY",
        default="openinwoner",
        documentation=DocumentationParams(
            help_text="API key for the configured SMS gateway.",
            group="Authentication",
        ),
    ),
    "ORIGINATOR": config(
        "ACCOUNTS_SMS_GATEWAY_ORIGINATOR",
        default="Gemeente",
        documentation=DocumentationParams(
            help_text="Sender name or number shown on SMS messages (max 11 alphanumeric characters).",
            group="Authentication",
        ),
    ),
}

from .app.csp import *  # noqa

SECURE_REFERRER_POLICY = "same-origin"


# mail-editor
from .parts.maileditor import (  # noqa
    MAIL_EDITOR_BASE_CONTEXT,
    MAIL_EDITOR_CONF,
    MAIL_EDITOR_DYNAMIC_CONTEXT,
)

if ALLOWED_HOSTS:
    BASE_URL = "https://{}".format(ALLOWED_HOSTS[0])
else:
    BASE_URL = "https://example.com"

MAIL_EDITOR_BASE_HOST = BASE_URL

CKEDITOR_CONFIGS = {
    "default": {
        "allowedContent": True,
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["Format"],  # Headings
            ["Bold", "Italic", "Underline"],
            ["NumberedList", "BulletedList"],
            ["Link", "Unlink"],
            ["Table", "HorizontalRule"],
            ["RemoveFormat", "Source"],
            ["Undo", "Redo"],
        ],
        "removeButtons": "TextColor,BGColor",  # Remove color-styling
        "versionCheck": False,
        "width": 600,
    },
    "mail_editor": {
        "allowedContent": True,
        "contentsCss": [
            "/static/mailcss/email.css"
        ],  # Enter the css file used to style the email.
        "height": 600,  # This is optional
        "entities": False,  # This is added because CKEDITOR escapes the ' when you do an if statement
    },
}

#
# django-setup-configuration
#
from .app.setup_configuration import *  # noqa

DJANGO_SETUP_CONFIG_TEMPLATE = "configurations/config_doc.rst"
DJANGO_SETUP_CONFIG_DOC_PATH = f"{BASE_DIR}/docs/configuration"
DJANGO_SETUP_CONFIG_CUSTOM_FIELDS = [
    {
        "field": "django_jsonform.models.fields.ArrayField",
        "description": "string, comma-delimited ('foo,bar,baz')",
    },
    {
        "field": "django.contrib.postgres.fields.ArrayField",
        "description": "string, comma-delimited ('foo,bar,baz')",
    },
    {
        "field": "django.db.models.fields.files.FileField",
        "description": "string representing the (absolute) path to a file, including file extension",
    },
    {
        "field": "privates.fields.PrivateMediaFileField",
        "description": "string representing the (absolute) path to a file, including file extension",
    },
]
