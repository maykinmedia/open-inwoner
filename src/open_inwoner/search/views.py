from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.translation import gettext as _
from django.http.response import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from open_inwoner.utils.mixins import PaginationMixin

from .searches import search_products
from .forms import FeedbackForm, SearchForm


class SearchView(PaginationMixin, FormView):
    form_class = SearchForm
    template_name = "pages/search.html"
    paginate_by = 20
    paginator_class = Paginator
    page_kwarg = "page"
    success_url = reverse_lazy("search:search")

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.search(form)
        else:
            context = super().get_context_data(form=form)
            return self.render_to_response(context)

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = {
            "initial": self.get_initial(),
            "prefix": self.get_prefix(),
            "data": self.request.GET,
        }
        return kwargs

    def search(self, form):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feedback_form"] = self.get_feedback_form()
        return context

    def get_feedback_form(self):
        if self.request.POST:
            form = FeedbackForm(data=self.request.POST)
        else:
            form = FeedbackForm(
                initial={
                    "query_params": self.request.GET.get("query"),
                    "query_url": self.request.get_full_path(),
                }
            )
        return form

    def post(self, request, *args, **kwargs):
        form = self.get_feedback_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        print(self.request.GET)
        if self.request.user.is_authenticated:
            form.instance.searched_by = self.request.user

        form.instance.search_query = self.request.POST.get("query_params")
        form.instance.search_url = self.request.POST.get("query_url")
        form.save()
        return HttpResponseRedirect(self.get_success_url())
