from unittest.mock import Mock, patch

from django.test import TestCase

import requests

from open_inwoner.mijn_afval.clients import OpenAfvalAPIClient
from open_inwoner.mijn_afval.exceptions import MijnAfvalException


class OpenAfvalClientTest(TestCase):
    def test_get_afval_profiel_success(self):
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response_data = {
            "klant": {
                "id": "klant-123",
                "bsn": "123456789",
                "naam": "Test User",
                "totaalKosten": 50.00,
            },
            "containers": [
                {
                    "id": "container-1",
                    "publicContainerId": "PUB-001",
                    "afvalType": "restafval",
                    "isVerzamelcontainer": True,
                    "heeftSleutel": True,
                    "totaalGewicht": 600.5,
                    "totaalKosten": 25.00,
                }
            ],
            "containerLocaties": [
                {
                    "id": "bag-1",
                    "adres": "Teststraat 1",
                    "totaalGewicht": 1000.5,
                    "totaalKosten": 50.00,
                }
            ],
            "ledigingen": [
                {
                    "id": "lediging-1",
                    "containerLocation": "bag-1",
                    "klant": "klant-123",
                    "container": "container-1",
                    "gewicht": 50.5,
                    "geleegdOp": "2024-01-15T10:00:00+01:00",
                    "kosten": 12.50,
                }
            ],
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch.object(client, "get", return_value=mock_response):
            profiel = client.get_afval_profiel(bsn="123456789")

        self.assertEqual(profiel.klant.id, "klant-123")
        self.assertEqual(profiel.klant.bsn, "123456789")
        self.assertEqual(len(profiel.containers), 1)
        self.assertEqual(profiel.containers[0].afval_type, "restafval")
        self.assertEqual(len(profiel.container_locaties), 1)
        self.assertEqual(profiel.container_locaties[0].adres, "Teststraat 1")
        self.assertEqual(len(profiel.ledigingen), 1)

    def test_get_afval_profiel_http_error(self):
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError("Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        with patch.object(client, "get", return_value=mock_response):
            with self.assertRaises(MijnAfvalException):
                client.get_afval_profiel(bsn="123456789")

    def test_get_afval_profiel_uses_correct_bsn_in_url(self):
        """
        Regression test: verify the BSN parameter is used in the API endpoint URL
        """
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.json.return_value = {
            "klant": {
                "id": "klant-456",
                "bsn": "987654321",
                "naam": "Jane Doe",
                "totaalKosten": 0.00,
            },
            "containers": [],
            "containerLocaties": [],
            "ledigingen": [],
        }
        mock_response.status_code = 200

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            client.get_afval_profiel(bsn="987654321")

            # Verify the correct endpoint was called with the provided BSN
            mock_get.assert_called_once_with("afval-profiel/987654321/", params={})

    def test_get_afval_profiel_different_bsns_call_different_endpoints(self):
        """
        Regression test: verify different BSN values result in different API calls
        """
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response_template = {
            "klant": {
                "id": "klant-id",
                "bsn": "000000000",
                "naam": "Test User",
                "totaalKosten": 0.00,
            },
            "containers": [],
            "containerLocaties": [],
            "ledigingen": [],
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_template
        mock_response.status_code = 200

        test_bsns = ["111111111", "222222222", "333333333"]

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            for bsn in test_bsns:
                client.get_afval_profiel(bsn=bsn)

            # Verify each BSN was used in its API call
            self.assertEqual(mock_get.call_count, 3)
            mock_get.assert_any_call("afval-profiel/111111111/", params={})
            mock_get.assert_any_call("afval-profiel/222222222/", params={})
            mock_get.assert_any_call("afval-profiel/333333333/", params={})

    def test_get_afval_profiel_with_filters(self):
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response_data = {
            "klant": {
                "id": "klant-123",
                "bsn": "123456789",
                "naam": "Test User",
                "totaalKosten": 50.00,
            },
            "containers": [],
            "containerLocaties": [],
            "ledigingen": [],
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            client.get_afval_profiel(
                bsn="123456789",
                adressen=["Teststraat 1"],
                afval_type="gft",
                startdatum="2024-01-01",
                einddatum="2024-01-31",
            )

            # Verify all query params were passed
            mock_get.assert_called_once_with(
                "afval-profiel/123456789/",
                params={
                    "adres": ["Teststraat 1"],
                    "afval-type": "gft",
                    "startdatum": "2024-01-01",
                    "einddatum": "2024-01-31",
                },
            )

    def test_get_afval_profiel_with_multiple_addresses(self):
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response_data = {
            "klant": {
                "id": "klant-123",
                "bsn": "123456789",
                "naam": "Test User",
                "totaalKosten": 50.00,
            },
            "containers": [],
            "containerLocaties": [],
            "ledigingen": [],
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            client.get_afval_profiel(
                bsn="123456789",
                adressen=["Teststraat 1", "Kerkweg 45 B [5678CD UTRECHT]"],
            )

            mock_get.assert_called_once_with(
                "afval-profiel/123456789/",
                params={"adres": ["Teststraat 1", "Kerkweg 45 B [5678CD UTRECHT]"]},
            )

    def test_get_afval_profiel_with_partial_filters(self):
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response_data = {
            "klant": {
                "id": "klant-123",
                "bsn": "123456789",
                "naam": "Test User",
                "totaalKosten": 50.00,
            },
            "containers": [],
            "containerLocaties": [],
            "ledigingen": [],
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            client.get_afval_profiel(bsn="123456789", afval_type="restafval")

            mock_get.assert_called_once_with(
                "afval-profiel/123456789/", params={"afval-type": "restafval"}
            )

    def test_get_afval_profiel_no_filters(self):
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response_data = {
            "klant": {
                "id": "klant-123",
                "bsn": "123456789",
                "naam": "Test User",
                "totaalKosten": 50.00,
            },
            "containers": [],
            "containerLocaties": [],
            "ledigingen": [],
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            client.get_afval_profiel(bsn="123456789")

            mock_get.assert_called_once_with("afval-profiel/123456789/", params={})
