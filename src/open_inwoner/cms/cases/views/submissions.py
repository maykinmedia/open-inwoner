from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.formapi import fetch_open_submissions
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, OuterCaseAccessMixin


class OuterOpenSubmissionListView(
    OuterCaseAccessMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    template_name = "pages/cases/submissions_outer.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("cases:open_submissions"))]

    def page_title(self):
        return _("Openstaande aanvragen")

    def get_anchors(self) -> list:
        return [
            ("#submissions", _("Openstaande aanvragen")),
            (reverse("cases:open_cases"), _("Lopende aanvragen")),
            (reverse("cases:closed_cases"), _("Afgeronde aanvragen")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = reverse("cases:open_submissions_content")
        context["anchors"] = self.get_anchors()
        return context


class InnerOpenSubmissionListView(
    RequiresHtmxMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    CaseAccessMixin,
    TemplateView,
):
    template_name = "pages/cases/submissions_inner.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("cases:open_submissions"))]

    def page_title(self):
        return _("Openstaande aanvragen")

    def get_submissions(self):
        submissions = fetch_open_submissions(self.request.user.bsn)
        return submissions

    def get_anchors(self) -> list:
        return [
            ("#submissions", _("Openstaande aanvragen")),
            (reverse("cases:open_cases"), _("Lopende aanvragen")),
            (reverse("cases:closed_cases"), _("Afgeronde aanvragen")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submissions"] = self.get_submissions()
        context["anchors"] = self.get_anchors()
        return context
