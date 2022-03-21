from django.http import Http404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView, TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin, ListBreadcrumbMixin

from open_inwoner.plans.models import Plan
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.utils.views import CustomDetailBreadcrumbMixin

from .models import Category, Product, ProductLocation


class CategoryBreadcrumbMixin:
    def get_orderd_categories(self, slug_name="slug"):
        slug = self.kwargs.get(slug_name, "")
        slugs = slug.split("/")
        categories = []
        older_slugs = ""
        for sl in slugs:
            if sl:
                categories.append(
                    {
                        "slug": sl,
                        "build_slug": f"{older_slugs}/{sl}" if older_slugs else sl,
                        "category": Category.objects.get(slug=sl),
                    }
                )
                if older_slugs:
                    older_slugs = f"{older_slugs}/{sl}"
                else:
                    older_slugs = sl
        return categories

    def get_categories_breadcrumbs(self, slug_name="slug"):
        return [
            (
                category.get("category").name,
                reverse(
                    "pdc:category_detail", kwargs={"slug": category.get("build_slug")}
                ),
            )
            for category in self.get_orderd_categories(slug_name=slug_name)
        ]


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        limit = 3 if self.request.user.is_authenticated else 4
        kwargs.update(categories=Category.get_root_nodes()[:limit])
        kwargs.update(product_locations=ProductLocation.objects.all()[:1000])
        kwargs.update(questionnaire_roots=QuestionnaireStep.get_root_nodes())
        if self.request.user.is_authenticated:
            kwargs.update(plans=Plan.objects.connected(self.request.user)[:limit])
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


class CategoryDetailView(BaseBreadcrumbMixin, CategoryBreadcrumbMixin, DetailView):
    template_name = "pages/category/detail.html"
    model = Category
    breadcrumb_use_pk = False

    @cached_property
    def crumbs(self):
        base_list = [(_("Thema's"), reverse("pdc:category_list"))]
        return base_list + self.get_categories_breadcrumbs()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get("slug", "")
        slugs = slug.split("/")
        queryset = queryset.filter(slug=slugs[-1])
        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subcategories"] = self.object.get_children()
        context["products"] = self.object.products.all()
        return context

    def get_breadcrumb_name(self):
        return self.object.name


class ProductDetailView(BaseBreadcrumbMixin, CategoryBreadcrumbMixin, DetailView):
    template_name = "pages/product/detail.html"
    model = Product
    breadcrumb_use_pk = False
    no_list = True

    @cached_property
    def crumbs(self):
        base_list = [(_("Thema's"), reverse("pdc:category_list"))]
        base_list += self.get_categories_breadcrumbs(slug_name="theme_slug")
        return base_list + [(self.get_object().name, self.request.path)]
