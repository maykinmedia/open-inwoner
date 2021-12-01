"""
this file contains tests for the RESTful API
The logic of `autocomplete` is tested at `open_inwoner.search.tests` folder
"""
from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APITestCase

from open_inwoner.pdc.tests.factories import ProductFactory
from open_inwoner.search.tests.utils import ESMixin


class AutocompleteApiTests(ESMixin, APITestCase):
    url = reverse_lazy("api:search_autocomplete")

    def setUp(self):
        super().setUp()

        ProductFactory.create(name="Some", keywords=["Other"])
        self.update_index()

    def test_autocomplete_success(self):
        response = self.client.get(self.url, {"search": "s"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"options": ["Some"]})

    def test_autocomplete_no_results(self):
        response = self.client.get(self.url, {"search": "m"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"options": []})

    def test_autocomplete_without_query(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"search": ["Dit veld is vereist."]})
