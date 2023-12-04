from copy import copy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from ..service.jaaropgave import JaarOpgaveInfoResponse
from ..service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)
from ..templatetags.ssd_tags import (
    calculate_loon_zvw,
    format_currency,
    format_date_month_name,
    format_period,
    format_sign_value,
    format_string,
    get_detail_value_for_column,
)
from ..xml import get_jaaropgaven, get_uitkeringen
from .utils import get_component_value, mock_get_report_info

JAAROPGAVE_INFO_RESPONSE_NODE = (
    "//{http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400}"
    "JaarOpgaveInfoResponse"
)

UITKERING_INFO_RESPONSE_NODE = (
    "//{http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600}"
    "UitkeringsSpecificatieInfoResponse"
)

FILES_DIR = Path(__file__).parent.resolve() / "files"


class JaaropgaveDataTest(TestCase):
    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_jaaropgave_raw(self, m):
        jaaropgave_path = FILES_DIR / "jaaropgave_response.xml"
        m.return_value = mock_get_report_info(
            jaaropgave_path, JAAROPGAVE_INFO_RESPONSE_NODE, JaarOpgaveInfoResponse
        )

        jaaropgaven = get_jaaropgaven(None)

        self.assertEqual(len(jaaropgaven), 1)

        jaaropgave = jaaropgaven[0]

        with self.subTest("client"):
            client = jaaropgave["client"]
            client_address = client.adres
            self.assertEqual(client.burger_service_nr, "900038937")
            self.assertEqual(client.voornamen, "Fabiënne Maria Charlotte Elsbeth")
            self.assertEqual(client.voorletters, "F.M.C.E")
            self.assertEqual(client.voorvoegsel, "van der")
            self.assertEqual(client.achternaam, "Achterhuüskamp")
            self.assertEqual(client_address.straatnaam, "Robinson Crusoëstraat")
            self.assertEqual(client_address.huisnummer, 21)
            self.assertEqual(client_address.huisletter, "a")
            self.assertEqual(client_address.postcode, "7541AA")
            self.assertEqual(client_address.woonplaatsnaam, "Enschede")

        with self.subTest("inhoudingsplichtige"):
            inhoudingsplichtige = jaaropgave["inhoudingsplichtige"]
            self.assertEqual(inhoudingsplichtige.gemeentecode, "0153")
            self.assertEqual(inhoudingsplichtige.gemeentenaam, "Enschede")
            self.assertEqual(inhoudingsplichtige.bezoekadres, "Hengelosestraat 51")
            self.assertEqual(inhoudingsplichtige.postcode, "7514AD")
            self.assertEqual(inhoudingsplichtige.woonplaatsnaam, "Enschede")

        with self.subTest("specificatie"):
            spec = jaaropgave["specificatie"]
            self.assertEqual(spec.regeling, "Participatiewet")
            self.assertEqual(spec.dienstjaar, 2022)
            self.assertEqual(spec.fiscaalloon.waarde_bedrag, 7305)
            self.assertEqual(spec.loonheffing.waarde_bedrag, 0)
            self.assertEqual(len(spec.loonheffingskorting), 2)
            self.assertEqual(spec.loonheffingskorting[0].ingangsdatum, "20220101")
            self.assertEqual(spec.loonheffingskorting[0].cd_loonheffingskorting, "1")
            self.assertEqual(spec.loonheffingskorting[1].ingangsdatum, "20230101")
            self.assertEqual(spec.loonheffingskorting[1].cd_loonheffingskorting, "1")
            self.assertEqual(spec.aangifte_periode_van, "20220101")
            self.assertEqual(spec.aangifte_periode_tot, "20221231")
            self.assertEqual(spec.werkgeversheffing_premie_zvw.waarde_bedrag, 494)
            self.assertEqual(spec.cd_premie_volksverzekering, "250")


class UitkeringDataTest(TestCase):
    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_uitkeringen_raw(self, m):
        uitkering_path = FILES_DIR / "uitkering_response_basic.xml"
        m.return_value = mock_get_report_info(
            uitkering_path, UITKERING_INFO_RESPONSE_NODE, UitkeringInfoResponse
        )

        uitkeringen = get_uitkeringen(None)

        self.assertEqual(len(uitkeringen), 1)

        uitkering = uitkeringen[0]

        with self.subTest("uitkeringsinstantie"):
            instantie = uitkering["uitkeringsinstantie"]
            self.assertEqual(instantie.gemeentenaam, "Enschede")
            self.assertEqual(instantie.bezoekadres, "Hengelosestraat 51")
            self.assertEqual(instantie.postcode, "7514AD")
            self.assertEqual(instantie.woonplaatsnaam, "Enschede")

        with self.subTest("client"):
            client = uitkering["client"]
            client_address = client.adres
            self.assertEqual(client.burger_service_nr, "900038937")
            self.assertEqual(client.voornamen, "Fabiënne Maria Charlotte Elsbeth")
            self.assertEqual(client.voorletters, "F.M.C.E")
            self.assertEqual(client.voorvoegsel, "van der")
            self.assertEqual(client.achternaam, "Achterhuüskamp")
            self.assertEqual(client_address.straatnaam, "Robinson Crusoëstraat")
            self.assertEqual(client_address.huisnummer, 21)
            self.assertEqual(client_address.huisletter, "a")
            self.assertEqual(client_address.postcode, "7541AA")
            self.assertEqual(client_address.woonplaatsnaam, "Enschede")

        dossierhistorie = uitkering["dossierhistorie"]

        with self.subTest("specificatie"):
            self.assertEqual(dossierhistorie.dossiernummer, "61913")
            self.assertEqual(dossierhistorie.periodenummer, "202301")
            self.assertEqual(dossierhistorie.regeling, "Participatiewet")

        with self.subTest("details"):
            components = dossierhistorie.componenthistorie

            kd_norm = get_component_value(components, "KD norm tot AOW")
            gekorte_inkomsten = get_component_value(
                components, "TOTAAL GEKORTE INKOMSTEN"
            )
            reserving_vakantiegeld = get_component_value(
                components, "RESERVERING VAKANTIEGELD"
            )
            totaal_netto = get_component_value(components, "TOTAAL NETTO BIJSTAND")
            aflossing_vordering = get_component_value(components, "Aflossing vordering")
            uit_te_betalen = get_component_value(components, "UIT TE BETALEN BEDRAG")

            self.assertEqual(
                totaal_netto, kd_norm - gekorte_inkomsten - reserving_vakantiegeld
            )
            self.assertEqual(uit_te_betalen, totaal_netto - aflossing_vordering)

        with self.subTest("inkomstenkorting"):
            opgegeven_inkomsten = dossierhistorie.opgegeven_inkomsten.waarde_bedrag
            inkomsten_vrijlating = dossierhistorie.inkomsten_vrijlating.waarde_bedrag
            vakantiegeld_over_inkomsten = (
                dossierhistorie.vakantiegeld_over_inkomsten.waarde_bedrag
            )
            gekorte_inkomsten = dossierhistorie.gekorte_inkomsten.waarde_bedrag

            self.assertEqual(
                gekorte_inkomsten,
                opgegeven_inkomsten
                - inkomsten_vrijlating
                + vakantiegeld_over_inkomsten,
            )

    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_uitkeringen_extra_report(self, m):
        uitkering_path = FILES_DIR / "uitkering_response_extra_report.xml"
        m.return_value = mock_get_report_info(
            uitkering_path, UITKERING_INFO_RESPONSE_NODE, UitkeringInfoResponse
        )

        uitkeringen = get_uitkeringen(None)

        self.assertEqual(len(uitkeringen), 2)

        uitkering1 = uitkeringen[0]
        uitkering2 = uitkeringen[1]

        with self.subTest("uitkeringsinstantie"):
            self.assertEqual(
                uitkering1["uitkeringsinstantie"], uitkering2["uitkeringsinstantie"]
            )

        with self.subTest("client"):
            self.assertEqual(uitkering1["client"], uitkering2["client"])
            self.assertEqual(uitkering1["client"].adres, uitkering2["client"].adres)

        dossierhistorie1 = uitkering1["dossierhistorie"]
        dossierhistorie2 = uitkering2["dossierhistorie"]

        with self.subTest("specificatie"):
            self.assertEqual(
                dossierhistorie1.dossiernummer, dossierhistorie2.dossiernummer
            )
            self.assertEqual(
                dossierhistorie1.periodenummer, dossierhistorie2.periodenummer
            )
            self.assertEqual(dossierhistorie1.regeling, dossierhistorie2.regeling)

        with self.subTest("details"):
            components = dossierhistorie2.componenthistorie

            vakantiegeld = get_component_value(components, "Uitbetaling vakantiegeld")
            totaal_netto = get_component_value(components, "TOTAAL NETTO BIJSTAND")
            uit_te_betalen = get_component_value(components, "UIT TE BETALEN BEDRAG")

            self.assertEqual(vakantiegeld, totaal_netto)
            self.assertEqual(totaal_netto, uit_te_betalen)


class SSDTagTest(TestCase):
    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_calculate_loon_zvw(self, m):
        jaaropgave_path = FILES_DIR / "jaaropgave_response.xml"
        m.return_value = mock_get_report_info(
            jaaropgave_path, JAAROPGAVE_INFO_RESPONSE_NODE, JaarOpgaveInfoResponse
        )

        jaaropgaven = get_jaaropgaven(None)

        specificatie = jaaropgaven[0]["specificatie"]

        # create copy for testing spec without vergoeding_premie_zvw
        specificatie2 = copy(specificatie)
        specificatie2.vergoeding_premie_zvw = None

        tests = [
            (specificatie, 7305),
            (specificatie2, 7305),
            (None, ""),
        ]
        for i, (specificatie, expected) in enumerate(tests):
            with self.subTest(i=i):
                res = calculate_loon_zvw(specificatie)
                self.assertEqual(res, expected)

    def test_format_date_month_name(self):
        tests = [
            ("202305", "mei 2023"),
            ("202306", "juni 2023"),
            (None, ""),
            ("", ""),
        ]
        for i, (input, expected) in enumerate(tests):
            with self.subTest(i=i):
                res = format_date_month_name(input)
                self.assertEqual(res, expected)

    def test_format_float(self):
        tests = [
            ("642", "6,42"),
            ("60", "0,60"),
            ("", "0,00"),
        ]
        for i, (input, expected) in enumerate(tests):
            with self.subTest(i=i):
                res = format_currency(input)
                self.assertEqual(res, expected)

    def test_format_period(self):
        tests = [
            ("20230826", "26-08-2023"),
            (None, ""),
            ("", ""),
        ]
        for i, (input, expected) in enumerate(tests):
            with self.subTest(i=i):
                res = format_period(input)
                self.assertEqual(res, expected)

    def test_format_string(self):
        tests = [
            ("J.", "de", "Silentio", "J. de Silentio"),
            ("J.M.S.", "de la", "Mancha", "J.M.S. de la Mancha"),
            ("  J.M.S.", "de la  ", " Mancha ", "J.M.S. de la Mancha"),
            ("J.", "", "Silentio", "J. Silentio"),
            ("J.", "   ", "Silentio", "J. Silentio"),
            ("J.", "Silentio", 1, "J. Silentio 1"),
        ]
        for i, (voorletters, voorvoegsel, achternaam, expected) in enumerate(tests):
            with self.subTest(i=i):
                res = format_string(voorletters, voorvoegsel, achternaam)
                self.assertEqual(res, expected)

    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_format_sign_value(self, m):
        jaaropgave_path = FILES_DIR / "jaaropgave_response.xml"
        m.return_value = mock_get_report_info(
            jaaropgave_path, JAAROPGAVE_INFO_RESPONSE_NODE, JaarOpgaveInfoResponse
        )

        jaaropgaven = get_jaaropgaven(None)

        self.assertEqual(len(jaaropgaven), 1)

        spec = jaaropgaven[0]["specificatie"]

        fiscaalloon = spec.fiscaalloon
        ontvangsten_premieloon = spec.ontvangsten_premieloon

        tests = [
            (fiscaalloon, "7305"),
            (ontvangsten_premieloon, "-400"),
            (None, ""),
        ]
        for i, (detail, expected) in enumerate(tests):
            with self.subTest(i=i):
                res = format_sign_value(detail)
                self.assertEqual(res, expected)

    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_get_detail_value_for_column(self, m):
        uitkering_path = FILES_DIR / "uitkering_response_basic.xml"
        m.return_value = mock_get_report_info(
            uitkering_path, UITKERING_INFO_RESPONSE_NODE, UitkeringInfoResponse
        )

        uitkering = get_uitkeringen(None)[0]
        componenthistorie = uitkering["dossierhistorie"].componenthistorie

        kd_norm = next(
            item for item in componenthistorie if item.omschrijving == "KD norm tot AOW"
        )
        gekorte_inkomsten = next(
            item
            for item in componenthistorie
            if item.omschrijving == "TOTAAL GEKORTE INKOMSTEN"
        )

        tests = [
            (kd_norm, "plus", "740,17"),
            (kd_norm, "minus", ""),
            (kd_norm, "basic", ""),
            (gekorte_inkomsten, "plus", ""),
            (gekorte_inkomsten, "minus", "36,44"),
            (gekorte_inkomsten, "basic", ""),
        ]

        for i, (detail, column_index, expected) in enumerate(tests):
            with self.subTest(i=i):
                res = get_detail_value_for_column(detail, column_index)
                self.assertEqual(res, expected)
