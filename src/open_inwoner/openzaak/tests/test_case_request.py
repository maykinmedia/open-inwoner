from django.test import TestCase

import requests_mock

from open_inwoner.openzaak.clients import build_zaken_client

from ...utils.test import ClearCachesMixin
from ..models import OpenZaakConfig
from .factories import ZGWApiGroupConfigFactory
from .helpers import generate_oas_component_cached
from .shared import ZAKEN_ROOT


@requests_mock.Mocker()
class TestFetchSpecificCase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()

        ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            form_service=None,
        )
        self.config = OpenZaakConfig.get_solo()
        self.zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
        )

        self.client = build_zaken_client()

    def test_case_is_retrieved(self, m):
        m.get(self.zaak["url"], json=self.zaak)

        case = self.client.fetch_single_case("d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertEqual(
            case.url,
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
        )

    def test_no_case_is_retrieved_when_http_404(self, m):
        m.get(self.zaak["url"], status_code=404)

        case = self.client.fetch_single_case("d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertIsNone(case)

    def test_no_case_is_retrieved_when_http_500(self, m):
        m.get(
            self.zaak["url"],
            status_code=500,
        )

        case = self.client.fetch_single_case("d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertIsNone(case)
