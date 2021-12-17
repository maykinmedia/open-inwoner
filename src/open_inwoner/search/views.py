from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.translation import gettext as _
from django.views.generic import FormView

from open_inwoner.search.searches import search_products

from .forms import SearchForm


class SearchView(FormView):
    form_class = SearchForm
    template_name = "pages/search.html"
    paginate_by = 20
    paginator_class = Paginator
    page_kwarg = "page"

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
        paginator, page, queryset, is_paginated = self.paginate_object_list(
            results.results, self.paginate_by
        )

        context.update(
            {
                "get_paginator_dict": paginator,
                "page_obj": page,
                "is_paginated": is_paginated,
                "results": results,
            }
        )
        return self.render_to_response(context)

    def paginate_object_list(self, object_list, page_size):
        """copy past of MultipleObjectMixin.paginate_queryset method"""
        paginator = self.paginator_class(object_list, page_size)
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == "last":
                page_number = paginator.num_pages
            else:
                raise Http404(
                    _("Page is not 'last', nor can it be converted to an int.")
                )
        try:
            page = paginator.page(page_number)
            return paginator, page, page.object_list, page.has_other_pages()
        except InvalidPage as e:
            raise Http404(
                _("Invalid page (%(page_number)s): %(message)s")
                % {"page_number": page_number, "message": str(e)}
            )
