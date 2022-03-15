from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openzaak.cases import fetch_cases, fetch_specific_case
from open_inwoner.openzaak.statuses import (
    fetch_case_information_objects,
    fetch_status_history,
    fetch_status_types,
)


class CasesListView(
    BaseBreadcrumbMixin, LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "pages/cases/list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("accounts:my_cases"))]

    def test_func(self):
        return self.request.user.bsn is not None

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("root"))

        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cases = fetch_cases(self.request.user.bsn)

        context["open_cases"] = [case for case in cases if not case.einddatum]
        context["open_cases"].sort(key=lambda case: case.startdatum, reverse=True)
        context["closed_cases"] = [case for case in cases if case.einddatum]
        context["closed_cases"].sort(key=lambda case: case.einddatum, reverse=True)

        return context


class CasesStatusView(
    BaseBreadcrumbMixin, LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "pages/cases/status.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn aanvragen"), reverse("accounts:my_cases")),
            (
                _("Status"),
                reverse("accounts:case_status", kwargs=self.kwargs),
            ),
        ]

    def test_func(self):
        return self.request.user.bsn is not None

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("root"))

        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        case_uuid = context["object_id"]
        case = fetch_specific_case(case_uuid)

        if not case:
            return context

        case_info_objects = fetch_case_information_objects(case.url)
        statuses = fetch_status_history(case.url)
        status_types = fetch_status_types(case.zaaktype)

        status_types = {st.url: st for st in status_types}
        for status in statuses:
            status.statustype = status_types.get(status.statustype)

        # Sort list of statuses in order to able to get the most recent one
        statuses.sort(key=lambda status: status.datum_status_gezet, reverse=True)

        context["case"] = {
            "obj": case,
            "documents": case_info_objects,
            "statuses": statuses,
            "current_status": statuses[0] if statuses else None,
        }

        return context
