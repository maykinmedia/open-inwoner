import itertools
from typing import Sequence

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

import structlog

from open_inwoner.cms.cases.views.mixins import CaseLogMixin
from open_inwoner.cms.cases.views.services import CaseListService
from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.types import UniformCase

logger = structlog.stdlib.get_logger(__name__)


NUM_ZAKEN_DISPLAY = 4


class ZakenPluginContentView(RequiresHtmxMixin, CaseLogMixin, View):
    """
    HTMX endpoint that fetches and returns zaken content for the `CMSZakenPlugin`
    """

    def get(self, request: HttpRequest, plugin_id: int) -> HttpResponse:
        case_service = CaseListService(request)

        open_submissions: Sequence[UniformCase] = case_service.get_submissions()
        preprocessed_cases: Sequence[UniformCase] = case_service.get_cases()

        zaken_dicts = [
            zaak.process_data()
            for zaak in itertools.islice(
                itertools.chain(open_submissions, preprocessed_cases), NUM_ZAKEN_DISPLAY
            )
        ]
        context = {
            "zaken": zaken_dicts,
        }

        self.log_case_list_accessed(zaken_dicts)

        return render(request, "cms/plugins/zaken/zaken.html", context)


zaken_plugin_content_view = ZakenPluginContentView.as_view()
