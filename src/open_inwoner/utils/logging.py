import time
from collections import OrderedDict
from datetime import timedelta
from logging import Handler  # noqa: TID251 -- needed for base class of handler
from typing import Mapping, Optional, cast
from urllib.parse import urlparse

from django.utils import timezone

import structlog
from log_outgoing_requests.compat import format_exception
from log_outgoing_requests.typing import (
    AnyLogRecord,
    ErrorRequestLogRecord,
    RequestLogRecord,
    is_request_log_record,
)
from requests import PreparedRequest, Request, RequestException, Response

logger = structlog.stdlib.get_logger(__name__)


class StructlogOutgoingRequestsHandler(Handler):
    """Emit an outgoing request log as structured data."""

    def emit(self, record: AnyLogRecord):
        # skip requests not coming from the library requests
        if not record or not is_request_log_record(record):
            return

        from log_outgoing_requests.models import OutgoingRequestsLogConfig
        from log_outgoing_requests.utils import process_body

        config = cast(OutgoingRequestsLogConfig, OutgoingRequestsLogConfig.get_solo())
        record = cast(RequestLogRecord, record)

        # check if we're dealing with success or error state
        request: PreparedRequest | Request | None
        response: Response | None
        exception = record.exc_info[1] if record.exc_info else None
        if (response := getattr(record, "res", None)) is not None:
            # we have a response - this is the 'happy' flow (connectivity is okay)
            request = record.req
        elif isinstance(exception, RequestException):
            record = cast(ErrorRequestLogRecord, record)
            # we have an requests-specific exception
            request = exception.request or None
            response: Optional[Response] = exception.response  # likely None
        else:
            logger.debug("Received log record that cannot be handled", record=record)
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
                "timestamp": timestamp,
                "response_ms": (
                    int(response.elapsed.total_seconds() * 1000)
                    if response is not None
                    else None
                ),
                "trace": "\n".join(format_exception(exception)) if exception else None,
                "params": parsed_url.params if parsed_url else "(unknown)",
                "query": parsed_url.query if parsed_url else "(unknown)",
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

        # check response
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

        # Emit the actual log message
        logger.debug("outgoing_request", **kwargs)

    @staticmethod
    def _headers_to_dict(headers: Mapping[str, str], type_prefix: str):
        mapped_headers = {}

        for header_name, header_value in headers.items():
            mapped_headers[
                f"{type_prefix}_header__" + header_name.lower().replace("-", "_")
            ] = header_value

        return mapped_headers
