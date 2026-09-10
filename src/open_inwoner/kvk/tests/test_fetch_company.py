from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.kvk.client import KvKClient
from open_inwoner.kvk.config_checks.fetch_company import (
    FetchCompanyCheck,
    FetchCompanyForm,
)
from open_inwoner.kvk.exceptions import KVKAPIException
from open_inwoner.kvk.models import KvKConfig

from . import mocks


class FetchCompanyCheckTests(TestCase):
    def setUp(self):
        self.check = FetchCompanyCheck()

    def test_invalid_kvk_number(self):
        form = FetchCompanyForm(data={"kvk_number": "123"})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Invalid KvK number format", result.message)

    def test_no_company_found(self):
        form = FetchCompanyForm(data={"kvk_number": "12345678"})
        self.assertTrue(form.is_valid())

        with patch.object(KvKClient, "get_basisprofiel", return_value={}):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("No company found", result.message)

    def test_company_found(self):
        form = FetchCompanyForm(data={"kvk_number": "68750110"})
        self.assertTrue(form.is_valid())

        with patch.object(
            KvKClient, "get_basisprofiel", return_value=mocks.hoofdvestiging
        ):
            result = self.check.run(form.cleaned_data)

        self.assertTrue(result.success)
        self.assertEqual(result.extra, mocks.hoofdvestiging)

    def test_api_exception(self):
        form = FetchCompanyForm(data={"kvk_number": "68750110"})
        self.assertTrue(form.is_valid())

        with patch.object(
            KvKClient,
            "get_basisprofiel",
            side_effect=KVKAPIException("Connection failed"),
        ):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Failed to connect to KvK API", result.message)


class FetchCompanyViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.user = UserFactory()
        self.config = KvKConfig.get_solo()

    def get_url(self):
        return reverse(
            "run_config_check",
            args=["kvk", "kvkconfig", self.config.pk, "fetch_company"],
        )

    def test_permission_denied_for_normal_user(self):
        self.client.force_login(self.user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_access(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fetch company for KvK number")

    def test_post_runs_check(self):
        self.client.force_login(self.superuser)

        with patch.object(
            KvKClient, "get_basisprofiel", return_value=mocks.hoofdvestiging
        ):
            response = self.client.post(self.get_url(), {"kvk_number": "68750110"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Company data returned")

    def test_button_shown_on_admin_change_page(self):
        self.client.force_login(self.superuser)

        url = reverse("admin:kvk_kvkconfig_change", args=[self.config.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.get_url())
