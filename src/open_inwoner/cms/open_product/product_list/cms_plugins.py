from datetime import date

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.conf import settings
from django.core.cache import cache as django_cache
from django.utils.translation import gettext_lazy as _

from open_inwoner.open_product.models import OpenProductConfig

from .forms import ProductListForm
from .models import ProductList
from .utils import get_open_product_client


@plugin_pool.register_plugin
class ProductListPlugin(CMSPluginBase):
    module = _("Open Product")
    name = _("List of products")
    model = ProductList
    form = ProductListForm
    render_template = "cms/product_list/product_list_plugin.html"
    cache = False

    def __init__(self, model=None, admin_site=None):
        super().__init__(model, admin_site)
        self._client = None

        # 1 hour intervals for caching producttypes data
        self.PRODUCTTYPES_CACHE_TIMEOUT = 3600

    # Needs to be a property for the tests to work
    @property
    def client(self):
        if self._client is None:
            self._client = get_open_product_client()
        return self._client

    def _get_producttypes(self, theme):
        """
        Retrieves cached producttypes. If not available,
         they are retrieved from the API.
        """

        cache_id = f"products:{theme}"
        cached_producttypes = django_cache.get(cache_id)

        if cached_producttypes:
            return cached_producttypes

        producttypes = self.client.list_product_types(themas__uuid=theme)["results"]

        # Retrieve local configuration of product actions
        producttypeactionsconfig = OpenProductConfig.get_solo()
        action_urls = producttypeactionsconfig.action_urls

        # For every producttype, insert local 'action_url' configuration
        for pt in producttypes:
            for key, value in action_urls.items():
                action_full_name = key.split(":")
                pt_name = action_full_name[0]
                action_name = action_full_name[1]

                if pt["naam"] == pt_name:
                    for action in pt["acties"]:
                        if action["naam"] == action_name:
                            action["action_url"] = value

        django_cache.set(cache_id, producttypes, self.PRODUCTTYPES_CACHE_TIMEOUT)
        return producttypes

    def _retrieve_user_products(self, theme, bsn):
        """
        Retrieve products from the user based on a given theme and BSN.
        """

        producttypes = self._get_producttypes(theme)

        codes = [pt["code"] for pt in producttypes]
        products = self.client.list_products(
            producttype__code__in=codes, eigenaren__bsn=bsn
        )["results"]

        today = date.today()

        # 'insert' each full producttype object into
        # its corresponding product
        producttype_by_code = {pt["code"]: pt for pt in producttypes}

        display_products = []
        for product in products:
            product_type_code = product["producttype"]["code"]
            if product_type_code in producttype_by_code:
                product["producttype"] = producttype_by_code[product_type_code]
                display_products.append(product)
            if not hasattr(product, "eind_datum"):
                continue
            year, month, day = product["eind_datum"].split("-")
            end_date = date(int(year), int(month), int(day))

            expiration_days_left = (end_date - today).days

            # Set 'expiration' indicator depending on
            # the end date of the product
            product["nearing_expiration"] = (
                0
                < expiration_days_left
                <= getattr(settings, "EXPIRATION_WARNING_TIME_SLOT")
            )
        return display_products

    def render(self, context, instance, placeholder):
        # TODO: Find some solution here to make sure
        # that the user is actually logged in
        bsn = context["request"].user.bsn

        products = self._retrieve_user_products(instance.theme, bsn)

        context.update({"instance": instance, "products": products})

        return context
