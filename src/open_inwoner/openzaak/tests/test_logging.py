from django.test import TestCase

import requests_mock
from log_outgoing_requests.models import OutgoingRequestsLog
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.openzaak.cases import fetch_single_case

from ...utils.test import ClearCachesMixin
from ..models import OpenZaakConfig
from .factories import ServiceFactory
from .shared import ZAKEN_ROOT


@requests_mock.Mocker()
class TestFetchSpecificCase(ClearCachesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        cls.config = OpenZaakConfig.get_solo()
        cls.config.zaak_service = cls.zaak_service
        cls.config.save()

        cls.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
        )

    def test_outgoing_requests_are_logged_and_saved(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(self.zaak["url"], json=self.zaak)

        self.assertFalse(OutgoingRequestsLog.objects.exists())

        with self.assertLogs() as captured:
            fetch_single_case("d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        logs_messages = [record.getMessage() for record in captured.records]
        saved_logs = OutgoingRequestsLog.objects.filter(url=self.zaak["url"])

        self.assertIn("Outgoing request", logs_messages)
        self.assertTrue(saved_logs.exists())
