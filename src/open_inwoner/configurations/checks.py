from urllib.parse import urlparse

from django.conf import settings
from django.core.checks import Error, Warning, register


class CheckID:
    missing_es_host = "missing_es_host"


@register("functional_config")
def check_elasticsearch_host_format(app_configs, **kwargs):
    """Check that ES_HOST is properly formatted with scheme and port."""
    errors = []

    # Get the ES_HOST from ELASTICSEARCH_DSL settings
    es_config = getattr(settings, "ELASTICSEARCH_DSL", {})
    default_config = es_config.get("default", {})
    hosts = default_config.get("hosts", "")

    if not hosts:
        errors.append(
            Error(
                "ELASTICSEARCH_DSL hosts configuration is missing.",
                hint="Set ES_HOST environment variable or configure ELASTICSEARCH_DSL in settings.",
                id="search.E001",
            )
        )
        return errors

    # Handle case where hosts might be a list
    if isinstance(hosts, list):
        if not hosts:
            errors.append(
                Error(
                    "ELASTICSEARCH_DSL hosts list is empty.",
                    hint="Set ES_HOST environment variable or configure ELASTICSEARCH_DSL in settings.",
                    id="search.E001",
                )
            )
            return errors
        # Check the first host in the list
        host_url = hosts[0]
    else:
        host_url = hosts

    # Parse the URL
    parsed = urlparse(host_url)

    # Check for missing scheme
    if not parsed.scheme:
        errors.append(
            Warning(
                f'ES_HOST missing scheme: "{host_url}". Consider adding "http://" or "https://" prefix.',
                hint="Add protocol scheme to ES_HOST for clarity.",
                id=CheckID.missing_es_host,
            )
        )

    # Check for missing port (ElasticSearch default is 9200)
    if not parsed.port:
        errors.append(
            Warning(
                f'ES_HOST missing port: "{host_url}". Consider adding port 9200 explicitly.',
                hint='Add port number to ES_HOST for clarity (e.g., "http://localhost:9200").',
                id=CheckID.missing_es_host,
            )
        )

    return errors
