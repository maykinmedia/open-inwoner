from django.urls import NoReverseMatch, resolve, reverse
from django.utils.translation import gettext_lazy as _

from cms.apphook_pool import apphook_pool
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.pdc.forms import ProductFinderForm
from open_inwoner.pdc.models import Category, ProductCondition, ProductLocation
from open_inwoner.questionnaire.models import QuestionnaireStep

from ..utils.plugin_mixins import CMSActiveAppMixin


def selected_categories_enabled() -> bool:
    profile_app = apphook_pool.get_apphook("ProfileApphook")

    # retrieve namespace of ProfileConfig instance that's being used
    try:
        categories_resolver = resolve(reverse("profile:categories"))
    except NoReverseMatch:
        return False

    profile_namespace = categories_resolver.namespace
    config = profile_app.get_config(profile_namespace)

    if config:
        return config.selected_categories
    return False


@plugin_pool.register_plugin
class CategoriesPlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("PDC")
    name = _("Categories Plugin")
    render_template = "cms/products/categories_plugin.html"
    app_hook = "ProductsApphook"
    cache = False

    def render(self, context, instance, placeholder):
        config = OpenZaakConfig.get_solo()
        request = context["request"]

        if (
            request.user.is_authenticated
            and selected_categories_enabled()
            and request.user.selected_categories.exists()
        ):
            context["categories"] = request.user.selected_categories.all()
        else:
            # Show the all the highlighted categories the user has access to, as well as
            # categories that are linked to ZaakTypen for which the user has Zaken within
            # the specified period
            visible_categories = Category.objects.published().visible_for_user(
                request.user
            )
            categories = visible_categories.filter(highlighted=True)
            if (
                config.enable_categories_filtering_with_zaken
                and request.user.is_authenticated
                and (request.user.bsn or request.user.kvk)
            ):
                categories |= visible_categories.filter_by_zaken_for_request(request)

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
