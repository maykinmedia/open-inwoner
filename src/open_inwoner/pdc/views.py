from django.views.generic import DetailView, ListView, TemplateView

from .models import Category


class HomeView(TemplateView):
    template_name = "master.html"

    def get_context_data(self, **kwargs):
        kwargs.update(categories=Category.get_root_nodes()[:4])
        return super().get_context_data(**kwargs)


class SearchView(TemplateView):
    template_name = "pages/search.html"


class CategoryListView(ListView):
    template_name = "pages/category/list.html"
    model = Category

    def get_queryset(self):
        return Category.get_root_nodes()


class CategoryDetailView(DetailView):
    template_name = "pages/category/detail.html"
    model = Category
