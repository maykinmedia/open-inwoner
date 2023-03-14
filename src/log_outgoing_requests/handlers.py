import logging
import traceback
from urllib.parse import urlparse

from django.conf import settings


class DatabaseOutgoingRequestsHandler(logging.Handler):
    def emit(self, record):
        if (
            settings.LOG_OUTGOING_REQUESTS_ENABLED
            and settings.LOG_OUTGOING_REQUESTS_DB_SAVE
        ):
            from .models import OutgoingRequestsLog

            trace = None

            # save only the requests coming from the library requests
            if record and record.getMessage() == "External request":
                if record.exc_info:
                    trace = traceback.format_exc()

                parsed_url = urlparse(record.req.url)

                kwargs = {
                    "hostname": parsed_url.hostname,
                    "path": parsed_url.path,
                    "params": parsed_url.params,
                    "query_params": parsed_url.query,
                    "status_code": record.res.status_code,
                    "method": record.req.method,
                    "timestamp": record.requested_at,
                    "response_ms": int(record.res.elapsed.total_seconds() * 1000),
                    "trace": trace,
                }

                OutgoingRequestsLog.objects.create(**kwargs)
