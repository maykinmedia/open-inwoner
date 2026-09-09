from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from log_outgoing_requests.constants import SaveLogsChoice
from log_outgoing_requests.models import OutgoingRequestsLogConfig
from maykin_2fa.test import disable_admin_mfa
from pydantic import ValidationError

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.haalcentraal.api_models import BRP2xPersoon
from open_inwoner.haalcentraal.clients import BRPClient
from open_inwoner.haalcentraal.config_checks.fetch_brp import (
    FetchBRPCheck,
    FetchBRPForm,
)
from open_inwoner.haalcentraal.exceptions import BRPAPINetworkError
from open_inwoner.haalcentraal.models import HaalCentraalConfig


def make_validation_error() -> ValidationError:
    try:
        BRP2xPersoon.model_validate(
            {"verblijfplaats": {"verblijfadres": {"huisnummer": "not-a-number"}}}
        )
    except ValidationError as exc:
        return exc
    raise AssertionError("expected a ValidationError")  # pragma: no cover


class FetchBRPCheckTests(TestCase):
    def setUp(self):
        self.check = FetchBRPCheck()

    def test_refuses_to_run_while_save_body_enabled(self):
        config = OutgoingRequestsLogConfig.get_solo()
        config.save_body = SaveLogsChoice.yes
        config.save()

        form = FetchBRPForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("cannot be run", result.message)

    def test_invalid_bsn(self):
        form = FetchBRPForm(data={"bsn": "123"})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Ongeldig BSN", result.message)

    def test_not_configured(self):
        form = FetchBRPForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("not configured", result.message)

    def test_network_error(self):
        form = FetchBRPForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        mock_client = MagicMock()
        mock_client.fetch_brp_data_for_bsn.side_effect = BRPAPINetworkError(
            "Connection failed"
        )

        with patch.object(BRPClient, "from_config", return_value=mock_client):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Failed to connect", result.message)

    def test_validation_error(self):
        form = FetchBRPForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        mock_client = MagicMock()
        mock_client.fetch_brp_data_for_bsn.side_effect = make_validation_error()

        with patch.object(BRPClient, "from_config", return_value=mock_client):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("failed validation", result.message)

    def test_unexpected_error(self):
        form = FetchBRPForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        mock_client = MagicMock()
        mock_client.fetch_brp_data_for_bsn.side_effect = RuntimeError("boom")

        with patch.object(BRPClient, "from_config", return_value=mock_client):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Unexpected error", result.message)

    def test_no_person_found(self):
        form = FetchBRPForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        mock_client = MagicMock()
        mock_client.fetch_brp_data_for_bsn.return_value = None
        mock_client.version = "2.1"

        with patch.object(BRPClient, "from_config", return_value=mock_client):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("No person found", result.message)

    def test_person_found(self):
        form = FetchBRPForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        mock_client = MagicMock()
        mock_client.fetch_brp_data_for_bsn.return_value = BRP2xPersoon()
        mock_client.version = "2.1"

        with patch.object(BRPClient, "from_config", return_value=mock_client):
            result = self.check.run(form.cleaned_data)

        self.assertTrue(result.success)
        self.assertIn("BRP data retrieved", result.message)
        self.assertEqual(result.extra["version"], "2.1")


class FetchBRPViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.user = UserFactory()
        self.config = HaalCentraalConfig.get_solo()

    def get_url(self):
        return reverse(
            "run_config_check",
            args=["haalcentraal", "haalcentraalconfig", self.config.pk, "fetch_brp"],
        )

    def test_permission_denied_for_normal_user(self):
        self.client.force_login(self.user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 403)

    def test_permission_denied_for_staff_user_with_model_access(self):
        staff_user = UserFactory(is_staff=True, is_superuser=False)
        staff_user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="haalcentraal",
                content_type__model="haalcentraalconfig",
            )
        )
        self.client.force_login(staff_user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_access(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)

    def test_post_runs_check(self):
        self.client.force_login(self.superuser)

        response = self.client.post(self.get_url(), {"bsn": "123456789"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not configured")

    @disable_admin_mfa()
    def test_config_check_button_on_admin_change_page(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse(
                "admin:haalcentraal_haalcentraalconfig_change", args=[self.config.pk]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.get_url())


class FetchBRPStandaloneTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)

    def test_standalone_runs_check(self):
        self.client.force_login(self.superuser)

        url = reverse("run_config_check_standalone", args=["fetch_brp"])

        response = self.client.post(url, {"bsn": "123456789"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not configured")
