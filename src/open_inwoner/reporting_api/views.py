from urllib.parse import urlsplit

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.http.request import validate_host
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import msgspec
import structlog

from .metrics import permissions_policy_violations, rejected_reports
from .reports import PermissionsPolicyReport, ReportBatch

logger = structlog.stdlib.get_logger("reporting_api")


# created once, decoders are reusable
_batch_decoder = msgspec.json.Decoder(ReportBatch)
_permissions_policy_report_decoder = msgspec.json.Decoder(PermissionsPolicyReport)


def _is_own_host(url: str) -> bool:
    return validate_host(urlsplit(url).hostname or "", settings.ALLOWED_HOSTS)


def _metric_source(source_file: str | None) -> str:
    # whether the violation comes from our own code or a third-party script, e.g.
    # custom JS or a widget; bounded to three values
    if not source_file:
        return "unknown"
    return "self" if _is_own_host(source_file) else "external"


def _metric_feature(feature: str) -> str:
    # the reports are untrusted input, only features from our own policy are
    # recorded by name to keep the metric's cardinality bounded
    known_features = settings.PERMISSIONS_POLICY.keys() | (
        settings.PERMISSIONS_POLICY_REPORT_ONLY.keys()
    )
    return feature if feature in known_features else "other"


@csrf_exempt
@require_POST
def reporting_api_view(request: HttpRequest) -> HttpResponse:
    """
    Receive reports sent by browsers via the Reporting API, and log them.

    Only Permissions Policy violations are of interest for now, other report types
    are ignored.
    """
    if not settings.REPORTING_API_ENABLED:
        raise Http404

    if request.content_type != "application/reports+json":
        return HttpResponse(status=415)

    try:
        raw_reports = _batch_decoder.decode(request.body)
    except (msgspec.DecodeError, RecursionError):
        # msgspec raises RecursionError on deeply nested input
        return HttpResponseBadRequest()

    logged = not_logged = 0
    for raw_report in raw_reports[: settings.REPORTING_API_MAX_REPORTS_PER_REQUEST]:
        try:
            report = _permissions_policy_report_decoder.decode(raw_report)
        except msgspec.DecodeError:
            # other report types sent to the default endpoint (e.g. deprecations)
            # are of no interest, nor are malformed reports
            continue

        # anyone can post here, at least drop reports about pages on other sites
        if not _is_own_host(report.url):
            if settings.REPORTING_API_METRICS_ENABLED:
                rejected_reports.add(1, {"reason": "unknown_host"})
            continue

        if settings.REPORTING_API_METRICS_ENABLED:
            permissions_policy_violations.add(
                1,
                {
                    "type": report.type,
                    "feature": _metric_feature(report.body.feature),
                    "disposition": report.body.disposition or "unknown",
                    "source": _metric_source(report.body.source_file),
                },
            )

        if not settings.REPORTING_API_LOGGING_ENABLED:
            continue

        if logged >= settings.REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST:
            not_logged += 1
            continue

        logged += 1
        logger.warning(
            "permissions_policy_violation",
            type=report.type,
            feature=report.body.feature,
            disposition=report.body.disposition,
            # drop query string and fragment, they might contain personal data
            url=urlsplit(report.url)._replace(query="", fragment="").geturl(),
            source_file=report.body.source_file,
            line_number=report.body.line_number,
            column_number=report.body.column_number,
            user_agent=report.user_agent,
        )

    if not_logged:
        logger.warning("permissions_policy_violations_not_logged", count=not_logged)

    return HttpResponse(status=204)
