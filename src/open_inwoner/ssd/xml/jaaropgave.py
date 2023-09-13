from lxml import etree
from pathlib import Path
from typing import Union

from requests import Response
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from ..service.jaaropgave import JaarOpgaveInfoResponse
from .utils import calculate_loon_zvw, format_period, format_string, get_sign


JAAROPGAVE_INFO_RESPONSE_NODE = \
    "//{http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400}JaarOpgaveInfoResponse"


# TODO: remove
def get_jaaropgave_data():
    path = Path(__file__).parent.parent / "tests" / "files" / "jaaropgave_response.xml"
    with open(path, "rb") as f:
        tree = etree.parse(f)
        node = tree.find(JAAROPGAVE_INFO_RESPONSE_NODE)
        parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
        res = parser.parse(node, JaarOpgaveInfoResponse)
    return res


def _get_jaaropgave_info(response: Response) -> JaarOpgaveInfoResponse:
    tree = etree.fromstring(response.content)
    node = tree.find(JAAROPGAVE_INFO_RESPONSE_NODE)
    parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
    info = parser.parse(node, JaarOpgaveInfoResponse)
    return info


def _get_client(data: JaarOpgaveInfoResponse):
    client_data = data.jaar_opgave_client.client
    client_adress = client_data.adres

    client = {
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
        "postcode": client_adress.postcode,
        "woonplaatsnaam": format_string(client_adress.woonplaatsnaam),
        "gemeentenaam": format_string(client_adress.gemeentenaam),
    }

    return client


def _get_inhoudingsplichtige(data: JaarOpgaveInfoResponse):
    jaaropgaven = data.jaar_opgave_client.jaar_opgave
    jaaropgave = jaaropgaven[0]

    inhoudingsplichtige = jaaropgave.inhoudingsplichtige

    return inhoudingsplichtige


def _get_specificatie(data: JaarOpgaveInfoResponse) -> dict[str, Union[int, str, dict, list[dict]]]:
    jaaropgaven = data.jaar_opgave_client.jaar_opgave
    jaaropgave = jaaropgaven[0]

    specificatien = jaaropgave.specificatie_jaar_opgave
    spec = specificatien[0]

    res = {
        "dienstjaar": spec.dienstjaar,
        "fiscaalloon": {
            "sign": get_sign(spec.fiscaalloon.cd_positief_negatief),
            "value": str(spec.fiscaalloon.waarde_bedrag),
        },
        "loonheffing": {
            "sign": get_sign(spec.loonheffing.cd_positief_negatief),
            "value": spec.loonheffing.waarde_bedrag,
        },
        "loonheffingskorting": [
            {
                "ingangsdatum": format_period(loonheffingskorting.ingangsdatum),
                "code": loonheffingskorting.cd_loonheffingskorting,
            }
            for loonheffingskorting in spec.loonheffingskorting
        ],
        "loon_zorgverzekeringswet": calculate_loon_zvw(
            spec.fiscaalloon.waarde_bedrag, spec.vergoeding_premie_zvw.waarde_bedrag
        ),
        "periode_van": format_period(spec.aangifte_periode_van),
        "periode_tot": format_period(spec.aangifte_periode_tot),
        "werkgevers_heffing_premie": spec.werkgeversheffing_premie_zvw.waarde_bedrag,
        "code_loonbelastingtabel": spec.cd_premie_volksverzekering,
    }

    return res


def get_jaaropgave(response: Response) -> dict:
    # jaaropgave_info = _get_jaaropgave_info(response)
    jaaropgave_info = get_jaaropgave_data()

    return {
        "client": _get_client(jaaropgave_info),
        "inhoudingsplichtige": _get_inhoudingsplichtige(jaaropgave_info),
        "specificatie": _get_specificatie(jaaropgave_info),
    }
