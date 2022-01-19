from django.views.generic import TemplateView

from open_inwoner.openzaak.cases import fetch_cases


class CasesListView(TemplateView):
    template_name = "pages/cases/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cases = fetch_cases(self.request.user)

        if cases is None:
            context[
                "errors"
            ] = "Your cases cannot be retrieved. Logging in by using DigiD is mandatory."
        else:
            context["cases"] = cases

        return context
