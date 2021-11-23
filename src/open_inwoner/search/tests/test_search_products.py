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

        self.product1 = ProductFactory.create(
            name="Name", summary="Some summary", content="Some content"
        )
        self.product2 = ProductFactory.create(
            name="Other", summary="other summary", content="Some other"
        )
        self.tag1, self.tag2 = sorted(TagFactory.create_batch(2), key=lambda x: x.name)
        self.org1, self.org2 = sorted(
            OrganizationFactory.create_batch(2), key=lambda x: x.name
        )
        self.category = CategoryFactory.create()

        self.product1.tags.add(self.tag1)
        self.product1.organizations.add(self.org1)
        self.product1.categories.add(self.category)

        self.product2.tags.add(self.tag2)
        self.product2.organizations.add(self.org2)
        self.product2.categories.add(self.category)

        self.update_index()

    def test_facets_top_level(self):
        results = search_products("")

        self.assertEqual(len(results.hits), 2)

        facets = results.facets.to_dict()

        self.assertEqual(
            facets,
            {
                FacetChoices.categories: [(self.category.name, 2, False)],
                FacetChoices.tags: [
                    (self.tag1.slug, 1, False),
                    (self.tag2.slug, 1, False),
                ],
                FacetChoices.organizations: [
                    (self.org1.slug, 1, False),
                    (self.org2.slug, 1, False),
                ],
            },
        )

    def test_facets_with_filter(self):
        results = search_products("", filters={"tags": self.tag1.slug})

        self.assertEqual(len(results.hits), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

        facets = results.facets.to_dict()
        self.assertEqual(
            facets,
            {
                FacetChoices.categories: [(self.category.name, 1, False)],
                FacetChoices.tags: [
                    (self.tag1.slug, 1, True),
                ],
                FacetChoices.organizations: [
                    (self.org1.slug, 1, False),
                ],
            },
        )

    def test_search_with_facet_filter(self):
        results = search_products("other", filters={"tags": self.tag1.slug})

        self.assertEqual(len(results.hits), 0)
