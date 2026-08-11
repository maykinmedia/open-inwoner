from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse

from requests.exceptions import RequestException

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.config_checks.fetch_cases import (
    FetchCasesCheck,
    FetchCasesForm,
)
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import (
    SkippedZaak,
    SkipReason,
    ZakenResult,
    ZGWService,
)
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory


def make_result(zaken=None, skipped=None):
    return ZakenResult(zaken=zaken or [], skipped=skipped or [])


class FetchCasesCheckTests(TestCase):
    def setUp(self):
        self.check = FetchCasesCheck()

    def test_invalid_bsn(self):
        form = FetchCasesForm(data={"bsn": "123"})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Ongeldig BSN", result.message)

    def test_no_cases_returned(self):
        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        with patch.object(ZGWService, "get_visible_zaken", return_value=make_result()):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Geen zichtbare zaken", result.message)
        self.assertEqual(result.extra["total"], 0)
        self.assertEqual(result.extra["total_visible"], 0)
        self.assertEqual(result.extra["total_not_visible"], 0)
        self.assertEqual(result.extra["not_visible"], {})

    def test_no_cases_returned_shows_skip_reasons(self):
        api_group = ZGWApiGroupConfigFactory()
        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        skipped = [
            SkippedZaak(
                zaak_url="https://api/zaak/1",
                reasons=frozenset({SkipReason.CONFIDENTIALITY_TOO_HIGH}),
                api_group=api_group,
            ),
            SkippedZaak(
                zaak_url="https://api/zaak/2",
                reasons=frozenset({SkipReason.CONFIDENTIALITY_TOO_HIGH}),
                api_group=api_group,
            ),
            SkippedZaak(
                zaak_url="https://api/zaak/3",
                reasons=frozenset({SkipReason.NO_STATUS}),
                api_group=api_group,
            ),
        ]
        with patch.object(
            ZGWService, "get_visible_zaken", return_value=make_result(skipped=skipped)
        ):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertEqual(result.extra["total"], 3)
        self.assertEqual(result.extra["total_visible"], 0)
        self.assertEqual(result.extra["total_not_visible"], 3)
        self.assertEqual(
            result.extra["not_visible"],
            {"confidentiality_too_high": 2, "no_status": 1},
        )

    def test_breakdown_per_api_group(self):
        group_a = ZGWApiGroupConfigFactory(name="Group A")
        group_b = ZGWApiGroupConfigFactory(name="Group B")
        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        mock_zaak = MagicMock()
        mock_zaak.api_group = group_a

        skipped = [
            SkippedZaak(
                zaak_url="https://api/zaak/1",
                reasons=frozenset({SkipReason.CONFIDENTIALITY_TOO_HIGH}),
                api_group=group_a,
            ),
            SkippedZaak(
                zaak_url="https://api/zaak/2",
                reasons=frozenset({SkipReason.NO_STATUS}),
                api_group=group_b,
            ),
        ]
        with patch.object(
            ZGWService,
            "get_visible_zaken",
            return_value=make_result(zaken=[mock_zaak], skipped=skipped),
        ):
            result = self.check.run(form.cleaned_data)

        by_group = result.extra["by_group"]
        self.assertEqual(by_group[str(group_a)]["total_visible"], 1)
        self.assertEqual(by_group[str(group_a)]["total_not_visible"], 1)
        self.assertEqual(
            by_group[str(group_a)]["not_visible"], {"confidentiality_too_high": 1}
        )
        self.assertEqual(by_group[str(group_b)]["total_visible"], 0)
        self.assertEqual(by_group[str(group_b)]["total_not_visible"], 1)
        self.assertEqual(by_group[str(group_b)]["not_visible"], {"no_status": 1})

    def test_cases_found(self):
        api_group = ZGWApiGroupConfigFactory()
        mock_zaak = MagicMock()
        mock_zaak.api_group = api_group

        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        with patch.object(
            ZGWService, "get_visible_zaken", return_value=make_result(zaken=[mock_zaak])
        ):
            result = self.check.run(form.cleaned_data)

        self.assertTrue(result.success)
        self.assertEqual(result.extra["total"], 1)
        self.assertEqual(result.extra["total_visible"], 1)
        self.assertEqual(result.extra["total_not_visible"], 0)

    def test_request_exception(self):
        form = FetchCasesForm(data={"bsn": "123456789"})
        self.assertTrue(form.is_valid())

        with patch.object(
            ZGWService,
            "get_visible_zaken",
            side_effect=RequestException("Connection failed"),
        ):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Gefaald om verbinding te maken", result.message)


class FetchCasesViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.user = UserFactory()
        self.config = OpenZaakConfig.get_solo()

    def get_url(self):
        return reverse(
            "run_config_check",
            args=["openzaak", "openzaakconfig", self.config.pk, "fetch_cases"],
        )

    def test_permission_denied_for_normal_user(self):
        self.client.force_login(self.user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_access(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zaken ophalen voor BSN")

    def test_post_runs_check(self):
        self.client.force_login(self.superuser)

        with patch.object(ZGWService, "get_visible_zaken", return_value=make_result()):
            response = self.client.post(self.get_url(), {"bsn": "123456789"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Geen zichtbare zaken")


class FetchCasesStandaloneTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)

    def test_standalone_runs_check(self):
        self.client.force_login(self.superuser)

        url = reverse("run_config_check_standalone", args=["fetch_cases"])

        with patch.object(ZGWService, "get_visible_zaken", return_value=make_result()):
            response = self.client.post(url, {"bsn": "123456789"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Geen zichtbare zaken")
