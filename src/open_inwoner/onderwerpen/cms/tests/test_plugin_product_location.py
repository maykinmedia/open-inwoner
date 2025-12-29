from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.core.cms.utils import cms_test_utils as cms_tools
from open_inwoner.onderwerpen.cms.cms_apps import ProductsApphook
from open_inwoner.onderwerpen.cms.cms_plugins import ProductLocationPlugin
from open_inwoner.onderwerpen.tests.factories import (
    ProductFactory,
    ProductLocationFactory,
)


@override_settings(ROOT_URLCONF="open_inwoner.core.cms.tests.urls")
class TestLocationViewThroughMap(WebTest):
    def test_product_location_link_is_rendered_in_plugin(self):
        cms_tools.create_apphook_page(ProductsApphook)
        product = ProductFactory()
        product_location = ProductLocationFactory()
        product.locations.add(product_location)

        html, context = cms_tools.render_plugin(ProductLocationPlugin)

        url = reverse(
            "products:location_detail", kwargs={"uuid": product_location.uuid}
        )
        self.assertIn(url, html)

    def test_no_output_generated_without_apphook(self):
        product = ProductFactory()
        product_location = ProductLocationFactory()
        product.locations.add(product_location)

        html, context = cms_tools.render_plugin(ProductLocationPlugin)
        self.assertEqual("", html)
