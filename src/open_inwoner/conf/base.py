import os

# Django-hijack (and Django-hijack-admin)
from django.urls import reverse_lazy

import sentry_sdk

from .utils import config, get_current_version, get_sentry_integrations

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
SITE_ID = config("SITE_ID", default=1)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

# NEVER run with DEBUG=True in production-like environments
DEBUG = config("DEBUG", default=False)

# = domains we're running on
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", split=True)

IS_HTTPS = config("IS_HTTPS", default=not DEBUG)

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "nl-nl"

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
        "ENGINE": config("DB_ENGINE", "django.contrib.gis.db.backends.postgis"),
        "NAME": config("DB_NAME", "open_inwoner"),
        "USER": config("DB_USER", "open_inwoner"),
        "PASSWORD": config("DB_PASSWORD", "open_inwoner"),
        "HOST": config("DB_HOST", "localhost"),
        "PORT": config("DB_PORT", 5432),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_DEFAULT', 'localhost:6379/0')}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
    "axes": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_AXES', 'localhost:6379/0')}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
}


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
    # Admin auth
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
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
    "rest_framework",
    "rest_framework.authtoken",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "drf_spectacular",
    "axes",
    "sniplates",
    "digid_eherkenning",
    # "hijack.contrib.admin", # This should be imported but it causes an error. So now there are
    "hijack",
    "localflavor",
    "treebeard",
    "easy_thumbnails",  # used by filer
    "filer",
    "mptt",  # used by filer
    "hijack.contrib.admin",
    "leaflet",
    "django_elasticsearch_dsl",
    "import_export",
    "solo",
    "colorfield",
    "view_breadcrumbs",
    "django_better_admin_arrayfield",
    # Project applications.
    "open_inwoner.accounts",
    "open_inwoner.components",
    "open_inwoner.ckeditor",
    "open_inwoner.pdc",
    "open_inwoner.search",
    "open_inwoner.utils",
    "open_inwoner.configurations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 'django.middleware.locale.LocaleMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "django_otp.middleware.OTPMiddleware",
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
            ],
            "loaders": TEMPLATE_LOADERS,
        },
    },
]

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

MEDIA_URL = "/media/"

FILE_UPLOAD_PERMISSIONS = 0o644

#
# Sending EMAIL
#
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config(
    "EMAIL_PORT", default=25
)  # disabled on Google Cloud, use 487 instead
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False)
EMAIL_TIMEOUT = 10

DEFAULT_FROM_EMAIL = "openinwoner@maykinmedia.nl"

#
# LOGGING
#
LOG_STDOUT = config("LOG_STDOUT", default=False)

LOGGING_DIR = os.path.join(BASE_DIR, "log")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(process)d %(thread)d  %(message)s"
        },
        "timestamped": {"format": "%(asctime)s %(levelname)s %(name)s  %(message)s"},
        "simple": {"format": "%(levelname)s  %(message)s"},
        "performance": {
            "format": "%(asctime)s %(process)d | %(thread)d | %(message)s",
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
            "formatter": "timestamped",
        },
        "django": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGGING_DIR, "django.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
        },
        "project": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGGING_DIR, "open_inwoner.log"),
            "formatter": "verbose",
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
    },
}

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
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Allow logging in with email+password
AUTHENTICATION_BACKENDS = [
    "open_inwoner.accounts.backends.CustomAxesBackend",
    "open_inwoner.accounts.backends.UserModelEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    "digid_eherkenning.backends.DigiDBackend",
]

SESSION_COOKIE_NAME = "open_inwoner_sessionid"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

LOGIN_REDIRECT_URL = reverse_lazy("root")
LOGOUT_REDIRECT_URL = reverse_lazy("root")

#
# SECURITY settings
#
SESSION_COOKIE_SECURE = IS_HTTPS
SESSION_COOKIE_HTTPONLY = False

CSRF_COOKIE_SECURE = IS_HTTPS
CSRF_FAILURE_VIEW = "open_inwoner.accounts.views.csrf_failure"

X_FRAME_OPTIONS = "DENY"

#
# FIXTURES
#

FIXTURE_DIRS = (os.path.join(DJANGO_PROJECT_DIR, "fixtures"),)

#
# Custom settings
#
PROJECT_NAME = "open_inwoner"
ENVIRONMENT = config("ENVIRONMENT", "")
SHOW_ALERT = True

##############################
#                            #
# 3RD PARTY LIBRARY SETTINGS #
#                            #
##############################

#
# Django-Admin-Index
#
ADMIN_INDEX_SHOW_REMAINING_APPS = False
ADMIN_INDEX_AUTO_CREATE_APP_GROUP = False
ADMIN_INDEX_SHOW_REMAINING_APPS_TO_SUPERUSERS = True

#
# DJANGO-AXES (4.0+)
#
AXES_CACHE = "axes"  # refers to CACHES setting
# The number of login attempts allowed before a record is created for the
# failed logins. Default: 3
AXES_FAILURE_LIMIT = 10
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
# DJANGO-HIJACK
#
HIJACK_LOGIN_REDIRECT_URL = "/"
HIJACK_LOGOUT_REDIRECT_URL = reverse_lazy("admin:accounts_user_changelist")
HIJACK_REGISTER_ADMIN = False
# This is a CSRF-security risk.
# See: http://django-hijack.readthedocs.io/en/latest/configuration/#allowing-get-method-for-hijack-views
HIJACK_ALLOW_GET_REQUESTS = True

#
# SENTRY - error monitoring
#
SENTRY_DSN = config("SENTRY_DSN", None)
RELEASE = get_current_version()

PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, "private_media")
SENDFILE_ROOT = PRIVATE_MEDIA_ROOT
SENDFILE_BACKEND = "django_sendfile.backends.simple"
PRIVATE_MEDIA_URL = "/private_files/"

CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = True

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "open_inwoner.api.accounts.serializers.RegisterSerializer"
}

REST_AUTH_SERIALIZERS = {
    "USER_DETAILS_SERIALIZER": "open_inwoner.api.accounts.serializers.users.UserCustomSerializer",
}

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
        **SENTRY_CONFIG, integrations=get_sentry_integrations(), send_default_pii=True
    )

# Elastic APM
ELASTIC_APM_SERVER_URL = os.getenv("ELASTIC_APM_SERVER_URL", None)
ELASTIC_APM = {
    "SERVICE_NAME": f"open_inwoner {ENVIRONMENT}",
    "SECRET_TOKEN": config("ELASTIC_APM_SECRET_TOKEN", "default"),
    "SERVER_URL": ELASTIC_APM_SERVER_URL,
}
if not ELASTIC_APM_SERVER_URL:
    ELASTIC_APM["ENABLED"] = False
    ELASTIC_APM["SERVER_URL"] = "http://localhost:8200"


# geopy
GEOPY_APP = "Openinwoner"
GEOPY_TIMEOUT = 10  # in seconds


# ELASTICSEARCH CONFIG
ELASTICSEARCH_DSL = {
    "default": {"hosts": config("ES_HOST", "localhost:9200")},
}
ES_INDEX_PRODUCTS = "products"
ES_MAX_SIZE = 10000

# Delete user after x days of inactivity
DELETE_USER_AFTER_X_DAYS_INACTIVE = 14

# django import-export
IMPORT_EXPORT_USE_TRANSACTIONS = True
