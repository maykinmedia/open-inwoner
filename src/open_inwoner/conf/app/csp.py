from django.urls import reverse_lazy

from csp.constants import NONCE, NONE, SELF
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
# These are the sources every installation needs. Anything installation specific is
# managed in the admin (maykin_common.csp), and merged into this policy per request.
#
_csp_report_only = config(
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
_csp_report_percentage = config(
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

_csp_policy = {
    "EXCLUDE_URL_PREFIXES": (
        # ReDoc/Swagger pull in external sources, so don't enforce CSP on API endpoints/documentation.
        "/api/",
        "/admin/",
    ),
    # django-csp expects a percentage (0-100), the envvar is a fraction (0-1)
    "REPORT_PERCENTAGE": _csp_report_percentage * 100,
    "DIRECTIVES": {
        # ideally we'd use BASE_URI but it'd have to be lazy or cause issues
        "default-src": [SELF],
        "base-uri": [SELF],
        "font-src": [SELF, OPEN_FORMS_SDK_DOMAIN],
        "frame-ancestors": [SELF],
        "frame-src": [SELF],
        "object-src": [NONE],
        # See if the unsafe-eval can be removed....
        "script-src": [SELF, NONCE, OPEN_FORMS_SDK_DOMAIN],
        # Fix this. I do not want to have the unsafe-inline here....
        "style-src": [SELF, NONCE, OPEN_FORMS_SDK_DOMAIN],
        "img-src": [SELF, "data:", OPEN_FORMS_SDK_DOMAIN],
        "connect-src": [SELF, OPEN_FORMS_API_DOMAIN],
        "upgrade-insecure-requests": False,  # TODO enable on production?
        "report-uri": [reverse_lazy("report_csp")],
    },
}

CONTENT_SECURITY_POLICY = None if _csp_report_only else _csp_policy
CONTENT_SECURITY_POLICY_REPORT_ONLY = _csp_policy if _csp_report_only else None

#
# Django CSP-report settings
#
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
CSP_REPORTS_FILTER_FUNCTION = "cspreports.filters.filter_browser_extensions"
