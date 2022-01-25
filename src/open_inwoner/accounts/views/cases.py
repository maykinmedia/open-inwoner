from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openzaak.cases import fetch_cases


class CasesListView(BaseBreadcrumbMixin, LoginRequiredMixin, TemplateView):
    template_name = "pages/cases/list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn aanvragen"), reverse("accounts:my_cases"))]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cases = fetch_cases(self.request.user)

        context["open_cases"] = [case for case in cases if not case.einddatum]
        context["closed_cases"] = [case for case in cases if case.einddatum]

        context["open_cases"].sort(key=lambda case: case.startdatum, reverse=True)
        context["closed_cases"].sort(key=lambda case: case.einddatum, reverse=True)

        return context
