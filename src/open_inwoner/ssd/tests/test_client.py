from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from lxml import etree

from ..client import JaaropgaveClient, SSDBaseClient, UitkeringClient
from .factories import JaaropgaveConfigFactory, SSDConfigFactory

FILES_DIR = Path(__file__).parent.resolve() / "files"


@patch("open_inwoner.ssd.client.SSDBaseClient._make_request_body", return_value="")
class SSDClientRequestInterfaceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # facilitate testing the request interface through abstract SSDBaseClient
        SSDBaseClient.__abstractmethods__ = []
        super().setUpTestData()

    @requests_mock.Mocker()
    def test_tsl_with_server_cert(self, mock_request_body, mock_request):
        """Assert that TSL server certs are correctly passed to the request"""

        client = SSDBaseClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
            service__with_server_cert=True,
        )

        mock_request.post("https://example.com/soap-service")

        context = {"bsn": "dummy", "period": "dummy"}
        client.templated_request(**context)

        self.assertEqual(
            mock_request.last_request.verify,
            client.config.service.server_certificate.public_certificate.path,
        )

    @requests_mock.Mocker()
    def test_tsl_without_server_cert(self, mock_request_body, mock_request):
        """Assert that requests work without TSL server certs"""

        client = SSDBaseClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
            service__with_client_cert=True,
            service__with_server_cert=False,
        )

        mock_request.post("https://example.com/soap-service")

        context = {"bsn": "dummy", "period": "dummy"}
        client.templated_request(**context)

        self.assertEqual(mock_request.last_request.verify, True)

    @requests_mock.Mocker()
    def test_tls_no_client_cert(self, mock_request_body, mock_request):
        """Assert that requests work without tsl client certificates"""

        client = SSDBaseClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
            service__with_client_cert=False,
            service__with_server_cert=False,
        )

        mock_request.post("https://example.com/soap-service")

        context = {"bsn": "dummy", "period": "dummy"}
        client.templated_request(**context)

        self.assertIsNone(mock_request.last_request.cert)

    @requests_mock.Mocker()
    def test_tsl_client_public_cert_missing(self, mock_request_body, mock_request):
        """Assert that requests work without tsl public certificate"""

        client = SSDBaseClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
            service__with_client_cert=True,
            service__client_certificate__public_certificate="",
            service__with_server_cert=False,
        )

        mock_request.post("https://example.com/soap-service")

        context = {"bsn": "dummy", "period": "dummy"}
        client.templated_request(**context)

        self.assertIsNone(mock_request.last_request.cert)

    @requests_mock.Mocker()
    def test_tsl_client_public_cert_only(self, mock_request_body, mock_request):
        """Assert that tsl client certs are correctly passed to the request"""

        client = SSDBaseClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
            service__with_client_cert=True,
            service__client_certificate__with_private_key=False,
            service__with_server_cert=False,
        )

        mock_request.post("https://example.com/soap-service")

        context = {"bsn": "dummy", "period": "dummy"}
        client.templated_request(**context)

        self.assertEqual(
            mock_request.last_request.cert,
            client.config.service.client_certificate.public_certificate.path,
        )

    @requests_mock.Mocker()
    def test_tsl_client_cert_and_private_key(self, mock_request_body, mock_request):
        """Assert that tsl client certs and private keys are correctly passed to the request"""

        client = SSDBaseClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
            service__with_client_cert=True,
            service__client_certificate__with_private_key=True,
            service__with_server_cert=False,
        )

        mock_request.post("https://example.com/soap-service")

        context = {"bsn": "dummy", "period": "dummy"}
        client.templated_request(**context)

        self.assertEqual(
            mock_request.last_request.cert,
            (
                client.config.service.client_certificate.public_certificate.path,
                client.config.service.client_certificate.private_key.path,
            ),
        )


class UitkeringClientTest(TestCase):
    @requests_mock.Mocker()
    def test_request_status_not_ok(self, mock_request):
        client = UitkeringClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
        )

        for code in [300, 400, 500]:
            with self.subTest(code=code):
                mock_request.post("https://example.com/soap-service", status_code=code)
                res = client.get_report(bsn="12345", report_date_iso="1985-07-25")
                self.assertIsNone(res)

    @patch("django.utils.timezone.localtime", return_value=datetime(2023, 7, 12, 11, 0))
    @requests_mock.Mocker()
    def test_request_body(self, mock_datetime, mock_request):
        client = UitkeringClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
        )

        mock_request.post("https://example.com/soap-service")

        client.get_report(bsn="12345", report_date_iso="1985-07-25")

        # get request body and parse XML
        body = mock_request.last_request.body
        root = etree.fromstring(body)

        # check content
        self.assertEqual(
            root.find(".//{http://www.w3.org/2005/08/addressing}Action").text,
            "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient-v0600/UitkeringsSpecificatieInfo",
        )
        self.assertEqual(root.findtext(".//ApplicatieNaam"), "Open Inwoner")
        self.assertEqual(root.findtext(".//ApplicatieInformatie"), "Open Inwoner")
        for elem in root.findall(".//Gemeentecode"):
            self.assertEqual(elem.text, "12345")
        self.assertEqual(
            root.findtext(".//DatTijdAanmaakRequest"), "2023-07-12T11:00:00"
        )
        self.assertEqual(root.findtext(".//BurgerServiceNr"), "12345")
        self.assertEqual(root.findtext(".//Periodenummer"), "198507")


class JaaropgaveClientTest(TestCase):
    @requests_mock.Mocker()
    def test_request_status_not_ok(self, mock_request):
        client = JaaropgaveClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
        )

        for code in [300, 400, 500]:
            with self.subTest(code=code):
                mock_request.post("https://example.com/soap-service", status_code=code)
                res = client.get_report(bsn="12345", report_date_iso="1985-12-24")
                self.assertIsNone(res)

    @patch("django.utils.timezone.localtime", return_value=datetime(2023, 7, 12, 11, 0))
    @requests_mock.Mocker()
    def test_request_body(self, mock_datetime, mock_request):
        client = JaaropgaveClient()
        client.config = SSDConfigFactory.build(
            service__url="https://example.com/soap-service",
        )
        client.config.jaaropgave = JaaropgaveConfigFactory.build()

        mock_request.post("https://example.com/soap-service")

        client.get_report(bsn="12345", report_date_iso="1985-12-12")

        # get request body and parse XML
        body = mock_request.last_request.body
        root = etree.fromstring(body)

        self.assertEqual(
            root.find(".//{http://www.w3.org/2005/08/addressing}Action").text,
            "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient-v0400/JaarOpgaveInfo",
        )
        self.assertEqual(root.findtext(".//ApplicatieNaam"), "Open Inwoner")
        self.assertEqual(root.findtext(".//ApplicatieInformatie"), "Open Inwoner")
        for elem in root.findall(".//Gemeentecode"):
            self.assertEqual(elem.text, "12345")
        self.assertEqual(
            root.findtext(".//DatTijdAanmaakRequest"), "2023-07-12T11:00:00"
        )
        self.assertEqual(root.findtext(".//BurgerServiceNr"), "12345")
        self.assertEqual(root.findtext(".//Dienstjaar"), "1985")
