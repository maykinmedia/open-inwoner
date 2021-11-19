"""
this file contains tests for the RESTful API
The logic of `search` is tested at `open_inwoner.search.tests` folder
"""

from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APITestCase

from open_inwoner.pdc.tests.factories import (
    CategoryFactory,
    OrganizationFactory,
    ProductFactory,
    TagFactory,
)
from open_inwoner.search.constants import FacetChoices
from open_inwoner.search.tests.utils import ESMixin


class SearchListTests(ESMixin, APITestCase):
    url = reverse_lazy("api:search")

    def test_search_list_with_search_param(self):
        product = ProductFactory.create(name="Some product")
        tags = sorted(TagFactory.create_batch(2), key=lambda x: x.name)
        orgs = sorted(OrganizationFactory.create_batch(2), key=lambda x: x.name)
        category = CategoryFactory.create()

        product.tags.add(*tags)
        product.organizations.add(*orgs)
        product.categories.add(category)

        self.update_index()

        response = self.client.get(self.url, {"search": "some"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "results": [
                    {
                        "name": "Some product",
                        "slug": product.slug,
                        "summary": product.summary,
                        "content": product.content,
                    }
                ],
                "facets": [
                    {
                        "name": FacetChoices.categories,
                        "buckets": [
                            {"slug": category.slug, "name": category.name, "count": 1}
                        ],
                    },
                    {
                        "name": FacetChoices.tags,
                        "buckets": [
                            {"slug": tags[0].slug, "name": tags[0].name, "count": 1},
                            {"slug": tags[1].slug, "name": tags[1].name, "count": 1},
                        ],
                    },
                    {
                        "name": FacetChoices.organizations,
                        "buckets": [
                            {"slug": orgs[0].slug, "name": orgs[0].name, "count": 1},
                            {"slug": orgs[1].slug, "name": orgs[1].name, "count": 1},
                        ],
                    },
                ],
            },
        )

    def test_search_list_without_facets(self):
        product = ProductFactory.create(name="Some product")
        self.update_index()

        response = self.client.get(self.url, {"search": "some"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "results": [
                    {
                        "name": "Some product",
                        "slug": product.slug,
                        "summary": product.summary,
                        "content": product.content,
                    }
                ],
                "facets": [
                    {
                        "name": FacetChoices.categories,
                        "buckets": [],
                    },
                    {
                        "name": FacetChoices.tags,
                        "buckets": [],
                    },
                    {
                        "name": FacetChoices.organizations,
                        "buckets": [],
                    },
                ],
            },
        )

    def test_search_list_without_search_param(self):
        """empty search will return all the results in order to use facets on them"""
        ProductFactory.create(name="Some product")
        self.update_index()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
