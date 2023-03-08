import logging
from urllib.parse import urlparse

from requests import Session

from .models import ExternalAPILog

logger = logging.getLogger(__name__)


def log_requests_data(response, *args, **kwargs):
    parsed_url = urlparse(response.url)

    ExternalAPILog.objects.create(
        hostname=parsed_url.hostname,
        path=parsed_url.path,
        params=parsed_url.params,
        query_params=parsed_url.query,
        status_code=response.status_code,
        method="",
        # response_ms=,
        # user=,
    )


def log_session_requests():
    """
    Log all external requests which are made by the library requests during a session.
    """
    if hasattr(Session, "_original_request"):
        logger.debug(
            "Session is already patched OR has an ``_original_request`` attribute."
        )
        return

    Session._original_request = Session.request

    def new_request(self, *args, **kwargs):
        kwargs.setdefault("hooks", {"response": log_requests_data})
        return self._original_request(*args, **kwargs)

    Session.request = new_request
