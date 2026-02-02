from unittest.mock import Mock, patch

from django.test import TestCase

import requests

from open_inwoner.mijn_afval.clients import OpenAfvalAPIClient
from open_inwoner.mijn_afval.exceptions import MijnAfvalException


class OpenAfvalClientTest(TestCase):
    def test_get_afval_profiel_success(self):
        """Test successful API call returns AfvalProfiel model"""
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        # Mock API response
        mock_response_data = {
            "klant": {"id": "klant-123", "bsn": "123456789", "naam": "Test User"},
            "summary": {
                "totaalGewicht": 1000.5,
                "totaalGewichtPerAfvalType": {"restafval": 600.5, "gft": 400.0},
                "aantalLedigingen": 10,
                "aantalContainers": 2,
                "aantalContainerLocaties": 1,
                "periode": {
                    "eersteLediging": "2024-01-01T10:00:00+01:00",
                    "laatsteLediging": "2024-12-31T10:00:00+01:00",
                },
            },
            "containers": [
                {
                    "id": "container-1",
                    "afvalType": "restafval",
                    "isVerzamelcontainer": True,
                    "heeftSleutel": True,
                    "totaalGewicht": 600.5,
                }
            ],
            "containerLocaties": [
                {"id": "bag-1", "adres": "Teststraat 1", "totaalGewicht": 1000.5}
            ],
            "ledigingen": [
                {
                    "id": "lediging-1",
                    "containerLocation": "bag-1",
                    "klant": "klant-123",
                    "container": "container-1",
                    "gewicht": 50.5,
                    "geleegdOp": "2024-01-15T10:00:00+01:00",
                }
            ],
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch.object(client, "get", return_value=mock_response):
            profiel = client.get_afval_profiel(bsn="123456789")

        # Verify AfvalProfiel structure
        self.assertEqual(profiel.klant.id, "klant-123")
        self.assertEqual(profiel.klant.bsn, "123456789")
        self.assertEqual(profiel.summary.totaal_gewicht, 1000.5)
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
            "klant": {"id": "klant-456", "bsn": "987654321", "naam": "Jane Doe"},
            "summary": {
                "totaalGewicht": 500.0,
                "totaalGewichtPerAfvalType": {"restafval": 500.0},
                "aantalLedigingen": 5,
                "aantalContainers": 1,
                "aantalContainerLocaties": 1,
                "periode": {
                    "eersteLediging": "2024-01-01T10:00:00+01:00",
                    "laatsteLediging": "2024-06-30T10:00:00+01:00",
                },
            },
            "containers": [],
            "containerLocaties": [],
            "ledigingen": [],
        }
        mock_response.status_code = 200

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            client.get_afval_profiel(bsn="987654321")

            # Verify the correct endpoint was called with the provided BSN
            mock_get.assert_called_once_with("afval-profiel/987654321")

    def test_get_afval_profiel_different_bsns_call_different_endpoints(self):
        """
        Regression test: verify different BSN values result in different API calls
        """
        client = OpenAfvalAPIClient(base_url="https://api.example.com")

        mock_response_template = {
            "klant": {"id": "klant-id", "bsn": "000000000", "naam": "Test User"},
            "summary": {
                "totaalGewicht": 100.0,
                "totaalGewichtPerAfvalType": {},
                "aantalLedigingen": 1,
                "aantalContainers": 1,
                "aantalContainerLocaties": 1,
                "periode": {
                    "eersteLediging": "2024-01-01T10:00:00+01:00",
                    "laatsteLediging": "2024-01-31T10:00:00+01:00",
                },
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
            mock_get.assert_any_call("afval-profiel/111111111")
            mock_get.assert_any_call("afval-profiel/222222222")
            mock_get.assert_any_call("afval-profiel/333333333")
