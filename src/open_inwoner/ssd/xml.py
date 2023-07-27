import calendar
from datetime import datetime
from xml.parsers.expat import ExpatError

from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

import xmltodict
from glom import glom


#
# utility functions
#
def calculate_loon_zvw(fiscalloon: str, vergoeding_premie_zvw: str) -> str:
    return str(int(fiscalloon) - int(vergoeding_premie_zvw))


def format_float_repr(value: str) -> str:
    return "{:.2f}".format(float(value) / 100).replace(".", ",")


def format_address(street_name: str, housse_nr: str, house_letter: str) -> str:
    return f"{street_name} {housse_nr} {house_letter}"


def format_date(date_str) -> str:
    return datetime.strptime(date_str, "%Y%m%d").strftime("%d-%m-%Y")


def format_date_month_name(date_str) -> str:
    """Transform '204805' into 'May 2048'"""

    patched = date_str + "01"
    date = datetime.strptime(patched, "%Y%m%d")
    month_name = calendar.month_name[date.month]

    formatted_date = _("{month_name} {year}").format(
        month_name=month_name, year=date.year
    )

    return formatted_date


def format_name(first_name: str, voorvoegsel: str, last_name: str):
    first_names = first_name.split(" ")
    first_name_initials = [name[0] + "." for name in first_names]
    first_name_formatted = " ".join(first_name_initials)

    return f"{first_name_formatted} {voorvoegsel} {last_name}"


def get_sign(base, target) -> str:
    return "-" if glom(base, target) == "-" else ""


def get_column(col_index: str) -> str:
    """Remap magic numbers to meaningful names"""

    if col_index == "1":
        return "plus"
    if col_index == "2":
        return "minus"
    return "base"


def sanitize_date_repr(date_str: str) -> str:
    """
    Transform `date_str` into ISO 8601 compliant format
    """
    patched = date_str + "01"
    return datetime.strptime(patched, "%Y%m%d").strftime("%Y-%m-%d")


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
                glom(client_spec, "Voornamen"),
                glom(client_spec, "Voorvoegsel"),
                glom(client_spec, "Achternaam"),
            ),
        },
        "adres": {
            "key": "Adres",
            "value": format_address(
                glom(client_address_spec, "Straatnaam"),
                glom(client_address_spec, "Huisnummer"),
                glom(client_address_spec, "Huisletter"),
            ),
        },
        "postcode": {
            "key": "Postcode",
            "value": glom(client_address_spec, "Postcode"),
        },
        "woonplaats": {
            "key": "Woonplaats",
            "value": glom(client_address_spec, "Woonplaatsnaam"),
        },
    }

    # dossier needed for the rest of the report
    dossierhistorie_spec = glom(uitkering_specificatie, "Dossierhistorie")
    dossier_dict = dossierhistorie_spec[0]

    #
    # Uitkeringsspeciﬁcatie
    #
    uitkeringsspecificatie = {
        "dossiernummer": {
            "key": "Dossiernummer",
            "value": glom(dossier_dict, "Dossiernummer"),
        },
        "periode": {
            "key": "Periode",
            "value": format_date_month_name(glom(dossier_dict, "Periodenummer")),
        },
        "regeling": {
            "key": "Regeling",
            "value": glom(dossier_dict, "Regeling"),
        },
    }

    #
    # Details
    #
    details = {}
    details_list = glom(dossier_dict, "Componenthistorie")

    for detail_row in details_list:
        # dict keys are slugified to facilitate access in tests
        internal_key = slugify(detail_row["Omschrijving"]).replace("-", "_")
        details[internal_key] = {
            "key": detail_row["Omschrijving"],
            "sign": glom(detail_row, "Bedrag.CdPositiefNegatief"),
            "value": format_float_repr(glom(detail_row, "Bedrag.WaardeBedrag")),
            "column": get_column(glom(detail_row, "IndicatieKolom")),
        }

    #
    # Speciﬁcatie inkomstenkorting
    #
    inkomstenkorting = {
        "opgegeven_inkomsten": {
            "key": "Opgegeven inkomsten",
            "sign": get_sign(dossier_dict, "OpgegevenInkomsten.CdPositiefNegatief"),
            "value": format_float_repr(
                glom(dossier_dict, "OpgegevenInkomsten.WaardeBedrag")
            ),
        },
        "inkomsten_vrijlating": {
            "key": "Inkomsten vrijlating",
            "sign": glom(dossier_dict, "InkomstenVrijlating.CdPositiefNegatief"),
            "value": format_float_repr(
                glom(dossier_dict, "InkomstenVrijlating.WaardeBedrag")
            ),
        },
        "inkomsten_na_vrijlating": {
            "key": "Inkomsten na vrijlating",
            "sign": get_sign(dossier_dict, "InkomstenNaVrijlating.CdPositiefNegatief"),
            "value": format_float_repr(
                glom(dossier_dict, "InkomstenNaVrijlating.WaardeBedrag")
            ),
        },
        "vakantiegeld_over_inkomsten": {
            "key": "Vakantiegeld inkomsten",
            "sign": glom(dossier_dict, "VakantiegeldOverInkomsten.CdPositiefNegatief"),
            "value": format_float_repr(
                glom(dossier_dict, "VakantiegeldOverInkomsten.WaardeBedrag")
            ),
        },
        "gekorte_inkomsten": {
            "key": "Totaal gekorte inkomsten",
            "sign": get_sign(dossier_dict, "GekorteInkomsten.CdPositiefNegatief"),
            "value": format_float_repr(
                glom(dossier_dict, "GekorteInkomsten.WaardeBedrag")
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
        "bsn_label": "BSN",
        "bsn": glom(client_spec, "BurgerServiceNr"),
        "naam": format_name(
            glom(client_spec, "Voornamen"),
            glom(client_spec, "Voorvoegsel"),
            glom(client_spec, "Achternaam"),
        ),
        "adres": f"{glom(client_address_spec, 'Straatnaam')} "
        f"{glom(client_address_spec, 'Huisnummer')} "
        f"{glom(client_address_spec, 'Huisletter')}",
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
        "key": "Inhoudingsplichtige",
        "gemeentenaam": glom(inhoudingsplichtige_spec, "Gemeentenaam"),
        "bezoekadres": glom(inhoudingsplichtige_spec, "Bezoekadres"),
        "postcode": glom(inhoudingsplichtige_spec, "Postcode"),
        "woonplaatsnaam": glom(inhoudingsplichtige_spec, "Woonplaatsnaam"),
    }

    # SpecificatieJaarOpgave
    specificatiejaaropgave_spec = glom(jaaropgave_spec, "SpecificatieJaarOpgave")
    jaaropgave = {
        "regeling": glom(specificatiejaaropgave_spec, "Regeling"),
        "dienstjaar": glom(specificatiejaaropgave_spec, "Dienstjaar"),
        "periode": {
            "key": "Tijdvak",
            "van": format_date(glom(specificatiejaaropgave_spec, "AangiftePeriodeVan")),
            "tot": format_date(glom(specificatiejaaropgave_spec, "AangiftePeriodeTot")),
        },
        "fiscaalloon": {
            "key": "Loon loonbelasting / volksverzekeringen",
            "sign": get_sign(
                specificatiejaaropgave_spec, "Fiscaalloon.CdPositiefNegatief"
            ),
            "value": glom(specificatiejaaropgave_spec, "Fiscaalloon.WaardeBedrag"),
        },
        "loonheffing": {
            "key": "Ingehouden Loonbelasting / Premie volksverzekeringen (loonheffing)",
            "sign": get_sign(
                specificatiejaaropgave_spec, "Loonheffing.CdPositiefNegatief"
            ),
            "value": glom(specificatiejaaropgave_spec, "Loonheffing.WaardeBedrag"),
        },
        # TODO: figure out if this is needed; see below
        "arbeidskorting": {
            "key": "Verrekende arbeidskorting",
            "value": "MYSTERY",
        },
        "code_loonbelastingtabel": {
            "key": "Code loonbelastingtabel",
            "value": glom(specificatiejaaropgave_spec, "CdPremieVolksverzekering"),
        },
        "ingehouden_bijdrage": {
            "key": "Ingehouden bijdrage Zorgverzekeringswet",
            "sign": get_sign(
                specificatiejaaropgave_spec, "IngehoudenPremieZVW.CdPositiefNegatief"
            ),
            "value": glom(
                specificatiejaaropgave_spec, "IngehoudenPremieZVW.WaardeBedrag"
            ),
        },
        "vergoeding_premie_zvw": {
            "sign": get_sign(
                specificatiejaaropgave_spec, "VergoedingPremieZVW.CdPositiefNegatief"
            ),
            "value": glom(
                specificatiejaaropgave_spec, "VergoedingPremieZVW.WaardeBedrag"
            ),
        },
        "loon_zorgverzekeringswet": {
            "key": "Loon Zorgverzekeringswet",
            "value": calculate_loon_zvw(
                glom(specificatiejaaropgave_spec, "Fiscaalloon.WaardeBedrag"),
                glom(specificatiejaaropgave_spec, "VergoedingPremieZVW.WaardeBedrag"),
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
            ),
        },
        # TODO: figure out where this is used; relation to `arbeitskorting`?
        # "belaste_alimentatie": {
        #     "sign": get_sign(
        #         specificatiejaaropgave_spec, "BelasteAlimentatie.CdPositiefNegatief"
        #     ),
        #     "bedrag": (
        #         float(
        #             glom(
        #                 specificatiejaaropgave_spec,
        #                 "BelasteAlimentatie.WaardeBedrag",
        #                 default=0,
        #             )
        #         )
        #         / 100
        #         if glom(
        #             specificatiejaaropgave_spec,
        #             "BelasteAlimentatie.WaardeBedrag",
        #             default=0,
        #         )
        #         else 0
        #     ),
        # },
    }

    #
    # update jaaropgave with loon_heffings_korting (list with potentially only one element)
    #
    date_list = glom(specificatiejaaropgave_spec, "Loonheffingskorting")

    # replace dict keys with our own for consistency
    for date in date_list:
        date["ingangsdatum"] = format_date(date.pop("Ingangsdatum"))
        date["code"] = date.pop("CdLoonheffingskorting")

    loon_heffings_korting = {
        "loon_heffings_korting": {
            "key": "Loonheffingskorting Met ingang van",
            "code_label": "Code",
            "dates": date_list,
        }
    }

    jaaropgave.update(**loon_heffings_korting)

    return {
        "client": client,
        "inhoudingsplichtige": inhoudingsplichtige,
        "jaaropgave": jaaropgave,
    }
