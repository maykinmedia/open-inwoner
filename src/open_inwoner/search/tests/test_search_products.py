from django.test import TestCase

from open_inwoner.pdc.tests.factories import ProductFactory

from ..searches import search_products
from .utils import ESMixin


class SearchTests(ESMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.product1 = ProductFactory.create(
            name="Name", summary="Some summary", content="Some content"
        )
        self.product2 = ProductFactory.create(
            name="Other", summary="Other", content="Other"
        )
        self.update_index()

    def test_search_product_on_title(self):
        results = search_products("Name")

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_summary(self):

        results = search_products("summary")

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_content(self):
        results = search_products("content")

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)
