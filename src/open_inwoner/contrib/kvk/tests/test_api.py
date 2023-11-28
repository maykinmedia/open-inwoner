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
        config = KvKConfig(
            api_root="https://api.kvk.nl/test/api/v1",
            api_key="12345",
            client_certificate=CLIENT_CERT,
            server_certificate=SERVER_CERT,
        )
        cls.kvk_client = KvKClient(config)

    def setUp(self):
        patched_requests = patch("open_inwoner.contrib.kvk.client.requests.get")
        self.mocked_requests = patched_requests.start()
        self.addCleanup(patch.stopall)

    #
    # search
    #
    def test_search_by_kvk(self):
        self.mocked_requests.return_value.json.return_value = mocks.simple

        company = self.kvk_client.search(kvk="69599084")

        self.assertEqual(
            company,
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
            },
        )

    def test_search_by_kvk_multiple_results(self):
        """
        Test that the first result is used when multiple matches are found for the given KVK
        """
        self.mocked_requests.return_value.json.return_value = mocks.multiple

        company = self.kvk_client.search(kvk="69599084")
        self.assertEqual(
            company,
            {
                "kvkNummer": "69599084",
                "handelsnaam": "Test Stichting Bolderbast",
                "adresType": "bezoekadres",
                "straatnaam": "Oosterwal",
                "plaats": "Lochem",
                "type": "hoofdvestiging",
                "links": [
                    {
                        "rel": "basisprofiel",
                        "href": "https://api.kvk.nl/test/api/v1/basisprofielen/69599068",
                    }
                ],
            },
        )

    def test_search_by_kvk_extra_params(self):
        self.mocked_requests.return_value.json.return_value = mocks.simple

        company = self.kvk_client.search(kvk="68750110", type="Rechtspersoon")
        self.assertEqual(
            company,
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
            },
        )

    #
    # requests interface
    #
    def test_kvk_client_with_certs(self):
        self.kvk_client.search(kvk="69599084")

        self.mocked_requests.assert_called_with(
            f"{self.kvk_client.search_endpoint}?kvkNummer=69599084",
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

        self.kvk_client.search(kvk="69599084")

        self.mocked_requests.assert_called_with(
            f"{self.kvk_client.search_endpoint}?kvkNummer=69599084",
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

        kvk_client.search(kvk="69599084")

        self.mocked_requests.assert_called_with(
            f"{kvk_client.search_endpoint}?kvkNummer=69599084",
            headers={"apikey": kvk_client.config.api_key},
            cert=None,
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

                company = self.kvk_client.search(kvk="69599084")
                self.assertEqual(company, {})

    def test_kvk_api_error(self):
        self.mocked_requests.side_effect = SSLError

        company = self.kvk_client.search(kvk="69599084")

        self.assertEqual(company, {})

    def test_kvk_invalid_json(self):
        self.mocked_requests.return_value.json.side_effect = InvalidJSONError

        company = self.kvk_client.search(kvk="69599084")

        self.assertEqual(company, {})

    def test_kvk_no_response(self):
        self.mocked_requests.return_value = None

        company = self.kvk_client.search(kvk="69599084")

        self.assertEqual(company, {})
