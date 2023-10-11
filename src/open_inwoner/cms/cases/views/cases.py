from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.formapi import fetch_open_submissions
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, CaseListMixin, OuterCaseAccessMixin


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
    RequiresHtmxMixin, CommonPageMixin, CaseAccessMixin, CaseListMixin, TemplateView
):
    """View on case list"""

    template_name = "pages/cases/list_inner.html"

    def page_title(self):
        return _("Mijn aanvragen")

    def get_cases(self):
        cases = super().get_cases()
        subs = fetch_open_submissions(self.request.user.bsn)

        cases.sort(key=lambda case: case.startdatum, reverse=True)
        subs.sort(key=lambda sub: sub.datum_laatste_wijziging, reverse=True)

        all_cases = subs + cases
        return all_cases

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = OpenZaakConfig.get_solo()

        context["hxget"] = reverse("cases:cases_content")
        context["title_text"] = config.title_text
        return context
