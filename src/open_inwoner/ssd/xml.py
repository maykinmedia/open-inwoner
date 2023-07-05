import datetime
from xml.parsers.expat import ExpatError

from django.utils.translation import gettext_lazy as _

import xmltodict
from glom import glom


#
# utils
#
def convert_to_float(base_path: str, target: str) -> float:
    res = glom(base_path, target, default=0)

    if res == 0:
        return res

    return float(res) / 100


def format_date(date_str):
    return datetime.datetime.strptime(date_str, "%Y%m%d").strftime("%d-%m-%Y")


def get_sign(base_path: str, target: str) -> str:
    return "-" if glom(base_path, target) == "-" else ""


def xml_to_dict(xml_data):
    try:
        return xmltodict.parse(xml_data)
    except ExpatError:
        return {}


#
# Maandspecificatie
#
def get_uitkering_dict(xml_data):
    xml_data_dict = xml_to_dict(xml_data)

    if not xml_data_dict:
        return {}

    BASE = "SOAP-ENV:Envelope.SOAP-ENV:Body.gwsd:UitkeringsSpecificatieInfoResponse"

    uitkering_specificatie = glom(
        xml_data_dict, BASE + ".UitkeringsSpecificatieClient.Uitkeringsspecificatie"
    )

    #
    # Uitkeringsinstatie
    #
    uitkeringsinstatie_spec = glom(uitkering_specificatie, "Uitkeringsinstantie")
    uitkeringsinstantie = {
        "gemeentenaam": glom(uitkeringsinstatie_spec, "Gemeentenaam"),
        "bezoekadres": glom(uitkeringsinstatie_spec, "Bezoekadres"),
        "postcode": glom(uitkeringsinstatie_spec, "Postcode"),
        "woonplaatsnaam": glom(uitkeringsinstatie_spec, "Woonplaatsnaam"),
    }

    #
    # Client
    #
    client_spec = glom(xml_data_dict, BASE + ".UitkeringsSpecificatieClient.Client")
    client_address_spec = glom(client_spec, "Adres")

    client = {
        "burgerservicenr": glom(client_spec, "BurgerServiceNr"),
        "voornamen": glom(client_spec, "Voornamen"),
        "voorvoegsel": glom(client_spec, "Voorvoegsel"),
        "achternaam": glom(client_spec, "Achternaam"),
        "straatnaam": glom(client_address_spec, "Straatnaam"),
        "client_postcode": glom(client_address_spec, "Postcode"),
        "client_woonplaatsnaam": glom(client_address_spec, "Woonplaatsnaam"),
    }

    # dossier needed for the rest of the report
    dossierhistorie_spec = glom(uitkering_specificatie, "Dossierhistorie")
    dossier_dict = dossierhistorie_spec[0]

    #
    # Uitkeringsspeciﬁcatie
    #
    uitkeringsspeciﬁcatie = {
        "dossiernummer": glom(dossier_dict, "Dossiernummer"),
        "periode": glom(dossier_dict, "Periodenummer"),
        "regeling": glom(dossier_dict, "Regeling"),
    }

    #
    # Details
    #
    details = {}
    details_list = glom(dossier_dict, "Componenthistorie")

    for detail_row in details_list:
        details[detail_row["Omschrijving"]] = {
            "sign": glom(detail_row, "Bedrag.CdPositiefNegatief"),
            "bedrag": convert_to_float(detail_row, "Bedrag.WaardeBedrag"),
            "column": glom(detail_row, "IndicatieKolom"),
        }

    #
    # Speciﬁcatie inkomstenkorting
    #
    inkomstenkorting = {
        "OpgegevenInkomsten": {
            "sign": get_sign(dossier_dict, "OpgegevenInkomsten.CdPositiefNegatief"),
            "bedrag": convert_to_float(dossier_dict, "OpgegevenInkomsten.WaardeBedrag"),
        },
        "InkomstenVrijlating": {
            "sign": get_sign(dossier_dict, "InkomstenVrijlating.CdPositiefNegatief"),
            "bedrag": convert_to_float(
                dossier_dict, "InkomstenVrijlating.WaardeBedrag"
            ),
        },
        "InkomstenNaVrijlating": {
            "sign": get_sign(dossier_dict, "InkomstenNaVrijlating.CdPositiefNegatief"),
            "bedrag": convert_to_float(
                dossier_dict, "InkomstenNaVrijlating.WaardeBedrag"
            ),
        },
        "VakantiegeldOverInkomsten": {
            "sign": get_sign(
                dossier_dict, "VakantiegeldOverInkomsten.CdPositiefNegatief"
            ),
            "bedrag": convert_to_float(
                dossier_dict, "VakantiegeldOverInkomsten.WaardeBedrag"
            ),
        },
        "GekorteInkomsten": {
            "sign": get_sign(dossier_dict, "GekorteInkomsten.CdPositiefNegatief"),
            "bedrag": convert_to_float(dossier_dict, "GekorteInkomsten.WaardeBedrag"),
        },
    }

    return {
        "uitkeringsinstantie": uitkeringsinstantie,
        "client": client,
        "uitkeringsspecificatie": uitkeringsspeciﬁcatie,
        "details": details,
        "inkomstenkorting": inkomstenkorting,
    }


#
# jaaropgave
#
def get_jaaropgave_dict(xml_data):
    xml_data_dict = xml_to_dict(xml_data)

    if not xml_data_dict:
        return {}

    BASE = "SOAP-ENV:Envelope.SOAP-ENV:Body.gwsd:JaarOpgaveInfoResponse"

    #
    # Client
    #
    client_spec = glom(xml_data_dict, BASE + ".JaarOpgaveClient.Client")
    client_address_spec = glom(xml_data_dict, BASE + ".JaarOpgaveClient.Client.Adres")
    client = {
        "bsn": glom(client_spec, "BurgerServiceNr"),
        "voornamen": glom(client_spec, "Voornamen"),
        "voorvoegsel": glom(client_spec, "Voorvoegsel"),
        "achternaam": glom(client_spec, "Achternaam"),
        "straatnaam": glom(client_address_spec, "Straatnaam"),
        "huisnummer": glom(client_address_spec, "Huisnummer"),
        "huisletter": glom(client_address_spec, "Huisletter"),
        "postcode": glom(client_address_spec, "Postcode"),
        "woonplaatsnaam": glom(client_address_spec, "Woonplaatsnaam"),
        "gemeentenaam": glom(client_address_spec, "Gemeentenaam"),
    }

    #
    # JaarOpgave
    #
    jaaropgave_spec = glom(xml_data_dict, BASE + ".JaarOpgaveClient.JaarOpgave")

    # Inhoudingsplichtige
    inhoudingsplichtige_spec = glom(jaaropgave_spec, "Inhoudingsplichtige")
    inhoudingsplichtige = {
        "gemeentenaam": glom(inhoudingsplichtige_spec, "Gemeentenaam"),
        "bezoekadres": glom(inhoudingsplichtige_spec, "Bezoekadres"),
        "postcode": glom(inhoudingsplichtige_spec, "Postcode"),
        "woonplaatsnaam": glom(inhoudingsplichtige_spec, "Woonplaatsnaam"),
    }

    # SpecificatieJaarOpgave
    specificatiejaaropgave_spec = glom(jaaropgave_spec, "SpecificatieJaarOpgave")
    jaaropgave = {
        "regeling": glom(specificatiejaaropgave_spec, "Regeling"),
        "fiscaalloon": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "Fiscaalloon.CdPositiefNegatief"
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec, "Fiscaalloon.WaardeBedrag"
            ),
        },
        "loonheffing": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "Loonheffing.CdPositiefNegatief"
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec, "Loonheffing.WaardeBedrag"
            ),
        },
        "premie_volksverzekering": glom(
            specificatiejaaropgave_spec, "CdPremieVolksverzekering"
        ),
        "indicatie_zvw": glom(specificatiejaaropgave_spec, "IndicatieZVW"),
        "ingehouden_premie_zvw": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "IngehoudenPremieZVW.CdPositiefNegatief"
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec, "IngehoudenPremieZVW.WaardeBedrag"
            ),
        },
        "vergoeding_premie_zvw": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "VergoedingPremieZVW.CdPositiefNegatief"
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec, "VergoedingPremieZVW.WaardeBedrag"
            ),
        },
        "ontvangsten_fiscaalloon": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "OntvangstenFiscaalloon.CdPositiefNegatief"
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec, "OntvangstenFiscaalloon.WaardeBedrag"
            ),
        },
        "ontvangsten_ingehouden_premie_zvw": {
            "sign": get_sign(
                specificatiejaaropgave_spec,
                "OntvangstenIngehoudenPremieZVW.CdPositiefNegatief",
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec,
                "OntvangstenIngehoudenPremieZVW.WaardeBedrag",
            ),
        },
        "ontvangsten_vergoeding_premie_zvw": {
            "sign": get_sign(
                specificatiejaaropgave_spec,
                "OntvangstenVergoedingPremieZVW.CdPositiefNegatief",
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec,
                "OntvangstenVergoedingPremieZVW.WaardeBedrag",
            ),
        },
        "ontvangsten_premieloon": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "OntvangstenPremieloon.CdPositiefNegatief"
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec, "OntvangstenPremieloon.WaardeBedrag"
            ),
        },
        "werkgevers_heffing_premie_zvw": {
            "sign": get_sign(
                specificatiejaaropgave_spec,
                "WerkgeversheffingPremieZVW.CdPositiefNegatief",
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec, "WerkgeversheffingPremieZVW.WaardeBedrag"
            ),
        },
        "ontvangsten_werkgevers_heffing_premie_zvw": {
            "sign": get_sign(
                specificatiejaaropgave_spec,
                "OntvangstenWerkgeversheffingPremieZVW.CdPositiefNegatief",
            ),
            "bedrag": convert_to_float(
                specificatiejaaropgave_spec,
                "OntvangstenWerkgeversheffingPremieZVW.WaardeBedrag",
            ),
        },
        "loon_heffings_korting": {
            "ingangsdatum": format_date(
                glom(specificatiejaaropgave_spec, "Loonheffingskorting.Ingangsdatum")
            ),
            "cdloonheffingskorting": glom(
                specificatiejaaropgave_spec, "Loonheffingskorting.CdLoonheffingskorting"
            ),
        },
        "belaste_alimentatie": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "BelasteAlimentatie.CdPositiefNegatief"
            ),
            "bedrag": (
                float(
                    glom(
                        specificatiejaaropgave_spec,
                        "BelasteAlimentatie.WaardeBedrag",
                        default=0,
                    )
                )
                / 100
                if glom(
                    specificatiejaaropgave_spec,
                    "BelasteAlimentatie.WaardeBedrag",
                    default=0,
                )
                else 0
            ),
        },
    }

    # In case we have multiple rows
    if glom(specificatiejaaropgave_spec, "Loonheffingskorting[2]", default=""):
        loon_heffings_korting_2 = {
            "Loonheffingskorting[2]": {
                "ingangsdatum_2": format_date(
                    glom(
                        specificatiejaaropgave_spec,
                        "Loonheffingskorting[2].Ingangsdatum",
                        default="",
                    )
                ),
                "cdloonheffingskorting_2": glom(
                    specificatiejaaropgave_spec,
                    "Loonheffingskorting[2].CdLoonheffingskorting",
                    default="",
                ),
            },
        }
        jaaropgave.update(loon_heffings_korting_2)

    if glom(specificatiejaaropgave_spec, "Loonheffingskorting[3]", default=""):
        loon_heffings_korting_3 = {
            "Loonheffingskorting[3]": {
                "ingangsdatum_3": format_date(
                    glom(
                        specificatiejaaropgave_spec,
                        "Loonheffingskorting[3].Ingangsdatum",
                        default="",
                    )
                ),
                "cdloonheffingskorting_3": glom(
                    specificatiejaaropgave_spec,
                    "Loonheffingskorting[3].CdLoonheffingskorting",
                    default="",
                ),
            },
        }
        jaaropgave.update(loon_heffings_korting_3)

    return {
        "client": client,
        "inhoudingsplichtige": inhoudingsplichtige,
        "jaaropgave": jaaropgave,
    }
