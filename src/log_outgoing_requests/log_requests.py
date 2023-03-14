import logging

from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from requests import Session

from .formatters import HttpFormatter
from .handlers import DatabaseOutgoingRequestsHandler

logger = logging.getLogger("requests")


def hook_requests_logging(response, *args, **kwargs):
    """
    A hook for requests library in order to add extra data to the logs
    """
    extra = {"requested_at": timezone.now(), "req": response.request, "res": response}
    logger.debug("External request", extra=extra)


def install_outgoing_requests_logging():
    """
    Log all external requests which are made by the library requests during a session.
    """
    if settings.LOG_OUTGOING_REQUESTS_ENABLED:
        if hasattr(Session, "_original_request"):
            logger.debug(
                "Session is already patched OR has an ``_original_request`` attribute."
            )
            return

        Session._original_request = Session.request

        # logs saved in db or shown in console based on settings
        if settings.LOG_OUTGOING_REQUESTS_DB_SAVE:
            handler = DatabaseOutgoingRequestsHandler()
        else:
            handler = logging.StreamHandler()
            formatter = HttpFormatter(
                "{asctime} {levelname} {name} {message}", style="{"
            )

            handler.setFormatter(formatter)

        logging.basicConfig(level=logging.DEBUG, handlers=[handler])

        def new_request(self, *args, **kwargs):
            kwargs.setdefault("hooks", {"response": hook_requests_logging})
            return self._original_request(*args, **kwargs)

        Session.request = new_request
