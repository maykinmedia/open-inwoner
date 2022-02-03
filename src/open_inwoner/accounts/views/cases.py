from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openzaak.cases import fetch_cases, fetch_specific_case
from open_inwoner.openzaak.statuses import fetch_status_history, fetch_status_types


class CasesListView(BaseBreadcrumbMixin, LoginRequiredMixin, TemplateView):
    template_name = "pages/cases/list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("accounts:my_cases"))]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_bsn = self.request.user.bsn
        if user_bsn is None:
            return context

        cases = fetch_cases(user_bsn)

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
        if self.request.user.bsn is None:
            return context

        case_uuid = context["object_id"]
        case = fetch_specific_case(case_uuid)

        if case:
            statuses = fetch_status_history(case.url)
            status_types = fetch_status_types(case.zaaktype)

            status_types = {st.url: st for st in status_types}
            for status in statuses:
                status.statustype = status_types[status.statustype]

            context["case"] = case
            context["statuses"] = statuses
            context["statuses"].sort(
                key=lambda status: status.datum_status_gezet, reverse=True
            )

        return context
