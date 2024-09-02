import concurrent.futures
import logging
from dataclasses import dataclass

from django.http import HttpRequest
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from furl import furl
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

from ..forms import CaseFilterForm
from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin

logger = logging.getLogger(__name__)

SUBMISSION_STATUS_OPEN = _("Openstaande aanvraag")


@dataclass(frozen=True)
class ZaakWithApiGroup(UniformCase):
    zaak: Zaak
    api_group: ZGWApiGroupConfig

    @property
    def identifier(self):
        return self.zaak.url

    def process_data(self) -> dict:
        return {**self.zaak.process_data(), "api_group": self.api_group}


class CaseListService:
    def __init__(self, request: HttpRequest):
        self.request = request

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

            cases_with_api_group = []
            for task in concurrent.futures.as_completed(futures):
                try:
                    group_for_task = all_api_groups[futures.index(task)]
                    for row in task.result():
                        cases_with_api_group.append(
                            ZaakWithApiGroup(zaak=row, api_group=group_for_task)
                        )
                except BaseException:
                    logger.exception("Error fetching and pre-processing cases")

        # Ensure stable sorting for pagination and testing purposes
        cases_with_api_group.sort(key=lambda c: all_api_groups.index(c.api_group))

        return cases_with_api_group

    def get_submissions(self):
        subs = fetch_open_submissions(self.request.user.bsn)
        subs.sort(key=lambda sub: sub.datum_laatste_wijziging, reverse=True)

        return subs

    def get_case_status_frequencies(self):
        cases = self.get_cases()
        submissions = self.get_submissions()

        case_statuses = [case.zaak.status_text for case in cases]

        # add static text for open submissions
        case_statuses += [SUBMISSION_STATUS_OPEN for submission in submissions]

        return {status: case_statuses.count(status) for status in case_statuses}


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

        statuses = self.request.GET.getlist("status")

        f_url = furl(reverse("cases:cases_content"))
        f_url.args.addlist("status", statuses)

        context["hxget"] = f_url.url
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = OpenZaakConfig.get_solo()
        case_service = CaseListService(self.request)
        form = None

        # update ctx with open submissions, cases, form for filtering
        open_submissions: list[UniformCase] = case_service.get_submissions()
        preprocessed_cases: list[UniformCase] = case_service.get_cases()

        statuses = self.request.GET.getlist("status")
        # GET.getlist returns [''] if no query params are passed, hence we test by GET.get
        if self.request.GET.get("status"):
            form = CaseFilterForm(
                status_freqs=case_service.get_case_status_frequencies(),
                status_initial=statuses,
                data={"status": statuses},
            )

            # error message to user would be unhelpful;
            # we pass silently over invalid input and send a ping to Sentry
            if not form.is_valid():
                form.errors["status"] = []
                logger.error(
                    "Invalid data (%s) for case filtering by %s",
                    self.request.GET,
                    self.request.user,
                )

            open_submissions = (
                open_submissions if SUBMISSION_STATUS_OPEN in statuses else []
            )
            preprocessed_cases = [
                case for case in preprocessed_cases if case.zaak.status_text in statuses
            ]

        paginator_dict = self.paginate_with_context(
            [*open_submissions, *preprocessed_cases]
        )
        case_dicts = [case.process_data() for case in paginator_dict["object_list"]]

        context["cases"] = case_dicts
        context.update(paginator_dict)

        self.log_access_cases(case_dicts)

        # note: separate here with checked state?
        context["form"] = form or CaseFilterForm(
            status_freqs=case_service.get_case_status_frequencies(),
            status_initial=statuses,
        )

        # other data
        context["hxget"] = reverse("cases:cases_content")
        context["title_text"] = config.title_text

        return context
