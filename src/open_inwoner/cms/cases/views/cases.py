from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.cases import preprocess_data
from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.formapi import fetch_open_submissions
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.types import UniformCase
from open_inwoner.openzaak.utils import get_fetch_parameters
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin


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

    def get_cases(self):
        client = build_client("zaak")

        if client is None:
            return []

        raw_cases = client.fetch_cases(**get_fetch_parameters(self.request))

        preprocessed_cases = preprocess_data(raw_cases)
        return preprocessed_cases

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
