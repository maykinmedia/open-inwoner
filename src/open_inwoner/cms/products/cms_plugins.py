from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.pdc.forms import ProductFinderForm
from open_inwoner.pdc.models import Category, ProductCondition, ProductLocation
from open_inwoner.questionnaire.models import QuestionnaireStep

from ..utils.plugin_mixins import CMSActiveAppMixin


@plugin_pool.register_plugin
class CategoriesPlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("PDC")
    name = _("Categories Plugin")
    render_template = "cms/products/categories_plugin.html"
    app_hook = "ProductsApphook"
    cache = False

    # own variables
    limit = 4

    def render(self, context, instance, placeholder):
        request = context["request"]
        # Show the categories if the user has selected them, otherwise
        # Show the highlighted published categories if they have been specified, otherwise
        # Show the first X published categories

        # Highlighted categories
        highlighted_categories = (
            Category.objects.published().filter(highlighted=True).order_by("name")
        )
        if request.user.is_authenticated and request.user.selected_categories.exists():
            categories = request.user.selected_categories.order_by("name")[: self.limit]
        elif highlighted_categories.exists():
            categories = highlighted_categories[: self.limit]
        else:
            categories = Category.objects.published().order_by("name")[: self.limit]

        context["categories"] = categories

        return context


@plugin_pool.register_plugin
class QuestionnairePlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("PDC")
    name = _("Questionnaire Plugin")
    render_template = "cms/questionnaire/questionnaire_plugin.html"
    app_hook = "ProductsApphook"

    def render(self, context, instance, placeholder):
        context["questionnaire_roots"] = QuestionnaireStep.get_root_nodes().filter(
            highlighted=True, published=True
        )
        return context


@plugin_pool.register_plugin
class ProductFinderPlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("PDC")
    name = _("Product Finder Plugin")
    render_template = "cms/products/product_finder_plugin.html"
    app_hook = "ProductsApphook"

    def render(self, context, instance, placeholder):
        context["condition"] = ProductCondition.objects.first()
        context["condition_form"] = ProductFinderForm()
        return context


@plugin_pool.register_plugin
class ProductLocationPlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("PDC")
    name = _("Product Location Plugin")
    render_template = "cms/products/product_location_plugin.html"
    app_hook = "ProductsApphook"

    def render(self, context, instance, placeholder):
        context["product_locations"] = ProductLocation.objects.all()[:1000]
        return context
