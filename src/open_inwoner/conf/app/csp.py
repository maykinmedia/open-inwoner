from django.urls import reverse_lazy

from ..utils import config

#
# Django CSP settings
#
# explanation of directives: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy
# and how to specify them: https://django-csp.readthedocs.io/en/latest/configuration.html
#
# NOTE: make sure values are a tuple or list, and to quote special values like 'self'
CSP_DEFAULT_SRC = (
    "'none'",
)  # ideally we'd use BASE_URI but it'd have to be lazy or cause issues
CSP_BASE_URI = ("'self'",)
CSP_FONT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/",
)  # See if the unsafe-eval can be removed....
CSP_STYLE_SRC = (
    "'self'",
)  # Fix this. I do not want to have the unsafe-inline here....
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/",
)

CSP_UPGRADE_INSECURE_REQUESTS = False  # TODO enable on production?
CSP_INCLUDE_NONCE_IN = [
    "script-src",
    "style-src",
]  # Want to have "style-src" here too.... but does not work with unsafe-inline

# note these are outdated/deprecated django-csp options
# CSP_BLOCK_ALL_MIXED_CONTENT
# CSP_PLUGIN_TYPES
# CSP_CHILD_SRC

CSP_EXCLUDE_URL_PREFIXES = (
    # ReDoc/Swagger pull in external sources, so don't enforce CSP on API endpoints/documentation.
    "/api/",
    "/admin/",
)

# report to our own django-csp-reports
CSP_REPORT_ONLY = config("CSP_REPORT_ONLY", False)  # danger
CSP_REPORT_URI = reverse_lazy("report_csp")

#
# Django CSP-report settings
#
CSP_REPORTS_SAVE = config("CSP_REPORTS_SAVE", True)  # save as model
CSP_REPORTS_LOG = config("CSP_REPORTS_LOG", True)  # logging
CSP_REPORTS_LOG_LEVEL = "warning"
CSP_REPORTS_EMAIL_ADMINS = False
CSP_REPORT_PERCENTAGE = config("CSP_REPORT_PERCENTAGE", 1.0)  # float between 0 and 1
CSP_REPORTS_FILTER_FUNCTION = "cspreports.filters.filter_browser_extensions"
