from pathlib import Path
from typing import Any

from lxml import etree
from requests import Response
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from ..service.uitkering import (
    Dossierhistorie,
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)
from .utils import format_date_month_name, format_string

UITKERING_INFO_RESPONSE_NODE = "//{http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600}UitkeringsSpecificatieInfoResponse"


# TODO: remove
path1 = (
    Path(__file__).parent.parent / "tests" / "files" / "uitkering_response_basic.xml"
)
path2 = (
    Path(__file__).parent.parent
    / "tests"
    / "files"
    / "uitkering_response_extra_report.xml"
)
path3 = (
    Path(__file__).parent.parent
    / "tests"
    / "files"
    / "uitkering_response_extra_report2.xml"
)


# TODO: remove
def get_uitkering_data(path):
    with open(path, "rb") as f:
        tree = etree.parse(f)
        node = tree.find(UITKERING_INFO_RESPONSE_NODE)
        parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
        res = parser.parse(node, UitkeringInfoResponse)
    return res


def _get_uitkering_info(response: Response):
    tree = etree.fromstring(response.content)
    node = tree.find(UITKERING_INFO_RESPONSE_NODE)
    parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
    info = parser.parse(node, UitkeringInfoResponse)
    return info


def _get_uitkering_instantie(data: UitkeringInfoResponse) -> dict[str, str]:
    uitkerings_instantie = data.uitkerings_specificatie_client.uitkeringsspecificatie[
        0
    ].uitkeringsinstantie

    return {
        "gemeentenaam": uitkerings_instantie.gemeentenaam,
        "bezoekadres": uitkerings_instantie.bezoekadres,
        "postcode": uitkerings_instantie.postcode,
        "woonplaatsnaam": uitkerings_instantie.woonplaatsnaam,
    }


def _get_uitkering_client(data: UitkeringInfoResponse):
    client_data = data.uitkerings_specificatie_client.client
    client_adress = client_data.adres

    return {
        "bsn": client_data.burger_service_nr,
        "naam": format_string(
            client_data.voorletters,
            client_data.voorvoegsel,
            client_data.achternaam,
        ),
        "adres": format_string(
            client_adress.straatnaam,
            client_adress.huisnummer,
            client_adress.huisletter,
        ),
        "postcode": format_string(client_adress.postcode),
        "woonplaats": format_string(client_adress.woonplaatsnaam),
    }


def _get_uitkering_specificatie(dossierhistorie: Dossierhistorie) -> dict[str, str]:
    return {
        "dossiernummer": dossierhistorie.dossiernummer,
        "periode": format_date_month_name(dossierhistorie.periodenummer),
        "regeling": dossierhistorie.regeling,
    }


def _get_uitkering_inkomstenkorting(
    dossierhistorie: Dossierhistorie,
) -> dict[str, dict[str, Any]]:
    """
    Return the 'specificatie inkomstenkorting', depending on the type of report

    Note: for the extra report (vakantiegeld) sent out in may, the fields are empty.
    A uniform approach with `getattr` is adopted to facilitate data retrieval in the
    template.
    """
    return {
        "opgegeven_inkomsten": {
            "key": "Opgegeven inkomsten",
            "value": getattr(dossierhistorie.opgegeven_inkomsten, "waarde_bedrag", "0"),
            "sign": "",
        },
        "inkomsten_vrijlating": {
            "key": "Inkomsten vrijlating",
            "value": getattr(
                dossierhistorie.inkomsten_vrijlating, "waarde_bedrag", "0"
            ),
            "sign": "-",
        },
        "inkomsten_na_vrijlating": {
            "key": "Inkomsten vrijlating",
            "value": getattr(
                dossierhistorie.inkomsten_na_vrijlating, "waarde_bedrag", "0"
            ),
            "sign": "",
        },
        "vakantiegeld_over_inkomsten": {
            "key": "Inkomsten vrijlating",
            "value": getattr(
                dossierhistorie.vakantiegeld_over_inkomsten, "waarde_bedrag", "0"
            ),
            "sign": "+",
        },
        "gekorte_inkomsten": {
            "key": "Inkomsten vrijlating",
            "value": getattr(dossierhistorie.gekorte_inkomsten, "waarde_bedrag", "0"),
            "sign": "",
        },
    }


def get_uitkeringen(response: Response) -> list[dict]:
    """
    Return a `list` of maandspecificatie reports for a given SOAP response.

    The `uitkeringsinstantie` and `client` details are retrieved once, the
    `uitkeringsinstantie` and details are retrieved separately for every
    `dossierhistorie`.
    """
    # uitkeringen_info = _get_uitkering_info(response)
    uitkeringen_info = get_uitkering_data(path2)

    uitkeringsinstantie = _get_uitkering_instantie(uitkeringen_info)
    client = _get_uitkering_client(uitkeringen_info)
    dossierhistorien = (
        uitkeringen_info.uitkerings_specificatie_client.uitkeringsspecificatie[
            0
        ].dossierhistorie
    )

    uitkeringen = []
    for historie in dossierhistorien:
        uitkering = {
            "uitkeringsinstantie": uitkeringsinstantie,
            "client": client,
            "uitkeringsspecificatie": _get_uitkering_specificatie(historie),
            "details": historie.componenthistorie,
            "inkomstenkorting": _get_uitkering_inkomstenkorting(historie),
        }
        uitkeringen.append(uitkering)

    return uitkeringen
