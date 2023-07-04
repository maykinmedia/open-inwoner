import datetime
from xml.parsers.expat import ExpatError

import xmltodict
from glom import glom


def xml_to_dict(xml_data):
    try:
        return xmltodict.parse(xml_data)
    except ExpatError:
        return {}


def format_date(date_str):
    return datetime.datetime.strptime(date_str, "%Y%m%d").strftime("%d-%m-%Y")


def get_uitkering_dict(xml_data):
    xml_data_dict = xml_to_dict(xml_data)

    if not xml_data_dict:
        return {}

    uitkering_specificatie = glom(
        xml_data_dict,
        "SOAP-ENV:Envelope.SOAP-ENV:Body.gwsd:UitkeringsSpecificatieInfoResponse.UitkeringsSpecificatieClient.Uitkeringsspecificatie",
    )

    # Uitkeringsinstatie
    uitkeringsinstatie_spec = glom(uitkering_specificatie, "Uitkeringsinstantie")

    gemeentenaam = glom(uitkeringsinstatie_spec, "Gemeentenaam")
    bezoekadres = glom(uitkeringsinstatie_spec, "Bezoekadres")
    postcode = glom(uitkeringsinstatie_spec, "Postcode")
    woonplaatsnaam = glom(uitkeringsinstatie_spec, "Woonplaatsnaam")

    # Client
    client_spec = glom(
        xml_data_dict,
        "SOAP-ENV:Envelope.SOAP-ENV:Body.gwsd:UitkeringsSpecificatieInfoResponse.UitkeringsSpecificatieClient.Client",
    )
    client_address_spec = glom(client_spec, "Adres")

    burgerservicenr = glom(client_spec, "BurgerServiceNr")
    voornamen = glom(client_spec, "Voornamen")
    voorvoegsel = glom(client_spec, "Voorvoegsel")
    achternaam = glom(client_spec, "Achternaam")
    straatnaam = glom(client_address_spec, "Straatnaam")
    client_postcode = glom(client_address_spec, "Postcode")
    client_woonplaatsnaam = glom(client_address_spec, "Woonplaatsnaam")

    # Uitkeringsspeciﬁcatie
    dossierhistorie_spec = glom(uitkering_specificatie, "Dossierhistorie")
    dossier = {}

    dossier_dict = dossierhistorie_spec[0]
    dossiernummer = glom(dossier_dict, "Dossiernummer")
    periodenummer = glom(dossier_dict, "Periodenummer")
    regeling = glom(dossier_dict, "Regeling")
    dossier.update(
        {
            "dossiernummer": dossiernummer,
            "periodenummer": periodenummer,
            "regeling": regeling,
        }
    )

    # Details
    details_list = glom(dossier_dict, "Componenthistorie")
    for detail_row in details_list:
        dossier[detail_row["Omschrijving"]] = {
            "positive_negative": glom(detail_row, "Bedrag.CdPositiefNegatief"),
            "amount": (
                float(glom(detail_row, "Bedrag.WaardeBedrag")) / 100
                if glom(detail_row, "Bedrag.WaardeBedrag")
                else 0
            ),
            "column": glom(detail_row, "IndicatieKolom"),
        }

    # Speciﬁcatie inkomstenkorting
    dossier["inkomstenkorting"] = {
        "OpgegevenInkomsten_pos_neg": glom(
            dossier_dict, "OpgegevenInkomsten.CdPositiefNegatief", default=""
        ),
        "OpgegevenInkomsten_amount": (
            float(glom(dossier_dict, "OpgegevenInkomsten.WaardeBedrag", default=0))
            / 100
            if glom(dossier_dict, "OpgegevenInkomsten.WaardeBedrag", default=0)
            else 0.0
        ),
        "InkomstenVrijlating_pos_neg": glom(
            dossier_dict, "InkomstenVrijlating.CdPositiefNegatief", default=""
        ),
        "InkomstenVrijlating_amount": (
            float(glom(dossier_dict, "InkomstenVrijlating.WaardeBedrag", default=0))
            / 100
            if glom(dossier_dict, "InkomstenVrijlating.WaardeBedrag", default=0)
            else 0.0
        ),
        "InkomstenNaVrijlating_pos_neg": glom(
            dossier_dict, "InkomstenNaVrijlating.CdPositiefNegatief", default=""
        ),
        "InkomstenNaVrijlating_amount": (
            float(glom(dossier_dict, "InkomstenNaVrijlating.WaardeBedrag", default=0))
            / 100
            if glom(dossier_dict, "InkomstenNaVrijlating.WaardeBedrag", default=0)
            else 0.0
        ),
        "VakantiegeldOverInkomsten_pos_neg": glom(
            dossier_dict, "VakantiegeldOverInkomsten.CdPositiefNegatief", default=""
        ),
        "VakantiegeldOverInkomsten_amount": (
            float(
                glom(
                    dossier_dict,
                    "InkomstenNaVakantiegeldOverInkomstenVrijlating.WaardeBedrag",
                    default=0,
                )
            )
            / 100
            if glom(dossier_dict, "VakantiegeldOverInkomsten.WaardeBedrag", default=0)
            else 0.0
        ),
        "GekorteInkomsten_pos_neg": glom(
            dossier_dict, "GekorteInkomsten.CdPositiefNegatief", default=""
        ),
        "GekorteInkomstenamount": (
            float(glom(dossier_dict, "GekorteInkomsten.WaardeBedrag", default=0)) / 100
            if glom(dossier_dict, "VakantiegeldOverInkomsten.WaardeBedrag", default=0)
            else 0.0
        ),
    }

    return {
        "gemeentenaam": gemeentenaam,
        "bezoekadres": bezoekadres,
        "postcode": postcode,
        "woonplaatsnaam": woonplaatsnaam,
        "burgerservicenr": burgerservicenr,
        "voornamen": voornamen,
        "voorvoegsel": voorvoegsel,
        "achternaam": achternaam,
        "straatnaam": straatnaam,
        "client_postcode": client_postcode,
        "client_woonplaatsnaam": client_woonplaatsnaam,
        "dossier": dossier,
    }


def get_jaaropgave_dict(xml_data):
    xml_data_dict = xml_to_dict(xml_data)

    if not xml_data_dict:
        return {}

    # Client
    client_spec = glom(
        "SOAP-ENV:Envelope.SOAP-ENV:Body.gwsd:JaarOpgaveInfoResponse.JaarOpgaveClient.Client"
    )
    client_address_spec = glom(client_spec, "Adres")

    burgerservicenr = glom(client_spec, "BurgerServiceNr")
    voornamen = glom(client_spec, "Voornamen")
    voorvoegsel = glom(client_spec, "Voorvoegsel")
    achternaam = glom(client_spec, "Achternaam")
    straatnaam = glom(client_address_spec, "Straatnaam")
    client_postcode = glom(client_address_spec, "Postcode")
    client_woonplaatsnaam = glom(client_address_spec, "Woonplaatsnaam")

    # Inhoudingsplichtige
    jaaropgave_spec = glom(
        "SOAP-ENV:Envelope.SOAP-ENV:Body.gwsd:JaarOpgaveInfoResponse.JaarOpgaveClient.JaarOpgave"
    )
    inhoudingsplichtige_spec = glom(jaaropgave_spec, "Inhoudingsplichtige")

    gemeentenaam = glom(jaaropgave_spec, "Gemeentenaam")
    bezoekadres = glom(jaaropgave_spec, "Bezoekadres")
    postcode = glom(jaaropgave_spec, "Postcode")
    woonplaatsnaam = glom(jaaropgave_spec, "Woonplaatsnaam")

    # SpecificatieJaarOpgave
    specificatiejaaropgave_spec = glom(jaaropgave_spec, "SpecificatieJaarOpgave")

    regeling = glom(specificatiejaaropgave_spec, "Regeling")
    fiscaalloon_pos_neg = (
        "-"
        if glom(specificatiejaaropgave_spec, "Fiscaalloon.CdPositiefNegatief") == "-"
        else ""
    )
    fiscaalloon = (
        float(glom(specificatiejaaropgave_spec, "Fiscaalloon.WaardeBedrag", default=0))
        / 100
        if glom(specificatiejaaropgave_spec, "Fiscaalloon.WaardeBedrag", default=0)
        else 0
    )
    loonheffing_pos_neg = (
        "-"
        if glom(specificatiejaaropgave_spec, "Loonheffing.CdPositiefNegatief") == "-"
        else ""
    )
    loonheffing = (
        float(glom(specificatiejaaropgave_spec, "Loonheffing.WaardeBedrag", default=0))
        / 100
        if glom(specificatiejaaropgave_spec, "Loonheffing.WaardeBedrag", default=0)
        else 0
    )
    ingangsdatum = format_date(
        glom(specificatiejaaropgave_spec, "Loonheffingskorting.Ingangsdatum")
    )
    cdloonheffingskorting = glom(
        specificatiejaaropgave_spec, "Loonheffingskorting.CdLoonheffingskorting"
    )

    # In case we have multiple rows
    if glom(specificatiejaaropgave_spec, "Loonheffingskorting[2]", default=""):
        ingangsdatum_2 = format_date(
            glom(
                specificatiejaaropgave_spec,
                "Loonheffingskorting[2].Ingangsdatum",
                default="",
            )
        )
        cdloonheffingskorting_2 = glom(
            specificatiejaaropgave_spec,
            "Loonheffingskorting[2].CdLoonheffingskorting",
            default="",
        )
    if glom(specificatiejaaropgave_spec, "Loonheffingskorting[3]", default=""):
        ingangsdatum_3 = format_date(
            glom(
                specificatiejaaropgave_spec,
                "Loonheffingskorting[3].Ingangsdatum",
                default="",
            )
        )
        cdloonheffingskorting_3 = glom(
            specificatiejaaropgave_spec,
            "Loonheffingskorting[3].CdLoonheffingskorting",
            default="",
        )
    # TODO
    # Add the rest of the required fields in the report

    return
