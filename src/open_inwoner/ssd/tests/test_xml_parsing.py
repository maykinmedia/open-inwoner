from pathlib import Path
from unittest import TestCase

from ..xml import get_jaaropgave_dict, get_uitkering_dict

FILES_DIR = Path(__file__).parent.resolve() / "files"


class XMLParsingTests(TestCase):
    def test_uitkering_response_parsing(self):
        uitkering_file = str(FILES_DIR / "uitkering_response.xml")

        with open(uitkering_file, "r") as file:
            maandspecificatie = file.read()

        data = get_uitkering_dict(maandspecificatie)

        # uitkeringinstantie
        self.assertEqual(data["uitkeringsinstantie"]["gemeente"]["key"], "Gemeente")
        self.assertEqual(data["uitkeringsinstantie"]["gemeente"]["value"], "Enschede")
        self.assertEqual(
            data["uitkeringsinstantie"]["bezoekadres"]["key"], "Bezoekadres"
        )
        self.assertEqual(
            data["uitkeringsinstantie"]["bezoekadres"]["value"], "Fantasiestraat 42"
        )
        self.assertEqual(data["uitkeringsinstantie"]["postcode"]["key"], "Postcode")
        self.assertEqual(data["uitkeringsinstantie"]["postcode"]["value"], "1234AD")
        self.assertEqual(data["uitkeringsinstantie"]["woonplaatsnaam"]["key"], "Plaats")
        self.assertEqual(
            data["uitkeringsinstantie"]["woonplaatsnaam"]["value"], "Enschede"
        )

        # client data
        self.assertEqual(data["client"]["bsn"]["key"], "Burgerservicenummer (BSN)")
        self.assertEqual(data["client"]["bsn"]["value"], "123456789")
        self.assertEqual(data["client"]["naam"]["key"], "Naam")
        self.assertEqual(data["client"]["naam"]["value"], "F. M. C. van den Berg")
        self.assertEqual(data["client"]["adres"]["key"], "Adres")
        self.assertEqual(data["client"]["adres"]["value"], "Dummystraat 42 a")
        self.assertEqual(data["client"]["postcode"]["key"], "Postcode")
        self.assertEqual(data["client"]["postcode"]["value"], "12345")
        self.assertEqual(data["client"]["woonplaats"]["key"], "Woonplaats")
        self.assertEqual(data["client"]["woonplaats"]["value"], "Alphaville")

        # uitkeringsspecificatie
        self.assertEqual(
            data["uitkeringsspecificatie"]["dossiernummer"]["key"], "Dossiernummer"
        )
        self.assertEqual(
            data["uitkeringsspecificatie"]["dossiernummer"]["value"], "61913"
        )
        self.assertEqual(data["uitkeringsspecificatie"]["periode"]["key"], "Periode")
        self.assertEqual(data["uitkeringsspecificatie"]["periode"]["value"], "May 1985")
        self.assertEqual(data["uitkeringsspecificatie"]["regeling"]["key"], "Regeling")
        self.assertEqual(
            data["uitkeringsspecificatie"]["regeling"]["value"], "Participatiewet"
        )

        # details
        self.assertEqual(
            data["details"]["5-aflossing-vordering"]["key"], "5% Aflossing vordering"
        )
        self.assertEqual(data["details"]["5-aflossing-vordering"]["value"], "37,01")
        self.assertEqual(data["details"]["5-aflossing-vordering"]["column"], "minus")

        self.assertEqual(
            data["details"]["ink-pensioenvut-65-geen-vt"]["key"],
            "Ink pensioen/VUT (65-)geen vt",
        )
        self.assertEqual(
            data["details"]["ink-pensioenvut-65-geen-vt"]["value"], "36,44"
        )
        self.assertEqual(
            data["details"]["ink-pensioenvut-65-geen-vt"]["column"], "base"
        )

        self.assertEqual(data["details"]["kd-norm-tot-aow"]["key"], "KD norm tot AOW")
        self.assertEqual(data["details"]["kd-norm-tot-aow"]["value"], "740,17")
        self.assertEqual(data["details"]["kd-norm-tot-aow"]["column"], "plus")

        self.assertEqual(
            data["details"]["reservering-vakantiegeld"]["key"],
            "RESERVERING VAKANTIEGELD",
        )
        self.assertEqual(data["details"]["reservering-vakantiegeld"]["value"], "37,01")

        self.assertEqual(
            data["details"]["totaal-gekorte-inkomsten"]["key"],
            "TOTAAL GEKORTE INKOMSTEN",
        )
        self.assertEqual(data["details"]["totaal-gekorte-inkomsten"]["value"], "36,44")
        self.assertEqual(data["details"]["totaal-gekorte-inkomsten"]["column"], "minus")

        self.assertEqual(
            data["details"]["totaal-netto-bijstand"]["key"], "TOTAAL NETTO BIJSTAND"
        )
        self.assertEqual(data["details"]["totaal-netto-bijstand"]["value"], "666,72")
        self.assertEqual(data["details"]["totaal-netto-bijstand"]["column"], "plus")

        self.assertEqual(
            data["details"]["uit-te-betalen-bedrag"]["key"], "UIT TE BETALEN BEDRAG"
        )
        self.assertEqual(data["details"]["uit-te-betalen-bedrag"]["value"], "629,71")
        self.assertEqual(data["details"]["uit-te-betalen-bedrag"]["column"], "plus")

        # inkomstenkorting
        self.assertEqual(
            data["inkomstenkorting"]["opgegeven_inkomsten"]["key"],
            "Opgegeven inkomsten",
        )
        self.assertEqual(
            data["inkomstenkorting"]["opgegeven_inkomsten"]["value"], "36,44"
        )
        self.assertEqual(
            data["inkomstenkorting"]["inkomsten_vrijlating"]["key"],
            "Inkomsten vrijlating",
        )
        self.assertEqual(
            data["inkomstenkorting"]["inkomsten_vrijlating"]["value"], "0,00"
        )
        self.assertEqual(
            data["inkomstenkorting"]["inkomsten_na_vrijlating"]["key"],
            "Inkomsten na vrijlating",
        )
        self.assertEqual(
            data["inkomstenkorting"]["inkomsten_na_vrijlating"]["value"], "36,44"
        )
        self.assertEqual(
            data["inkomstenkorting"]["vakantiegeld_over_inkomsten"]["key"],
            "Vakantiegeld inkomsten",
        )
        self.assertEqual(
            data["inkomstenkorting"]["vakantiegeld_over_inkomsten"]["value"], "0,00"
        )
        self.assertEqual(
            data["inkomstenkorting"]["gekorte_inkomsten"]["key"],
            "Totaal gekorte inkomsten",
        )
        self.assertEqual(
            data["inkomstenkorting"]["gekorte_inkomsten"]["value"], "36,44"
        )

    def test_jaaropgave_response_parsing(self):
        jaaropgave_file = str(FILES_DIR / "jaaropgave_response.xml")

        with open(jaaropgave_file, "r") as file:
            maandspecificatie = file.read()

        data = get_jaaropgave_dict(maandspecificatie)

        # client
        self.assertEqual(data["client"]["bsn_label"], "BSN")
        self.assertEqual(data["client"]["bsn"], "123456789")
        self.assertEqual(data["client"]["naam"], "F. M. C. van den Berg")
        self.assertEqual(data["client"]["adres"], "Dummystraat 42 a")
        self.assertEqual(data["client"]["woonplaatsnaam"], "Enschede")

        # inhoudingsplichtige
        self.assertEqual(data["inhoudingsplichtige"]["key"], "Inhoudingsplichtige")
        self.assertEqual(
            data["inhoudingsplichtige"]["bezoekadres"], "Fantasiestraat 42"
        )
        self.assertEqual(data["inhoudingsplichtige"]["gemeentenaam"], "Enschede")
        self.assertEqual(data["inhoudingsplichtige"]["postcode"], "1234AD")
        self.assertEqual(data["inhoudingsplichtige"]["woonplaatsnaam"], "Enschede")

        # jaaropgave
        self.assertEqual(
            data["jaaropgave"]["arbeidskorting"]["key"], "Verrekende arbeidskorting"
        )
        self.assertEqual(data["jaaropgave"]["arbeidskorting"]["value"], "MYSTERY")
        self.assertEqual(
            data["jaaropgave"]["code_loonbelastingtabel"]["key"],
            "Code loonbelastingtabel",
        )
        self.assertEqual(data["jaaropgave"]["code_loonbelastingtabel"]["value"], "250")
        self.assertEqual(data["jaaropgave"]["dienstjaar"], "1985")
        self.assertEqual(
            data["jaaropgave"]["fiscaalloon"]["key"],
            "Loon loonbelasting / volksverzekeringen",
        )
        self.assertEqual(data["jaaropgave"]["fiscaalloon"]["value"], "7305")
        self.assertEqual(
            data["jaaropgave"]["ingehouden_bijdrage"]["key"],
            "Ingehouden bijdrage Zorgverzekeringswet",
        )
        self.assertEqual(data["jaaropgave"]["ingehouden_bijdrage"]["value"], "0")
        self.assertEqual(
            data["jaaropgave"]["loon_heffings_korting"]["key"],
            "Loonheffingskorting Met ingang van",
        )
        self.assertEqual(
            data["jaaropgave"]["loon_heffings_korting"]["dates"][0]["ingangsdatum"],
            "19840101",
        )
        self.assertEqual(
            data["jaaropgave"]["loon_heffings_korting"]["dates"][1]["ingangsdatum"],
            "19850101",
        )
        self.assertEqual(
            data["jaaropgave"]["loon_zorgverzekeringswet"]["key"],
            "Loon Zorgverzekeringswet",
        )
        self.assertEqual(
            data["jaaropgave"]["loon_zorgverzekeringswet"]["value"], "7305"
        )
        self.assertEqual(
            data["jaaropgave"]["loonheffing"]["key"],
            "Ingehouden Loonbelasting / Premie volksverzekeringen (loonheffing)",
        )
        self.assertEqual(data["jaaropgave"]["loonheffing"]["value"], "0")
        self.assertEqual(data["jaaropgave"]["periode"]["key"], "Tijdvak")
        self.assertEqual(data["jaaropgave"]["periode"]["van"], "01-01-1985")
        self.assertEqual(data["jaaropgave"]["periode"]["tot"], "31-12-1985")
        self.assertEqual(data["jaaropgave"]["vergoeding_premie_zvw"]["value"], "0")
        self.assertEqual(
            data["jaaropgave"]["werkgevers_heffing_premie"]["key"],
            "Werkgeversheffing Zorgverzekeringswet",
        )
        self.assertEqual(
            data["jaaropgave"]["werkgevers_heffing_premie"]["value"], "494"
        )
