from pathlib import Path

from lxml import etree
from requests import Response
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from ..service.jaaropgave import JaarOpgaveInfoResponse
from ..service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)

# TODO: remove
path1 = Path(__file__).parent.parent / "tests" / "files" / "jaaropgave_response.xml"
path2 = Path(__file__).parent.parent / "tests" / "files" / "jaaropgave_response_extra_spec.xml"


def get_jaaropgave_data(path, info_type):
    with open(path, "rb") as f:
        tree = etree.parse(f)
        node = tree.find(JAAROPGAVE_INFO_RESPONSE_NODE)
        parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
        res = parser.parse(node, info_type)
    return res


JAAROPGAVE_INFO_RESPONSE_NODE = "//{http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400}JaarOpgaveInfoResponse"


# fmt: off
def get_jaaropgaven(response: Response) -> list[dict]:
    jaaropgave_info = get_jaaropgave_data(path2, JaarOpgaveInfoResponse)

    client = jaaropgave_info.jaar_opgave_client.client
    inhoudingsplichtige = jaaropgave_info.jaar_opgave_client\
                                         .jaar_opgave[0]\
                                         .inhoudingsplichtige
    specificatien = jaaropgave_info.jaar_opgave_client\
                                   .jaar_opgave[0]\
                                   .specificatie_jaar_opgave
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
