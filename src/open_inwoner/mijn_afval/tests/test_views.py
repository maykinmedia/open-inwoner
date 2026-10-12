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
    _filter_containers_by_afval_type,
    _format_address,
    _format_afval_profiel,
)


def _make_container(id: str, afval_type: str) -> AfvalContainer:
    return AfvalContainer(
        id=id,
        public_container_id=f"PUB-{id}",
        afval_type=afval_type,
        is_verzamelcontainer=False,
        heeft_sleutel=False,
        totaal_gewicht=10.0,
        totaal_kosten=1.00,
    )


def _make_lediging(id: str, container: str) -> AfvalLediging:
    return AfvalLediging(
        id=id,
        container_location="loc-1",
        klant="klant-1",
        container=container,
        gewicht=10.0,
        geleegd_op=datetime(2024, 1, 15, 10, 0, 0),
        kosten=1.00,
    )


def _make_profiel(containers: list[AfvalContainer]) -> AfvalProfiel:
    return AfvalProfiel(
        klant=Klant(id="klant-1", bsn="123456789", naam="Test User", totaal_kosten=0),
        containers=containers,
        container_locaties=[
            AfvalContainerLocatie(
                id="loc-1",
                adres="Dorpsstraat 12 [1234AB AMSTERDAM]",
                totaal_gewicht=10.0,
                totaal_kosten=1.00,
            )
        ],
        ledigingen=[
            _make_lediging(f"led-{container.id}", container.id)
            for container in containers
        ],
    )


class ExtractFilterOptionsTest(TestCase):
    def test_extract_filter_options_with_data(self):
        profiel = AfvalProfiel(
            klant=Klant(
                id="klant-1", bsn="123456789", naam="Test User", totaal_kosten=0.00
            ),
            containers=[
                AfvalContainer(
                    id="container-1",
                    public_container_id="PUB-001",
                    afval_type="GFT",
                    is_verzamelcontainer=False,
                    heeft_sleutel=True,
                    totaal_gewicht=100.0,
                    totaal_kosten=11.50,
                )
            ],
            container_locaties=[
                AfvalContainerLocatie(
                    id="loc-1",
                    adres="Dorpsstraat 12 [1234AB AMSTERDAM]",
                    totaal_gewicht=100.0,
                    totaal_kosten=5.00,
                ),
                AfvalContainerLocatie(
                    id="loc-2",
                    adres="Kerkweg 45 B [5678CD UTRECHT]",
                    totaal_gewicht=50.0,
                    totaal_kosten=6.50,
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
                    kosten=5.00,
                ),
                AfvalLediging(
                    id="led-2",
                    container_location="loc-2",
                    klant="klant-1",
                    container="container-1",
                    gewicht=30.0,
                    geleegd_op=datetime(2025, 3, 20, 14, 30, 0),
                    kosten=6.50,
                ),
            ],
        )

        options = _extract_filter_options(profiel)

        # Verify addresses are formatted and sorted
        self.assertEqual(len(options["addresses"]), 2)
        self.assertIn("Dorpsstraat 12, 1234 AB, Amsterdam", options["addresses"])
        self.assertIn("Kerkweg 45 B, 5678 CD, Utrecht", options["addresses"])

        # Verify afval types are taken from the containers
        self.assertEqual(options["afval_types"], [{"value": "GFT", "label": "GFT"}])

        # Verify year range calculated from ledigingen
        self.assertListEqual(options["periode"], [2025, 2023])

    def test_extract_filter_options_no_ledigingen(self):
        profiel = AfvalProfiel(
            klant=Klant(
                id="klant-1", bsn="123456789", naam="Test User", totaal_kosten=0.00
            ),
            containers=[],
            container_locaties=[
                AfvalContainerLocatie(
                    id="loc-1",
                    adres="Dorpsstraat 12 [1234AB AMSTERDAM]",
                    totaal_gewicht=0.0,
                    totaal_kosten=0.00,
                )
            ],
            ledigingen=[],
        )

        options = _extract_filter_options(profiel)

        # Verify emptry period options when no ledigingen
        self.assertListEqual(options["periode"], [])

    def test_extract_filter_options_same_year(self):
        profiel = AfvalProfiel(
            klant=Klant(
                id="klant-1", bsn="123456789", naam="Test User", totaal_kosten=0.00
            ),
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
                    kosten=5.00,
                ),
                AfvalLediging(
                    id="led-2",
                    container_location="loc-1",
                    klant="klant-1",
                    container="container-1",
                    gewicht=30.0,
                    geleegd_op=datetime(2024, 12, 20, 14, 30, 0),
                    kosten=6.50,
                ),
            ],
        )

        options = _extract_filter_options(profiel)

        # Verify single period options
        self.assertListEqual(options["periode"], [2024])

    def test_extract_filter_options_afval_types_unique_sorted_non_empty(self):
        profiel = _make_profiel(
            [
                _make_container("c1", "Restafval"),
                _make_container("c2", "GFT"),
                _make_container("c3", "Restafval"),
                _make_container("c4", ""),
            ]
        )

        options = _extract_filter_options(profiel)

        self.assertEqual(
            options["afval_types"],
            [
                {"value": "GFT", "label": "GFT"},
                {"value": "Restafval", "label": "Restafval"},
            ],
        )


class FilterContainersByAfvalTypeTest(TestCase):
    def test_keeps_only_containers_of_given_types(self):
        profiel = _make_profiel(
            [
                _make_container("c1", "GFT"),
                _make_container("c2", "Restafval"),
                _make_container("c3", "Oud papier en karton"),
            ]
        )

        filtered = _filter_containers_by_afval_type(profiel, ["GFT", "Restafval"])

        self.assertEqual([c.id for c in filtered.containers], ["c1", "c2"])
        self.assertEqual(len(profiel.containers), 3)

    def test_formatted_profiel_excludes_filtered_containers(self):
        profiel = _make_profiel(
            [
                _make_container("c1", "GFT"),
                _make_container("c2", "Oud papier en karton"),
            ]
        )

        result = _format_afval_profiel(
            _filter_containers_by_afval_type(profiel, ["GFT", "Restafval"])
        )

        self.assertEqual([c["identifier"] for c in result[0]["containers"]], ["c1"])


class FormatAfvalProfielTest(TestCase):
    def test_container_caption_uses_afval_type_from_api(self):
        profiel = _make_profiel([_make_container("c1", "Oud papier en karton")])

        result = _format_afval_profiel(profiel)

        container = result[0]["containers"][0]
        self.assertEqual(container["type"], "Oud papier en karton")
        self.assertEqual(
            container["table_data"]["caption"],
            "Container: Oud papier en karton - PUB-c1",
        )

    def test_container_caption_without_afval_type(self):
        profiel = _make_profiel([_make_container("c1", "")])

        result = _format_afval_profiel(profiel)

        self.assertEqual(
            result[0]["containers"][0]["table_data"]["caption"], "Container: PUB-c1"
        )


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
