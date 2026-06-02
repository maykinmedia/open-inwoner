from django.urls import reverse_lazy

from maykin_common.config import DocumentationParams, config

# The Open Forms SDK files might differ from the API domain.
OPEN_FORMS_API_DOMAIN = config(
    "OPEN_FORMS_DOMAIN",
    default="",
    documentation=DocumentationParams(
        help_text=(
            "Domain of the Open Forms installation (e.g. ``https://forms.example.nl``). "
            "Used to whitelist the Open Forms SDK in the Content Security Policy so the "
            "browser permits loading its scripts, styles, fonts, and API requests."
        ),
        group="Security",
    ),
)
OPEN_FORMS_SDK_DOMAIN = OPEN_FORMS_API_DOMAIN

#
# Django CSP settings
#
# explanation of directives: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy
# and how to specify them: https://django-csp.readthedocs.io/en/latest/configuration.html
#
# NOTE: make sure values are a tuple or list, and to quote special values like 'self'
CSP_DEFAULT_SRC = (
    "'self'",
)  # ideally we'd use BASE_URI but it'd have to be lazy or cause issues
CSP_BASE_URI = ("'self'",)
CSP_FONT_SRC = ("'self'", OPEN_FORMS_SDK_DOMAIN)
CSP_FRAME_ANCESTORS = ["'self'"]
CSP_FRAME_SRC = ["'self'"]
CSP_OBJECT_SRC = "'none'"
CSP_SCRIPT_SRC = (
    "'self'",
    "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/",
    OPEN_FORMS_SDK_DOMAIN,
)  # See if the unsafe-eval can be removed....
CSP_STYLE_SRC = (
    "'self'",
    OPEN_FORMS_SDK_DOMAIN,
)  # Fix this. I do not want to have the unsafe-inline here....
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/",
    OPEN_FORMS_SDK_DOMAIN,
)
CSP_CONNECT_SRC = ("'self'", OPEN_FORMS_API_DOMAIN)

CSP_UPGRADE_INSECURE_REQUESTS = False  # TODO enable on production?
CSP_INCLUDE_NONCE_IN = [
    "script-src",
    "style-src",
]  # Want to have "style-src" here too.... but does not work with unsafe-inline

CSP_EXCLUDE_URL_PREFIXES = (
    # ReDoc/Swagger pull in external sources, so don't enforce CSP on API endpoints/documentation.
    "/api/",
    "/admin/",
)

#
# Django CSP-report settings
#
CSP_REPORT_ONLY = config(
    "CSP_REPORT_ONLY",
    default=False,
    documentation=DocumentationParams(
        help_text=(
            "When enabled, the Content Security Policy is applied in report-only mode: "
            "violations are reported but not blocked. Use only for testing a new policy; "
            "disables enforcement while active."
        ),
        group="Security",
    ),
)
CSP_REPORT_URI = reverse_lazy("report_csp")
CSP_REPORTS_SAVE = config(
    "CSP_REPORTS_SAVE",
    default=True,
    documentation=DocumentationParams(
        help_text="Save CSP reports in database",
        group="Security",
    ),
)
CSP_REPORTS_LOG = config(
    "CSP_REPORTS_LOG",
    default=True,
    documentation=DocumentationParams(
        help_text="Log CSP reports",
        group="Security",
    ),
)
CSP_REPORTS_LOG_LEVEL = "warning"
CSP_REPORTS_EMAIL_ADMINS = False
CSP_REPORT_PERCENTAGE = config(
    "CSP_REPORT_PERCENTAGE",
    default=1.0,
    documentation=DocumentationParams(
        help_text=(
            "Fraction of responses (0.0–1.0) for which the CSP report-uri directive is "
            "included. Values below 1.0 sample reports to reduce load on the reporting "
            "endpoint."
        ),
        group="Security",
    ),
)
CSP_REPORTS_FILTER_FUNCTION = "cspreports.filters.filter_browser_extensions"
