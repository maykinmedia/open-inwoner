import logging
from typing import Sequence

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from furl import furl
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.types import UniformCase
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin
from .services import CaseFilterFormOption, CaseListService

logger = logging.getLogger(__name__)


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
        context["filter_form_enabled"] = config.zaken_filter_enabled

        # update ctx with open submissions and cases (possibly fitered)
        open_submissions: Sequence[UniformCase] = case_service.get_submissions()
        preprocessed_cases: Sequence[UniformCase] = case_service.get_cases()

        if config.zaken_filter_enabled:
            case_status_frequencies = case_service.get_case_status_frequencies()
            # Separate frequency data from statusname
            context["status_freqs"] = [
                (status.value, frequency)
                for status, frequency in case_status_frequencies.items()
            ]

            # Validate statuses are valid according to the options enum
            statuses: list[CaseFilterFormOption] = []
            for status in self.request.GET.getlist("status"):
                try:
                    statuses.append(CaseFilterFormOption(status))
                except ValueError:
                    logger.error(
                        "Invalid data (%s) for case filtering by %s",
                        self.request.GET,
                        self.request.user,
                    )

            # Actually filter the submissions
            if statuses:
                open_submissions = (
                    open_submissions
                    if CaseFilterFormOption.OPEN_SUBMISSION in statuses
                    else []
                )
                preprocessed_cases = [
                    case
                    for case in preprocessed_cases
                    if case_service.get_case_filter_status(case.zaak) in statuses
                ]

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
