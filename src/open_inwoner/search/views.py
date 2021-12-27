from django.views.generic import FormView

from open_inwoner.utils.mixins import PaginationMixin

from .forms import SearchForm
from .searches import search_products


class SearchView(PaginationMixin, FormView):
    form_class = SearchForm
    template_name = "pages/search.html"
    paginate_by = 20

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
        context = super().get_context_data(form=form)

        if not query:
            return self.render_to_response(context)

        # perform search
        results = search_products(query, filters=data)

        # update form fields with choices
        for facet in results.facets:
            if facet.name in form.fields:
                form.fields[facet.name].choices = facet.choices()

        # paginate
        paginator_dict = self.paginate_with_context(results.results)

        context.update(paginator_dict)
        context.update({"results": results})

        return self.render_to_response(context)
