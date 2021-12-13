from django.views.generic import FormView

from open_inwoner.search.searches import search_products

from .forms import SearchForm


class SearchView(FormView):
    form_class = SearchForm
    template_name = "pages/search.html"

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = {
            "initial": self.get_initial(),
            "prefix": self.get_prefix(),
            "data": self.request.GET,
        }
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data.copy()
        query = data.pop("query")

        if not query:
            return self.render_to_response(self.get_context_data(form=form))

        # perform search
        results = search_products(query, filters=data)

        # update form fields with choices
        for facet in results.facets:
            if facet.name in form.fields:
                form.fields[facet.name].choices = facet.choices()

        context = self.get_context_data(form=form, results=results)
        return self.render_to_response(context)
