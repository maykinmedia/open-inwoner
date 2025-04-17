from collections import OrderedDict
import threading
import structlog
import logging
import time
from contextlib import contextmanager
from datetime import timedelta
from typing import Any, Mapping, Optional, cast
from urllib.parse import urlparse
from django.utils import timezone

from requests import PreparedRequest, RequestException, Response

from log_outgoing_requests.compat import format_exception
from log_outgoing_requests.typing import (
    AnyLogRecord,
    ErrorRequestLogRecord,
    RequestLogRecord,
    is_request_log_record,
)

logger = structlog.getLogger(__name__)


class StructlogOutgoingRequestsHandler(logging.Handler):
    """
    Save the log record to the database if conditions are met.

    The handler checks if saving to the database is desired. If not, nothing happens.
    Next, request and response body are each checked if:

        * saving to database is desired
        * the content type is appropriate
        * the size of the body does not exceed the configured treshold

    If any of the conditions don't match, then the body is omitted.
    """

    @staticmethod
    def _headers_to_dict(headers: Mapping[str, str], type_prefix: str):
        mapped_headers = {}

        for header_name, header_value in headers.items():
            mapped_headers[
                f"{type_prefix}_header__" + header_name.lower().replace("-", "_")
            ] = header_value

        return mapped_headers

    def emit(self, record: AnyLogRecord):

        from log_outgoing_requests.models import (
            OutgoingRequestsLog,
            OutgoingRequestsLogConfig,
        )
        from log_outgoing_requests.utils import process_body

        # skip requests not coming from the library requests
        if not record or not is_request_log_record(record):
            return

        config = OutgoingRequestsLogConfig.get_solo()
        assert isinstance(config, OutgoingRequestsLogConfig)

        # Python 3.10 TypeGuard can be useful here
        record = cast(RequestLogRecord, record)

        # check if we're dealing with success or error state
        exception = record.exc_info[1] if record.exc_info else None
        if (response := getattr(record, "res", None)) is not None:
            # we have a response - this is the 'happy' flow (connectivity is okay)
            record = cast(RequestLogRecord, record)
            request = record.req
        elif isinstance(exception, RequestException):
            record = cast(ErrorRequestLogRecord, record)
            # we have an requests-specific exception
            request: Optional[PreparedRequest] = exception.request
            response: Optional[Response] = exception.response  # likely None
        else:  # pragma: no cover
            logger.debug("Received log record that cannot be handled %r", record)
            return

        scrubbed_req_headers = request.headers.copy() if request else {}
        if "Authorization" in scrubbed_req_headers:
            scrubbed_req_headers["Authorization"] = "***hidden***"

        parsed_url = urlparse(request.url) if request else None

        # ensure we have a timezone aware timestamp. time.time() is platform dependent
        # about being UTC or a local time. A robust way is checking how many seconds ago
        # this record was created, and subtracting that from the current tz aware time.
        time_delta_logged_seconds = time.time() - record.created
        timestamp = timezone.now() - timedelta(seconds=time_delta_logged_seconds)

        kwargs = OrderedDict(
            {
                "status_code": response.status_code if response is not None else None,
                "method": request.method if request else "(unknown)",
                "url": request.url if request else "(unknown)",
                "hostname": parsed_url.netloc if parsed_url else "(unknown)",
                "params": parsed_url.params if parsed_url else "(unknown)",
                "timestamp": timestamp,
                "response_ms": (
                    int(response.elapsed.total_seconds() * 1000)
                    if response is not None
                    else None
                ),
                # "req_headers": scrubbed_req_headers,
                # "res_headers": response.headers if response is not None else {},
                "trace": "\n".join(format_exception(exception)) if exception else None,
            }
        )
        kwargs.update(self._headers_to_dict(scrubbed_req_headers, "req"))
        kwargs.update(
            self._headers_to_dict(
                response.headers if response is not None else {}, "resp"
            )
        )

        # check request
        if (
            request
            and (
                processed_request_body := process_body(request, config)
            ).allow_saving_to_db
        ):
            kwargs.update(
                {
                    "req_content_type": processed_request_body.content_type,
                    "req_body": processed_request_body.content,
                    "req_body_encoding": processed_request_body.encoding,
                }
            )

        # # check response
        if (
            response is not None
            and (
                processed_response_body := process_body(response, config)
            ).allow_saving_to_db
        ):
            kwargs.update(
                {
                    "res_content_type": processed_response_body.content_type,
                    "res_body": processed_response_body.content,
                    "res_body_encoding": processed_response_body.encoding,
                }
            )

        logger.debug("outgoing_request", **kwargs)

    def format_headers(self, headers):
        return "\n".join(f"{k}: {v}" for k, v in headers.items())


class StructlogSentryProcessor:
    """
    A Sentry processor that captures recent structlog logs and adds them as extra data to Sentry events.

    This processor maintains a thread-local storage of recent log entries and attaches them to
    Sentry events when they occur.
    """

    _thread_local = threading.local()

    def __init__(self, max_logs: int = 20, max_age_seconds: int = 60):
        """
        Initialize the processor.

        Args:
            max_logs: Maximum number of log entries to keep per thread
            max_age_seconds: Maximum age of log entries to keep (in seconds)
        """
        self.max_logs = max_logs
        self.max_age_seconds = max_age_seconds

    @classmethod
    def get_logs(cls) -> list[dict[str, Any]]:
        """Get the current logs for this thread."""
        if not hasattr(cls._thread_local, "logs"):
            cls._thread_local.logs = []
        return cls._thread_local.logs

    @classmethod
    def add_log(cls, log_entry: dict[str, Any]) -> None:
        """Add a log entry to the thread-local storage."""
        logs = cls.get_logs()

        # Add timestamp if not present
        if "timestamp" not in log_entry:
            log_entry["timestamp"] = time.time()

        logs.append(log_entry)

    @classmethod
    @contextmanager
    def capture_logs(cls):
        """Context manager to capture logs in the current context."""
        # Clear logs before capturing
        cls._thread_local.logs = []
        try:
            yield
        finally:
            pass

    def __call__(self, event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
        """
        Process the Sentry event by adding recent logs as extra data.

        Args:
            event: The Sentry event data
            hint: Hint data about the event

        Returns:
            The modified event with logs attached
        """
        logs = self.get_logs()

        if logs:
            # Filter out old logs
            now = time.time()
            recent_logs = [
                log
                for log in logs
                if now - log.get("timestamp", now) <= self.max_age_seconds
            ]

            # Limit to the most recent logs
            recent_logs = recent_logs[-self.max_logs :]

            # Add logs to extra data
            if "extra" not in event:
                event["extra"] = {}

            event["extra"]["structlog_context"] = recent_logs

        return event


# Structlog processor to capture logs for Sentry
def sentry_log_capturer(logger, method_name, event_dict):
    """
    Structlog processor that captures log entries for Sentry.

    This should be added to your structlog processor chain.
    """
    if not isinstance(event_dict, dict):
        return event_dict
    # Make a copy to avoid modifying the original event_dict
    log_entry = event_dict.copy()

    # Add method name (log level) if not present
    if "level" not in log_entry:
        log_entry["level"] = method_name

    # Add to Sentry processor's thread-local storage
    StructlogSentryProcessor.add_log(log_entry)

    # Return the original event dict unchanged
    return event_dict
