from typing import Any

import requests
from lxml import etree  # nosec
from lxml.etree import LxmlError, XMLSyntaxError  # nosec
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
) -> JaarOpgaveInfoResponse | UitkeringInfoResponse | None:
    """
    Return the `info_type` (e.g. JaarOpgaveInfoResponse) from the request
    response, or `None` if a parsing error occurs

    Note: bandit identifies the use of `lxml.etree.fromstring` as a security issue
    because the parser is vulnerable to certain XML attacks. We count the origin of the
    `response` as a trusted source, hence the warning is considered a false positive
    """
    if not response.content:
        return None

    try:
        tree = etree.fromstring(response.content).getroottree()
        node = tree.find(info_response_node)
    except (LxmlError, XMLSyntaxError):
        return None

    parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)

    try:
        info = parser.parse(node, info_type)
    except ParserError:
        return None

    return info


def get_jaaropgaven(response: requests.Response) -> list[dict] | None:
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
        jaar_opgave = jaaropgave_info.jaar_opgave_client.jaar_opgave[0]
        inhoudingsplichtige = jaar_opgave.inhoudingsplichtige
        specificatien = jaar_opgave.specificatie_jaar_opgave
    except AttributeError:
        return None

    return [
        {
            "client": client,
            "inhoudingsplichtige": inhoudingsplichtige,
            "specificatie": specificatie,
        }
        for specificatie in specificatien
    ]


def get_uitkeringen(response: requests.Response) -> list[dict] | None:
    """
    Wrapper function: guard against `AttributeError` while fetching uitkering data
    """
    uitkeringen_info = _get_report_info(
        response, UITKERING_INFO_RESPONSE_NODE, UitkeringInfoResponse
    )

    if not uitkeringen_info or not isinstance(uitkeringen_info, UitkeringInfoResponse):
        return None

    try:
        uitkeringsspecificatie = (
            uitkeringen_info.uitkerings_specificatie_client.uitkeringsspecificatie[0]
        )
        uitkeringsinstantie = uitkeringsspecificatie.uitkeringsinstantie
        client = uitkeringen_info.uitkerings_specificatie_client.client
        dossierhistorien = uitkeringsspecificatie.dossierhistorie
    except AttributeError:
        return None

    return [
        {
            "uitkeringsinstantie": uitkeringsinstantie,
            "client": client,
            "dossierhistorie": historie,
            "details": historie.componenthistorie,
        }
        for historie in dossierhistorien
    ]
