from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin, ListBreadcrumbMixin

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.models.product import ProductCondition
from open_inwoner.plans.models import Plan
from open_inwoner.questionnaire.models import QuestionnaireStep

from ..utils.views import CommonPageMixin
from .choices import YesNo
from .forms import ProductFinderForm
from .models import Category, Product, ProductLocation, Question


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


class HomeView(CommonPageMixin, TemplateView):
    template_name = "pages/home.html"

    def page_title(self):
        return _("Home")

    def get_context_data(self, **kwargs):
        config = SiteConfiguration.get_solo()

        limit = 4
        kwargs.update(categories=Category.objects.published().order_by("name")[:limit])
        kwargs.update(product_locations=ProductLocation.objects.all()[:1000])
        kwargs.update(
            questionnaire_roots=QuestionnaireStep.get_root_nodes().filter(
                highlighted=True, published=True
            )
        )
        if self.request.user.is_authenticated and config.show_plans:
            kwargs.update(plans=Plan.objects.connected(self.request.user)[:limit])

        # Show the categories if the user has selected them, otherwise
        # Show the highlighted published categories if they have been specified, otherwise
        # Show the first X published categories

        # Highlighted categories
        highlighted_categories = (
            Category.objects.published()
            .filter(highlighted=True)
            .order_by("name")[:limit]
        )
        if (
            self.request.user.is_authenticated
            and self.request.user.selected_themes.exists()
        ):
            kwargs.update(
                categories=self.request.user.selected_themes.order_by("name")[:limit]
            )
        elif highlighted_categories:
            kwargs.update(categories=highlighted_categories)

        # Product finder:
        if config.show_product_finder:
            kwargs.update(
                condition=ProductCondition.objects.first(),
                condition_form=ProductFinderForm(),
            )
        return super().get_context_data(**kwargs)

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["pages/user-home.html"]
        else:
            return [self.template_name]


class FAQView(CommonPageMixin, TemplateView):
    template_name = "pages/faq.html"

    def page_title(self):
        return _("Veelgestelde vragen")

    def get_context_data(self, **kwargs):
        kwargs.update(faqs=Question.objects.general())
        return super().get_context_data(**kwargs)


class CategoryListView(CommonPageMixin, ListBreadcrumbMixin, ListView):
    template_name = "pages/category/list.html"
    model = Category

    def get_queryset(self):
        return Category.get_root_nodes().published()

    @cached_property
    def crumbs(self):
        config = SiteConfiguration.get_solo()
        return [(config.theme_title, reverse("pdc:category_list"))]


class CategoryDetailView(
    CommonPageMixin, BaseBreadcrumbMixin, CategoryBreadcrumbMixin, DetailView
):
    template_name = "pages/category/detail.html"
    model = Category
    breadcrumb_use_pk = False

    @cached_property
    def crumbs(self):
        base_list = [(_("Onderwerpen"), reverse("pdc:category_list"))]
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
        context["subcategories"] = self.object.get_children().published()
        context["products"] = self.object.products.published().order_in_category()
        context["questionnaire_roots"] = QuestionnaireStep.get_root_nodes().filter(
            category=self.object
        )
        return context

    def get_breadcrumb_name(self):
        return self.object.name


class ProductDetailView(
    CommonPageMixin, BaseBreadcrumbMixin, CategoryBreadcrumbMixin, DetailView
):
    template_name = "pages/product/detail.html"
    model = Product
    breadcrumb_use_pk = False
    no_list = True

    @cached_property
    def crumbs(self):
        base_list = [(_("Onderwerpen"), reverse("pdc:category_list"))]
        base_list += self.get_categories_breadcrumbs(slug_name="theme_slug")
        return base_list + [(self.get_object().name, self.request.path)]

    def get_context_data(self, **kwargs):
        product = self.get_object()
        context = super().get_context_data(**kwargs)

        anchors = [
            ("#title", product.name),
        ]
        if product.question_set.exists():
            anchors.append(("#faq", _("Veelgestelde vragen")))
        if product.files.exists():
            anchors.append(("#files", _("Bestanden")))
        if product.locations.exists():
            anchors.append(("#locations", _("Locaties")))
        if product.links.exists():
            anchors.append(("#links", _("Links")))
        if product.contacts.exists():
            anchors.append(("#contact", _("Contact")))
        if product.related_products.published().exists():
            anchors.append(("#see", _("Zie ook")))
        # anchors.append(("#share", _("Delen")))  disabled for #822

        context["anchors"] = anchors
        context["related_products_start"] = 6 if product.links.exists() else 1
        context["product_links"] = product.links.order_by("pk")
        return context


class ProductFormView(
    CommonPageMixin, BaseBreadcrumbMixin, CategoryBreadcrumbMixin, DetailView
):
    template_name = "pages/product/form.html"
    model = Product
    breadcrumb_use_pk = False
    no_list = True

    def page_title(self):
        return f"{self.object.name} {_('Formulier')}"

    @cached_property
    def crumbs(self):
        base_list = [(_("Onderwerpen"), reverse("pdc:category_list"))]
        base_list += self.get_categories_breadcrumbs(slug_name="theme_slug")
        return base_list + [
            (self.get_object().name, self.get_object().get_absolute_url()),
            (_("Formulier"), self.request.path),
        ]

    def get_context_data(self, **kwargs):
        product = self.get_object()
        context = super().get_context_data(**kwargs)

        anchors = [
            ("#title", product.name),
        ]

        context["anchors"] = anchors
        return context


class ProductFinderView(CommonPageMixin, FormView):
    template_name = "pages/product/finder.html"
    form_class = ProductFinderForm
    condition = None
    success_url = reverse_lazy("pdc:product_finder")

    def page_title(self):
        return _("Producten")

    def get(self, request, *args, **kwargs):
        self.condition = self.get_product_condition()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.loaded_previous = False
        if self.request.POST.get("reset") is not None:
            self.request.session["product_finder"] = {}
            self.request.session["current_condition"] = None
            self.request.session["conditions_done"] = False

        self.condition = self.get_product_condition()
        previous_condition = self.get_previous_condition()
        if self.request.POST.get("previous") is not None and previous_condition:
            self.request.session["current_condition"] = previous_condition.pk
            self.condition = previous_condition
            self.loaded_previous = True

        return super().post(request, *args, **kwargs)

    def get_initial(self):
        """See if we have an initial value to be set."""
        initial = super().get_initial()
        current_answers = self.request.session.get("product_finder")
        if current_answers:
            for _order, answer in current_answers.items():
                if answer.get("condition") == self.condition.pk:
                    initial["answer"] = answer.get("answer")
        return initial

    def get_next_condition(self):
        try:
            return ProductCondition.objects.filter(
                order__gt=self.condition.order
            ).first()
        except AttributeError:
            return None

    def get_previous_condition(self):
        try:
            return ProductCondition.objects.filter(
                order__lt=self.condition.order
            ).last()
        except AttributeError:
            return None

    def get_product_condition(self):
        current_condition = self.request.session.get("current_condition")
        if current_condition:
            try:
                return ProductCondition.objects.get(pk=current_condition)
            except ProductCondition.DoesNotExist:
                pass

        return ProductCondition.objects.first()

    def set_product_condition_sessions(self, answer):
        current_answers = self.request.session.get("product_finder")
        if current_answers:
            current_answers[str(self.condition.order)] = {
                "answer": answer,
                "condition": self.condition.pk,
            }
            self.request.session["product_finder"] = current_answers
        else:
            self.request.session["product_finder"] = {
                str(self.condition.order): {
                    "answer": answer,
                    "condition": self.condition.pk,
                }
            }

    def get_condition_products(self):
        current_answers = self.request.session.get("product_finder")
        filters = None
        if current_answers:
            for _order, answer in current_answers.items():
                new_filter = Q(conditions=answer.get("condition"))

                if filters:
                    filters = filters | new_filter
                else:
                    filters = new_filter

        if filters:
            return Product.objects.published().filter(filters).distinct()
        return Product.objects.none()

    def filter_matched_products(self, condition_products):
        products = condition_products
        current_answers = self.request.session.get("product_finder")
        if current_answers:
            for _order, answer in current_answers.items():
                if answer.get("answer") == YesNo.no:
                    products = products.exclude(conditions=answer.get("condition"))
        return products

    def filter_possible_products(self, condition_products, matched):
        qs = Product.objects.published().exclude(pk__in=matched.values_list("pk"))
        current_answers = self.request.session.get("product_finder")
        if current_answers:
            for _order, answer in current_answers.items():
                if answer.get("answer") == YesNo.no:
                    qs = qs.exclude(conditions=answer.get("condition"))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_condition = self.get_previous_condition()
        context["show_previous"] = previous_condition is not None
        context["condition"] = self.condition
        condition_products = self.get_condition_products()
        matched = self.filter_matched_products(condition_products)
        context["matched_products"] = matched
        context["possible_products"] = self.filter_possible_products(
            condition_products, matched
        )
        context["conditions_done"] = self.request.session.get("conditions_done", False)
        return context

    def form_valid(self, form):
        # redirect user to reset product finder if no conditions exist
        if not self.condition:
            self.request.session["product_finder"] = {}
            self.request.session["current_condition"] = None
            self.request.session["conditions_done"] = False
            return HttpResponseRedirect(self.get_success_url())

        self.set_product_condition_sessions(form.cleaned_data.get("answer"))
        next_condition = self.get_next_condition()
        if next_condition:
            self.request.session["current_condition"] = next_condition.pk
        self.request.session["conditions_done"] = next_condition is None
        return super().form_valid(form)

    def form_invalid(self, form):
        if (
            self.request.POST.get("reset") is not None
            or self.request.POST.get("previous") is not None
        ):
            del form.errors["answer"]
            return HttpResponseRedirect(self.get_success_url())
        return super().form_invalid(form)


class ProductLocationDetailView(
    CommonPageMixin, BaseBreadcrumbMixin, CategoryBreadcrumbMixin, DetailView
):
    template_name = "pages/product/location_detail.html"
    model = ProductLocation
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    @cached_property
    def crumbs(self):
        return [
            (
                self.get_object().name,
                reverse("pdc:location_detail", kwargs={"uuid": self.get_object().uuid}),
            )
        ]

    def get_context_data(self, **kwargs):
        location = self.get_object()
        context = super().get_context_data(**kwargs)
        context["products"] = location.products.published().order_by("name")
        return context
