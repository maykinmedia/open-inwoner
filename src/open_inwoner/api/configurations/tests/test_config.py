from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from open_inwoner.configurations.models import SiteConfiguration


class TestConfig(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.config = SiteConfiguration.get_solo()

    def test_config_endpoint_returns_expected_fields(self):
        url = reverse("api:site_configuration")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "name": self.config.name,
                "primaryColor": self.config.primary_color,
                "secondaryColor": self.config.secondary_color,
                "accentColor": self.config.accent_color,
                "logo": self.config.logo,
            },
        )
