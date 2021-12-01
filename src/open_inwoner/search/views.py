from django.views.generic import FormView

from open_inwoner.search.searches import search_products

from .forms import SearchForm


class SearchView(FormView):
    form_class = SearchForm
    template_name = "pages/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(self.request.GET.get("query"))
        if self.request.GET.get("query"):
            context["results"] = search_products(
                self.request.GET.get("query"),
            )
        return context
