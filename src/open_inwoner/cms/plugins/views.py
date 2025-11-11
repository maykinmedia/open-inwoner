import itertools
from typing import Sequence

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

import structlog

from open_inwoner.cms.cases.views.mixins import CaseLogMixin
from open_inwoner.cms.cases.views.services import CaseListService
from open_inwoner.cms.plugins.models.zaken import MAX_CASES_DEFAULT, MIN_CASES
from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.openzaak.types import UniformCase

logger = structlog.stdlib.get_logger(__name__)


class ZakenPluginContentView(RequiresHtmxMixin, CaseLogMixin, View):
    """
    HTMX endpoint that fetches and returns zaken content for the `CMSZakenPlugin`.

    The view accepts and validates a `num_zaken` query parameter to limit the number
    of cases displayed.
    """

    def get(self, request: HttpRequest, plugin_id: int) -> HttpResponse:
        if not ZGWApiGroupConfig.objects.exists():
            logger.warning(
                "ZGWApiGroupConfig required to fetch zaken for CMS zaken plugin"
            )
            return render(request, "cms/plugins/zaken/zaken.html", {})

        case_service = CaseListService(request)

        num_zaken = request.GET.get("num_zaken", None)
        try:
            num_zaken = int(num_zaken)
            if num_zaken < MIN_CASES or num_zaken > MAX_CASES_DEFAULT:
                logger.warning(
                    "Invalid num_zaken value, using default",
                    num_zaken=num_zaken,
                )
                num_zaken = MAX_CASES_DEFAULT
        except (ValueError, TypeError) as exc:
            logger.warning(
                "Invalid num_zaken parameter, using default",
                value=num_zaken,
                error=str(exc),
            )
            num_zaken = MAX_CASES_DEFAULT

        open_submissions: Sequence[UniformCase] = case_service.get_submissions()
        preprocessed_cases: Sequence[UniformCase] = case_service.get_cases()

        zaken_dicts = [
            zaak.process_data()
            for zaak in itertools.islice(
                itertools.chain(open_submissions, preprocessed_cases),
                num_zaken,
            )
        ]
        context = {
            "zaken": zaken_dicts,
        }

        self.log_case_list_accessed(zaken_dicts)

        return render(request, "cms/plugins/zaken/zaken.html", context)


zaken_plugin_content_view = ZakenPluginContentView.as_view()
