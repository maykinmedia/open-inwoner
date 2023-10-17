from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.cases import fetch_cases, preprocess_data
from open_inwoner.openzaak.formapi import fetch_open_submissions
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin


class OuterCaseListView(
    OuterCaseAccessMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    """View on case list while being loaded"""

    template_name = "pages/cases/list_outer.html"

    def page_title(self):
        return _("Mijn aanvragen")

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("cases:redirect"))]

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
    """View on case list"""

    template_name = "pages/cases/list_inner.html"
    paginate_by = 9

    def page_title(self):
        return _("Mijn aanvragen")

    def get_cases(self):
        raw_cases = fetch_cases(self.request.user.bsn)
        preprocessed_cases = preprocess_data(raw_cases)
        preprocessed_cases.sort(key=lambda case: case.startdatum, reverse=True)
        return preprocessed_cases

    def get_submissions(self):
        subs = fetch_open_submissions(self.request.user.bsn)
        subs.sort(key=lambda sub: sub.datum_laatste_wijziging, reverse=True)
        return subs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = OpenZaakConfig.get_solo()

        # update ctx with cases + submissions
        preprocessed_cases = self.get_cases()
        open_submissions = self.get_submissions()
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
