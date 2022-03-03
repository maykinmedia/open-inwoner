from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openzaak.cases import fetch_cases, fetch_specific_case
from open_inwoner.openzaak.status import fetch_status_history, fetch_status_type


class CasesListView(BaseBreadcrumbMixin, LoginRequiredMixin, TemplateView):
    template_name = "pages/cases/list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("accounts:my_cases"))]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cases = fetch_cases(self.request.user)

        context["open_cases"] = [case for case in cases if not case.einddatum]
        context["open_cases"].sort(key=lambda case: case.startdatum, reverse=True)
        context["closed_cases"] = [case for case in cases if case.einddatum]
        context["closed_cases"].sort(key=lambda case: case.einddatum, reverse=True)

        return context


class CasesStatusView(BaseBreadcrumbMixin, LoginRequiredMixin, TemplateView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        case_uuid = context["object_id"]
        case = fetch_specific_case(user, case_uuid)

        if case:
            status_list = fetch_status_history(user, case.url)
            status_url_list = [status.statustype for status in status_list]
            status_type_list = fetch_status_type(user, status_url_list)

            context["case"] = case
            context["status_list"] = status_list
            context["status_list"].sort(
                key=lambda status: status.datum_status_gezet, reverse=True
            )
            context["status_type_list"] = (
                status_type_list
                if isinstance(status_type_list, list)
                else [status_type_list]
            )

        return context
