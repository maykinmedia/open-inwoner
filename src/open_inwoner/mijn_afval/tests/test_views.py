from datetime import datetime

from django.test import TestCase

from open_inwoner.mijn_afval.api_models import (
    AfvalContainer,
    AfvalContainerLocatie,
    AfvalLediging,
    AfvalProfiel,
    Klant,
)
from open_inwoner.mijn_afval.views import (
    _convert_period_to_dates,
    _extract_filter_options,
    _format_address,
)


class ExtractFilterOptionsTest(TestCase):
    def test_extract_filter_options_with_data(self):
        profiel = AfvalProfiel(
            klant=Klant(id="klant-1", bsn="123456789", naam="Test User"),
            containers=[
                AfvalContainer(
                    id="container-1",
                    afval_type="gft",
                    is_verzamelcontainer=False,
                    heeft_sleutel=True,
                    totaal_gewicht=100.0,
                )
            ],
            container_locaties=[
                AfvalContainerLocatie(
                    id="loc-1",
                    adres="Dorpsstraat 12 [1234AB AMSTERDAM]",
                    totaal_gewicht=100.0,
                ),
                AfvalContainerLocatie(
                    id="loc-2",
                    adres="Kerkweg 45 B [5678CD UTRECHT]",
                    totaal_gewicht=50.0,
                ),
            ],
            ledigingen=[
                AfvalLediging(
                    id="led-1",
                    container_location="loc-1",
                    klant="klant-1",
                    container="container-1",
                    gewicht=25.0,
                    geleegd_op=datetime(2023, 6, 15, 10, 0, 0),
                ),
                AfvalLediging(
                    id="led-2",
                    container_location="loc-2",
                    klant="klant-1",
                    container="container-1",
                    gewicht=30.0,
                    geleegd_op=datetime(2025, 3, 20, 14, 30, 0),
                ),
            ],
        )

        options = _extract_filter_options(profiel)

        # Verify addresses are formatted and sorted
        self.assertEqual(len(options["addresses"]), 2)
        self.assertIn("Dorpsstraat 12, 1234 AB, Amsterdam", options["addresses"])
        self.assertIn("Kerkweg 45 B, 5678 CD, Utrecht", options["addresses"])

        # Verify afval types
        self.assertEqual(len(options["afval_types"]), 2)
        self.assertEqual(options["afval_types"][0]["value"], "gft")
        self.assertEqual(options["afval_types"][1]["value"], "restafval")

        # Verify year range calculated from ledigingen
        self.assertEqual(options["earliest_year"], 2023)
        self.assertEqual(options["latest_year"], 2025)

    def test_extract_filter_options_no_ledigingen(self):
        profiel = AfvalProfiel(
            klant=Klant(id="klant-1", bsn="123456789", naam="Test User"),
            containers=[],
            container_locaties=[
                AfvalContainerLocatie(
                    id="loc-1",
                    adres="Dorpsstraat 12 [1234AB AMSTERDAM]",
                    totaal_gewicht=0.0,
                )
            ],
            ledigingen=[],
        )

        options = _extract_filter_options(profiel)

        # Verify year range is None when no ledigingen
        self.assertIsNone(options["earliest_year"])
        self.assertIsNone(options["latest_year"])

    def test_extract_filter_options_same_year(self):
        profiel = AfvalProfiel(
            klant=Klant(id="klant-1", bsn="123456789", naam="Test User"),
            containers=[],
            container_locaties=[],
            ledigingen=[
                AfvalLediging(
                    id="led-1",
                    container_location="loc-1",
                    klant="klant-1",
                    container="container-1",
                    gewicht=25.0,
                    geleegd_op=datetime(2024, 1, 15, 10, 0, 0),
                ),
                AfvalLediging(
                    id="led-2",
                    container_location="loc-1",
                    klant="klant-1",
                    container="container-1",
                    gewicht=30.0,
                    geleegd_op=datetime(2024, 12, 20, 14, 30, 0),
                ),
            ],
        )

        options = _extract_filter_options(profiel)

        # Verify same year for both earliest and latest
        self.assertEqual(options["earliest_year"], 2024)
        self.assertEqual(options["latest_year"], 2024)


class ConvertPeriodToDatesTest(TestCase):
    def test_convert_period_to_dates_single_year(self):
        """Test converting a year to start and end dates"""
        startdatum, einddatum = _convert_period_to_dates("2025")

        self.assertEqual(startdatum, "2025-01-01")
        self.assertEqual(einddatum, "2025-12-31")

    def test_convert_period_to_dates_none(self):
        """Test that None period returns None for both dates"""
        startdatum, einddatum = _convert_period_to_dates(None)

        self.assertIsNone(startdatum)
        self.assertIsNone(einddatum)

    def test_convert_period_to_dates_invalid_format(self):
        """Test that invalid period format returns None"""
        startdatum, einddatum = _convert_period_to_dates("invalid")

        self.assertIsNone(startdatum)
        self.assertIsNone(einddatum)


class FormatAddressTest(TestCase):
    def test_format_address_removes_double_spaces(self):
        """Test that double spaces are normalized to single spaces"""
        address = "Dorpsstraat  12 [1234AB AMSTERDAM]"
        formatted = _format_address(address)

        # Should have single spaces only
        self.assertEqual(formatted, "Dorpsstraat 12, 1234 AB, Amsterdam")
        self.assertNotIn("  ", formatted)  # No double spaces

    def test_format_address_removes_multiple_spaces(self):
        """Test that multiple consecutive spaces are normalized"""
        address = "Kerkweg   45   B [5678CD UTRECHT]"
        formatted = _format_address(address)

        # Should have single spaces only
        self.assertEqual(formatted, "Kerkweg 45 B, 5678 CD, Utrecht")
        self.assertNotIn("  ", formatted)  # No double spaces
