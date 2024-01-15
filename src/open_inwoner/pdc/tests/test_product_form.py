from django.test import TestCase, override_settings
from django.urls import reverse

from .factories import ProductFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ProductFormTestCase(TestCase):
    def test_product_form_referrer_policy_header(self):
        product = ProductFactory(form="foo")

        response = self.client.get(
            reverse("products:product_form", kwargs={"slug": product.slug})
        )

        self.assertEqual(
            response.headers["Referrer-Policy"], "origin-when-cross-origin"
        )
