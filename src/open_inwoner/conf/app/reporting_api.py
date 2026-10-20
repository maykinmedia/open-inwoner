from django.urls import reverse_lazy

from maykin_common.config import DocumentationParams, config

#
# Reporting API: endpoint for reports sent by browsers, e.g. Permissions Policy
# violations
#
REPORTING_API_ENABLED = config(
    "REPORTING_API_ENABLED",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Ask browsers to send reports, e.g. Permissions Policy violations, to the "
            "Reporting API endpoint. When disabled, browsers send no reports and the "
            "endpoint is unavailable; policies are still applied."
        ),
        group="Monitoring",
    ),
)
REPORTING_API_URI = reverse_lazy("api:reporting_api")

REPORTING_API_MAX_REPORTS_PER_REQUEST = config(
    "REPORTING_API_MAX_REPORTS_PER_REQUEST",
    default=100,
    documentation=DocumentationParams(
        help_text=(
            "Maximum number of reports processed per request to the Reporting API "
            "endpoint, further reports in the same request are ignored. Bounds the "
            "work an (unauthenticated) request can cause; browsers send far smaller "
            "batches."
        ),
        group="Security",
    ),
)

REPORTING_API_LOGGING_ENABLED = config(
    "REPORTING_API_LOGGING_ENABLED",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Log every report received through the Reporting API, up to a few per "
            "request. Metrics are emitted regardless of this setting."
        ),
        group="Logging",
    ),
)

REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST = config(
    "REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST",
    default=5,
    documentation=DocumentationParams(
        help_text=(
            "Maximum number of violations logged per request to the Reporting API "
            "endpoint; the rest are summarized in a single log entry. All violations "
            "are counted in the metric regardless."
        ),
        group="Logging",
    ),
)

REPORTING_API_METRICS_ENABLED = config(
    "REPORTING_API_METRICS_ENABLED",
    default=True,
    documentation=DocumentationParams(
        help_text=(
            "Emit an OpenTelemetry metric for every report received through the "
            "Reporting API, next to the log entry."
        ),
        group="Monitoring",
    ),
)
