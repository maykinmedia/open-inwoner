from opentelemetry import metrics

meter = metrics.get_meter("open_inwoner.reporting_api")

permissions_policy_violations = meter.create_counter(
    "oip.reporting_api.permissions_policy_violations",
    unit="{report}",
    description=(
        "Number of Permissions Policy violations reported by browsers through the "
        "Reporting API. "
        "Attributes: type (str): 'permissions-policy-violation' - a document used a "
        "feature the policy does not allow; 'potential-permissions-policy-violation' "
        "- an iframe requested a feature (through its `allow` attribute) the policy "
        "does not allow. "
        "feature (str): the policy-controlled feature, e.g. 'geolocation'. "
        "disposition (str): 'enforce' or 'report' (report-only mode). "
        "source (str): 'self' - the offending script is served from one of our own "
        "hosts; 'external' - from another host, e.g. custom JS or a third-party "
        "widget; 'unknown' - no script known, e.g. inline scripts or iframes."
    ),
)

rejected_reports = meter.create_counter(
    "oip.reporting_api.rejected_reports",
    unit="{report}",
    description=(
        "Number of otherwise valid reports that were rejected, and neither logged "
        "nor counted as violations. "
        "Attributes: reason (str): 'unknown_host' - the report is about a page on a "
        "host that is not in ALLOWED_HOSTS. If all reports are rejected this way, "
        "check ALLOWED_HOSTS and the Host header set by the reverse proxy."
    ),
)
