from datetime import datetime
from typing import Optional
from xml.parsers.expat import ExpatError

from django.template.defaultfilters import date as django_date
from django.utils.text import slugify

import xmltodict
from glom import glom
from glom.core import PathAccessError


#
# utility functions
#
def calculate_loon_zvw(fiscalloon: str, vergoeding_premie_zvw: str) -> str:
    return str(int(fiscalloon) - int(vergoeding_premie_zvw))


def format_float_repr(value: str) -> str:
    return "{:.2f}".format(float(value) / 100).replace(".", ",")


def format_address(street_name: str, house_nr: str, house_letter: str) -> str:
    elements = (street_name, house_nr, house_letter)
    return " ".join((item.strip() for item in elements if item != ""))


def format_date(date_str: str) -> str:
    if not date_str:
        return date_str
    return datetime.strptime(date_str, "%Y%m%d").strftime("%d-%m-%Y")


def format_date_month_name(date_str) -> str:
    """Transform '204805' into 'Mei 2048'"""

    if not date_str:
        return date_str

    patched = date_str + "01"
    dt = datetime.strptime(patched, "%Y%m%d")

    formatted_date = django_date(dt, "F Y").capitalize()

    return formatted_date


def format_name(first_name: str, voorvoegsel: str, last_name: str):
    first_names = first_name.strip().split(" ")
    first_name_initials = (name[0] + "." for name in first_names)
    first_name_formatted = " ".join(first_name_initials)

    elements = (first_name_formatted, voorvoegsel, last_name)

    return " ".join((item.strip() for item in elements if item))


def get_sign(target, spec) -> str:
    return "-" if glom(target, spec, default="") == "-" else ""


def get_column(col_index: str) -> str:
    """Remap magic numbers to meaningful names"""

    if col_index == "1":
        return "plus"
    if col_index == "2":
        return "minus"
    return "base"


def xml_to_dict(xml_data):
    try:
        return xmltodict.parse(xml_data)
    except ExpatError:
        return {}


#
# Maandspecificatie
#
def get_uitkering_dict(xml_data) -> Optional[dict]:
    xml_data_dict = xml_to_dict(xml_data)

    if not xml_data_dict:
        return None

    BASE = "SOAP-ENV:Envelope.SOAP-ENV:Body.gwsd:UitkeringsSpecificatieInfoResponse"

    try:
        uitkering_specificatie = glom(
            xml_data_dict, BASE + ".UitkeringsSpecificatieClient.Uitkeringsspecificatie"
        )
    except PathAccessError:
        return None

    #
    # Uitkeringsinstatie
    #
    uitkeringsinstatie_spec = glom(uitkering_specificatie, "Uitkeringsinstantie")
    uitkeringsinstantie = {
        "gemeente": {
            "key": "Gemeente",
            "value": glom(uitkeringsinstatie_spec, "Gemeentenaam"),
        },
        "bezoekadres": {
            "key": "Bezoekadres",
            "value": glom(uitkeringsinstatie_spec, "Bezoekadres"),
        },
        "postcode": {
            "key": "Postcode",
            "value": glom(uitkeringsinstatie_spec, "Postcode"),
        },
        "woonplaatsnaam": {
            "key": "Plaats",
            "value": glom(uitkeringsinstatie_spec, "Woonplaatsnaam"),
        },
    }

    #
    # Client
    #
    client_spec = glom(xml_data_dict, BASE + ".UitkeringsSpecificatieClient.Client")
    client_address_spec = glom(client_spec, "Adres")

    client = {
        "bsn": {
            "key": "Burgerservicenummer (BSN)",
            "value": glom(client_spec, "BurgerServiceNr"),
        },
        "naam": {
            "key": "Naam",
            "value": format_name(
                glom(client_spec, "Voornamen", default=""),
                glom(client_spec, "Voorvoegsel", default=""),
                glom(client_spec, "Achternaam", default=""),
            ),
        },
        "adres": {
            "key": "Adres",
            "value": format_address(
                glom(client_address_spec, "Straatnaam", default=""),
                glom(client_address_spec, "Huisnummer", default=""),
                glom(client_address_spec, "Huisletter", default=""),
            ),
        },
        "postcode": {
            "key": "Postcode",
            "value": glom(client_address_spec, "Postcode", default=""),
        },
        "woonplaats": {
            "key": "Woonplaats",
            "value": glom(client_address_spec, "Woonplaatsnaam", default=""),
        },
    }

    # dossier needed for the rest of the report
    dossierhistorie_spec = glom(uitkering_specificatie, "Dossierhistorie", default="")

    # normalize
    if not isinstance(dossierhistorie_spec, list):
        dossierhistorie_spec = [dossierhistorie_spec]

    dossier_dict = dossierhistorie_spec[0]

    #
    # Uitkeringsspeciﬁcatie
    #
    uitkeringsspecificatie = {
        "dossiernummer": {
            "key": "Dossiernummer",
            "value": glom(dossier_dict, "Dossiernummer", default=""),
        },
        "periode": {
            "key": "Periode",
            "value": format_date_month_name(
                glom(dossier_dict, "Periodenummer", default="")
            ),
        },
        "regeling": {
            "key": "Regeling",
            "value": glom(dossier_dict, "Regeling", default=""),
        },
    }

    #
    # Details
    #
    details = {}
    details_list = glom(dossier_dict, "Componenthistorie", default="")

    for detail_row in details_list:
        # dict keys are slugified to facilitate access in tests
        internal_key = slugify(detail_row["Omschrijving"]).replace("-", "_")
        details[internal_key] = {
            "key": detail_row["Omschrijving"],
            "sign": glom(detail_row, "Bedrag.CdPositiefNegatief", default=""),
            "value": format_float_repr(
                glom(detail_row, "Bedrag.WaardeBedrag", default="")
            ),
            "column": get_column(glom(detail_row, "IndicatieKolom", default="")),
        }

    #
    # Specificatie inkomstenkorting
    #
    inkomstenkorting = {
        "opgegeven_inkomsten": {
            "key": "Opgegeven inkomsten",
            "sign": get_sign(dossier_dict, "OpgegevenInkomsten.CdPositiefNegatief"),
            "value": format_float_repr(
                glom(dossier_dict, "OpgegevenInkomsten.WaardeBedrag", default="")
            ),
        },
        "inkomsten_vrijlating": {
            "key": "Inkomsten vrijlating",
            "sign": glom(
                dossier_dict, "InkomstenVrijlating.CdPositiefNegatief", default=""
            ),
            "value": format_float_repr(
                glom(dossier_dict, "InkomstenVrijlating.WaardeBedrag", default="")
            ),
        },
        "inkomsten_na_vrijlating": {
            "key": "Inkomsten na vrijlating",
            "sign": get_sign(dossier_dict, "InkomstenNaVrijlating.CdPositiefNegatief"),
            "value": format_float_repr(
                glom(dossier_dict, "InkomstenNaVrijlating.WaardeBedrag", default="")
            ),
        },
        "vakantiegeld_over_inkomsten": {
            "key": "Vakantiegeld inkomsten",
            "sign": glom(
                dossier_dict, "VakantiegeldOverInkomsten.CdPositiefNegatief", default=""
            ),
            "value": format_float_repr(
                glom(dossier_dict, "VakantiegeldOverInkomsten.WaardeBedrag", default="")
            ),
        },
        "gekorte_inkomsten": {
            "key": "Totaal gekorte inkomsten",
            "sign": get_sign(dossier_dict, "GekorteInkomsten.CdPositiefNegatief"),
            "value": format_float_repr(
                glom(dossier_dict, "GekorteInkomsten.WaardeBedrag", default="")
            ),
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
def get_jaaropgave_dict(xml_data) -> Optional[dict]:
    xml_data_dict = xml_to_dict(xml_data)

    if not xml_data_dict:
        return None

    BASE = "SOAP-ENV:Envelope.SOAP-ENV:Body.gwsd:JaarOpgaveInfoResponse"

    #
    # Client
    #
    try:
        client_spec = glom(xml_data_dict, BASE + ".JaarOpgaveClient.Client", default="")
    except PathAccessError:
        return None

    client_address_spec = glom(
        xml_data_dict, BASE + ".JaarOpgaveClient.Client.Adres", default=""
    )
    client = {
        "bsn_label": "BSN",
        "bsn": glom(client_spec, "BurgerServiceNr"),
        "naam": format_name(
            glom(client_spec, "Voornamen", default=""),
            glom(client_spec, "Voorvoegsel", default=""),
            glom(client_spec, "Achternaam", default=""),
        ),
        "adres": format_address(
            street_name=glom(client_address_spec, "Straatnaam", default=""),
            house_nr=glom(client_address_spec, "Huisnummer", default=""),
            house_letter=glom(client_address_spec, "Huisletter", default=""),
        ),
        "postcode": glom(client_address_spec, "Postcode", default=""),
        "woonplaatsnaam": glom(client_address_spec, "Woonplaatsnaam", default=""),
        "gemeentenaam": glom(client_address_spec, "Gemeentenaam", default=""),
    }

    #
    # JaarOpgave
    #
    try:
        jaaropgave_spec = glom(
            xml_data_dict, BASE + ".JaarOpgaveClient.JaarOpgave", default=""
        )
    except PathAccessError:
        return None

    # Inhoudingsplichtige
    inhoudingsplichtige_spec = glom(jaaropgave_spec, "Inhoudingsplichtige", default="")
    inhoudingsplichtige = {
        "key": "Inhoudingsplichtige",
        "gemeentenaam": glom(inhoudingsplichtige_spec, "Gemeentenaam", default=""),
        "bezoekadres": glom(inhoudingsplichtige_spec, "Bezoekadres", default=""),
        "postcode": glom(inhoudingsplichtige_spec, "Postcode", default=""),
        "woonplaatsnaam": glom(inhoudingsplichtige_spec, "Woonplaatsnaam", default=""),
    }

    # SpecificatieJaarOpgave
    specificatiejaaropgave_spec = glom(
        jaaropgave_spec, "SpecificatieJaarOpgave", default=""
    )
    jaaropgave = {
        "regeling": glom(specificatiejaaropgave_spec, "Regeling", default=""),
        "dienstjaar": glom(specificatiejaaropgave_spec, "Dienstjaar", default=""),
        "periode": {
            "key": "Tijdvak",
            "van": format_date(
                glom(specificatiejaaropgave_spec, "AangiftePeriodeVan", default="")
            ),
            "tot": format_date(
                glom(specificatiejaaropgave_spec, "AangiftePeriodeTot", default="")
            ),
        },
        "fiscaalloon": {
            "key": "Loon loonbelasting / volksverzekeringen",
            "sign": get_sign(
                specificatiejaaropgave_spec, "Fiscaalloon.CdPositiefNegatief"
            ),
            "value": glom(
                specificatiejaaropgave_spec, "Fiscaalloon.WaardeBedrag", default=""
            ),
        },
        "loonheffing": {
            "key": "Ingehouden Loonbelasting / Premie volksverzekeringen (loonheffing)",
            "sign": get_sign(
                specificatiejaaropgave_spec, "Loonheffing.CdPositiefNegatief"
            ),
            "value": glom(
                specificatiejaaropgave_spec, "Loonheffing.WaardeBedrag", default=""
            ),
        },
        "arbeidskorting": {
            "key": "Verrekende arbeidskorting",
            "value": "0",
        },
        "code_loonbelastingtabel": {
            "key": "Code loonbelastingtabel",
            "value": glom(
                specificatiejaaropgave_spec, "CdPremieVolksverzekering", default=""
            ),
        },
        "vergoeding_premie_zvw": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "VergoedingPremieZVW.CdPositiefNegatief"
            ),
            "value": glom(
                specificatiejaaropgave_spec,
                "VergoedingPremieZVW.WaardeBedrag",
                default="",
            ),
        },
        "loon_zorgverzekeringswet": {
            "key": "Loon Zorgverzekeringswet",
            "value": calculate_loon_zvw(
                glom(
                    specificatiejaaropgave_spec, "Fiscaalloon.WaardeBedrag", default=""
                ),
                glom(
                    specificatiejaaropgave_spec,
                    "VergoedingPremieZVW.WaardeBedrag",
                    default="",
                ),
            ),
        },
        "werkgevers_heffing_premie": {
            "key": "Werkgeversheffing Zorgverzekeringswet",
            "sign": get_sign(
                specificatiejaaropgave_spec,
                "WerkgeversheffingPremieZVW.CdPositiefNegatief",
            ),
            "value": glom(
                specificatiejaaropgave_spec,
                "WerkgeversheffingPremieZVW.WaardeBedrag",
                default="",
            ),
        },
    }

    #
    # update jaaropgave with loon_heffings_korting (list with potentially only one element)
    #
    dates = glom(specificatiejaaropgave_spec, "Loonheffingskorting")

    # normalize `dates`: xmltodict returns a dict or list here, depending on the number of results
    if not isinstance(dates, list):
        dates = [dates]

    # replace dict keys with our own for consistency
    for date in dates:
        date["ingangsdatum"] = format_date(date.pop("Ingangsdatum"))
        date["code"] = date.pop("CdLoonheffingskorting")

    loon_heffings_korting = {
        "loon_heffings_korting": {
            "key": "Loonheffingskorting Met ingang van",
            "code_label": "Code",
            "dates": dates,
        }
    }

    jaaropgave.update(**loon_heffings_korting)

    return {
        "client": client,
        "inhoudingsplichtige": inhoudingsplichtige,
        "jaaropgave": jaaropgave,
    }
