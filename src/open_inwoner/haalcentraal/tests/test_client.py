from django.test import TestCase

import requests_mock

from ..api import BRP_2_1
from .mixins import HaalCentraalMixin


@requests_mock.Mocker()
class BRPClientTest(HaalCentraalMixin, TestCase):
    def test_request_content_type(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        api_client = BRP_2_1()
        response = api_client.make_request("999993847")

        self.assertEqual(
            response.request.body,
            b'{"fields": ["naam.geslachtsnaam", "naam.voorletters", "naam.voornamen", "naam.voorvoegsel", "geslacht.omschrijving", "geboorte.plaats.omschrijving", "geboorte.datum.datum", "verblijfplaats.verblijfadres.officieleStraatnaam", "verblijfplaats.verblijfadres.huisnummer", "verblijfplaats.verblijfadres.huisletter", "verblijfplaats.verblijfadres.huisnummertoevoeging", "verblijfplaats.verblijfadres.postcode", "verblijfplaats.verblijfadres.woonplaats"], "type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": ["999993847"]}',
        )
