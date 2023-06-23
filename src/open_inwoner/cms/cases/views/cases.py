from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, CaseListMixin, OuterCaseAccessMixin


class OuterOpenCaseListView(
    OuterCaseAccessMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    template_name = "pages/cases/list_outer.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("cases:open_cases"))]

    def page_title(self):
        return _("Lopende aanvragen")

    def get_anchors(self) -> list:
        return [
            (reverse("cases:open_submissions"), _("Open aanvragen")),
            ("#cases", _("Lopende aanvragen")),
            (reverse("cases:closed_cases"), _("Afgeronde aanvragen")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # anchors are needed here as well for rendering the mobile ones
        context["anchors"] = self.get_anchors()
        context["hxget"] = reverse("cases:open_cases_content")
        return context


class InnerOpenCaseListView(
    RequiresHtmxMixin, CommonPageMixin, CaseAccessMixin, CaseListMixin, TemplateView
):
    template_name = "pages/cases/list_inner.html"

    def page_title(self):
        return _("Lopende aanvragen")

    def get_cases(self):
        all_cases = super().get_cases()

        cases = [case for case in all_cases if not case.einddatum]
        cases.sort(key=lambda case: case.startdatum, reverse=True)
        return cases

    def get_anchors(self) -> list:
        return [
            (reverse("cases:open_submissions"), _("Open aanvragen")),
            ("#cases", _("Lopende aanvragen")),
            (reverse("cases:closed_cases"), _("Afgeronde aanvragen")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = reverse("cases:open_cases_content")
        return context


class OuterClosedCaseListView(
    OuterCaseAccessMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    template_name = "pages/cases/list_outer.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("cases:closed_cases"))]

    def page_title(self):
        return _("Afgeronde aanvragen")

    def get_anchors(self) -> list:
        return [
            (reverse("cases:open_submissions"), _("Open aanvragen")),
            (reverse("cases:open_cases"), _("Lopende aanvragen")),
            ("#cases", _("Afgeronde aanvragen")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = reverse("cases:closed_cases_content")
        context["anchors"] = self.get_anchors()
        return context


class InnerClosedCaseListView(
    RequiresHtmxMixin, CommonPageMixin, CaseAccessMixin, CaseListMixin, TemplateView
):
    template_name = "pages/cases/list_inner.html"

    def page_title(self):
        return _("Afgeronde aanvragen")

    def get_cases(self):
        all_cases = super().get_cases()

        cases = [case for case in all_cases if case.einddatum]
        cases.sort(key=lambda case: case.einddatum, reverse=True)
        return cases

    def get_anchors(self) -> list:
        return [
            (reverse("cases:open_submissions"), _("Open aanvragen")),
            (reverse("cases:open_cases"), _("Lopende aanvragen")),
            ("#cases", _("Afgeronde aanvragen")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = reverse("cases:closed_cases_content")
        return context
