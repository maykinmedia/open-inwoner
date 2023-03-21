import logging
import traceback
from urllib.parse import urlparse

from django.conf import settings


class DatabaseOutgoingRequestsHandler(logging.Handler):
    def emit(self, record):
        if settings.LOG_OUTGOING_REQUESTS_DB_SAVE:
            from .models import OutgoingRequestsLog

            trace = None

            # save only the requests coming from the library requests
            if record and record.getMessage() == "Outgoing request":
                exclude_headers = ["Authorization"]
                safe_req_headers = {
                    k: v
                    for k, v in record.req.headers.items()
                    if k not in exclude_headers
                }

                if record.exc_info:
                    trace = traceback.format_exc()

                parsed_url = urlparse(record.req.url)
                kwargs = {
                    "url": record.req.url,
                    "hostname": parsed_url.hostname,
                    "params": parsed_url.params,
                    "status_code": record.res.status_code,
                    "method": record.req.method,
                    "req_content_type": record.req.headers.get("Content-Type", ""),
                    "res_content_type": record.res.headers.get("Content-Type", ""),
                    "timestamp": record.requested_at,
                    "response_ms": int(record.res.elapsed.total_seconds() * 1000),
                    "req_headers": safe_req_headers,
                    "res_headers": record.res.headers,
                    "trace": trace,
                }

                OutgoingRequestsLog.objects.create(**kwargs)
