from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin, ListBreadcrumbMixin

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.models.product import ProductCondition
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.utils.views import LoginMaybeRequiredMixin

from ..utils.ckeditor import get_rendered_content
from ..utils.views import CommonPageMixin
from .choices import YesNo
from .forms import ProductFinderForm
from .models import Category, Product, ProductLocation, Question
from .utils import extract_subheadings


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
                        "category": get_object_or_404(Category, slug=sl),
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
                    "products:category_detail",
                    kwargs={"slug": category.get("build_slug")},
                ),
            )
            for category in self.get_orderd_categories(slug_name=slug_name)
        ]


class RedirectToLinkMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.auto_redirect_to_link:
            return HttpResponseRedirect(obj.auto_redirect_to_link)
        return super().dispatch(request, *args, **kwargs)


class FAQView(CommonPageMixin, TemplateView):
    template_name = "pages/faq.html"

    def page_title(self):
        return _("Veelgestelde vragen")

    def get_context_data(self, **kwargs):
        kwargs.update(faqs=Question.objects.general())
        return super().get_context_data(**kwargs)


class CategoryListView(
    LoginMaybeRequiredMixin, CommonPageMixin, ListBreadcrumbMixin, ListView
):
    template_name = "pages/category/list.html"
    model = Category

    def get_queryset(self):
        return Category.get_root_nodes().published().visible_for_user(self.request.user)

    @cached_property
    def crumbs(self):
        config = SiteConfiguration.get_solo()
        return [(config.theme_title, reverse("products:category_list"))]

    @property
    def display_restricted(self):
        config = SiteConfiguration.get_solo()
        return (
            not self.request.user.is_authenticated
            and config.hide_categories_from_anonymous_users is True
        )


class CategoryDetailView(
    LoginMaybeRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    CategoryBreadcrumbMixin,
    RedirectToLinkMixin,
    DetailView,
):
    template_name = "pages/category/detail.html"
    model = Category
    breadcrumb_use_pk = False

    @cached_property
    def crumbs(self):
        base_list = [(_("Onderwerpen"), reverse("products:category_list"))]
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
        context["category_rendered_description"] = get_rendered_content(
            self.object.description
        )
        return context

    def get_breadcrumb_name(self):
        return self.object.name

    @property
    def display_restricted(self):
        obj = self.get_object()

        if self.request.user.is_authenticated:
            if self.request.user.bsn:
                if obj.visible_for_citizens:
                    return False
                return True
            elif self.request.user.kvk:
                if obj.visible_for_companies:
                    return False
                return True

        if not obj.visible_for_anonymous:
            return True

        config = SiteConfiguration.get_solo()
        return (
            not self.request.user.is_authenticated
            and config.hide_categories_from_anonymous_users
        )

    def get_permission_denied_message(self):
        if self.request.user.is_authenticated:
            if self.request.user.bsn:
                return _("This page cannot be accessed by citizens")
            elif self.request.user.kvk:
                return _("This page cannot be accessed by companies")


class ProductDetailView(
    CommonPageMixin,
    BaseBreadcrumbMixin,
    CategoryBreadcrumbMixin,
    RedirectToLinkMixin,
    DetailView,
):
    template_name = "pages/product/detail.html"
    model = Product
    breadcrumb_use_pk = False
    no_list = True

    @cached_property
    def crumbs(self):
        base_list = [(_("Onderwerpen"), reverse("products:category_list"))]
        base_list += self.get_categories_breadcrumbs(slug_name="category_slug")
        return base_list + [(self.get_object().name, self.request.path)]

    def get_context_data(self, **kwargs):
        config = SiteConfiguration.get_solo()
        product = self.get_object()
        context = super().get_context_data(**kwargs)
        request = context["view"].request

        subheadings = extract_subheadings(product.content, tag="h2")

        anchors = subheadings
        if product.content_is_collapsable:
            anchors = []
        if product.question_set.exists():
            anchors.append(("#faq", _("Veelgestelde vragen")))
        if product.files.exists():
            anchors.append(("#files", _("Bestanden")))
        if product.locations.exists():
            anchors.append(("#locations", _("Locaties")))
        if product.contacts.exists():
            anchors.append(("#contact", _("Contact")))

        context["meta_description"] = product.summary
        if product.icon:
            context["meta_image_url"] = request.build_absolute_uri(product.icon.url)
        context["meta_page_url"] = request.build_absolute_uri(request.path)
        context["anchors"] = anchors
        context["related_products_start"] = 6 if product.links.exists() else 1
        context["product_links"] = product.links.order_by("pk")
        context["display_social"] = config.display_social
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
        base_list = [(_("Onderwerpen"), reverse("products:category_list"))]
        base_list += self.get_categories_breadcrumbs(slug_name="category_slug")
        return base_list + [
            (self.get_object().name, self.get_object().get_absolute_url()),
            (_("Formulier"), self.request.path),
        ]


class ProductFinderView(CommonPageMixin, FormView):
    template_name = "pages/product/finder.html"
    form_class = ProductFinderForm
    condition = None
    success_url = reverse_lazy("products:product_finder")

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
                reverse(
                    "products:location_detail", kwargs={"uuid": self.get_object().uuid}
                ),
            )
        ]

    def get_context_data(self, **kwargs):
        location = self.get_object()
        context = super().get_context_data(**kwargs)
        context["products"] = location.products.published().order_by("name")
        return context
