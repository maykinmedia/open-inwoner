from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openzaak.cases import (
    fetch_case_types,
    fetch_cases,
    fetch_single_case,
    fetch_single_case_type,
)
from open_inwoner.openzaak.statuses import (
    fetch_case_information_objects,
    fetch_single_status_type,
    fetch_specific_statuses,
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
        case_types = {case_type.url: case_type for case_type in fetch_case_types()}
        status_types = {
            status_type.url: status_type for status_type in fetch_status_types()
        }
        current_statuses = {
            status.zaak: status
            for status in fetch_specific_statuses([case.status for case in cases])
        }
        updated_cases = []
        for case in cases:
            current_status = current_statuses[case.url]

            # If the status type does not exist in the status types, retrieve it manually
            if current_status and not current_status.statustype in status_types:
                status_type = fetch_single_status_type(current_status.statustype)
                status_types.update({status_type.url: status_type})

            updated_cases.append(
                {
                    "uuid": str(case.uuid),
                    "start_date": case.startdatum,
                    "end_date": case.einddatum if hasattr(case, 'einddatum') else None,
                    "description": case_types[case.zaaktype].omschrijving
                    if case_types
                    else _("No data available"),
                    "current_status": status_types[
                        current_status.statustype
                    ].omschrijving
                    if current_status and status_types
                    else _("No data available"),
                }
            )

        context["anchors"] = [
            ("#pending_apps", _("Lopende aanvragen")),
            ("#completed_apps", _("Afgeronde aanvragen")),
        ]

        context["open_cases"] = [case for case in updated_cases if not case["end_date"]]
        context["open_cases"].sort(key=lambda case: case["start_date"])
        context["closed_cases"] = [case for case in updated_cases if case["end_date"]]
        context["closed_cases"].sort(key=lambda case: case["end_date"])

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
        case = fetch_single_case(case_uuid)

        if case:
            case_info_objects = fetch_case_information_objects(case.url)
            statuses = fetch_status_history(case.url)
            statuses.sort(key=lambda status: status.datum_status_gezet)

            case_type = fetch_single_case_type(case.zaaktype)
            status_types = fetch_status_types(case_type=case.zaaktype)

            status_types_mapping = {st.url: st for st in status_types}
            for status in statuses:
                status_type = status_types_mapping[status.statustype]
                status.statustype = status_type

            context["case"] = {
                "start_date": case.startdatum,
                "end_date": case.einddatum if hasattr(case, 'einddatum') else None,
                "description": case_type.omschrijving
                if case_type
                else _("No data available"),
                "current_status": statuses[-1].statustype.omschrijving
                if statuses
                and statuses[-1].statustype.omschrijving
                in [st.omschrijving for st in status_types]
                else _("No data available"),
                "statuses": statuses,
                "documents": case_info_objects,
            }
            context["anchors"] = self.get_anchors(statuses, case_info_objects)
        else:
            context["case"] = None
        return context

    def get_anchors(self, statuses, documents):
        anchors = [["#title", _("Gegevens")]]

        if statuses:
            anchors.append(["#statuses", _("Status")])

        if documents:
            anchors.append(["#documents", _("Documenten")])

        return anchors
