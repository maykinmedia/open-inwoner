# fmt: off

from typing import Any, Optional, Union

import requests
from lxml import etree  # nosec
from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from .service.jaaropgave import JaarOpgaveInfoResponse
from .service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)

JAAROPGAVE_INFO_RESPONSE_NODE = (
    "//{http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400}"
    "JaarOpgaveInfoResponse"
)

UITKERING_INFO_RESPONSE_NODE = (
    "//{http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600}"
    "UitkeringsSpecificatieInfoResponse"
)


def _get_report_info(
    response: requests.Response,
    info_response_node: str,
    info_type: Any,
) -> Optional[Union[JaarOpgaveInfoResponse, UitkeringInfoResponse]]:
    """
    Return the `info_type` (e.g. JaarOpgaveInfoResponse) from the request
    response, or `None` if a parsing error occurs

    Note: bandit identifies the use of `lxml.etree.fromstring` as a security issue
    because the parser is vulnerable to certain XML attacks. We count the origin of the
    `response` as a trusted source, hence the warning is considered a false positive
    """
    if not response.content:
        return None

    tree = etree.fromstring(response.content)
    node = tree.find(info_response_node)
    parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)

    try:
        info = parser.parse(node, info_type)
    except ParserError:
        return None
    return info


def get_jaaropgaven(response: requests.Response) -> Optional[list[dict]]:
    """
    Wrapper function: guard against `AttributeError` while fetching Jaaropgave data
    """
    jaaropgave_info = _get_report_info(
        response, JAAROPGAVE_INFO_RESPONSE_NODE, JaarOpgaveInfoResponse
    )

    if not jaaropgave_info or not isinstance(jaaropgave_info, JaarOpgaveInfoResponse):
        return None

    try:
        client = jaaropgave_info.jaar_opgave_client.client
        inhoudingsplichtige = jaaropgave_info.jaar_opgave_client.jaar_opgave[
            0
        ].inhoudingsplichtige
        specificatien = jaaropgave_info.jaar_opgave_client.jaar_opgave[
            0
        ].specificatie_jaar_opgave
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
    """
    Wrapper function: guard against `AttributeError` while fetching uitkering data
    """
    uitkeringen_info = _get_report_info(
        response, UITKERING_INFO_RESPONSE_NODE, UitkeringInfoResponse
    )

    if not uitkeringen_info or not isinstance(uitkeringen_info, UitkeringInfoResponse):
        return None

    try:
        uitkeringsinstantie = uitkeringen_info.uitkerings_specificatie_client\
                                              .uitkeringsspecificatie[0]\
                                              .uitkeringsinstantie
        client = uitkeringen_info.uitkerings_specificatie_client.client
        dossierhistorien = uitkeringen_info.uitkerings_specificatie_client\
                                           .uitkeringsspecificatie[0]\
                                           .dossierhistorie
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
