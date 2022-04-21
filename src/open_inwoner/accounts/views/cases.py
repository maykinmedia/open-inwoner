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
    fetch_substatuses,
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

        context["anchors"] = [
            ("#pending_apps", _("Lopende aanvragen")),
            ("#completed_apps", _("Afgeronde aanvragen")),
        ]
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

        statuses = fetch_status_history(case.url)
        status_types_done = [status.statustype for status in statuses]
        status_with_status_type = {status.url: status.statustype for status in statuses}

        status_types = fetch_status_types(case.zaaktype)
        status_types.sort(key=lambda status_type: status_type.volgnummer)
        status_types_urls = {st.url: st for st in status_types}

        substatuses = fetch_substatuses(case.url)
        substatuses.sort(key=lambda substatus: substatus.tijdstip)

        case_info_objects = fetch_case_information_objects(case.url)

        # dict with statustype as a key and the substatuses as a value
        final_substatuses = {}
        for status in statuses:
            for substatus in substatuses:
                if substatus.status == status.url:
                    if status.statustype in final_substatuses:
                        final_substatuses[status.statustype].append(substatus)
                    else:
                        final_substatuses[status.statustype] = [substatus]

        # dict with all the necessary data for the frontend
        final_statuses = []
        for status_type in status_types:
            final_statuses.append(
                {
                    "done": status_type.url in status_types_done,
                    "description": status_type.omschrijving,
                    "substatuses": final_substatuses.get(status_type.url),
                }
            )

        context["anchors"] = self.get_anchors(case, statuses, case_info_objects)
        context["case"] = {
            "obj": case,
            "current_status": status_types_urls.get(
                status_with_status_type.get(case.status)
            ),
            "final_statuses": final_statuses,
            "documents": case_info_objects,
        }
        # breakpoint()
        return context

    def get_anchors(self, case, statuses, documents):
        anchors = [["#title", _("Gegevens")]]

        if statuses:
            anchors.append(["#statuses", _("Status")])

        if documents:
            anchors.append(["#documents", _("Documenten")])

        return anchors
