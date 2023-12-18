from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.openzaak.models import OpenZaakConfig
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
        config = OpenZaakConfig.get_solo()
        request = context["request"]
        # Show the all the highlighted categories the user has access to, as well as
        # categories that are linked to ZaakTypen for which the user has Zaken within
        # the specified period
        visible_categories = Category.objects.published().visible_for_user(request.user)
        categories = visible_categories.filter(highlighted=True)
        if (
            config.enable_categories_filtering_with_zaken
            and request.user.is_authenticated
            and request.user.bsn
        ):
            categories |= visible_categories.filter_for_user_with_zaken(request.user)

        context["categories"] = categories.order_by("path")

        return context


@plugin_pool.register_plugin
class QuestionnairePlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("PDC")
    name = _("Questionnaire Plugin")
    render_template = "cms/questionnaire/questionnaire_plugin.html"
    app_hook = "ProductsApphook"
    cache = False

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
    cache = False

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
    cache = False

    def render(self, context, instance, placeholder):
        context["product_locations"] = ProductLocation.objects.all()[:1000]
        return context
