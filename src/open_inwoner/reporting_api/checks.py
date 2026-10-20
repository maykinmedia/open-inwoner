from django.conf import settings
from django.core.checks import Warning, register


@register
def check_reports_are_used(app_configs, **kwargs):
    """
    Warn when browsers are asked to send reports that are then discarded.
    """
    if (
        settings.REPORTING_API_ENABLED
        and not settings.REPORTING_API_LOGGING_ENABLED
        and not settings.REPORTING_API_METRICS_ENABLED
    ):
        return [
            Warning(
                "Reporting API logging and metrics are both disabled, received "
                "reports are discarded.",
                hint=(
                    "Enable REPORTING_API_LOGGING_ENABLED and/or "
                    "REPORTING_API_METRICS_ENABLED, or disable REPORTING_API_ENABLED "
                    "so browsers stop sending reports."
                ),
                id="reporting_api.W001",
            )
        ]

    return []
