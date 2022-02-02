from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView, TemplateView

from view_breadcrumbs import ListBreadcrumbMixin

from open_inwoner.utils.views import CustomDetailBreadcrumbMixin

from .models import Category, Product, ProductLocation


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        limit = 3 if self.request.user.is_authenticated else 4
        kwargs.update(categories=Category.get_root_nodes()[:limit])
        kwargs.update(product_locations=ProductLocation.objects.all()[:1000])
        return super().get_context_data(**kwargs)

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["pages/user-home.html"]
        else:
            return [self.template_name]


class CategoryListView(ListBreadcrumbMixin, ListView):
    template_name = "pages/category/list.html"
    model = Category

    def get_queryset(self):
        return Category.get_root_nodes()

    @cached_property
    def crumbs(self):
        return [(_("Categories"), reverse("pdc:category_list"))]


class CategoryDetailView(CustomDetailBreadcrumbMixin, DetailView):
    template_name = "pages/category/detail.html"
    model = Category
    breadcrumb_use_pk = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subcategories"] = self.object.get_children()
        context["products"] = self.object.products.all()
        return context

    def get_breadcrumb_name(self):
        return self.object.name


class ProductDetailView(CustomDetailBreadcrumbMixin, DetailView):
    template_name = "pages/product/detail.html"
    model = Product
    breadcrumb_use_pk = False
    no_list = True

    def get_breadcrumb_name(self):
        return self.object.name
