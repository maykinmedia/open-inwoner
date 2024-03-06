from django.test import TestCase
from django.urls import reverse


class APIMockTest(TestCase):
    def test_basic_response(self):
        url = reverse(
            "apimock:mock",
            kwargs={
                "set_name": "openklant-read",
                "api_name": "klanten",
                "endpoint": "klanten",
            },
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("results", data)

        # check url transform
        url = data["results"][0]["url"]
        self.assertNotIn("https://klanten.nl/", url)
        self.assertIn("http://testserver/", url)

    def test_doctored_response_endpoint(self):
        url = reverse(
            "apimock:mock",
            kwargs={
                "set_name": "openklant-read",
                "api_name": "klanten",
                # let's try to read package.json
                "endpoint": "../../../../../../package",
            },
        )
        response = self.client.get(url)
        # status 403 if we get blocked on directory traversal
        self.assertEqual(response.status_code, 403)
