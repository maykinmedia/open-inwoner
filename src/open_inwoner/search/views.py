from django.views.generic import FormView

from open_inwoner.search.searches import search_products

from .forms import SearchForm


class SearchView(FormView):
    form_class = SearchForm
    template_name = "pages/search.html"

    def form_valid(self, form):
        data = form.cleaned_data.copy()
        query = data.pop("query")

        # perform search
        results = search_products(query, filters=data)

        # update form fields with choices
        for facet in results.facets:
            if facet.name in form.fields:
                form.fields[facet.name].choices = facet.choices()

        context = self.get_context_data(form=form, results=results)
        return self.render_to_response(context)
