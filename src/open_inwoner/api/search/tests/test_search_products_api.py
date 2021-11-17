"""
this file contains tests for the RESTful API
The logic of `search` is tested at `open_inwoner.search.tests` folder
"""

from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APITestCase

from open_inwoner.pdc.tests.factories import ProductFactory
from open_inwoner.search.tests.utils import ESMixin


class SearchListTests(ESMixin, APITestCase):
    url = reverse_lazy("api:search")

    def setUp(self):
        super().setUp()

        self.product = ProductFactory.create(name="Some product")
        self.update_index()

    def test_search_list_with_query_param(self):
        response = self.client.get(self.url, {"search": "some"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "name": "Some product",
                    "slug": self.product.slug,
                    "summary": self.product.summary,
                    "content": self.product.content,
                }
            ],
        )

    def test_search_list_without_query_param(self):
        """empty search will return all the results in order to use facets on them"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "name": "Some product",
                    "slug": self.product.slug,
                    "summary": self.product.summary,
                    "content": self.product.content,
                }
            ],
        )
