from typing import Any, TypedDict, cast

import requests
import structlog
from lxml import etree  # nosec
from lxml.etree import LxmlError, XMLSyntaxError  # nosec
from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from open_inwoner.ssd.service.jaaropgave.body_reaction_resolved import (
    Inhoudingsplichtige,
    JaarOpgave,
    SpecificatieJaarOpgave,
)

from .exceptions import SSDClientException, SSDServiceFaultException
from .service.jaaropgave import Client, JaarOpgaveInfoResponse
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


logger = structlog.stdlib.get_logger(__name__)


def _get_report_info(
    response: requests.Response,
    info_response_node: str,
    info_type: Any,
) -> JaarOpgaveInfoResponse | UitkeringInfoResponse | None:
    """
    Return the `info_response` (e.g. `JaarOpgaveInfoResponse`) from the request
    response, raise `SSDClientException` if an error occurs

    Note: bandit identifies the use of `lxml.etree.fromstring` as a security issue
    because the parser is vulnerable to certain XML attacks. We count the origin of the
    `response` as a trusted source, hence the warning is considered a false positive
    """
    if not response.content:
        raise SSDClientException("response had no content")

    try:
        tree = etree.fromstring(response.content).getroottree()  # noqa: S320
    except (LxmlError, XMLSyntaxError) as exc:
        raise SSDClientException("error generating XML from content") from exc

    if not (info_node := tree.find(info_response_node)):
        raise SSDClientException(
            "XML node %s not found in response", info_response_node
        )

    parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)

    try:
        info_response = parser.parse(info_node, info_type)
    except ParserError as exc:
        raise SSDClientException("failed to parse XML for %s", info_response) from exc

    # fout, waarschuwing, informatie
    if info_response.fwi:
        raise SSDServiceFaultException.from_xml_response(xml_response=info_response)

    return info_response


class JaaropgaveReturn(TypedDict):
    client: Client
    inhoudingsplichtige: Inhoudingsplichtige
    specificatie: SpecificatieJaarOpgave


def get_jaaropgaven(response: requests.Response) -> list[JaaropgaveReturn] | None:
    """
    Wrapper function: guard against `AttributeError` while fetching Jaaropgave data
    """
    jaaropgave_info = _get_report_info(
        response, JAAROPGAVE_INFO_RESPONSE_NODE, JaarOpgaveInfoResponse
    )
    if jaaropgave_info.niets_gevonden:
        return []

    client = cast(Client, jaaropgave_info.jaar_opgave_client.client)
    jaar_opgave = cast(JaarOpgave, jaaropgave_info.jaar_opgave_client.jaar_opgave[0])
    inhoudingsplichtige = cast(Inhoudingsplichtige, jaar_opgave.inhoudingsplichtige)
    specificatien = cast(
        list[SpecificatieJaarOpgave], jaar_opgave.specificatie_jaar_opgave
    )

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
    if uitkeringen_info.niets_gevonden:
        return []

    uitkeringsspecificatie = (
        uitkeringen_info.uitkerings_specificatie_client.uitkeringsspecificatie[0]
    )
    uitkeringsinstantie = uitkeringsspecificatie.uitkeringsinstantie
    client = uitkeringen_info.uitkerings_specificatie_client.client
    dossierhistorien = uitkeringsspecificatie.dossierhistorie

    return [
        {
            "uitkeringsinstantie": uitkeringsinstantie,
            "client": client,
            "dossierhistorie": historie,
            "details": historie.componenthistorie,
        }
        for historie in dossierhistorien
    ]
