from django.test import TestCase

from open_inwoner.pdc.tests.factories import (
    CategoryFactory,
    OrganizationFactory,
    ProductFactory,
    TagFactory,
)
from open_inwoner.search.constants import FacetChoices

from ..results import FacetBucket
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
        results = search_products("Name").results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_summary(self):
        results = search_products("summary").results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_content(self):
        results = search_products("content").results

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
        result = search_products("")

        self.assertEqual(len(result.results), 2)

        facets = result.facets
        self.assertEqual(len(facets), 3)
        facet_categories, facet_tags, facet_orgs = facets
        self.assertEqual(facet_categories.name, FacetChoices.categories)
        self.assertEqual(
            facet_categories.buckets,
            [
                FacetBucket(
                    slug=self.category.slug,
                    name=self.category.name,
                    count=2,
                    selected=False,
                )
            ],
        )
        self.assertEqual(facet_tags.name, FacetChoices.tags)
        self.assertEqual(
            facet_tags.buckets,
            [
                FacetBucket(
                    slug=self.tag1.slug, name=self.tag1.name, count=1, selected=False
                ),
                FacetBucket(
                    slug=self.tag2.slug, name=self.tag2.name, count=1, selected=False
                ),
            ],
        )
        self.assertEqual(facet_orgs.name, FacetChoices.organizations)
        self.assertEqual(
            facet_orgs.buckets,
            [
                FacetBucket(
                    slug=self.org1.slug, name=self.org1.name, count=1, selected=False
                ),
                FacetBucket(
                    slug=self.org2.slug, name=self.org2.name, count=1, selected=False
                ),
            ],
        )

    def test_facets_with_filter(self):
        result = search_products("", filters={"tags": self.tag1.slug})

        self.assertEqual(len(result.results), 1)
        self.assertEqual(int(result.results[0].meta.id), self.product1.id)

        facets = result.facets
        self.assertEqual(len(facets), 3)

        facet_categories, facet_tags, facet_orgs = facets
        self.assertEqual(facet_categories.name, FacetChoices.categories)
        self.assertEqual(
            facet_categories.buckets,
            [
                FacetBucket(
                    slug=self.category.slug,
                    name=self.category.name,
                    count=1,
                    selected=False,
                )
            ],
        )
        self.assertEqual(facet_tags.name, FacetChoices.tags)
        self.assertEqual(
            facet_tags.buckets,
            [
                FacetBucket(
                    slug=self.tag1.slug, name=self.tag1.name, count=1, selected=True
                )
            ],
        )
        self.assertEqual(facet_orgs.name, FacetChoices.organizations)
        self.assertEqual(
            facet_orgs.buckets,
            [
                FacetBucket(
                    slug=self.org1.slug, name=self.org1.name, count=1, selected=False
                )
            ],
        )

    def test_search_with_facet_filter(self):
        result = search_products("other", filters={"tags": self.tag1.slug})

        self.assertEqual(len(result.results), 0)
