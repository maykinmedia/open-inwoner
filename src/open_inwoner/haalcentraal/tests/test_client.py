import json

from django.test import TestCase

import requests_mock

from ..api import BRP_2_1
from ..models import HaalCentraalConfig
from .mixins import HaalCentraalMixin


@requests_mock.Mocker()
class BRPClientTest(HaalCentraalMixin, TestCase):
    def test_brp_client_request_content(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        api_client = BRP_2_1()
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
        config.api_origin_oin = "test_x-origin-oin_header"
        config.api_doelbinding = "test_x-doelbinding_header"
        config.api_verwerking = "test_x-verwerking_header"
        config.save()

        api_client = BRP_2_1()
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

        api_client = BRP_2_1()
        api_client.make_request("999993847")

        self.assertEqual(
            m.request_history[0].headers["Content-Type"], "application/json"
        )
        # check that that additional headers are absent (not empty strings)
        self.assertIsNone(m.request_history[0].headers.get("x-origin-oin"))
        self.assertIsNone(m.request_history[0].headers.get("x-doelbinding"))
        self.assertIsNone(m.request_history[0].headers.get("x-verwerking"))
