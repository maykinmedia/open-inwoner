import concurrent.futures
import logging
from dataclasses import dataclass

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin
from zgw_consumers.concurrent import parallel

from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.cases import preprocess_data
from open_inwoner.openzaak.formapi import fetch_open_submissions
from open_inwoner.openzaak.models import OpenZaakConfig, ZGWApiGroupConfig
from open_inwoner.openzaak.types import UniformCase
from open_inwoner.openzaak.utils import get_user_fetch_parameters
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZaakWithApiGroup(UniformCase):
    zaak: Zaak
    api_group: ZGWApiGroupConfig

    @property
    def identifier(self):
        return self.zaak.url

    def process_data(self) -> dict:
        return {**self.zaak.process_data(), "api_group": self.api_group}


class OuterCaseListView(
    OuterCaseAccessMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    """View on the case list while content is loaded via htmx"""

    template_name = "pages/cases/list_outer.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn aanvragen"), reverse("cases:index")),
        ]

    def page_title(self):
        return _("Mijn aanvragen")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["hxget"] = reverse("cases:cases_content")
        return context


class InnerCaseListView(
    RequiresHtmxMixin,
    CommonPageMixin,
    CaseAccessMixin,
    CaseLogMixin,
    PaginationMixin,
    TemplateView,
):
    template_name = "pages/cases/list_inner.html"
    paginate_by = 9

    def page_title(self):
        return _("Mijn aanvragen")

    def get_cases_for_api_group(self, group: ZGWApiGroupConfig):
        raw_cases = group.zaken_client.fetch_cases(
            **get_user_fetch_parameters(self.request)
        )
        preprocessed_cases = preprocess_data(raw_cases, group)
        return preprocessed_cases

    def get_cases(self) -> list[ZaakWithApiGroup]:
        all_api_groups = list(ZGWApiGroupConfig.objects.all())
        with parallel() as executor:
            futures = [
                executor.submit(self.get_cases_for_api_group, group)
                for group in all_api_groups
            ]

            cases = []
            for task in concurrent.futures.as_completed(futures):
                try:
                    group_for_task = all_api_groups[futures.index(task)]
                    for row in task.result():
                        cases.append(
                            ZaakWithApiGroup(zaak=row, api_group=group_for_task)
                        )
                except BaseException:
                    logger.exception("Error fetching and pre-processing cases")

        # Ensure stable sorting for pagination and testing purposes
        cases.sort(key=lambda c: all_api_groups.index(c.api_group))
        return cases

    def get_submissions(self):
        subs = fetch_open_submissions(self.request.user.bsn)
        subs.sort(key=lambda sub: sub.datum_laatste_wijziging, reverse=True)
        return subs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = OpenZaakConfig.get_solo()

        # update ctx with submissions + cases
        open_submissions: list[UniformCase] = self.get_submissions()
        preprocessed_cases: list[UniformCase] = self.get_cases()
        paginator_dict = self.paginate_with_context(
            [*open_submissions, *preprocessed_cases]
        )
        case_dicts = [case.process_data() for case in paginator_dict["object_list"]]

        context["cases"] = case_dicts
        context.update(paginator_dict)

        self.log_access_cases(case_dicts)

        # other data
        context["hxget"] = reverse("cases:cases_content")
        context["title_text"] = config.title_text
        return context
