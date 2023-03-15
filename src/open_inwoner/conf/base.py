import os

# Django-hijack (and Django-hijack-admin)
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

import sentry_sdk

from log_outgoing_requests.formatters import HttpFormatter

from .utils import config, get_sentry_integrations

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
    "oidc": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_OIDC', 'localhost:6379/0')}",
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
CACHE_ZGW_CATALOGI_TIMEOUT = config("CACHE_ZGW_CATALOGI_TIMEOUT", default=60 * 15)
CACHE_ZGW_ZAKEN_TIMEOUT = config("CACHE_ZGW_ZAKEN_TIMEOUT", default=60 * 1)

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
    "drf_spectacular",
    "axes",
    "sniplates",
    "digid_eherkenning",
    # "hijack.contrib.admin", # This should be imported but it causes an error. So now there are
    "hijack",
    "localflavor",
    "treebeard",
    "easy_thumbnails",  # used by filer
    "image_cropping",
    "filer",
    "mptt",
    "hijack.contrib.admin",
    "django_elasticsearch_dsl",
    "import_export",
    "solo",
    "colorfield",
    "view_breadcrumbs",
    "django_better_admin_arrayfield",
    "simple_certmanager",
    "zgw_consumers",
    "notifications_api_common",
    "mail_editor",
    "ckeditor",
    "privates",
    "fontawesomefree",
    "timeline_logger",
    "csp",
    "cspreports",
    "mozilla_django_oidc",
    "mozilla_django_oidc_db",
    "sessionprofile",
    "openformsclient",
    "django_htmx",
    "django_yubin",
    "log_outgoing_requests",
    # Project applications.
    "open_inwoner.accounts",
    "open_inwoner.components",
    "open_inwoner.ckeditor5",
    "open_inwoner.pdc",
    "open_inwoner.plans",
    "open_inwoner.search",
    "open_inwoner.utils",
    "open_inwoner.configurations",
    "open_inwoner.haalcentraal",
    "open_inwoner.openzaak",
    "open_inwoner.questionnaire",
    "open_inwoner.extended_sessions",
    "open_inwoner.custom_csp",
]

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
    "csp.contrib.rate_limiting.RateLimitedCSPMiddleware",
    "csp.middleware.CSPMiddleware",
    "open_inwoner.custom_csp.middleware.UpdateCSPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "open_inwoner.extended_sessions.middleware.SessionTimeoutMiddleware",
    "open_inwoner.accounts.middleware.NecessaryFieldsMiddleware",
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
MEDIA_SUBFOLDER = config("MEDIA_SUBFOLDER", "")

if MEDIA_SUBFOLDER:
    MEDIA_ROOT = os.path.join(MEDIA_ROOT, MEDIA_SUBFOLDER)

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

DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="openinwoner@maykinmedia.nl")

EMAIL_BACKEND = "django_yubin.smtp_queue.EmailBackend"

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
        "outgoing_requests": {"()": HttpFormatter},
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
        "log_outgoing_requests": {
            "level": "DEBUG",
            "formatter": "outgoing_requests",
            "class": "logging.StreamHandler",
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
        "requests": {
            "handlers": ["log_outgoing_requests", "save_outgoing_requests"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


#
# LOG OUTGOING REQUESTS
#
LOG_OUTGOING_REQUESTS_DB_SAVE = config("LOG_OUTGOING_REQUESTS_DB_SAVE", default=False)


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
    "open_inwoner.accounts.backends.CustomOIDCBackend",
]

SESSION_COOKIE_NAME = "open_inwoner_sessionid"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
ADMIN_SESSION_COOKIE_AGE = 86400
SESSION_WARN_DELTA = 60  # Warn 1 minute before end of session.
SESSION_COOKIE_AGE = 900  # Set to 15 minutes

LOGIN_REDIRECT_URL = reverse_lazy("root")
LOGOUT_REDIRECT_URL = reverse_lazy("root")

#
# SECURITY settings
#
SESSION_COOKIE_SECURE = IS_HTTPS
SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_SECURE = IS_HTTPS
CSRF_FAILURE_VIEW = "open_inwoner.accounts.views.csrf_failure"

if IS_HTTPS:
    SECURE_HSTS_SECONDS = 63072000

X_FRAME_OPTIONS = "DENY"

#
# FIXTURES
#

FIXTURE_DIRS = (os.path.join(DJANGO_PROJECT_DIR, "conf", "fixtures"),)

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
ADMIN_INDEX_SHOW_REMAINING_APPS_TO_SUPERUSERS = False

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
RELEASE = "v1.0"  # get_current_version()

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

from easy_thumbnails.conf import Settings as thumbnail_settings

THUMBNAIL_PROCESSORS = (
    "image_cropping.thumbnail_processors.crop_corners",
) + thumbnail_settings.THUMBNAIL_PROCESSORS

IMAGE_CROPPING_BACKEND = "image_cropping.backends.easy_thumbs.EasyThumbnailsBackend"
IMAGE_CROPPING_JQUERY_URL = "/static/admin/js/vendor/jquery/jquery.min.js"

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
        traces_sample_rate=1,
        integrations=get_sentry_integrations(),
        send_default_pii=True,
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
LOCATIESERVER_DOMAIN = "geodata.nationaalgeoregister.nl/locatieserver/v3"
GEOCODER = "open_inwoner.utils.geocode.PdocLocatieserver"


# ELASTICSEARCH CONFIG
ELASTICSEARCH_DSL = {
    "default": {"hosts": config("ES_HOST", "localhost:9200")},
}
ES_INDEX_PRODUCTS = config("ES_INDEX_PRODUCTS", "products")
ES_MAX_SIZE = 10000
ES_SUGGEST_SIZE = 5

# Delete user after x days of inactivity
DELETE_USER_AFTER_X_DAYS_INACTIVE = 14

# django import-export
IMPORT_EXPORT_USE_TRANSACTIONS = True

# mail-editor
MAIL_EDITOR_CONF = {
    "invite": {
        "name": _("Invitation Email"),
        "description": _(
            "This email is used to invite people to sing up to the website"
        ),
        "subject_default": "Uitnodiging voor {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>Je bent door {{ inviter_name}} uitgenodigd om in te loggen op {{ site_name }}.
            Gebruik onderstaande link om je aan te melden </p>

            <p><a href="{{ invite_link }}">aanmelden</a> </p>

            <p>Mocht je geen behoefte hieraan hebben dan staat het je vrij om dit bericht te negeren </p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
        """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
            {"name": "inviter_name", "description": _("Full name of the inviter")},
        ],
        "body": [
            {
                "name": "inviter_name",
                "description": _("Full name of the inviter"),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
            {
                "name": "invite_link",
                "description": _("Link to activate their account."),
            },
            {"name": "email", "description": _("Email of the invited user")},
        ],
    },
    "contact_approval": {
        "name": _("Contact Approval Email"),
        "description": _(
            "This email is used to notify people for pending approvals of new contacts"
        ),
        "subject_default": "Goedkeuring geven op {{ site_name }}: {{ sender_name }} wilt u toevoegen als contactpersoon",
        "body_default": """
            <p>Beste</p>

            <p>Gebruiker {{ sender_name }} wilt u toevoegen als contactpersoon op {{ site_name }}.
            Volg onderstaande link waarop u uw goedkeuring kan geven of kan aangeven {{ sender_name }} niet als contactpersoon te willen. </p>

            <p><a href="{{ contacts_link }}">Mijn Contacten</a> </p>

            <p>U kunt ook op een later moment toestemming geven, het verzoek van {{ sender_name }} blijft open staat totdat u een keuze heeft gemaakt.</p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
        """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
            {
                "name": "sender_name",
                "description": _("Full name of the inviter-sender"),
            },
        ],
        "body": [
            {
                "name": "sender_name",
                "description": _("Full name of the inviter-sender"),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
            {
                "name": "contacts_link",
                "description": _("Link to contact list page."),
            },
            {"name": "email", "description": _("Email of the receiver user")},
        ],
    },
    "new_messages": {
        "name": _("New Message Email"),
        "description": _(
            "This email is used to inform users about the new messages in their inbox"
        ),
        "subject_default": "New messages at {{ site_name }}",
        "body_default": """
           <p>Beste</p>

           <p>You've received {{ total_messages }} new messages from {{ total_senders }} users</p>

           <p><a href="{{ inbox_link }}">Go to the inbox</a> </p>

           <p>Met vriendelijke groet,
           {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "total_messages",
                "description": _("Number of the new messages"),
            },
            {
                "name": "total_senders",
                "description": _("Number of the senders"),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
            {
                "name": "inbox_link",
                "description": _("Link to see the conversation."),
            },
        ],
    },
    "expiring_action": {
        "name": _("Action end date today"),
        "description": _(
            "This email is used to remind users that there are actions that are ending today"
        ),
        "subject_default": "Actions about to end today at {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>You are receiving this email because you have some actions that are expiring.</p>

            <table>
                <tr>
                    <td>Action name</td>
                    <td>End date</td>
                </tr>
            {% for action in actions %}
                <tr>
                    <td>{{ action.name }}</td>
                    <td>{{ action.end_date|date:"d-m-Y" }}</td>
                </tr>
            {% endfor %}
            </table>

            <p><a href="{{ actions_link }}">Go to your actions</a> </p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "actions",
                "description": _("A list of actions that will expire today"),
            },
            {
                "name": "actions_link",
                "description": _("The link to your actions page."),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
        ],
    },
    "expiring_plan": {
        "name": _("Plan end date today"),
        "description": _(
            "This email is used to remind users that there are plans that are ending today"
        ),
        "subject_default": "Plans about to end today at {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>You are receiving this email because you have some plans that are expiring.</p>

            <table>
                <tr>
                    <td>Plan name</td>
                    <td>Goal</td>
                    <td>End date</td>
                </tr>
            {% for plan in plans %}
                <tr>
                    <td>{{ plan.title }}</td>
                    <td>{{ plan.goal }}</td>
                    <td>{{ plan.end_date|date:"d-m-Y" }}</td>
                </tr>
            {% endfor %}
            </table>

            <p><a href="{{ plan_list_link }}">Go to your plans</a> </p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "plans",
                "description": _("A list of plans that will expire today"),
            },
            {
                "name": "plan_list_link",
                "description": _("The link to your plans page."),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
        ],
    },
    "plan_action_update": {
        "name": _("Plan action update"),
        "description": _(
            "This email is used to notify plan participants about the change in the plan action"
        ),
        "subject_default": "Plan action has been updated at {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>You are receiving this email because the action in your <a href="{{ plan_url }}">plan</a> was updated.</p>

            <table>
                <tr>
                    <th>Action name</th>
                    <td>{{ action.name }}</td>
                </tr>
                <tr>
                    <th>Plan</th>
                    <td><a href="{{ plan_url }}">{{ plan.title }}</a></td>
                </tr>
                <tr>
                    <th>Updated at</th>
                    <td>{{ action.updated_on }}</td>
                </tr>
                <tr>
                    <th>Details</th>
                    <td>{{ message }}</td>
                </tr>
            </table>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "action",
                "description": _("Action that was updated"),
            },
            {
                "name": "plan",
                "description": _("Plan the updated action belongs to"),
            },
            {
                "name": "plan_url",
                "description": _("The link to the plan."),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
        ],
    },
    "case_notification": {
        "name": _("Case update notification"),
        "description": _(
            "This email is used to notify people an update happened to their case"
        ),
        "subject_default": "Update to your case at {{ site_name }}",
        "body_default": """
            <p>Beste</p>

            <p>You are receiving this email because one of your cases received a new status update or document attachment.</p>

            <table>
                <tr>
                    <th>Case identification</th>
                    <td>{{ identification }}</td>
                </tr>
                <tr>
                    <th>Case type</th>
                    <td>{{ type_description }}</td>
                </tr>
                <tr>
                    <th>Start date</th>
                    <td>{{ start_date }}</td>
                </tr>
            </table>

            <p><a href="{{ case_link }}">Go to your case</a> </p>

            <p>Met vriendelijke groet,
            {{ site_name }} </p>
       """,
        "subject": [
            {
                "name": "site_name",
                "description": _("Name of the site."),
            },
        ],
        "body": [
            {
                "name": "identification",
                "description": _("The identification of the case"),
            },
            {
                "name": "type_description",
                "description": _("The description of the type of the case"),
            },
            {
                "name": "start_date",
                "description": _("The start date of the case"),
            },
            {
                "name": "case_link",
                "description": _("The link to the case details."),
            },
            {
                "name": "site_name",
                "description": _("Name of the site"),
            },
        ],
    },
}
MAIL_EDITOR_BASE_CONTEXT = {"site_name": "Open Inwoner Platform"}
CKEDITOR_CONFIGS = {
    "mail_editor": {
        "allowedContent": True,
        "height": 600,  # This is optional
        "entities": False,  # This is added because CKEDITOR escapes the ' when you do an if statement
    }
}


# invite expires in X days after sending
INVITE_EXPIRY = 14

# zgw-consumers
ZGW_CONSUMERS_TEST_SCHEMA_DIRS = [
    os.path.join(DJANGO_PROJECT_DIR, "openzaak", "tests", "files"),
]

#
# Maykin fork of DJANGO-TWO-FACTOR-AUTH
#
TWO_FACTOR_FORCE_OTP_ADMIN = config("TWO_FACTOR_FORCE_OTP_ADMIN", default=not DEBUG)
TWO_FACTOR_PATCH_ADMIN = config("TWO_FACTOR_PATCH_ADMIN", default=True)

# file upload limits
MIN_UPLOAD_SIZE = 1  # in bytes
MAX_UPLOAD_SIZE = 1024**2 * 100  # 100MB
UPLOAD_FILE_TYPES = "application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/plain,application/vnd.oasis.opendocument.text,application/vnd.oasis.opendocument.formula,application/vnd.oasis.opendocument.spreadsheet,application/pdf,image/jpeg,image/png"

# HaalCentraal BRP versions
BRP_VERSION = config("BRP_VERSION", default="2.0")

#
# DIGID
#

if ALLOWED_HOSTS:
    BASE_URL = "https://{}".format(ALLOWED_HOSTS[0])
else:
    BASE_URL = "https://example.com"

DIGID_MOCK = config("DIGID_MOCK", default=True)
DIGID_ENABLED = config("DIGID_ENABLED", default=True)
DIGID_METADATA = config("DIGID_METADATA", "")
SSL_CERTIFICATE_PATH = config("SSL_CERTIFICATE_PATH", "")
SSL_KEY_PATH = config("SSL_KEY_PATH", "")
DIGID_SERVICE_ENTITY_ID = config(
    "DIGID_SERVICE_ENTITY_ID", "https://was-preprod1.digid.nl/saml/idp/metadata"
)
DIGID_WANT_ASSERTIONS_SIGNED = config("DIGID_WANT_ASSERTIONS_SIGNED", default=True)

DIGID = {
    "base_url": BASE_URL,
    "entity_id": BASE_URL,
    # This is the metadata of the **Identity provider** NOT our own!
    "metadata_file": DIGID_METADATA,
    # SSL/TLS key
    "key_file": SSL_KEY_PATH,
    "cert_file": SSL_CERTIFICATE_PATH,
    "service_entity_id": DIGID_SERVICE_ENTITY_ID,
    "attribute_consuming_service_index": "1",
    "requested_attributes": ["bsn"],
    # Logius can sign the assertions (True) but others sign the entire response
    # (False).
    "want_assertions_signed": DIGID_WANT_ASSERTIONS_SIGNED,
}

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
MOZILLA_DJANGO_OIDC_DB_CACHE = "oidc"
MOZILLA_DJANGO_OIDC_DB_CACHE_TIMEOUT = 1

from .app.csp import *  # noqa

SECURE_REFERRER_POLICY = "origin-when-cross-origin"
