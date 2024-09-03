from lxml import etree
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from open_inwoner.conf.base import DJANGO_PROJECT_DIR
from open_inwoner.ssd.service.jaaropgave import JaarOpgaveInfoResponse
from open_inwoner.ssd.service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)

FILES_DIR = f"{DJANGO_PROJECT_DIR}/ssd/tests/files"


def mock_get_uitkeringen():
    uitkering_path = f"{FILES_DIR}/uitkering_response_basic.xml"
    uitkering_path = f"{FILES_DIR}/uitkering_response_extra_report.xml"
    UITKERING_INFO_RESPONSE_NODE = (
        "//{http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600}"
        "UitkeringsSpecificatieInfoResponse"
    )
    with open(uitkering_path, "rb") as f:
        tree = etree.parse(f)
        node = tree.find(UITKERING_INFO_RESPONSE_NODE)
        parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
        info = parser.parse(node, UitkeringInfoResponse)

    uitkeringsinstantie = info.uitkerings_specificatie_client.uitkeringsspecificatie[
        0
    ].uitkeringsinstantie
    client = info.uitkerings_specificatie_client.client
    dossierhistorien = info.uitkerings_specificatie_client.uitkeringsspecificatie[
        0
    ].dossierhistorie
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


def mock_get_jaaropgaven():
    jaaropgave_path = f"{FILES_DIR}/jaaropgave_response.xml"
    # jaaropgave_path = FILES_DIR / "jaaropgave_response_extra_spec.xml"
    JAAROPGAVE_INFO_RESPONSE_NODE = (
        "//{http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400}"
        "JaarOpgaveInfoResponse"
    )
    with open(jaaropgave_path, "rb") as f:
        tree = etree.parse(f)
        node = tree.find(JAAROPGAVE_INFO_RESPONSE_NODE)
        parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
        info = parser.parse(node, JaarOpgaveInfoResponse)

        client = info.jaar_opgave_client.client
        inhoudingsplichtige = info.jaar_opgave_client.jaar_opgave[0].inhoudingsplichtige
        specificatien = info.jaar_opgave_client.jaar_opgave[0].specificatie_jaar_opgave

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
