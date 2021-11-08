from django.test import TestCase

from open_inwoner.pdc.tests.factories import ProductFactory

from ..searches import search_products
from .utils import ESMixin


class SearchTests(ESMixin, TestCase):
    def test_search_product_on_title(self):
        product1 = ProductFactory.create(name="Some product")
        product2 = ProductFactory.create(name="Other product")
        self.update_index()

        results = search_products("some")

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), product1.id)

    def test_search_product_on_summary(self):
        product1 = ProductFactory.create(summary="Some summary for the first product")
        product2 = ProductFactory.create(name="Text for another product")
        self.update_index()

        results = search_products("some")

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), product1.id)

    def test_search_product_on_content(self):
        product1 = ProductFactory.create(
            content="Some description of the first product"
        )
        product2 = ProductFactory.create(content="Other description")
        self.update_index()

        results = search_products("some")

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), product1.id)
