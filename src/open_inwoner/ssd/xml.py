from typing import Any, Optional, Union

import requests
from lxml import etree
from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from .service.jaaropgave import JaarOpgaveInfoResponse
from .service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)

JAAROPGAVE_INFO_RESPONSE_NODE = "//{http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400}" "JaarOpgaveInfoResponse"

UITKERING_INFO_RESPONSE_NODE = (
    "//{http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600}" "UitkeringsSpecificatieInfoResponse"
)


def _get_report_info(
    response: requests.Response,
    info_response_node: str,
    info_type: Any,
) -> Optional[Union[JaarOpgaveInfoResponse, UitkeringInfoResponse]]:
    """
    :returns: the `info_type` (e.g. JaarOpgaveInfoResponse) from
        the request response, or `None` if a parsing error occurs
    """
    tree = etree.fromstring(response.content)
    node = tree.find(info_response_node)
    parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)

    try:
        info = parser.parse(node, info_type)
    except ParserError:
        return None
    return info


def get_jaaropgaven(response: requests.Response) -> Optional[list[dict]]:
    jaaropgave_info = _get_report_info(response, JAAROPGAVE_INFO_RESPONSE_NODE, JaarOpgaveInfoResponse)

    if not jaaropgave_info or not isinstance(jaaropgave_info, JaarOpgaveInfoResponse):
        return None

    try:
        client = jaaropgave_info.jaar_opgave_client.client
        inhoudingsplichtige = jaaropgave_info.jaar_opgave_client.jaar_opgave[0].inhoudingsplichtige
        specificatien = jaaropgave_info.jaar_opgave_client.jaar_opgave[0].specificatie_jaar_opgave
    except AttributeError:
        return None

    jaaropgaven = []
    for specificatie in specificatien:
        jaaropgaven.append(
            {
                "client": client,
                "inhoudingsplichtige": inhoudingsplichtige,
                "specificatie": specificatie,
            }
        )
    return jaaropgaven


def get_uitkeringen(response: requests.Response) -> Optional[list[dict]]:
    uitkeringen_info = _get_report_info(response, UITKERING_INFO_RESPONSE_NODE, UitkeringInfoResponse)

    if not uitkeringen_info or not isinstance(uitkeringen_info, UitkeringInfoResponse):
        return None

    # fmt: off
    try:
        uitkeringsinstantie = uitkeringen_info.uitkerings_specificatie_client\
                                              .uitkeringsspecificatie[0]\
                                              .uitkeringsinstantie
        client = uitkeringen_info.uitkerings_specificatie_client.client
        dossierhistorien = uitkeringen_info.uitkerings_specificatie_client.uitkeringsspecificatie[0].dossierhistorie
    except AttributeError:
        return None

    uitkeringen = []
    for historie in dossierhistorien:
        uitkeringen.append(
            {
                "uitkeringsinstantie": uitkeringsinstantie,
                "client": client,
                "dossierhistorie": historie,
                "details": historie.componenthistorie,
            }
        )
    return uitkeringen
