from unittest.mock import PropertyMock, patch

from django.test import Client, TestCase
from django.urls import reverse

from requests.exceptions import RequestException

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.config_checks.fetch_cases import (
    FetchCasesCheck,
    FetchCasesForm,
)
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory


class FetchCasesCheckTests(TestCase):
    def setUp(self):
        self.check = FetchCasesCheck()
        self.api_group = ZGWApiGroupConfigFactory()

    def test_invalid_bsn(self):
        form = FetchCasesForm(data={"bsn": "123"})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Invalid BSN", result.message)

    def test_no_api_group(self):
        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        result = self.check.run(
            form.cleaned_data,
            instance=None,
        )

        self.assertFalse(result.success)
        self.assertIn("No API group selected", result.message)

    def test_no_cases_returned(self):
        class DummyClient:
            base_url = "https://test.api"

            def fetch_zaken(self, user_identification):
                return []

        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        with patch.object(
            type(self.api_group),
            "zaken_client",
            new_callable=PropertyMock,
        ) as mock_client:
            mock_client.return_value = DummyClient()

            result = self.check.run(
                form.cleaned_data,
                instance=self.api_group,
            )

        self.assertFalse(result.success)
        self.assertEqual(result.extra["count"], 0)
        self.assertIn("diagnosis", result.extra)

    def test_cases_found(self):
        class DummyZaak:
            identificatie = "ZAAK-123"

        class DummyClient:
            base_url = "https://test.api"

            def fetch_zaken(self, user_identification):
                return [DummyZaak()]

        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        with patch.object(
            type(self.api_group),
            "zaken_client",
            new_callable=PropertyMock,
        ) as mock_client:
            mock_client.return_value = DummyClient()

            result = self.check.run(
                form.cleaned_data,
                instance=self.api_group,
            )

        self.assertTrue(result.success)
        self.assertEqual(result.extra["count"], 1)
        self.assertEqual(result.extra["sample"], "ZAAK-123")

    def test_request_exception(self):
        class DummyClient:
            base_url = "https://test.api"

            def fetch_zaken(self, user_identification):
                raise RequestException("Connection failed")

        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        with patch.object(
            type(self.api_group),
            "zaken_client",
            new_callable=PropertyMock,
        ) as mock_client:
            mock_client.return_value = DummyClient()

            result = self.check.run(
                form.cleaned_data,
                instance=self.api_group,
            )

        self.assertFalse(result.success)
        self.assertIn("Failed to connect", result.message)


class FetchCasesViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.superuser = UserFactory(
            is_superuser=True,
            is_staff=True,
        )
        self.user = UserFactory()

        self.api_group = ZGWApiGroupConfigFactory()

    def get_url(self):
        return reverse(
            "run_config_check",
            args=[
                "openzaak",
                "zgwapigroupconfig",
                self.api_group.pk,
                "fetch_cases",
            ],
        )

    def test_permission_denied_for_normal_user(self):
        self.client.force_login(self.user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_access(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fetch cases for BSN")

    def test_post_runs_check(self):
        class DummyClient:
            base_url = "https://test.api"

            def fetch_zaken(self, user_identification):
                return []

        self.client.force_login(self.superuser)

        with patch.object(
            type(self.api_group),
            "zaken_client",
            new_callable=PropertyMock,
        ) as mock_client:
            mock_client.return_value = DummyClient()

            response = self.client.post(self.get_url(), {"bsn": "123456789"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No cases returned")


class FetchCasesStandaloneTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = UserFactory(
            is_superuser=True,
            is_staff=True,
        )

    def test_requires_api_group(self):
        self.client.force_login(self.superuser)

        url = reverse(
            "run_config_check_standalone",
            args=["fetch_cases"],
        )

        response = self.client.post(url, {"bsn": "123456789"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No API group selected")
