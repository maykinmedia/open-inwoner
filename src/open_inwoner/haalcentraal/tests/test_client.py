import json

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

import requests_mock

from open_inwoner.haalcentraal.clients import BRPClient, BRPClient2x, BRPClient13
from open_inwoner.haalcentraal.models import BrpVersionChoices, HaalCentraalConfig
from open_inwoner.utils.test import ClearCachesMixin

from .mixins import HaalCentraalMixin


class BRPClientFromConfigTest(ClearCachesMixin, HaalCentraalMixin, TestCase):
    def test_raises_when_no_service_configured(self):
        with self.assertRaises(ImproperlyConfigured):
            BRPClient.from_config()

    def test_returns_1_3_client_for_version_1_3(self):
        self._setUpService()
        self._setUpVersion(BrpVersionChoices.V1_3)

        client = BRPClient.from_config()

        self.assertIsInstance(client, BRPClient13)
        self.assertEqual(client.version, BrpVersionChoices.V1_3)

    def test_returns_2_x_client_for_all_2_x_versions(self):
        self._setUpService()
        two_x_versions = [v for v in BrpVersionChoices if v != BrpVersionChoices.V1_3]

        for version in two_x_versions:
            with self.subTest(version=version):
                self._setUpVersion(version)
                client = BRPClient.from_config()
                self.assertIsInstance(client, BRPClient2x)
                self.assertEqual(client.version, version)

    def test_raises_on_unknown_version(self):
        self._setUpService()
        # bypass model validation to force an unrecognised version string
        HaalCentraalConfig.objects.update(brp_version="9.9")

        with self.assertRaises(NotImplementedError):
            BRPClient.from_config()


@requests_mock.Mocker()
class BRPClientTest(HaalCentraalMixin, TestCase):
    def test_brp_client_request_content(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        api_client = BRPClient.from_config()
        response = api_client.make_request("999993847")

        data = {
            "fields": [
                "naam.geslachtsnaam",
                "naam.voorletters",
                "naam.voornamen",
                "naam.voorvoegsel",
                "geslacht.omschrijving",
                "geboorte.plaats.omschrijving",
                "geboorte.datum.datum",
                "verblijfplaats.verblijfadres.officieleStraatnaam",
                "verblijfplaats.verblijfadres.huisnummer",
                "verblijfplaats.verblijfadres.huisletter",
                "verblijfplaats.verblijfadres.huisnummertoevoeging",
                "verblijfplaats.verblijfadres.postcode",
                "verblijfplaats.verblijfadres.woonplaats",
            ],
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": ["999993847"],
        }

        self.assertEqual(json.loads(response.request.body), data)

    def test_brp_client_additional_request_headers_defined(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        config = HaalCentraalConfig.get_solo()
        config.headers = [
            {"key": "x-origin-oin", "value": "test_x-origin-oin_header"},
            {"key": "x-doelbinding", "value": "test_x-doelbinding_header"},
            {"key": "x-verwerking", "value": "test_x-verwerking_header"},
        ]
        config.save()

        api_client = BRPClient.from_config()
        api_client.make_request("999993847")

        self.assertEqual(
            m.request_history[0].headers["Content-Type"], "application/json"
        )
        self.assertEqual(
            m.request_history[0].headers["x-origin-oin"], "test_x-origin-oin_header"
        )
        self.assertEqual(
            m.request_history[0].headers["x-doelbinding"], "test_x-doelbinding_header"
        )
        self.assertEqual(
            m.request_history[0].headers["x-verwerking"], "test_x-verwerking_header"
        )

    def test_brp_client_additional_request_headers_not_defined(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        api_client = BRPClient.from_config()
        api_client.make_request("999993847")

        self.assertEqual(
            m.request_history[0].headers["Content-Type"], "application/json"
        )
        # check that that additional headers are absent (not empty strings)
        self.assertIsNone(m.request_history[0].headers.get("x-origin-oin"))
        self.assertIsNone(m.request_history[0].headers.get("x-doelbinding"))
        self.assertIsNone(m.request_history[0].headers.get("x-verwerking"))
