from django.test import TestCase

from open_inwoner.pdc.tests.factories import (
    CategoryFactory,
    OrganizationFactory,
    ProductFactory,
    TagFactory,
)
from open_inwoner.search.constants import FacetChoices

from ..searches import search_products
from .utils import ESMixin


class SearchQueryTests(ESMixin, TestCase):
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
        results = search_products("Name").hits

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_summary(self):
        results = search_products("summary").hits

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_content(self):
        results = search_products("content").hits

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)


class SearchFacetTests(ESMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.product = ProductFactory.create(
            name="Name", summary="Some summary", content="Some content"
        )
        self.tags = sorted(TagFactory.create_batch(2), key=lambda x: x.name)
        self.orgs = sorted(OrganizationFactory.create_batch(2), key=lambda x: x.name)
        self.category = CategoryFactory.create()

        self.product.tags.add(*self.tags)
        self.product.organizations.add(*self.orgs)
        self.product.categories.add(self.category)

        self.update_index()

    def test_search_facets_top_level(self):
        results = search_products("some")

        self.assertEqual(len(results.hits), 1)

        facets = results.facets.to_dict()

        self.assertEqual(len(facets), 3)
        self.assertEqual(
            facets,
            {
                FacetChoices.categories: [(self.category.name, 1, False)],
                FacetChoices.tags: [
                    (self.tags[0].name, 1, False),
                    (self.tags[1].name, 1, False),
                ],
                FacetChoices.organizations: [
                    (self.orgs[0].name, 1, False),
                    (self.orgs[1].name, 1, False),
                ],
            },
        )
