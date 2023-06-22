from django.test import TestCase, tag

from open_inwoner.pdc.tests.factories import ProductFactory

from ..models import FieldBoost
from ..searches import search_products
from .utils import ESMixin


@tag("no-parallel")
class SearchBoostTests(ESMixin, TestCase):
    def setUp(self):
        super().setUp()

        # clear boosts
        FieldBoost.objects.all().delete()

        # add products
        self.product_name = ProductFactory.create(
            name="Some found",
            summary="Some",
            content="Some",
            keywords=["Some"],
        )
        self.product_summary = ProductFactory.create(
            name="Other", summary="Other found", content="Other", keywords=["other"]
        )
        self.product_content = ProductFactory.create(
            name="Any", summary="Any", content="Any found", keywords=["Any"]
        )
        self.update_index()

    def test_boost_name(self):
        FieldBoost.objects.create(field="name", boost=10)
        results = search_products("found").results

        self.assertEqual(len(results), 3)
        self.assertEqual(int(results[0].meta.id), self.product_name.id)

    def test_boost_summary(self):
        FieldBoost.objects.create(field="summary", boost=10)
        results = search_products("found").results

        self.assertEqual(len(results), 3)
        self.assertEqual(int(results[0].meta.id), self.product_summary.id)

    def test_boost_content(self):
        FieldBoost.objects.create(field="content", boost=10)
        results = search_products("found").results

        self.assertEqual(len(results), 3)
        self.assertEqual(int(results[0].meta.id), self.product_content.id)
