from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.pdc.models import Category, ProductLocation


@plugin_pool.register_plugin
class CategoriesPlugin(CMSPluginBase):
    module = _("PDC")
    name = _("Categories Plugin")
    render_template = "cms/products/categories_plugin.html"

    # own variables
    limit = 4

    def render(self, context, instance, placeholder):
        context["categories"] = Category.objects.published().order_by("name")[
            0 : self.limit
        ]
        return context


@plugin_pool.register_plugin
class ProductLocationPlugin(CMSPluginBase):
    module = _("PDC")
    name = _("Product Location Plugin")
    render_template = "cms/products/product_location_plugin.html"

    def render(self, context, instance, placeholder):
        context["product_locations"] = ProductLocation.objects.all()[:1000]
        return context
