from django.test import TestCase, tag

from open_inwoner.onderwerpen.tests.factories import (
    CategoryFactory,
    OrganizationFactory,
    ProductFactory,
    TagFactory,
)
from open_inwoner.search.constants import FacetChoices
from open_inwoner.search.results import FacetBucket
from open_inwoner.search.views import multi_search

from .utils import ESMixin


@tag("elastic")
class SearchQueryTests(ESMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.product1 = ProductFactory.create(
            name="Name",
            summary="Some summary",
            content="Some content",
            keywords=["keyword1", "keyword2"],
        )
        self.product2 = ProductFactory.create(
            name="Other", summary="Other", content="Other", keywords=["other"]
        )
        self.update_index()

    def test_search_product_on_name(self):
        response, _ = multi_search("Name")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_name_partial(self):
        response, _ = multi_search("nam")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_summary(self):
        response, _ = multi_search("summary")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_summary_partial(self):
        response, _ = multi_search("sum")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_content(self):
        response, _ = multi_search("content")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_content_partial(self):
        response, _ = multi_search("cont")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_keyword(self):
        response, _ = multi_search("keyword1")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_on_keyword_partial(self):
        response, _ = multi_search("key")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_with_typo(self):
        response, _ = multi_search("sumary")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)

    def test_search_product_hide_unpublished(self):
        product_unpublished = ProductFactory.create(
            name="Name 3",
            summary="Some summary",
            content="Some content",
            keywords=["keyword1", "keyword2"],
            published=False,
        )
        self.update_index()
        response, _ = multi_search("Name")
        results = response.results

        self.assertEqual(len(results), 1)
        self.assertEqual(int(results[0].meta.id), self.product1.id)


@tag("elastic")
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
        result, _ = multi_search("")

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
        result, _ = multi_search("", filters={"tags": self.tag1.slug})

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
        result, _ = multi_search("other", filters={"tags": self.tag1.slug})

        self.assertEqual(len(result.results), 0)
