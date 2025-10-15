from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import structlog
from elasticsearch.dsl.connections import connections

logger = structlog.stdlib.get_logger(__name__)


class SearchAppConfig(AppConfig):
    name = "open_inwoner.search"

    def ready(self):
        es_settings = getattr(settings, "ELASTICSEARCH_DSL", None)
        if not es_settings:
            logger.info("No elasticsearch configured")
            return

        connections.configure(**es_settings)

        try:
            connections.get_connection()
        except BaseException as exc:
            # This check serves two purposes:
            #
            # - Detect elasticsearch errors on start-up, and not when running the
            #   index rebuild or an actual search query and;
            # - Give context to exceptions raised for e.g. incomplete connecting strings
            #   which might otherwise be a bit opaque for end-users.
            raise ImproperlyConfigured(
                "Unable to configure elasticsearch client, which failed with error: "
                f"{exc}"
            ) from exc
