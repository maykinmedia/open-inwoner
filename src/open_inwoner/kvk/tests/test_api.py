from unittest.mock import patch

from django.test import TestCase

import requests_mock
from requests.exceptions import InvalidJSONError, SSLError

from ..client import KvKClient
from ..models import KvKConfig
from . import mocks
from .factories import CLIENT_CERT, CLIENT_CERT_PAIR, SERVER_CERT


class KvKAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.config = KvKConfig(
            api_root="https://api.kvk.nl/test/api/",
            api_key="12345",
            client_certificate=CLIENT_CERT,
            server_certificate=SERVER_CERT,
        )
        cls.kvk_client = KvKClient(cls.config)

    def setUp(self):
        patched_requests = patch("open_inwoner.kvk.client.requests.get")
        self.mocked_requests = patched_requests.start()
        self.addCleanup(patch.stopall)

    def test_search_endpoint(self):
        """
        Assert that the "Zoeken" API url is constructed properly from the API root:
            - trailing slashes are ignored
            - correct API version number is inserted
            - endpoint is appended
        """
        endpoint1 = self.kvk_client.search_endpoint

        # second client for contrast: same root but without '/'
        kvk_client2 = KvKClient(self.config)
        kvk_client2.config.api_root = "https://api.kvk.nl/test/api"

        endpoint2 = kvk_client2.search_endpoint

        self.assertEqual(endpoint1, "https://api.kvk.nl/test/api/v2/zoeken")
        self.assertEqual(endpoint1, endpoint2)

    def test_basisprofielen_endpoint(self):
        """
        Assert that the "Basisprofielen" API url is constructed properly from the API root:
            - trailing slashes are ignored
            - correct API version number is inserted
            - endpoint is appended
        """
        endpoint1 = self.kvk_client.basisprofielen_endpoint

        # second client for contrast: same root but without '/'
        kvk_client2 = KvKClient(self.config)
        kvk_client2.config.api_root = "https://api.kvk.nl/test/api"

        endpoint2 = kvk_client2.basisprofielen_endpoint

        self.assertEqual(endpoint1, "https://api.kvk.nl/test/api/v1/basisprofielen")
        self.assertEqual(endpoint1, endpoint2)

    def test_generic_search_by_kvk(self):
        self.mocked_requests.return_value.json.return_value = mocks.simple

        company = self.kvk_client.search(kvk="68750110")

        self.assertEqual(
            company,
            {
                "pagina": 1,
                "aantal": 1,
                "totaal": 1,
                "resultaten": [
                    {
                        "kvkNummer": "68750110",
                        "handelsnaam": "Test BV Donald",
                        "type": "rechtspersoon",
                        "links": [
                            {
                                "rel": "basisprofiel",
                                "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
                            }
                        ],
                    }
                ],
            },
        )

    def test_search_headquarters(self):
        self.mocked_requests.return_value.json.return_value = mocks.multiple

        headquarters = self.kvk_client.get_company_headquarters(kvk="68750110")
        self.assertEqual(
            headquarters,
            {
                "kvkNummer": "68750110",
                "vestigingsnummer": "000037178598",
                "handelsnaam": "Test BV Donald",
                "adresType": "bezoekadres",
                "straatnaam": "Hizzaarderlaan",
                "plaats": "Lollum",
                "type": "hoofdvestiging",
                "links": [
                    {
                        "rel": "basisprofiel",
                        "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
                    },
                    {
                        "rel": "vestigingsprofiel",
                        "href": "https://api.kvk.nl/test/api/v1/vestigingsprofielen/000037178598",
                    },
                ],
            },
        )

    def test_search_all_branches(self):
        self.mocked_requests.return_value.json.return_value = mocks.multiple

        branches = self.kvk_client.get_all_company_branches(kvk="68750110")

        self.assertEqual(
            branches,
            [
                {
                    "kvkNummer": "68750110",
                    "vestigingsnummer": "000037178598",
                    "handelsnaam": "Test BV Donald",
                    "adresType": "bezoekadres",
                    "straatnaam": "Hizzaarderlaan",
                    "plaats": "Lollum",
                    "type": "hoofdvestiging",
                    "links": [
                        {
                            "rel": "basisprofiel",
                            "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
                        },
                        {
                            "rel": "vestigingsprofiel",
                            "href": "https://api.kvk.nl/test/api/v1/vestigingsprofielen/000037178598",
                        },
                    ],
                },
                {
                    "kvkNummer": "68750110",
                    "vestigingsnummer": "000037178601",
                    "handelsnaam": "Test BV Donald Nevenvestiging",
                    "adresType": "bezoekadres",
                    "straatnaam": "Brinkerinckbaan",
                    "plaats": "Diepenveen",
                    "type": "nevenvestiging",
                    "links": [
                        {
                            "rel": "basisprofiel",
                            "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
                        },
                        {
                            "rel": "vestigingsprofiel",
                            "href": "https://api.kvk.nl/test/api/v1/vestigingsprofielen/000037178601",
                        },
                    ],
                },
            ],
        )

    def test_no_search_without_config(self):
        config = None
        kvk_client = KvKClient(config)

        company = kvk_client.search(kvk="68750110")

        self.assertEqual(company, {})

    def test_no_search_with_empty_api_root(self):
        """Sentry 343407"""

        config = KvKConfig(
            api_root="",
            api_key="12345",
            client_certificate=CLIENT_CERT,
            server_certificate=SERVER_CERT,
        )
        kvk_client = KvKClient(config)

        company = kvk_client.search(kvk="68750110")

        self.assertEqual(company, {})


class KvKRequestsInterfaceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = KvKConfig(
            api_root="https://api.kvk.nl/test/api/v1",
            api_key="12345",
            client_certificate=CLIENT_CERT,
            server_certificate=SERVER_CERT,
        )
        cls.kvk_client = KvKClient(config)

    def setUp(self):
        patched_requests = patch("open_inwoner.kvk.client.requests.get")
        self.mocked_requests = patched_requests.start()
        self.addCleanup(patch.stopall)

    def test_kvk_client_with_certs(self):
        self.kvk_client.get_company_headquarters(kvk="69599084")

        self.mocked_requests.assert_called_with(
            f"{self.kvk_client.search_endpoint}?kvkNummer=69599084&type=hoofdvestiging",
            headers={"apikey": self.kvk_client.config.api_key},
            cert=self.kvk_client.config.client_certificate.public_certificate.path,
            verify=self.kvk_client.config.server_certificate.public_certificate.path,
        )

    def test_kvk_client_with_key_pair(self):
        config = KvKConfig(
            api_root="https://api.kvk.nl/test/api/v1",
            api_key="12345",
            client_certificate=CLIENT_CERT_PAIR,
            server_certificate=SERVER_CERT,
        )
        self.kvk_client.config = config

        self.kvk_client.get_company_headquarters(kvk="69599084")

        self.mocked_requests.assert_called_with(
            f"{self.kvk_client.search_endpoint}?kvkNummer=69599084&type=hoofdvestiging",
            headers={"apikey": self.kvk_client.config.api_key},
            cert=(
                self.kvk_client.config.client_certificate.public_certificate.path,
                self.kvk_client.config.client_certificate.private_key.path,
            ),
            verify=self.kvk_client.config.server_certificate.public_certificate.path,
        )

    def test_kvk_client_no_certs(self):
        config = KvKConfig(
            api_root="https://api.kvk.nl/test/api/v1",
            api_key="12345",
        )
        kvk_client = KvKClient(config)

        kvk_client.search(kvkNummer="69599084")

        self.mocked_requests.assert_called_with(
            f"{kvk_client.search_endpoint}?kvkNummer=69599084",
            headers={"apikey": kvk_client.config.api_key},
            verify=True,
        )

    @requests_mock.Mocker()
    def test_kvk_response_not_ok(self, mocker):
        patch.stopall()  # use custom requests mock for this test

        for code in [300, 400, 500]:
            with self.subTest(code=code):
                mocker.get(
                    f"{self.kvk_client.search_endpoint}?kvkNummer=69599084",
                    status_code=code,
                )

                company = self.kvk_client.search(kvkNummer="69599084")
                self.assertEqual(company, {})

    def test_kvk_api_error(self):
        self.mocked_requests.side_effect = SSLError

        company = self.kvk_client.search(kvkNummer="69599084")

        self.assertEqual(company, {})

    def test_kvk_invalid_json(self):
        self.mocked_requests.return_value.json.side_effect = InvalidJSONError

        company = self.kvk_client.search(kvkNummer="69599084")

        self.assertEqual(company, {})

    def test_kvk_no_response(self):
        self.mocked_requests.return_value = None

        company = self.kvk_client.search(kvkNummer="69599084")

        self.assertEqual(company, {})
