from django.test import TestCase, override_settings
from django.urls import reverse


class ReportingEndpointsMiddlewareTests(TestCase):
    def test_declares_default_endpoint(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(
            response["Reporting-Endpoints"], 'default="/api/reporting-api/"'
        )

    @override_settings(REPORTING_API_ENABLED=False)
    def test_without_reporting(self):
        response = self.client.get(reverse("login"))

        self.assertNotIn("Reporting-Endpoints", response)
