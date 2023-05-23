from django.test import TestCase
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory


class APIMockTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse(
            "apimock:mock",
            kwargs={
                "set_name": "openklant-read",
                "api_name": "klanten",
                "endpoint": "klanten",
            },
        )

    def test_basic_response(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("results", data)

        # check url transform
        url = data["results"][0]["url"]
        self.assertNotIn("https://klanten.nl/", url)
        self.assertIn("http://testserver/", url)
