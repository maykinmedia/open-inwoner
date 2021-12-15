from django.urls import reverse_lazy

from django_webtest import WebTest

from open_inwoner.pdc.tests.factories import (
    CategoryFactory,
    OrganizationFactory,
    ProductFactory,
    TagFactory,
)

from ..constants import FacetChoices
from .utils import ESMixin


class SearchPageTests(ESMixin, WebTest):
    url = reverse_lazy("search:search")

    def setUp(self):
        super().setUp()

        self.product1 = ProductFactory.create(
            name="Name", summary="Some summary", content="Some content"
        )
        self.product2 = ProductFactory.create(
            name="Other", summary="other summary", content="other content"
        )
        self.tag = TagFactory.create()
        self.org = OrganizationFactory.create()
        self.category = CategoryFactory.create()

        self.product1.tags.add(self.tag)
        self.product1.organizations.add(self.org)
        self.product1.categories.add(self.category)

        self.update_index()

    def test_not_show_results_and_filter_without_search(self):
        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        # check that form has `query` field
        self.assertIn("query", response.form.fields)
        for facet in FacetChoices.values:
            # check that facet fields are not shown
            self.assertNotIn(facet, response.form.fields)

        results_div = response.html.find("div", {"class": "search-results"})
        self.assertIsNone(results_div)  # check that results are not shown

    def test_show_results_and_filter_with_search(self):
        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.form
        form["query"] = "content"
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.request.url, f"http://testserver{self.url}?query=content"
        )
        # check that form has `query` field
        self.assertIn("query", response.form.fields)
        # check that facet fields are shown
        for facet in FacetChoices.values:
            self.assertIn(facet, response.form.fields)

        results_div = response.html.find("div", {"class": "search-results"})
        self.assertIsNotNone(results_div)  # check that results are shown

        results = response.context["results"].results
        self.assertEqual(len(results), 2)

    def test_search_with_filter(self):
        response = self.app.get(self.url, {"query": "content"})

        self.assertEqual(response.status_code, 200)

        form = response.form

        self.assertEqual(form["query"].value, "content")

        form["tags"] = [self.tag.slug]
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.request.url,
            f"http://testserver{self.url}?query=content&tags={self.tag.slug}",
        )
        # check that form has `query` field
        self.assertIn("query", response.form.fields)
        # check that facet fields are shown
        for facet in FacetChoices.values:
            self.assertIn(facet, response.form.fields)

        results_div = response.html.find("div", {"class": "search-results"})
        self.assertIsNotNone(results_div)  # check that results are shown

        results = response.context["results"].results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, self.product1.slug)

    def test_pagination_links(self):
        products = ProductFactory.create_batch(20, content="content")
        self.tag.products.add(*products)
        self.update_index()

        response = self.app.get(self.url, {"query": "content", "tags": self.tag.slug})

        self.assertEqual(response.status_code, 200)

        results = response.context["results"].results
        self.assertEqual(len(results), 21)

        pagination_div = response.html.find("div", {"class": "pagination"})
        pagination_links = pagination_div.find_all("a")

        # check that all query params are appended
        for link in pagination_links:
            self.assertEqual(
                link["href"], f"?query=content&tags={self.tag.slug}&page=2"
            )
