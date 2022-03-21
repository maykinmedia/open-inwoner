from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from open_inwoner.pdc.tests.factories import ProductFactory, ProductLocationFactory


class TestPDCLocation(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_products_endpoint_returns_location_coordinates(self):
        location = ProductLocationFactory()
        ProductFactory(locations=(location,))

        response = self.client.get(reverse("api:products-list"), format="json")

        coordinates = response.json()[0]["locations"][0]["coordinates"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(coordinates, [5.0, 52.0])
